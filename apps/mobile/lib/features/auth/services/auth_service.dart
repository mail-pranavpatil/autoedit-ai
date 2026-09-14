import 'package:flutter/foundation.dart';
import 'package:flutter_web_auth_2/flutter_web_auth_2.dart';
import 'package:sign_in_with_apple/sign_in_with_apple.dart';
import '../../../core/api/api_client.dart';
import '../../../core/storage/session_manager.dart';

class AuthService {
  /// Authenticate with email & password
  static Future<Map<String, dynamic>> login({
    required String email,
    required String password,
  }) async {
    final res = await ApiClient.post(
      '/api/auth/login',
      body: {
        'email': email,
        'password': password,
      },
      requiresAuth: false,
    );

    final token = res['token'] as String;
    final user = res['user'] as Map<String, dynamic>;
    await SessionManager.saveSession(token: token, user: user);
    return user;
  }

  /// Register new user with email & password (generates email verification code)
  static Future<Map<String, dynamic>> register({
    required String email,
    required String password,
    String? name,
  }) async {
    final res = await ApiClient.post(
      '/api/auth/register',
      body: {
        'email': email,
        'password': password,
        'name': name,
      },
      requiresAuth: false,
    );

    return res as Map<String, dynamic>;
  }

  /// Verify email with 6-digit OTP code
  static Future<Map<String, dynamic>> verifyEmail({
    required String email,
    required String code,
  }) async {
    final res = await ApiClient.post(
      '/api/auth/verify-email',
      body: {
        'email': email,
        'code': code,
      },
      requiresAuth: false,
    );

    final token = res['token'] as String;
    final user = res['user'] as Map<String, dynamic>;
    await SessionManager.saveSession(token: token, user: user);
    return user;
  }

  /// Resend 6-digit email verification code
  static Future<void> resendVerificationCode({required String email}) async {
    await ApiClient.post(
      '/api/auth/resend-code',
      body: {'email': email},
      requiresAuth: false,
    );
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

      final displayName = [
        credential.givenName,
        credential.familyName,
      ].where((e) => e != null && e.isNotEmpty).join(' ');

      final res = await ApiClient.post(
        '/api/auth/apple',
        body: {
          'identity_token': credential.identityToken,
          'authorization_code': credential.authorizationCode,
          'user_id': credential.userIdentifier,
          'email': credential.email,
          'name': displayName.isNotEmpty ? displayName : null,
        },
        requiresAuth: false,
      );

      final token = res['token'] as String;
      final user = res['user'] as Map<String, dynamic>;
      await SessionManager.saveSession(token: token, user: user);
      return user;
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

  /// Crash-free Browser-based Google Sign-In (Apple ASWebAuthenticationSession)
  static Future<Map<String, dynamic>> signInWithGoogle() async {
    try {
      final callback = await FlutterWebAuth2.authenticate(
        url: '${ApiClient.baseUrl}/api/auth/google?platform=ios',
        callbackUrlScheme: 'autoedit',
      );

      final uri = Uri.parse(callback);
      final error = uri.queryParameters['error'];
      if (error != null) {
        throw ApiException(400, 'Google sign-in was not completed');
      }

      final token = uri.queryParameters['token'];
      if (token == null || token.isEmpty) {
        throw ApiException(400, 'Authentication token missing from Google callback');
      }

      // Save token and fetch user identity
      await SessionManager.saveToken(token);
      final user = await fetchMe();
      await SessionManager.saveSession(token: token, user: user);
      return user;
    } catch (e) {
      if (kDebugMode) print('Google Sign-In Exception: $e');
      final errStr = e.toString().toLowerCase();
      if (errStr.contains('canceled') || errStr.contains('cancelled') || errStr.contains('user cancelled')) {
        throw ApiException(400, 'Google sign in was cancelled');
      }
      rethrow;
    }
  }

  /// Check current user profile from server
  static Future<Map<String, dynamic>> fetchMe() async {
    final res = await ApiClient.get('/api/auth/me');
    return res as Map<String, dynamic>;
  }

  /// Logout and clear storage
  static Future<void> logout() async {
    try {
      await ApiClient.post('/api/auth/logout', body: {});
    } catch (_) {}
    await SessionManager.clear();
  }
}

