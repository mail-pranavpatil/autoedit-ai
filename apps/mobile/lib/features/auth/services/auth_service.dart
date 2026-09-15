import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:sign_in_with_apple/sign_in_with_apple.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import '../../../app_config.dart';
import '../../../core/api/api_client.dart';
import '../../../core/storage/session_manager.dart';

class AuthService {
  static SupabaseClient get _client => Supabase.instance.client;

  /// Authenticate with email & password
  static Future<Map<String, dynamic>> login({
    required String email,
    required String password,
  }) async {
    try {
      await _client.auth.signInWithPassword(email: email, password: password);
    } on AuthException catch (e) {
      if (e.message.toLowerCase().contains('confirm')) {
        // Matches the substring login_screen.dart greps for to route to
        // EmailVerificationScreen instead of showing a plain error.
        throw ApiException(403, 'Please verify your email address to log in');
      }
      throw ApiException(401, e.message);
    }
    return _syncProfile();
  }

  /// Register new user with email & password (Supabase emails a 6-digit OTP)
  static Future<Map<String, dynamic>> register({
    required String email,
    required String password,
    String? name,
  }) async {
    try {
      await _client.auth.signUp(
        email: email,
        password: password,
        data: (name != null && name.isNotEmpty) ? {'name': name} : null,
      );
    } on AuthException catch (e) {
      throw ApiException(400, e.message);
    }
    return {'ok': true, 'requiresVerification': true, 'email': email};
  }

  /// Verify email with 6-digit OTP code
  static Future<Map<String, dynamic>> verifyEmail({
    required String email,
    required String code,
  }) async {
    try {
      await _client.auth.verifyOTP(email: email, token: code, type: OtpType.signup);
    } on AuthException catch (e) {
      throw ApiException(400, e.message);
    }
    return _syncProfile();
  }

  /// Resend 6-digit email verification code
  static Future<void> resendVerificationCode({required String email}) async {
    try {
      await _client.auth.resend(type: OtpType.signup, email: email);
    } on AuthException catch (e) {
      throw ApiException(400, e.message);
    }
  }

  /// Native Sign in with Apple (App Store required)
  static Future<Map<String, dynamic>> signInWithApple() async {
    try {
      final credential = await SignInWithApple.getAppleIDCredential(
        scopes: [
          AppleIDAuthorizationScopes.email,
          AppleIDAuthorizationScopes.fullName,
        ],
      );

      final idToken = credential.identityToken;
      if (idToken == null) {
        throw ApiException(400, 'Apple Sign-In did not return an identity token');
      }

      // Supabase verifies the token's signature against Apple's keys itself.
      await _client.auth.signInWithIdToken(provider: OAuthProvider.apple, idToken: idToken);

      final displayName = [
        credential.givenName,
        credential.familyName,
      ].where((e) => e != null && e.isNotEmpty).join(' ');
      if (displayName.isNotEmpty) {
        try {
          await _client.auth.updateUser(UserAttributes(data: {'name': displayName}));
        } catch (_) {
          // Apple only returns the name on first sign-in; losing it on a
          // later retry shouldn't block sign-in.
        }
      }

      return await _syncProfile();
    } catch (e) {
      if (e is SignInWithAppleAuthorizationException) {
        if (e.code == AuthorizationErrorCode.canceled) {
          throw ApiException(400, 'Apple sign in was cancelled');
        } else if (e.code == AuthorizationErrorCode.unknown ||
            e.code == AuthorizationErrorCode.failed) {
          throw ApiException(
            400,
            'Apple Sign-In could not be completed. Please ensure you are signed into an Apple ID in iOS Settings, or continue with Google or Email.',
          );
        }
      }
      final errStr = e.toString().toLowerCase();
      if (errStr.contains('1000') || errStr.contains('authorizationservices')) {
        throw ApiException(
          400,
          'Apple Sign-In could not be completed. Please ensure you are signed into an Apple ID in iOS Settings, or continue with Google or Email.',
        );
      }
      rethrow;
    }
  }

  /// Google Sign-In via Supabase's Google provider (external browser + deep
  /// link back into the app - autoedit:// is already a registered URL scheme).
  static Future<Map<String, dynamic>> signInWithGoogle() async {
    final completer = Completer<void>();
    late final StreamSubscription<AuthState> sub;
    sub = _client.auth.onAuthStateChange.listen((state) {
      if (state.event == AuthChangeEvent.signedIn && !completer.isCompleted) {
        completer.complete();
      }
    });

    try {
      await _client.auth.signInWithOAuth(
        OAuthProvider.google,
        redirectTo: '$authScheme://login-callback',
      );
      await completer.future.timeout(const Duration(minutes: 2));
      return await _syncProfile();
    } on TimeoutException {
      throw ApiException(400, 'Google sign in was cancelled');
    } catch (e) {
      if (kDebugMode) print('Google Sign-In Exception: $e');
      final errStr = e.toString().toLowerCase();
      if (errStr.contains('canceled') || errStr.contains('cancelled') || errStr.contains('user cancelled')) {
        throw ApiException(400, 'Google sign in was cancelled');
      }
      rethrow;
    } finally {
      await sub.cancel();
    }
  }

  /// Check current user profile from server
  static Future<Map<String, dynamic>> fetchMe() async {
    final res = await ApiClient.get('/api/auth/me');
    return res as Map<String, dynamic>;
  }

  /// Fetches the profile after a successful Supabase sign-in and caches it
  /// locally (the `public.users` row always exists by then - the DB trigger
  /// creates it the moment Supabase creates the auth.users row).
  static Future<Map<String, dynamic>> _syncProfile() async {
    final user = await fetchMe();
    await SessionManager.cacheUser(user);
    return user;
  }

  /// Logout and clear local cache
  static Future<void> logout() async {
    try {
      await _client.auth.signOut();
    } catch (_) {}
    await SessionManager.clear();
  }
}
