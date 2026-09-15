import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../models/onboarding_models.dart';
import 'motivation_screen.dart';

class ExperienceScreen extends StatefulWidget {
  const ExperienceScreen({super.key});

  @override
  State<ExperienceScreen> createState() => _ExperienceScreenState();
}

class _ExperienceScreenState extends State<ExperienceScreen> {
  EditingExperience _selectedExperience = EditingExperience.rookie;

  void _proceedToMotivation() {
    OnboardingState.instance.experience = _selectedExperience;
    Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => const MotivationScreen()),
    );
  }

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    return Scaffold(
      backgroundColor: colors.background,
      appBar: AppBar(
        title: const Text('Experience Level'),
        leading: IconButton(
          icon: const Icon(CupertinoIcons.back),
          onPressed: () => Navigator.of(context).pop(),
        ),
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Progress Bar (Step 4 of 5)
              Row(
                children: List.generate(5, (index) {
                  return Expanded(
                    child: Container(
                      height: 4,
                      margin: EdgeInsets.only(right: index < 4 ? 6 : 0),
                      decoration: BoxDecoration(
                        color: index <= 3 ? colors.accent : colors.cardBorder,
                        borderRadius: BorderRadius.circular(2),
                      ),
                    ),
                  );
                }),
              ),
              const SizedBox(height: 24),

              Text(
                'How much do you know about video editing?',
                style: TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                  color: colors.textPrimary,
                  letterSpacing: -0.5,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                'Eren AI customizes video pacing, caption styles, and automation levels based on your experience.',
                style: TextStyle(
                  fontSize: 14,
                  color: colors.textSecondary,
                  height: 1.4,
                ),
              ),
              const SizedBox(height: 24),

              Expanded(
                child: ListView(
                  children: EditingExperience.values.map((exp) {
                    final isSelected = _selectedExperience == exp;

                    IconData iconData;
                    switch (exp) {
                      case EditingExperience.noob:
                        iconData = CupertinoIcons.wand_stars;
                        break;
                      case EditingExperience.rookie:
                        iconData = CupertinoIcons.scissors;
                        break;
                      case EditingExperience.pro:
                        iconData = CupertinoIcons.rocket_fill;
                        break;
                    }
                    final accentColor = colors.accent;

                    return Padding(
                      padding: const EdgeInsets.only(bottom: 14),
                      child: AnimatedContainer(
                        duration: const Duration(milliseconds: 180),
                        decoration: BoxDecoration(
                          color: isSelected ? accentColor.withValues(alpha: 0.12) : colors.card,
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(
                            color: isSelected ? accentColor : colors.cardBorder,
                            width: isSelected ? 2 : 1,
                          ),
                        ),
                        child: InkWell(
                          borderRadius: BorderRadius.circular(16),
                          onTap: () {
                            setState(() => _selectedExperience = exp);
                          },
                          child: Padding(
                            padding: const EdgeInsets.all(18),
                            child: Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Container(
                                  width: 46,
                                  height: 46,
                                  decoration: BoxDecoration(
                                    color: accentColor.withValues(alpha: 0.18),
                                    borderRadius: BorderRadius.circular(12),
                                  ),
                                  child: Icon(iconData, color: accentColor, size: 24),
                                ),
                                const SizedBox(width: 14),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Row(
                                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                        children: [
                                          Text(
                                            exp.title,
                                            style: TextStyle(
                                              fontSize: 18,
                                              fontWeight: FontWeight.bold,
                                              color: colors.textPrimary,
                                            ),
                                          ),
                                          if (isSelected)
                                            Icon(CupertinoIcons.checkmark_circle_fill,
                                                color: accentColor, size: 22),
                                        ],
                                      ),
                                      const SizedBox(height: 2),
                                      Text(
                                        exp.subtitle,
                                        style: TextStyle(
                                          fontSize: 13,
                                          fontWeight: FontWeight.w600,
                                          color: isSelected
                                              ? colors.textPrimary
                                              : colors.textSecondary,
                                        ),
                                      ),
                                      const SizedBox(height: 6),
                                      Text(
                                        exp.description,
                                        style: TextStyle(
                                          fontSize: 13,
                                          color: colors.textSecondary,
                                          height: 1.3,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),
                    );
                  }).toList(),
                ),
              ),

              ElevatedButton(
                onPressed: _proceedToMotivation,
                child: const Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text('Continue to Next Step'),
                    SizedBox(width: 8),
                    Icon(CupertinoIcons.arrow_right, size: 18),
                  ],
                ),
              ),
              const SizedBox(height: 8),
            ],
          ),
        ),
      ),
    );
  }
}
