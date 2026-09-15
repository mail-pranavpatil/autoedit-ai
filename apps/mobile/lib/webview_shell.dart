import 'dart:async';
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:webview_flutter/webview_flutter.dart';

import 'app_config.dart';
import 'download_queue.dart';
import 'native_upload.dart';

/// A bare WebView can't do four things the hosted web app needs:
///   1. Google OAuth - Google rejects its consent screen inside an embedded
///      webview ("disallowed_useragent"). Run it in an external auth session
///      (ASWebAuthenticationSession on iOS) and inject the returned session
///      token as the `autoedit_session` cookie.
///   2. File downloads - `GET /api/videos/{id}/download` sends
///      `Content-Disposition: attachment`, which WKWebView ignores. Fetch it
///      ourselves and hand it to the share sheet (see [DownloadQueue]).
///   3. External links (e.g. a YouTube watch URL) - open in Safari instead of
///      replacing the app's webview.
///   4. Picking footage from Photos/Files - the web page can't reach the
///      native picker UI on its own, so it calls the `ErenNative` JS channel
///      and we upload the result (see [NativeUpload]).
class WebViewShell extends StatefulWidget {
  const WebViewShell({super.key});

  @override
  State<WebViewShell> createState() => _WebViewShellState();
}

/// What to do with a pending navigation - pulled out of the widget as a pure
/// function of (url, appHost) so the routing rules are unit-testable without
/// a live WebViewController.
enum NavigationAction { authDivert, download, externalLink, allow }

final RegExp _downloadPath = RegExp(r'^/api/videos/[^/]+/download$');

NavigationAction classifyNavigation(Uri uri, String appHost) {
  // Google's own consent host, or our OAuth entry point (the web login
  // button navigates to /api/auth/google).
  if (uri.host == 'accounts.google.com' || uri.path.startsWith('/api/auth/google')) {
    return NavigationAction.authDivert;
  }
  if (_downloadPath.hasMatch(uri.path)) {
    return NavigationAction.download;
  }
  // Anything off our origin over http(s) -> system browser.
  if ((uri.scheme == 'http' || uri.scheme == 'https') && uri.host != appHost) {
    return NavigationAction.externalLink;
  }
  return NavigationAction.allow;
}

class _WebViewShellState extends State<WebViewShell> {
  late final WebViewController _controller;
  final _downloads = DownloadQueue();
  final _uploads = NativeUpload();

  @override
  void initState() {
    super.initState();
    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setBackgroundColor(const Color(0xFF0F1115))
      ..setNavigationDelegate(NavigationDelegate(onNavigationRequest: _onNavigationRequest))
      ..addJavaScriptChannel('ErenNative', onMessageReceived: (m) => unawaited(_onNativeMessage(m.message)))
      ..loadRequest(serverUri);
  }

  /// The web page's Create flow posts `{type: "pickVideo", source, projectId}`
  /// when the user taps "Choose from Photos/Files"; `window.ErenNative` being
  /// defined is also how the web page knows to offer that option at all.
  Future<void> _onNativeMessage(String raw) async {
    Map<String, dynamic> payload;
    try {
      payload = jsonDecode(raw) as Map<String, dynamic>;
    } catch (_) {
      return;
    }
    if (payload['type'] != 'pickVideo') return;
    final projectId = payload['projectId'] as String?;
    if (projectId == null) return;
    final result = await _uploads.pickAndUpload(
      projectId: projectId,
      fromFiles: payload['source'] == 'files',
      cookieHeader: _cookieHeader,
    );
    await _controller.runJavaScript(
      'window.onErenNativeUpload && window.onErenNativeUpload(${jsonEncode(result)})',
    );
  }

  Future<NavigationDecision> _onNavigationRequest(NavigationRequest request) async {
    final uri = Uri.tryParse(request.url);
    if (uri == null) return NavigationDecision.navigate;

    switch (classifyNavigation(uri, appHost)) {
      case NavigationAction.authDivert:
        unawaited(_startAuthSession());
        return NavigationDecision.prevent;
      case NavigationAction.download:
        final cookieHeader = await _cookieHeader();
        _downloads.enqueue(uri, cookieHeader);
        return NavigationDecision.prevent;
      case NavigationAction.externalLink:
        unawaited(launchUrl(uri, mode: LaunchMode.externalApplication));
        return NavigationDecision.prevent;
      case NavigationAction.allow:
        return NavigationDecision.navigate;
    }
  }

  Future<String?> _cookieHeader() async {
    final cookies = await WebViewCookieManager().getCookies(domain: serverUri);
    if (cookies.isEmpty) return null;
    return cookies.map((c) => '${c.name}=${c.value}').join('; ');
  }

  // Currently dead code - WebViewShell has no caller anywhere in the app -
  // but kept correct rather than left stale, in case it's revived. Login is
  // Supabase Auth now (see features/auth/services/auth_service.dart); this
  // mirrors the same signInWithOAuth + onAuthStateChange pattern used there,
  // then hands the resulting access token to the WebView as a cookie so
  // apps/web (which mirrors its own session into the same cookie name - see
  // apps/web/components/providers.tsx) picks it up on reload.
  Future<void> _startAuthSession() async {
    final auth = Supabase.instance.client.auth;
    final completer = Completer<void>();
    late final StreamSubscription<AuthState> sub;
    sub = auth.onAuthStateChange.listen((state) {
      if (state.event == AuthChangeEvent.signedIn && !completer.isCompleted) {
        completer.complete();
      }
    });
    try {
      await auth.signInWithOAuth(OAuthProvider.google, redirectTo: '$authScheme://login-callback');
      await completer.future.timeout(const Duration(minutes: 2));
      final token = auth.currentSession?.accessToken;
      if (token == null) return;
      // ponytail: webview_flutter's WebViewCookie has no secure/httpOnly/expiry
      // knobs (unlike the native HTTPCookie the old Capacitor plugin used) -
      // fine for a same-origin https session cookie, revisit if that changes.
      await WebViewCookieManager().setCookie(
        WebViewCookie(name: sessionCookieName, value: token, domain: appHost),
      );
      await _controller.reload();
    } catch (_) {
      // User cancelled or auth failed - the web app's own login button lets
      // them retry, so there is nothing to recover here.
    } finally {
      await sub.cancel();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0F1115),
      body: SafeArea(child: WebViewWidget(controller: _controller)),
    );
  }
}
