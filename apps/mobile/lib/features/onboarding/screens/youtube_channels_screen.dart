import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:flutter_web_auth_2/flutter_web_auth_2.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import '../../../core/api/api_client.dart';
import '../../../core/theme/app_theme.dart';
import '../models/onboarding_models.dart';
import 'goals_screen.dart';
import '../../../core/widgets/google_logo.dart';

class YouTubeChannelsScreen extends StatefulWidget {
  const YouTubeChannelsScreen({super.key});

  @override
  State<YouTubeChannelsScreen> createState() => _YouTubeChannelsScreenState();
}

class _YouTubeChannelsScreenState extends State<YouTubeChannelsScreen> {
  final List<YouTubeChannel> _channels = [];
  bool _isLoading = true;
  bool _isConnectingGoogle = false;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _fetchMyChannels();
  }

  Future<void> _fetchMyChannels() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final res = await ApiClient.get('/api/channels/youtube/my-channels');
      if (res is List) {
        setState(() {
          _channels.clear();
          for (final item in res) {
            final subs = item['subscriberCount'];
            String subStr = 'Connected';
            if (subs != null && subs is int && subs > 0) {
              if (subs >= 1000000) {
                subStr = '${(subs / 1000000).toStringAsFixed(1)}M subscribers';
              } else if (subs >= 1000) {
                subStr = '${(subs / 1000).toStringAsFixed(1)}K subscribers';
              } else {
                subStr = '$subs subscribers';
              }
            }

            _channels.add(
              YouTubeChannel(
                id: item['channelId'] ?? '',
                title: item['channelTitle'] ?? 'YouTube Channel',
                avatarUrl: item['thumbnailUrl'],
                subscriberCount: subStr,
                isSelected: true,
              ),
            );
          }
        });
      }
    } catch (e) {
      // If error or no channels yet, channels list is empty
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _connectWithGoogle() async {
    setState(() {
      _isConnectingGoogle = true;
      _errorMessage = null;
    });

    final supabaseToken = Supabase.instance.client.auth.currentSession?.accessToken;
    if (supabaseToken == null) {
      setState(() {
        _isConnectingGoogle = false;
        _errorMessage = 'Please sign in again before connecting YouTube.';
      });
      return;
    }

    try {
      await FlutterWebAuth2.authenticate(
        url: '${ApiClient.baseUrl}/api/channels/youtube/connect'
            '?platform=ios&token=${Uri.encodeComponent(supabaseToken)}',
        callbackUrlScheme: 'autoedit',
      );

      // Re-fetch channels directly from Google/server
      await _fetchMyChannels();
    } catch (e) {
      final err = e.toString().toLowerCase();
      if (!err.contains('cancel') && !err.contains('canceled')) {
        setState(() {
          _errorMessage = 'Failed to connect Google account: $e';
        });
      }
    } finally {
      if (mounted) setState(() => _isConnectingGoogle = false);
    }
  }

  Future<void> _proceedToGoals() async {
    final selected = _channels.where((c) => c.isSelected).toList();
    if (selected.isEmpty) return;

    // Save to singleton state
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
    final colors = context.colors;
    final selectedCount = _channels.where((c) => c.isSelected).length;

    return Scaffold(
      backgroundColor: colors.background,
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
                        color: index <= 1 ? colors.accent : colors.cardBorder,
                        borderRadius: BorderRadius.circular(2),
                      ),
                    ),
                  );
                }),
              ),
              const SizedBox(height: 24),

              Text(
                'Select YouTube Channels',
                style: TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                  color: colors.textPrimary,
                  letterSpacing: -0.5,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                'Sign in with your Google account to automatically import and manage your YouTube channels.',
                style: TextStyle(
                  fontSize: 14,
                  color: colors.textSecondary,
                  height: 1.4,
                ),
              ),
              const SizedBox(height: 20),

              if (_errorMessage != null) ...[
                Container(
                  padding: const EdgeInsets.all(12),
                  margin: const EdgeInsets.only(bottom: 16),
                  decoration: BoxDecoration(
                    color: colors.danger.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: colors.danger.withValues(alpha: 0.3)),
                  ),
                  child: Text(
                    _errorMessage!,
                    style: TextStyle(color: colors.danger, fontSize: 13),
                  ),
                ),
              ],

              // Channels list or empty state
              Expanded(
                child: _isLoading
                    ? const Center(child: CircularProgressIndicator())
                    : _channels.isEmpty
                        ? _buildEmptyState()
                        : _buildChannelsList(),
              ),

              const SizedBox(height: 16),

              // Continue Button
              ElevatedButton(
                onPressed: selectedCount > 0 ? _proceedToGoals : null,
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  disabledBackgroundColor: colors.card,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(14),
                  ),
                ),
                child: Text(
                  selectedCount > 0
                      ? 'Continue with $selectedCount Channel${selectedCount > 1 ? "s" : ""}'
                      : 'Select a Channel to Continue',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                    color: selectedCount > 0 ? Colors.white : colors.textMuted,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildEmptyState() {
    final colors = context.colors;
    return Center(
      child: Container(
        padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(
          color: colors.card,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: colors.cardBorder),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 64,
              height: 64,
              decoration: BoxDecoration(
                color: AppTheme.youtubeRed.withValues(alpha: 0.12),
                shape: BoxShape.circle,
              ),
              child: const Center(
                child: Icon(
                  Icons.play_circle_fill_rounded,
                  color: AppTheme.youtubeRed,
                  size: 38,
                ),
              ),
            ),
            const SizedBox(height: 18),
            Text(
              'No YouTube Channel Connected',
              style: TextStyle(
                fontSize: 17,
                fontWeight: FontWeight.bold,
                color: colors.textPrimary,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Authenticate via Google to load your YouTube channels automatically without typing IDs manually.',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 13,
                color: colors.textSecondary,
                height: 1.4,
              ),
            ),
            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              height: 48,
              child: OutlinedButton.icon(
                onPressed: _isConnectingGoogle ? null : _connectWithGoogle,
                icon: _isConnectingGoogle
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const GoogleLogo(size: 18),
                label: Text(
                  _isConnectingGoogle ? 'Connecting in Safari...' : 'Connect YouTube with Google',
                  style: TextStyle(fontWeight: FontWeight.w600, color: colors.textPrimary),
                ),
                style: OutlinedButton.styleFrom(
                  side: BorderSide(color: colors.cardBorder),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  backgroundColor: colors.surface,
                ),
              ),
            ),

          ],
        ),
      ),
    );
  }

  Widget _buildChannelsList() {
    final colors = context.colors;
    return ListView(
      children: [
        ..._channels.map((channel) {
          final isSelected = channel.isSelected;
          return Container(
            margin: const EdgeInsets.only(bottom: 12),
            decoration: BoxDecoration(
              color: isSelected
                  ? colors.accent.withValues(alpha: 0.08)
                  : colors.card,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(
                color: isSelected ? colors.accent : colors.cardBorder,
                width: isSelected ? 1.5 : 1,
              ),
            ),
            child: InkWell(
              borderRadius: BorderRadius.circular(16),
              onTap: () {
                setState(() {
                  channel.isSelected = !channel.isSelected;
                });
              },
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Row(
                  children: [
                    // Channel Avatar
                    CircleAvatar(
                      radius: 24,
                      backgroundColor: colors.cardBorder,
                      backgroundImage: channel.avatarUrl != null
                          ? NetworkImage(channel.avatarUrl!)
                          : null,
                      child: channel.avatarUrl == null
                          ? Icon(
                              Icons.play_circle_outline,
                              color: colors.textPrimary,
                              size: 26,
                            )
                          : null,
                    ),
                    const SizedBox(width: 14),

                    // Channel Info
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            channel.title,
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.w600,
                              color: colors.textPrimary,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            channel.subscriberCount ?? 'Connected',
                            style: TextStyle(
                              fontSize: 13,
                              color: colors.textSecondary,
                            ),
                          ),
                        ],
                      ),
                    ),

                    // Selection Checkbox
                    Container(
                      width: 24,
                      height: 24,
                      decoration: BoxDecoration(
                        color: isSelected ? colors.accent : Colors.transparent,
                        shape: BoxShape.circle,
                        border: Border.all(
                          color: isSelected ? colors.accent : colors.textSecondary,
                          width: 2,
                        ),
                      ),
                      child: isSelected
                          ? const Icon(
                              Icons.check,
                              size: 16,
                              color: Colors.white,
                            )
                          : null,
                    ),
                  ],
                ),
              ),
            ),
          );
        }),

        const SizedBox(height: 12),

        // Connect another account via Google OAuth
        OutlinedButton.icon(
          onPressed: _isConnectingGoogle ? null : _connectWithGoogle,
          icon: _isConnectingGoogle
              ? const SizedBox(
                  width: 16,
                  height: 16,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Icon(CupertinoIcons.add, size: 18),
          label: Text(_isConnectingGoogle
              ? 'Opening Google Sign-In...'
              : 'Connect Another Google Account'),
          style: OutlinedButton.styleFrom(
            padding: const EdgeInsets.symmetric(vertical: 14),
            side: BorderSide(color: colors.cardBorder),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(14),
            ),
            foregroundColor: colors.textPrimary,
          ),
        ),
      ],
    );
  }
}
