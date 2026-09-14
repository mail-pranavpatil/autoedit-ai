import 'package:flutter/foundation.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:sign_in_with_apple/sign_in_with_apple.dart';
import '../../../core/api/api_client.dart';
import '../../../core/storage/session_manager.dart';

class AuthService {
  static final GoogleSignIn _googleSignIn = GoogleSignIn(
    scopes: ['email', 'profile'],
  );

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

  /// Register new user with email & password
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

    final token = res['token'] as String;
    final user = res['user'] as Map<String, dynamic>;
    await SessionManager.saveSession(token: token, user: user);
    return user;
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
      if (e is SignInWithAppleAuthorizationException &&
          e.code == AuthorizationErrorCode.canceled) {
        throw ApiException(400, 'Apple sign in was cancelled');
      }
      rethrow;
    }
  }

  /// Native Sign in with Google (Identity only, no YouTube scopes bundled here)
  static Future<Map<String, dynamic>> signInWithGoogle() async {
    try {
      final account = await _googleSignIn.signIn();
      if (account == null) {
        throw ApiException(400, 'Google sign in was cancelled');
      }

      await account.authentication;

      // Exchange credentials or register user with Google profile
      final res = await ApiClient.post(
        '/api/auth/register',
        body: {
          'email': account.email,
          'password': 'google_oauth_${account.id}',
          'name': account.displayName ?? account.email.split('@')[0],
        },
        requiresAuth: false,
      ).catchError((err) async {
        // If already registered, log in
        return await ApiClient.post(
          '/api/auth/login',
          body: {
            'email': account.email,
            'password': 'google_oauth_${account.id}',
          },
          requiresAuth: false,
        );
      });

      final token = res['token'] as String;
      final user = res['user'] as Map<String, dynamic>;
      await SessionManager.saveSession(token: token, user: user);
      return user;
    } catch (e) {
      if (kDebugMode) print('Google Sign-In Error: $e');
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
    try {
      await _googleSignIn.signOut();
    } catch (_) {}
    await SessionManager.clear();
  }
}
