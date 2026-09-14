import 'package:flutter/widgets.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:autoedit_mobile/core/widgets/google_logo.dart';
import 'package:autoedit_mobile/webview_shell.dart';

void main() {
  const host = 'autoedit.example';

  test('diverts the OAuth entry point to an auth session', () {
    expect(
      classifyNavigation(Uri.parse('https://$host/api/auth/google'), host),
      NavigationAction.authDivert,
    );
    expect(
      classifyNavigation(Uri.parse('https://accounts.google.com/o/oauth2/auth'), host),
      NavigationAction.authDivert,
    );
  });

  test('intercepts finished-reel downloads', () {
    expect(
      classifyNavigation(Uri.parse('https://$host/api/videos/abc-123/download'), host),
      NavigationAction.download,
    );
    // Not the exact download route -> falls through to allow.
    expect(
      classifyNavigation(Uri.parse('https://$host/api/videos/abc-123/stream'), host),
      NavigationAction.allow,
    );
  });

  test('sends off-origin http(s) links to the system browser', () {
    expect(
      classifyNavigation(Uri.parse('https://youtube.com/watch?v=xyz'), host),
      NavigationAction.externalLink,
    );
  });

  test('allows same-origin and non-http(s) navigation through', () {
    expect(classifyNavigation(Uri.parse('https://$host/projects/1'), host), NavigationAction.allow);
    expect(classifyNavigation(Uri.parse('about:blank'), host), NavigationAction.allow);
  });

  testWidgets('renders GoogleLogo without crashing', (tester) async {
    await tester.pumpWidget(
      const Directionality(
        textDirection: TextDirection.ltr,
        child: GoogleLogo(size: 24),
      ),
    );
    expect(find.byType(GoogleLogo), findsOneWidget);
  });
}
