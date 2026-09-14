import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import '../../../core/api/api_client.dart';
import '../../../core/storage/session_manager.dart';
import '../../../core/theme/app_theme.dart';
import '../../dashboard/screens/dashboard_screen.dart';
import '../models/onboarding_models.dart';

class PaywallScreen extends StatefulWidget {
  const PaywallScreen({super.key});

  @override
  State<PaywallScreen> createState() => _PaywallScreenState();
}

class _PaywallScreenState extends State<PaywallScreen> {
  bool _isProcessing = false;

  Future<void> _completeOnboardingAndEnterDashboard({bool subscribed = false}) async {
    setState(() => _isProcessing = true);

    try {
      // Call backend to mark onboarding completed
      await ApiClient.post(
        '/api/channels/onboarding/complete',
        body: {
          'editing_experience': OnboardingState.instance.experience?.key,
          'creation_reason': OnboardingState.instance.creationReason,
        },
      );
    } catch (_) {
      // Allow moving forward even if offline
    }

    await SessionManager.setOnboardingCompleted(true);

    if (!mounted) return;
    setState(() => _isProcessing = false);

    if (subscribed) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Pro Plan Activated! Welcome to Unlimited Creator Access.'),
          backgroundColor: AppTheme.success,
        ),
      );
    }

    Navigator.of(context).pushAndRemoveUntil(
      MaterialPageRoute(builder: (_) => const DashboardScreen()),
      (route) => false,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.background,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Top badge
              Center(
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(
                      colors: [AppTheme.primary, AppTheme.accent],
                    ),
                    borderRadius: BorderRadius.circular(20),
                    boxShadow: [
                      BoxShadow(
                        color: AppTheme.primary.withOpacity(0.3),
                        blurRadius: 12,
                        offset: const Offset(0, 4),
                      ),
                    ],
                  ),
                  child: const Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(CupertinoIcons.sparkles, color: Colors.white, size: 14),
                      SizedBox(width: 6),
                      Text(
                        'PRO CREATOR ACCESS',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 11,
                          fontWeight: FontWeight.w800,
                          letterSpacing: 0.8,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 18),

              const Text(
                'Scale Your Channel With Zero Editing Friction',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 26,
                  fontWeight: FontWeight.bold,
                  color: AppTheme.textPrimary,
                  letterSpacing: -0.6,
                ),
              ),
              const SizedBox(height: 8),
              const Text(
                'High-converting edits, viral caption styles, and automatic distribution.',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 14,
                  color: AppTheme.textSecondary,
                  height: 1.4,
                ),
              ),
              const SizedBox(height: 28),

              // Pricing Plan Card
              Container(
                padding: const EdgeInsets.all(22),
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [
                      AppTheme.card,
                      AppTheme.surface,
                    ],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: AppTheme.primary, width: 2),
                  boxShadow: [
                    BoxShadow(
                      color: AppTheme.primary.withOpacity(0.18),
                      blurRadius: 24,
                      offset: const Offset(0, 10),
                    ),
                  ],
                ),
                child: Column(
                  children: [
                    const Text(
                      'All-Inclusive Creator Pass',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                        color: AppTheme.primaryLight,
                      ),
                    ),
                    const SizedBox(height: 10),

                    // Price display
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      crossAxisAlignment: CrossAxisAlignment.baseline,
                      textBaseline: TextBaseline.alphabetic,
                      children: [
                        const Text(
                          '\$',
                          style: TextStyle(
                            fontSize: 26,
                            fontWeight: FontWeight.bold,
                            color: AppTheme.textPrimary,
                          ),
                        ),
                        const Text(
                          '49',
                          style: TextStyle(
                            fontSize: 52,
                            fontWeight: FontWeight.w900,
                            color: AppTheme.textPrimary,
                            letterSpacing: -1.5,
                          ),
                        ),
                        const SizedBox(width: 4),
                        const Text(
                          'USD / month',
                          style: TextStyle(
                            fontSize: 14,
                            color: AppTheme.textSecondary,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 6),

                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: AppTheme.success.withOpacity(0.15),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: const Text(
                        '✨ Unlimited Videos on Any Platform',
                        style: TextStyle(
                          color: AppTheme.success,
                          fontSize: 13,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                    const SizedBox(height: 20),

                    const Divider(color: AppTheme.cardBorder),
                    const SizedBox(height: 16),

                    // Features checklist
                    _buildFeatureItem('Unlimited AI Video Edits & Renders'),
                    _buildFeatureItem('Publish to Any Platform (YouTube + Upcoming)'),
                    _buildFeatureItem('AI Auto-Captions with Custom Fonts & Emojis'),
                    _buildFeatureItem('Smart B-Roll & SFX Music Matching'),
                    _buildFeatureItem('Multi-Channel Goal & Velocity Tracking'),
                    _buildFeatureItem('Priority Cloud GPU Rendering Queue'),
                  ],
                ),
              ),
              const SizedBox(height: 28),

              // Subscribe CTA Button
              ElevatedButton(
                onPressed: _isProcessing
                    ? null
                    : () => _completeOnboardingAndEnterDashboard(subscribed: true),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppTheme.primary,
                  minimumSize: const Size.fromHeight(56),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16),
                  ),
                ),
                child: _isProcessing
                    ? const SizedBox(
                        width: 24,
                        height: 24,
                        child: CircularProgressIndicator(
                          strokeWidth: 2.5,
                          valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                        ),
                      )
                    : const Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(CupertinoIcons.checkmark_seal_fill, size: 20),
                          SizedBox(width: 8),
                          Text(
                            'Start 7-Day Free Trial (\$49/mo)',
                            style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                          ),
                        ],
                      ),
              ),
              const SizedBox(height: 16),

              // Skip / Continue to Dashboard link
              Center(
                child: TextButton(
                  onPressed: _isProcessing
                      ? null
                      : () => _completeOnboardingAndEnterDashboard(subscribed: false),
                  child: const Text(
                    'Continue to Dashboard (Explore First)',
                    style: TextStyle(
                      color: AppTheme.textSecondary,
                      fontSize: 14,
                      fontWeight: FontWeight.w600,
                      decoration: TextDecoration.underline,
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 12),

              const Text(
                'Cancel anytime in iOS App Store Subscriptions. Mockup billing simulation.',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 11,
                  color: AppTheme.textMuted,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildFeatureItem(String title) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        children: [
          Container(
            width: 22,
            height: 22,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: AppTheme.primary.withOpacity(0.2),
            ),
            child: const Icon(
              CupertinoIcons.checkmark,
              color: AppTheme.primaryLight,
              size: 13,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              title,
              style: const TextStyle(
                fontSize: 14,
                color: AppTheme.textPrimary,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
