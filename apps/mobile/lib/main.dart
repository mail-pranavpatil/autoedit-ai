import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'app_config.dart';
import 'core/storage/session_manager.dart';
import 'core/theme/app_theme.dart';
import 'core/theme/theme_controller.dart';
import 'features/auth/screens/login_screen.dart';
import 'features/dashboard/screens/dashboard_screen.dart';
import 'features/onboarding/screens/platform_select_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Supabase.initialize(url: supabaseUrl, anonKey: supabaseAnonKey);
  themeModeNotifier.value = await SessionManager.getThemeMode();
  runApp(const AutoEditApp());
}

class AutoEditApp extends StatelessWidget {
  const AutoEditApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<ThemeMode>(
      valueListenable: themeModeNotifier,
      builder: (context, mode, _) {
        return MaterialApp(
          title: 'Eren - AI Video Creator',
          debugShowCheckedModeBanner: false,
          theme: AppTheme.light,
          darkTheme: AppTheme.dark,
          themeMode: mode,
          home: const AuthBootstrap(),
        );
      },
    );
  }
}

class AuthBootstrap extends StatefulWidget {
  const AuthBootstrap({super.key});

  @override
  State<AuthBootstrap> createState() => _AuthBootstrapState();
}

class _AuthBootstrapState extends State<AuthBootstrap> {
  @override
  void initState() {
    super.initState();
    _checkAuthStatus();
  }

  Future<void> _checkAuthStatus() async {
    // Supabase's SDK persists/refreshes the session itself.
    final loggedIn = Supabase.instance.client.auth.currentSession != null;
    if (!loggedIn) {
      _navigate(const LoginScreen());
      return;
    }

    final onboardingDone = await SessionManager.isOnboardingCompleted();
    if (onboardingDone) {
      _navigate(const DashboardScreen());
    } else {
      _navigate(const PlatformSelectScreen());
    }
  }

  void _navigate(Widget screen) {
    if (!mounted) return;
    Navigator.of(context).pushReplacement(
      MaterialPageRoute(builder: (_) => screen),
    );
  }

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    return Scaffold(
      backgroundColor: colors.background,
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 64,
              height: 64,
              decoration: BoxDecoration(
                color: colors.accent,
                borderRadius: BorderRadius.circular(18),
              ),
              child: const Icon(Icons.play_arrow_rounded, color: Colors.white, size: 36),
            ),
            const SizedBox(height: 24),
            SizedBox(
              width: 24,
              height: 24,
              child: CircularProgressIndicator(
                strokeWidth: 2.5,
                valueColor: AlwaysStoppedAnimation<Color>(colors.accent),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
