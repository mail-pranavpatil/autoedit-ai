import 'dart:convert';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class SessionManager {
  static const _storage = FlutterSecureStorage(
    iOptions: IOSOptions(
      accessibility: KeychainAccessibility.first_unlock,
    ),
    aOptions: AndroidOptions(
      resetOnError: true,
    ),
  );

  static const _keyToken = 'auth_token';
  static const _keyUser = 'user_data';
  static const _keyOnboarding = 'onboarding_completed';

  /// Saves the user token and profile data securely
  static Future<void> saveSession({
    required String token,
    required Map<String, dynamic> user,
  }) async {
    await _storage.write(key: _keyToken, value: token);
    await _storage.write(key: _keyUser, value: jsonEncode(user));
    final onboarding = user['onboardingCompleted'] == true;
    await _storage.write(key: _keyOnboarding, value: onboarding.toString());
  }

  /// Retrieves the active auth token, if any
  static Future<String?> getToken() async {
    return await _storage.read(key: _keyToken);
  }

  /// Checks if user is currently signed in
  static Future<bool> isLoggedIn() async {
    final token = await getToken();
    return token != null && token.isNotEmpty;
  }

  /// Checks if onboarding was marked completed
  static Future<bool> isOnboardingCompleted() async {
    final val = await _storage.read(key: _keyOnboarding);
    return val == 'true';
  }

  /// Updates local onboarding completion flag
  static Future<void> setOnboardingCompleted(bool completed) async {
    await _storage.write(key: _keyOnboarding, value: completed.toString());
  }

  /// Retrieves cached user profile
  static Future<Map<String, dynamic>?> getUser() async {
    final raw = await _storage.read(key: _keyUser);
    if (raw == null) return null;
    try {
      return jsonDecode(raw) as Map<String, dynamic>;
    } catch (_) {
      return null;
    }
  }

  /// Clears stored session on logout
  static Future<void> clear() async {
    await _storage.delete(key: _keyToken);
    await _storage.delete(key: _keyUser);
    await _storage.delete(key: _keyOnboarding);
  }
}
