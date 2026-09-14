import 'package:flutter/material.dart';
import 'core/storage/session_manager.dart';
import 'core/theme/app_theme.dart';
import 'features/auth/screens/login_screen.dart';
import 'features/dashboard/screens/dashboard_screen.dart';
import 'features/onboarding/screens/platform_select_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const AutoEditApp());
}

class AutoEditApp extends StatelessWidget {
  const AutoEditApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Eren - AI Video Creator',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.darkTheme,
      home: const AuthBootstrap(),
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
    // Check if session token exists in secure storage (persistent login)
    final loggedIn = await SessionManager.isLoggedIn();
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
    return Scaffold(
      backgroundColor: AppTheme.background,
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 64,
              height: 64,
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [AppTheme.primary, AppTheme.accent],
                ),
                borderRadius: BorderRadius.circular(18),
              ),
              child: const Icon(Icons.play_arrow_rounded, color: Colors.white, size: 36),
            ),
            const SizedBox(height: 24),
            const SizedBox(
              width: 24,
              height: 24,
              child: CircularProgressIndicator(
                strokeWidth: 2.5,
                valueColor: AlwaysStoppedAnimation<Color>(AppTheme.primaryLight),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
