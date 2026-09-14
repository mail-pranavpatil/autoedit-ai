import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../models/onboarding_models.dart';
import 'youtube_channels_screen.dart';

class PlatformSelectScreen extends StatefulWidget {
  const PlatformSelectScreen({super.key});

  @override
  State<PlatformSelectScreen> createState() => _PlatformSelectScreenState();
}

class _PlatformSelectScreenState extends State<PlatformSelectScreen> {
  final List<SocialPlatform> _platforms = [
    SocialPlatform(
      id: 'yt',
      name: 'YouTube',
      icon: '▶',
      isAvailable: true,
      isSelected: true,
    ),
    SocialPlatform(
      id: 'ig',
      name: 'Instagram Reels',
      icon: '📷',
      isAvailable: false,
      isSelected: false,
    ),
    SocialPlatform(
      id: 'fb',
      name: 'Facebook Video',
      icon: 'f',
      isAvailable: false,
      isSelected: false,
    ),
    SocialPlatform(
      id: 'li',
      name: 'LinkedIn Video',
      icon: 'in',
      isAvailable: false,
      isSelected: false,
    ),
    SocialPlatform(
      id: 'x',
      name: 'X (Twitter)',
      icon: '𝕏',
      isAvailable: false,
      isSelected: false,
    ),
  ];

  void _proceedToYouTubeSetup() {
    Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => const YouTubeChannelsScreen()),
    );
  }

  @override
  Widget build(BuildContext context) {
    final hasActiveSelection = _platforms.any((p) => p.isSelected && p.isAvailable);

    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: AppBar(
        title: const Text('Distribution Channels'),
        elevation: 0,
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Progress Bar
              Row(
                children: List.generate(5, (index) {
                  return Expanded(
                    child: Container(
                      height: 4,
                      margin: EdgeInsets.only(right: index < 4 ? 6 : 0),
                      decoration: BoxDecoration(
                        color: index == 0 ? AppTheme.primary : AppTheme.cardBorder,
                        borderRadius: BorderRadius.circular(2),
                      ),
                    ),
                  );
                }),
              ),
              const SizedBox(height: 24),

              const Text(
                'Where do you publish?',
                style: TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                  color: AppTheme.textPrimary,
                  letterSpacing: -0.5,
                ),
              ),
              const SizedBox(height: 8),
              const Text(
                'Select the platforms you want your AI videos uploaded to. YouTube is available now; others are unlocking soon.',
                style: TextStyle(
                  fontSize: 14,
                  color: AppTheme.textSecondary,
                  height: 1.4,
                ),
              ),
              const SizedBox(height: 24),

              // Platform List
              Expanded(
                child: ListView.separated(
                  itemCount: _platforms.length,
                  separatorBuilder: (_, _) => const SizedBox(height: 12),
                  itemBuilder: (context, index) {
                    final platform = _platforms[index];
                    final isAvailable = platform.isAvailable;

                    return AnimatedContainer(
                      duration: const Duration(milliseconds: 200),
                      decoration: BoxDecoration(
                        color: platform.isSelected && isAvailable
                            ? AppTheme.primary.withOpacity(0.12)
                            : AppTheme.card,
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(
                          color: platform.isSelected && isAvailable
                              ? AppTheme.primary
                              : AppTheme.cardBorder,
                          width: platform.isSelected && isAvailable ? 1.5 : 1,
                        ),
                      ),
                      child: InkWell(
                        borderRadius: BorderRadius.circular(16),
                        onTap: isAvailable
                            ? () {
                                setState(() {
                                  platform.isSelected = !platform.isSelected;
                                });
                              }
                            : () {
                                ScaffoldMessenger.of(context).showSnackBar(
                                  SnackBar(
                                    content: Text('${platform.name} integration is coming soon!'),
                                    duration: const Duration(seconds: 2),
                                    backgroundColor: AppTheme.card,
                                  ),
                                );
                              },
                        child: Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
                          child: Row(
                            children: [
                              // Icon badge
                              Container(
                                width: 44,
                                height: 44,
                                alignment: Alignment.center,
                                decoration: BoxDecoration(
                                  color: isAvailable
                                      ? AppTheme.youtubeRed.withOpacity(0.15)
                                      : Colors.white.withOpacity(0.06),
                                  borderRadius: BorderRadius.circular(12),
                                ),
                                child: isAvailable
                                    ? const Icon(
                                        CupertinoIcons.play_rectangle_fill,
                                        color: AppTheme.youtubeRed,
                                        size: 24,
                                      )
                                    : Text(
                                        platform.icon,
                                        style: TextStyle(
                                          fontSize: 18,
                                          fontWeight: FontWeight.bold,
                                          color: isAvailable
                                              ? AppTheme.textPrimary
                                              : AppTheme.textMuted,
                                        ),
                                      ),
                              ),
                              const SizedBox(width: 14),

                              // Name & Status
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Row(
                                      children: [
                                        Text(
                                          platform.name,
                                          style: TextStyle(
                                            fontSize: 16,
                                            fontWeight: FontWeight.w600,
                                            color: isAvailable
                                                ? AppTheme.textPrimary
                                                : AppTheme.textSecondary,
                                          ),
                                        ),
                                        if (!isAvailable) ...[
                                          const SizedBox(width: 8),
                                          Container(
                                            padding: const EdgeInsets.symmetric(
                                                horizontal: 8, vertical: 3),
                                            decoration: BoxDecoration(
                                              color: Colors.white.withOpacity(0.08),
                                              borderRadius: BorderRadius.circular(6),
                                            ),
                                            child: const Text(
                                              'Coming Soon',
                                              style: TextStyle(
                                                fontSize: 10,
                                                fontWeight: FontWeight.bold,
                                                color: AppTheme.textMuted,
                                                letterSpacing: 0.3,
                                              ),
                                            ),
                                          ),
                                        ],
                                      ],
                                    ),
                                    const SizedBox(height: 2),
                                    Text(
                                      isAvailable
                                          ? 'Ready to connect & upload'
                                          : 'In active development',
                                      style: TextStyle(
                                        fontSize: 12,
                                        color: isAvailable
                                            ? AppTheme.textSecondary
                                            : AppTheme.textMuted,
                                      ),
                                    ),
                                  ],
                                ),
                              ),

                              // Toggle Switch
                              CupertinoSwitch(
                                value: platform.isSelected,
                                activeTrackColor: AppTheme.primary,
                                onChanged: isAvailable
                                    ? (value) {
                                        setState(() {
                                          platform.isSelected = value;
                                        });
                                      }
                                    : null,
                              ),
                            ],
                          ),
                        ),
                      ),
                    );
                  },
                ),
              ),

              // Continue Button
              ElevatedButton(
                onPressed: hasActiveSelection ? _proceedToYouTubeSetup : null,
                child: const Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text('Continue to Connect Channel'),
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
