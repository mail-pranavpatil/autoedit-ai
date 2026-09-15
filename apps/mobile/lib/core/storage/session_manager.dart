import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Local app-state cache only - the Supabase SDK (`Supabase.instance.client.auth`)
/// owns the actual session/token and persists/refreshes it itself.
class SessionManager {
  static const _storage = FlutterSecureStorage(
    iOptions: IOSOptions(
      accessibility: KeychainAccessibility.first_unlock,
    ),
    aOptions: AndroidOptions(
      resetOnError: true,
    ),
  );

  static const _keyUser = 'user_data';
  static const _keyOnboarding = 'onboarding_completed';
  static const _keyThemeMode = 'theme_mode';

  /// Caches the fetched profile (from GET /api/auth/me) for offline fallback.
  static Future<void> cacheUser(Map<String, dynamic> user) async {
    await _storage.write(key: _keyUser, value: jsonEncode(user));
    final onboarding = user['onboardingCompleted'] == true;
    await _storage.write(key: _keyOnboarding, value: onboarding.toString());
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

  /// Clears cached app state on logout
  static Future<void> clear() async {
    await _storage.delete(key: _keyUser);
    await _storage.delete(key: _keyOnboarding);
  }

  /// Reads the persisted appearance preference (defaults to system).
  static Future<ThemeMode> getThemeMode() async {
    final val = await _storage.read(key: _keyThemeMode);
    return switch (val) {
      'light' => ThemeMode.light,
      'dark' => ThemeMode.dark,
      _ => ThemeMode.system,
    };
  }

  /// Persists the Settings > Appearance choice.
  static Future<void> setThemeMode(ThemeMode mode) async {
    await _storage.write(key: _keyThemeMode, value: mode.name);
  }
}
