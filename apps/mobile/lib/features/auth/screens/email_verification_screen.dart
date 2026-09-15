import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/widgets/glass_container.dart';
import '../../onboarding/screens/platform_select_screen.dart';
import '../services/auth_service.dart';

class EmailVerificationScreen extends StatefulWidget {
  final String email;
  final String? name;

  const EmailVerificationScreen({
    super.key,
    required this.email,
    this.name,
  });

  @override
  State<EmailVerificationScreen> createState() => _EmailVerificationScreenState();
}

class _EmailVerificationScreenState extends State<EmailVerificationScreen> {
  final TextEditingController _codeController = TextEditingController();
  bool _isLoading = false;
  String? _errorMessage;
  String? _successMessage;

  int _resendCountdown = 60;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _startResendTimer();
  }

  void _startResendTimer() {
    _timer?.cancel();
    setState(() => _resendCountdown = 60);
    _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (_resendCountdown > 0) {
        setState(() => _resendCountdown--);
      } else {
        timer.cancel();
      }
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    _codeController.dispose();
    super.dispose();
  }

  Future<void> _verifyCode() async {
    final code = _codeController.text.trim();
    if (code.length < 6) {
      setState(() => _errorMessage = 'Please enter the 6-digit verification code.');
      return;
    }

    setState(() {
      _isLoading = true;
      _errorMessage = null;
      _successMessage = null;
    });

    try {
      final user = await AuthService.verifyEmail(
        email: widget.email,
        code: code,
      );

      if (!mounted) return;
      HapticFeedback.heavyImpact();

      final onboardingCompleted = user['onboardingCompleted'] == true;
      if (onboardingCompleted) {
        Navigator.of(context).pushNamedAndRemoveUntil('/dashboard', (route) => false);
      } else {
        Navigator.of(context).pushReplacement(
          MaterialPageRoute(builder: (_) => const PlatformSelectScreen()),
        );
      }
    } catch (e) {
      setState(() {
        _errorMessage = e.toString().replaceAll('ApiException: ', '');
      });
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _resendCode() async {
    if (_resendCountdown > 0) return;

    setState(() {
      _errorMessage = null;
      _successMessage = null;
    });

    try {
      await AuthService.resendVerificationCode(email: widget.email);
      setState(() => _successMessage = 'A new code has been sent to your email.');
      _startResendTimer();
    } catch (e) {
      setState(() => _errorMessage = e.toString().replaceAll('ApiException: ', ''));
    }
  }

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    return Scaffold(
      backgroundColor: colors.background,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: Icon(Icons.arrow_back_ios_new_rounded, color: colors.textPrimary, size: 20),
          onPressed: () => Navigator.of(context).pop(),
        ),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              const SizedBox(height: 24),
              // Icon Badge
              Container(
                width: 76,
                height: 76,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: colors.accent.withValues(alpha: 0.18),
                  border: Border.all(
                    color: colors.accent.withValues(alpha: 0.35),
                    width: 1.5,
                  ),
                ),
                child: Center(
                  child: Icon(
                    Icons.mark_email_read_outlined,
                    color: colors.accent,
                    size: 38,
                  ),
                ),
              ),
              const SizedBox(height: 24),
              Text(
                'Verify Your Email',
                style: TextStyle(
                  fontSize: 28,
                  fontWeight: FontWeight.w800,
                  color: colors.textPrimary,
                  letterSpacing: -0.5,
                ),
              ),
              const SizedBox(height: 12),
              RichText(
                textAlign: TextAlign.center,
                text: TextSpan(
                  style: TextStyle(
                    fontSize: 15,
                    color: colors.textSecondary,
                    height: 1.4,
                  ),
                  children: [
                    const TextSpan(text: "We've sent a 6-digit verification code to\n"),
                    TextSpan(
                      text: widget.email,
                      style: TextStyle(
                        fontWeight: FontWeight.w700,
                        color: colors.textPrimary,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 36),

              // Code Input Card
              GlassContainer(
                padding: const EdgeInsets.all(24),
                child: Column(
                  children: [
                    TextField(
                      controller: _codeController,
                      keyboardType: TextInputType.number,
                      textAlign: TextAlign.center,
                      maxLength: 6,
                      inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                      style: TextStyle(
                        fontSize: 32,
                        fontWeight: FontWeight.w800,
                        letterSpacing: 16,
                        color: colors.textPrimary,
                      ),
                      decoration: InputDecoration(
                        counterText: '',
                        hintText: '------',
                        hintStyle: TextStyle(
                          fontSize: 32,
                          letterSpacing: 16,
                          color: colors.textMuted.withValues(alpha: 0.6),
                        ),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(16),
                          borderSide: BorderSide(color: colors.cardBorder),
                        ),
                        focusedBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(16),
                          borderSide: BorderSide(
                            color: colors.accent,
                            width: 1.5,
                          ),
                        ),
                      ),
                      onSubmitted: (_) => _verifyCode(),
                    ),
                    if (_errorMessage != null) ...[
                      const SizedBox(height: 14),
                      Text(
                        _errorMessage!,
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          color: colors.danger,
                          fontSize: 13,
                          fontWeight: FontWeight.w600,
                        ),

                      ),
                    ],
                    if (_successMessage != null) ...[
                      const SizedBox(height: 14),
                      Text(
                        _successMessage!,
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          color: colors.success,
                          fontSize: 13,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                    const SizedBox(height: 24),

                    // Verify CTA
                    SizedBox(
                      width: double.infinity,
                      height: 52,
                      child: ElevatedButton(
                        onPressed: _isLoading ? null : _verifyCode,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: colors.accent,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(14),
                          ),
                          elevation: 0,
                        ),
                        child: _isLoading
                            ? const SizedBox(
                                width: 22,
                                height: 22,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2.5,
                                  color: Colors.white,
                                ),
                              )
                            : const Text(
                                'Verify & Continue',
                                style: TextStyle(
                                  fontSize: 16,
                                  fontWeight: FontWeight.w700,
                                  color: Colors.white,
                                ),
                              ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 28),

              // Resend Timer Row
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    "Didn't receive the code? ",
                    style: TextStyle(
                      color: colors.textMuted,
                      fontSize: 14,
                    ),
                  ),
                  if (_resendCountdown > 0)
                    Text(
                      'Resend in ${_resendCountdown}s',
                      style: TextStyle(
                        color: colors.textSecondary,
                        fontSize: 14,
                        fontWeight: FontWeight.w600,
                      ),
                    )
                  else
                    GestureDetector(
                      onTap: _resendCode,
                      child: Text(
                        'Resend Code',
                        style: TextStyle(
                          color: colors.accent,
                          fontSize: 14,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ),
                ],
              ),
              const SizedBox(height: 32),
            ],
          ),
        ),
      ),
    );
  }
}
