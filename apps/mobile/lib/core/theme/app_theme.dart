import 'package:flutter/material.dart';

/// Semantic color tokens, looked up via `context.colors.xxx` (see [AppColorsX]
/// below) instead of a hardcoded static palette, so every screen re-themes
/// automatically when [AppTheme.light]/[AppTheme.dark] switch.
class AppColors extends ThemeExtension<AppColors> {
  final Color background;
  final Color surface;
  final Color card;
  final Color cardBorder;
  final Color textPrimary;
  final Color textSecondary;
  final Color textMuted;
  final Color accent;
  final Color success;
  final Color warning;
  final Color danger;

  const AppColors({
    required this.background,
    required this.surface,
    required this.card,
    required this.cardBorder,
    required this.textPrimary,
    required this.textSecondary,
    required this.textMuted,
    required this.accent,
    required this.success,
    required this.warning,
    required this.danger,
  });

  static const light = AppColors(
    background: Color(0xFFFFFFFF),
    surface: Color(0xFFFFFFFF),
    card: Color(0xFFF7F7F8),
    cardBorder: Color(0xFFE5E7EB),
    textPrimary: Color(0xFF0B0D12),
    textSecondary: Color(0xFF6B7280),
    textMuted: Color(0xFF9CA3AF),
    accent: Color(0xFF6366F1),
    success: Color(0xFF10B981),
    warning: Color(0xFFF59E0B),
    danger: Color(0xFFEF4444),
  );

  static const dark = AppColors(
    background: Color(0xFF090D14),
    surface: Color(0xFF111726),
    card: Color(0xFF161F32),
    cardBorder: Color(0xFF243048),
    textPrimary: Color(0xFFF8FAFC),
    textSecondary: Color(0xFF94A3B8),
    textMuted: Color(0xFF64748B),
    accent: Color(0xFF6366F1),
    success: Color(0xFF10B981),
    warning: Color(0xFFF59E0B),
    danger: Color(0xFFEF4444),
  );

  @override
  AppColors copyWith({
    Color? background,
    Color? surface,
    Color? card,
    Color? cardBorder,
    Color? textPrimary,
    Color? textSecondary,
    Color? textMuted,
    Color? accent,
    Color? success,
    Color? warning,
    Color? danger,
  }) {
    return AppColors(
      background: background ?? this.background,
      surface: surface ?? this.surface,
      card: card ?? this.card,
      cardBorder: cardBorder ?? this.cardBorder,
      textPrimary: textPrimary ?? this.textPrimary,
      textSecondary: textSecondary ?? this.textSecondary,
      textMuted: textMuted ?? this.textMuted,
      accent: accent ?? this.accent,
      success: success ?? this.success,
      warning: warning ?? this.warning,
      danger: danger ?? this.danger,
    );
  }

  @override
  AppColors lerp(ThemeExtension<AppColors>? other, double t) {
    if (other is! AppColors) return this;
    return AppColors(
      background: Color.lerp(background, other.background, t)!,
      surface: Color.lerp(surface, other.surface, t)!,
      card: Color.lerp(card, other.card, t)!,
      cardBorder: Color.lerp(cardBorder, other.cardBorder, t)!,
      textPrimary: Color.lerp(textPrimary, other.textPrimary, t)!,
      textSecondary: Color.lerp(textSecondary, other.textSecondary, t)!,
      textMuted: Color.lerp(textMuted, other.textMuted, t)!,
      accent: Color.lerp(accent, other.accent, t)!,
      success: Color.lerp(success, other.success, t)!,
      warning: Color.lerp(warning, other.warning, t)!,
      danger: Color.lerp(danger, other.danger, t)!,
    );
  }
}

/// `context.colors.textPrimary` instead of `Theme.of(context).extension<AppColors>()!.textPrimary`.
extension AppColorsX on BuildContext {
  AppColors get colors => Theme.of(this).extension<AppColors>()!;
}

class AppTheme {
  // Fixed real-world brand colors — never theme-toggled.
  static const Color googleRed = Color(0xFFEA4335);
  static const Color youtubeRed = Color(0xFFFF0000);
  static const Color appleDark = Color(0xFF000000);

  static ThemeData get light => _themeFrom(AppColors.light, Brightness.light);
  static ThemeData get dark => _themeFrom(AppColors.dark, Brightness.dark);

  static ThemeData _themeFrom(AppColors colors, Brightness brightness) {
    return ThemeData(
      brightness: brightness,
      scaffoldBackgroundColor: colors.background,
      primaryColor: colors.accent,
      extensions: [colors],
      colorScheme: (brightness == Brightness.dark
              ? const ColorScheme.dark()
              : const ColorScheme.light())
          .copyWith(
        primary: colors.accent,
        secondary: colors.accent,
        surface: colors.surface,
        error: colors.danger,
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: Colors.transparent,
        elevation: 0,
        centerTitle: true,
        iconTheme: IconThemeData(color: colors.textPrimary),
        titleTextStyle: TextStyle(
          color: colors.textPrimary,
          fontSize: 18,
          fontWeight: FontWeight.w700,
          letterSpacing: -0.4,
        ),
      ),
      cardTheme: CardThemeData(
        color: colors.card,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
          side: BorderSide(color: colors.cardBorder, width: 1),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: colors.card,
        hintStyle: TextStyle(color: colors.textMuted, fontSize: 14),
        contentPadding: const EdgeInsets.symmetric(horizontal: 18, vertical: 16),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: BorderSide(color: colors.cardBorder, width: 1),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: BorderSide(color: colors.cardBorder, width: 1),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: BorderSide(color: colors.accent, width: 1.5),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: BorderSide(color: colors.danger, width: 1),
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: colors.accent,
          foregroundColor: Colors.white,
          elevation: 0,
          minimumSize: const Size.fromHeight(54),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
          textStyle: const TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w700,
            letterSpacing: -0.2,
          ),
        ),
      ),
    );
  }
}
