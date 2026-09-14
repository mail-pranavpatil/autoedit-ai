import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../models/onboarding_models.dart';
import 'paywall_screen.dart';

class MotivationScreen extends StatefulWidget {
  const MotivationScreen({super.key});

  @override
  State<MotivationScreen> createState() => _MotivationScreenState();
}

class _MotivationScreenState extends State<MotivationScreen> {
  final _reasonController = TextEditingController();
  final Set<String> _selectedChips = {};

  final List<String> _presetReasons = [
    '🚀 Build Personal Brand',
    '💼 Grow My Business / Product',
    '💰 Create Passive Income',
    '🎓 Share Knowledge & Skills',
    '🌟 Become a Full-Time Creator',
    '🎨 Creative Expression',
  ];

  @override
  void dispose() {
    _reasonController.dispose();
    super.dispose();
  }

  void _proceedToPaywall({bool isSkipped = false}) {
    if (!isSkipped) {
      final combined = [
        ..._selectedChips,
        if (_reasonController.text.trim().isNotEmpty) _reasonController.text.trim(),
      ].join('; ');
      OnboardingState.instance.creationReason = combined.isNotEmpty ? combined : null;
    } else {
      OnboardingState.instance.creationReason = null;
    }

    Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => const PaywallScreen()),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: AppBar(
        title: const Text('Your Motivation'),
        leading: IconButton(
          icon: const Icon(CupertinoIcons.back),
          onPressed: () => Navigator.of(context).pop(),
        ),
        actions: [
          TextButton(
            onPressed: () => _proceedToPaywall(isSkipped: true),
            child: const Text(
              'Skip',
              style: TextStyle(
                color: AppTheme.textSecondary,
                fontSize: 15,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ],
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Progress Bar (Step 5 of 5)
              Row(
                children: List.generate(5, (index) {
                  return Expanded(
                    child: Container(
                      height: 4,
                      margin: EdgeInsets.only(right: index < 4 ? 6 : 0),
                      decoration: BoxDecoration(
                        color: AppTheme.primary,
                        borderRadius: BorderRadius.circular(2),
                      ),
                    ),
                  );
                }),
              ),
              const SizedBox(height: 24),

              Row(
                children: [
                  const Text(
                    'Why start creating?',
                    style: TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                      color: AppTheme.textPrimary,
                      letterSpacing: -0.5,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.08),
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: const Text(
                      'Optional',
                      style: TextStyle(
                        fontSize: 11,
                        color: AppTheme.textMuted,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              const Text(
                'Tell us what drives you. We use this to fine-tune your video narrative hooks and content strategy.',
                style: TextStyle(
                  fontSize: 14,
                  color: AppTheme.textSecondary,
                  height: 1.4,
                ),
              ),
              const SizedBox(height: 20),

              Expanded(
                child: SingleChildScrollView(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      // Preset Reasons Chips
                      Wrap(
                        spacing: 8,
                        runSpacing: 10,
                        children: _presetReasons.map((reason) {
                          final isSelected = _selectedChips.contains(reason);
                          return FilterChip(
                            label: Text(reason),
                            selected: isSelected,
                            selectedColor: AppTheme.primary.withOpacity(0.25),
                            backgroundColor: AppTheme.card,
                            side: BorderSide(
                              color: isSelected ? AppTheme.primary : AppTheme.cardBorder,
                              width: isSelected ? 1.5 : 1,
                            ),
                            labelStyle: TextStyle(
                              color: isSelected ? AppTheme.textPrimary : AppTheme.textSecondary,
                              fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                              fontSize: 13,
                            ),
                            onSelected: (selected) {
                              setState(() {
                                if (selected) {
                                  _selectedChips.add(reason);
                                } else {
                                  _selectedChips.remove(reason);
                                }
                              });
                            },
                          );
                        }).toList(),
                      ),
                      const SizedBox(height: 20),

                      // Freeform Text Input
                      TextFormField(
                        controller: _reasonController,
                        maxLines: 4,
                        style: const TextStyle(color: AppTheme.textPrimary),
                        decoration: const InputDecoration(
                          hintText: 'Share more about your dream channel or content vision... (Optional)',
                          alignLabelWithHint: true,
                        ),
                      ),
                      const SizedBox(height: 24),

                      // Motivation Quote Card
                      Container(
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          gradient: LinearGradient(
                            colors: [
                              AppTheme.primary.withOpacity(0.15),
                              AppTheme.accent.withOpacity(0.08),
                            ],
                            begin: Alignment.topLeft,
                            end: Alignment.bottomRight,
                          ),
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(color: AppTheme.primary.withOpacity(0.3)),
                        ),
                        child: const Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('💡', style: TextStyle(fontSize: 22)),
                            SizedBox(width: 12),
                            Expanded(
                              child: Text(
                                'Creators who post 3+ AI-assisted videos per week reach their 10,000 subscriber goal 4.2x faster.',
                                style: TextStyle(
                                  fontSize: 13,
                                  color: AppTheme.textPrimary,
                                  height: 1.4,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ),

              // Action Buttons
              Row(
                children: [
                  Expanded(
                    flex: 2,
                    child: OutlinedButton(
                      onPressed: () => _proceedToPaywall(isSkipped: true),
                      style: OutlinedButton.styleFrom(
                        side: const BorderSide(color: AppTheme.cardBorder),
                        minimumSize: const Size.fromHeight(52),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(14),
                        ),
                      ),
                      child: const Text(
                        'Skip',
                        style: TextStyle(color: AppTheme.textSecondary),
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    flex: 3,
                    child: ElevatedButton(
                      onPressed: () => _proceedToPaywall(isSkipped: false),
                      child: const Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Text('Continue'),
                          SizedBox(width: 6),
                          Icon(CupertinoIcons.arrow_right, size: 16),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
            ],
          ),
        ),
      ),
    );
  }
}
