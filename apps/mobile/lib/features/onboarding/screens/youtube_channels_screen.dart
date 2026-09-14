import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:google_sign_in/google_sign_in.dart';
import '../../../core/api/api_client.dart';
import '../../../core/theme/app_theme.dart';
import '../models/onboarding_models.dart';
import 'goals_screen.dart';

class YouTubeChannelsScreen extends StatefulWidget {
  const YouTubeChannelsScreen({super.key});

  @override
  State<YouTubeChannelsScreen> createState() => _YouTubeChannelsScreenState();
}

class _YouTubeChannelsScreenState extends State<YouTubeChannelsScreen> {
  final List<YouTubeChannel> _channels = [
    YouTubeChannel(
      id: 'UC_tech_default',
      title: 'Main Tech Channel',
      avatarUrl: null,
      subscriberCount: '24.5K subscribers',
      isSelected: true,
    ),
  ];

  bool _isConnectingGoogle = false;
  String? _activeGoogleEmail;

  final GoogleSignIn _googleSignIn = GoogleSignIn(
    scopes: [
      'email',
      'profile',
      'https://www.googleapis.com/auth/youtube.upload',
      'https://www.googleapis.com/auth/youtube.readonly',
    ],
  );

  Future<void> _chooseGoogleAccount() async {
    setState(() => _isConnectingGoogle = true);
    try {
      // Force account picker by signing out first
      await _googleSignIn.signOut();
      final account = await _googleSignIn.signIn();
      if (account != null) {
        setState(() {
          _activeGoogleEmail = account.email;
          final newChannel = YouTubeChannel(
            id: 'UC_${account.id.substring(0, 8)}',
            title: '${account.displayName ?? "Creator"}\'s Channel',
            avatarUrl: account.photoUrl,
            subscriberCount: 'Ready to connect',
            isSelected: true,
          );
          if (!_channels.any((c) => c.title == newChannel.title)) {
            _channels.add(newChannel);
          }
        });
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Account selection: ${e.toString()}'),
            backgroundColor: AppTheme.card,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _isConnectingGoogle = false);
    }
  }

  void _showAddCustomChannelDialog() {
    final titleController = TextEditingController();
    final handleController = TextEditingController();

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppTheme.card,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) => Padding(
        padding: EdgeInsets.only(
          left: 20,
          right: 20,
          top: 20,
          bottom: MediaQuery.of(ctx).viewInsets.bottom + 20,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'Add Another Channel',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: AppTheme.textPrimary,
                  ),
                ),
                IconButton(
                  icon: const Icon(CupertinoIcons.xmark, color: AppTheme.textSecondary),
                  onPressed: () => Navigator.of(ctx).pop(),
                ),
              ],
            ),
            const SizedBox(height: 12),
            TextField(
              controller: titleController,
              decoration: const InputDecoration(
                labelText: 'Channel Name',
                hintText: 'e.g. Daily AI Shorts / Tech Reviews',
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: handleController,
              decoration: const InputDecoration(
                labelText: 'Channel Handle / ID',
                hintText: '@yourchannelhandle',
              ),
            ),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: () {
                final title = titleController.text.trim();
                final handle = handleController.text.trim();
                if (title.isNotEmpty) {
                  setState(() {
                    _channels.add(
                      YouTubeChannel(
                        id: 'UC_${DateTime.now().millisecondsSinceEpoch}',
                        title: title,
                        subscriberCount: handle.isNotEmpty ? handle : 'New channel',
                        isSelected: true,
                      ),
                    );
                  });
                  Navigator.of(ctx).pop();
                }
              },
              child: const Text('Add Channel'),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _proceedToGoals() async {
    final selected = _channels.where((c) => c.isSelected).toList();
    if (selected.isEmpty) return;

    // Save to state singleton
    OnboardingState.instance.selectedChannels = selected;

    // Persist channels to backend in background
    for (final ch in selected) {
      try {
        await ApiClient.post(
          '/api/channels/connect',
          body: ch.toJson(),
        );
      } catch (_) {}
    }

    if (!mounted) return;
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => GoalsScreen(channels: selected),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final selectedCount = _channels.where((c) => c.isSelected).length;

    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: AppBar(
        title: const Text('Connect YouTube'),
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
              // Progress Bar (Step 2 of 5)
              Row(
                children: List.generate(5, (index) {
                  return Expanded(
                    child: Container(
                      height: 4,
                      margin: EdgeInsets.only(right: index < 4 ? 6 : 0),
                      decoration: BoxDecoration(
                        color: index <= 1 ? AppTheme.primary : AppTheme.cardBorder,
                        borderRadius: BorderRadius.circular(2),
                      ),
                    ),
                  );
                }),
              ),
              const SizedBox(height: 24),

              const Text(
                'Select YouTube Channels',
                style: TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                  color: AppTheme.textPrimary,
                  letterSpacing: -0.5,
                ),
              ),
              const SizedBox(height: 8),
              const Text(
                'Choose the Google account and channels you want to manage. You can connect multiple channels below.',
                style: TextStyle(
                  fontSize: 14,
                  color: AppTheme.textSecondary,
                  height: 1.4,
                ),
              ),
              const SizedBox(height: 20),

              // Switch / Choose Google Account banner
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: AppTheme.card,
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: AppTheme.cardBorder),
                ),
                child: Row(
                  children: [
                    Container(
                      width: 36,
                      height: 36,
                      decoration: const BoxDecoration(
                        shape: BoxShape.circle,
                        color: Colors.white,
                      ),
                      alignment: Alignment.center,
                      child: const Text(
                        'G',
                        style: TextStyle(
                          color: AppTheme.googleRed,
                          fontWeight: FontWeight.bold,
                          fontSize: 18,
                        ),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            'Google Account',
                            style: TextStyle(
                              fontSize: 12,
                              color: AppTheme.textMuted,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                          Text(
                            _activeGoogleEmail ?? 'Default Linked Account',
                            style: const TextStyle(
                              fontSize: 14,
                              fontWeight: FontWeight.w600,
                              color: AppTheme.textPrimary,
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ],
                      ),
                    ),
                    TextButton(
                      onPressed: _isConnectingGoogle ? null : _chooseGoogleAccount,
                      child: _isConnectingGoogle
                          ? const SizedBox(
                              width: 16,
                              height: 16,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : const Text(
                              'Switch',
                              style: TextStyle(
                                color: AppTheme.primaryLight,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 18),

              // Channel List Header
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    'Available Channels (${_channels.length})',
                    style: const TextStyle(
                      fontSize: 15,
                      fontWeight: FontWeight.w600,
                      color: AppTheme.textPrimary,
                    ),
                  ),
                  Text(
                    '$selectedCount selected',
                    style: const TextStyle(
                      fontSize: 13,
                      color: AppTheme.primaryLight,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),

              // Channels List
              Expanded(
                child: ListView.separated(
                  itemCount: _channels.length,
                  separatorBuilder: (_, _) => const SizedBox(height: 10),
                  itemBuilder: (context, index) {
                    final channel = _channels[index];
                    return AnimatedContainer(
                      duration: const Duration(milliseconds: 150),
                      decoration: BoxDecoration(
                        color: channel.isSelected
                            ? AppTheme.primary.withOpacity(0.09)
                            : AppTheme.card,
                        borderRadius: BorderRadius.circular(14),
                        border: Border.all(
                          color: channel.isSelected ? AppTheme.primary : AppTheme.cardBorder,
                          width: channel.isSelected ? 1.5 : 1,
                        ),
                      ),
                      child: CheckboxListTile(
                        value: channel.isSelected,
                        activeColor: AppTheme.primary,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(14),
                        ),
                        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 4),
                        secondary: CircleAvatar(
                          radius: 20,
                          backgroundColor: AppTheme.youtubeRed.withOpacity(0.18),
                          backgroundImage: channel.avatarUrl != null
                              ? NetworkImage(channel.avatarUrl!)
                              : null,
                          child: channel.avatarUrl == null
                              ? const Icon(
                                  CupertinoIcons.play_rectangle_fill,
                                  color: AppTheme.youtubeRed,
                                  size: 20,
                                )
                              : null,
                        ),
                        title: Text(
                          channel.title,
                          style: const TextStyle(
                            fontSize: 15,
                            fontWeight: FontWeight.w600,
                            color: AppTheme.textPrimary,
                          ),
                        ),
                        subtitle: Text(
                          channel.subscriberCount ?? 'YouTube Channel',
                          style: const TextStyle(
                            fontSize: 12,
                            color: AppTheme.textSecondary,
                          ),
                        ),
                        onChanged: (val) {
                          setState(() {
                            channel.isSelected = val ?? false;
                          });
                        },
                      ),
                    );
                  },
                ),
              ),

              // Add Multiple Channels Button
              OutlinedButton.icon(
                onPressed: _showAddCustomChannelDialog,
                style: OutlinedButton.styleFrom(
                  foregroundColor: AppTheme.primaryLight,
                  side: const BorderSide(color: AppTheme.cardBorder, width: 1.2),
                  minimumSize: const Size.fromHeight(48),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                icon: const Icon(CupertinoIcons.plus_circle_fill, size: 20),
                label: const Text(
                  'Add Another YouTube Channel',
                  style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600),
                ),
              ),
              const SizedBox(height: 14),

              // Proceed to Goals Button
              ElevatedButton(
                onPressed: selectedCount > 0 ? _proceedToGoals : null,
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text('Continue to Goals ($selectedCount Channels)'),
                    const SizedBox(width: 8),
                    const Icon(CupertinoIcons.arrow_right, size: 18),
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
