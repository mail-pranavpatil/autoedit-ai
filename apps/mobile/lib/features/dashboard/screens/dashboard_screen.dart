import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:intl/intl.dart';
import '../../../core/api/api_client.dart';
import '../../../core/storage/session_manager.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/theme/theme_controller.dart';
import '../../../core/utils/video_import.dart';
import '../../../core/widgets/glass_container.dart';
import '../../../core/widgets/ios_pill_navbar.dart';
import '../../../core/widgets/trend_sparkline.dart';
import '../../auth/screens/login_screen.dart';
import '../../auth/services/auth_service.dart';
import '../../onboarding/models/onboarding_models.dart';
import '../../videos/screens/videos_grid_screen.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  Map<String, dynamic>? _user;
  List<dynamic> _channels = [];
  bool _isLoading = true;
  int _selectedBottomTab = 0;

  final List<IOSPillNavItem> _navItems = const [
    IOSPillNavItem(
      icon: CupertinoIcons.house,
      activeIcon: CupertinoIcons.house_fill,
      label: 'Home',
    ),
    IOSPillNavItem(
      icon: CupertinoIcons.film,
      activeIcon: CupertinoIcons.film_fill,
      label: 'Videos',
    ),
    IOSPillNavItem(
      icon: CupertinoIcons.chart_bar,
      activeIcon: CupertinoIcons.chart_bar_fill,
      label: 'Goals',
    ),
    IOSPillNavItem(
      icon: CupertinoIcons.gear_alt,
      activeIcon: CupertinoIcons.gear_alt_fill,
      label: 'Settings',
    ),
  ];

  List<dynamic> _projects = [];
  List<dynamic> _history = [];

  @override
  void initState() {
    super.initState();
    _loadDashboardData();
  }

  Future<void> _loadDashboardData() async {
    setState(() => _isLoading = true);
    try {
      final user = await AuthService.fetchMe().catchError((_) async => await SessionManager.getUser() ?? {});
      final channelsRes = await ApiClient.get('/api/channels').catchError((_) => []);
      final projectsRes = await ApiClient.get('/api/projects').catchError((_) => []);

      final channels = channelsRes is List ? channelsRes : [];
      List<dynamic> history = [];
      if (channels.isNotEmpty && channels.first is Map && channels.first['id'] != null) {
        final historyRes = await ApiClient
            .get('/api/channels/${channels.first['id']}/history')
            .catchError((_) => []);
        history = historyRes is List ? historyRes : [];
      }

      setState(() {
        _user = user;
        _channels = channels;
        _projects = projectsRes is List ? projectsRes : [];
        _history = history;
        _isLoading = false;
      });

    } catch (_) {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _logout() async {
    final confirmed = await showCupertinoDialog<bool>(
      context: context,
      builder: (ctx) => CupertinoAlertDialog(
        title: const Text('Log Out'),
        content: const Text('Are you sure you want to log out of your account?'),
        actions: [
          CupertinoDialogAction(
            child: const Text('Cancel'),
            onPressed: () => Navigator.of(ctx).pop(false),
          ),
          CupertinoDialogAction(
            isDestructiveAction: true,
            child: const Text('Log Out'),
            onPressed: () => Navigator.of(ctx).pop(true),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      await AuthService.logout();
      if (!mounted) return;
      Navigator.of(context).pushAndRemoveUntil(
        MaterialPageRoute(builder: (_) => const LoginScreen()),
        (route) => false,
      );
    }
  }

  void _pickThemeMode() {
    showCupertinoModalPopup(
      context: context,
      builder: (ctx) => CupertinoActionSheet(
        title: const Text('Appearance'),
        actions: [
          for (final mode in ThemeMode.values)
            CupertinoActionSheetAction(
              onPressed: () {
                Navigator.of(ctx).pop();
                themeModeNotifier.value = mode;
                SessionManager.setThemeMode(mode);
                setState(() {});
              },
              child: Text(_themeModeLabel(mode)),
            ),
        ],
        cancelButton: CupertinoActionSheetAction(
          isDefaultAction: true,
          onPressed: () => Navigator.of(ctx).pop(),
          child: const Text('Cancel'),
        ),
      ),
    );
  }

  String _themeModeLabel(ThemeMode mode) => switch (mode) {
        ThemeMode.light => 'Light',
        ThemeMode.dark => 'Dark',
        ThemeMode.system => 'System',
      };

  String get _activeChannelTitle {
    if (_channels.isNotEmpty && _channels.first['channelTitle'] != null) {
      return _channels.first['channelTitle'];
    }
    if (OnboardingState.instance.selectedChannels.isNotEmpty) {
      return OnboardingState.instance.selectedChannels.first.title;
    }
    return 'My YouTube Channel';
  }

  Map<String, dynamic> get _activeChannel {
    if (_channels.isNotEmpty && _channels.first is Map) {
      return _channels.first as Map<String, dynamic>;
    }
    return {};
  }

  Map<String, dynamic> get _activeGoals {
    if (_activeChannel['goals'] is Map) {
      return _activeChannel['goals'] as Map<String, dynamic>;
    }
    return {};
  }

  bool get _hasGoals => _activeGoals['targetViews'] != null || _activeGoals['targetSubs'] != null;
  bool get _hasLiveStats => _currentViews != null || _currentSubs != null;

  int get _targetViews => (_activeGoals['targetViews'] as num?)?.toInt() ?? 50000;
  int get _targetSubs => (_activeGoals['targetSubs'] as num?)?.toInt() ?? 10000;
  String? get _targetDate => _activeGoals['targetDate'] as String?;

  int? get _currentViews => (_activeChannel['currentViews'] as num?)?.toInt();
  int? get _currentSubs => (_activeChannel['currentSubs'] as num?)?.toInt();
  double? get _velocityPercent => (_activeChannel['velocityPercent'] as num?)?.toDouble();
  String? get _pacingLabel => _activeChannel['pacingLabel'] as String?;

  String _formatNumber(int n) {
    if (n >= 1000000) return '${(n / 1000000).toStringAsFixed(1)}M';
    if (n >= 1000) return '${(n / 1000).toStringAsFixed(1)}K';
    return n.toString();
  }

  String _formatDate(String isoDate) {
    try {
      return DateFormat('MMMM d, yyyy').format(DateTime.parse(isoDate));
    } catch (_) {
      return isoDate;
    }
  }


  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Scaffold(
      backgroundColor: colors.background,
      extendBody: true, // Content flows behind floating pill bar
      appBar: _selectedBottomTab == 1
          ? null
          : PreferredSize(
              preferredSize: const Size.fromHeight(60),
              child: _buildHeaderBar(),
            ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _loadDashboardData,
              child: IndexedStack(
                index: _selectedBottomTab,
                children: [
                  _buildHomeTab(),
                  VideosGridScreen(
                    userInitial: _userInitial,
                    onAvatarTap: () => setState(() => _selectedBottomTab = 3),
                  ),
                  _buildGoalsTab(),
                  _buildSettingsTab(),
                ],
              ),
            ),
      floatingActionButton: FloatingActionButton(
        backgroundColor: isDark ? Colors.white : Colors.black,
        shape: const CircleBorder(),
        onPressed: () => showVideoImportSheet(context, onImported: _loadDashboardData),
        child: Icon(Icons.add_rounded, color: isDark ? Colors.black : Colors.white),
      ),
      bottomNavigationBar: IOSPillNavBar(
        currentIndex: _selectedBottomTab,
        onTap: (idx) => setState(() => _selectedBottomTab = idx),
        items: _navItems,
      ),
    );
  }

  String get _userInitial {
    final name = _user?['name'] as String?;
    return (name != null && name.isNotEmpty) ? name[0].toUpperCase() : 'C';
  }

  // Top App Bar (Home/Goals/Settings — Videos tab owns its own header)
  Widget _buildHeaderBar() {
    final colors = context.colors;
    return Container(
      padding: EdgeInsets.only(
        top: MediaQuery.of(context).padding.top + 4,
        left: 18,
        right: 18,
        bottom: 10,
      ),
      decoration: BoxDecoration(
        color: colors.background,
        border: Border(bottom: BorderSide(color: colors.cardBorder, width: 1)),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Row(
            children: [
              Container(
                width: 34,
                height: 34,
                decoration: BoxDecoration(
                  color: colors.accent,
                  borderRadius: BorderRadius.circular(10),
                ),
                child: const Icon(CupertinoIcons.play_fill, size: 18, color: Colors.white),
              ),
              const SizedBox(width: 10),
              Text(
                'Eren AI Studio',
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 18,
                  color: colors.textPrimary,
                  letterSpacing: -0.4,
                ),
              ),
            ],
          ),
          // Channel Pill Badge
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
            decoration: BoxDecoration(
              color: colors.card,
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: colors.cardBorder),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(
                  CupertinoIcons.play_rectangle_fill,
                  color: AppTheme.youtubeRed,
                  size: 14,
                ),
                const SizedBox(width: 6),
                ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 110),
                  child: Text(
                    _activeChannelTitle,
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                      color: colors.textPrimary,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // TAB 0: HOME / DASHBOARD
  Widget _buildHomeTab() {
    final colors = context.colors;
    final userName = _user?['name'] ?? 'Creator';

    return SingleChildScrollView(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.fromLTRB(18, 16, 18, 110), // Bottom padding for pill navbar
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Greeting & Status
          Text(
            'Hey, $userName',
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
              color: colors.textPrimary,
              letterSpacing: -0.5,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            'AI automation is active • Channel pipeline running',
            style: TextStyle(fontSize: 13, color: colors.textSecondary),
          ),
          const SizedBox(height: 20),

          // Growth Goals Card
          if (!_hasGoals)
            _buildGoalsEmptyState()
          else if (!_hasLiveStats)
            _buildStatsUnavailableCard()
          else
            GlassContainer(
              padding: const EdgeInsets.all(18),
              borderRadius: 22,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Row(
                        children: [
                          Icon(CupertinoIcons.chart_pie_fill, color: colors.accent, size: 20),
                          const SizedBox(width: 8),
                          Text(
                            'Quarterly Goal Progress',
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                              color: colors.textPrimary,
                            ),
                          ),
                        ],
                      ),
                      _buildVelocityBadge(),
                    ],
                  ),
                  const SizedBox(height: 16),

                  _buildGoalProgress(
                    label: 'Channel Views (Target: ${_formatNumber(_targetViews)})',
                    current: _currentViews ?? 0,
                    target: _targetViews,
                    color: colors.accent,
                  ),
                  const SizedBox(height: 14),

                  _buildGoalProgress(
                    label: 'Channel Subscribers (Target: ${_formatNumber(_targetSubs)})',
                    current: _currentSubs ?? 0,
                    target: _targetSubs,
                    color: colors.accent,
                  ),
                ],
              ),
            ),
          const SizedBox(height: 20),

          // Primary Quick Action: Camera Roll Import
          ElevatedButton.icon(
            onPressed: () => pickAndUploadVideo(context, ImageSource.gallery, onImported: _loadDashboardData),
            icon: const Icon(CupertinoIcons.camera_fill, size: 20),
            label: const Text(
              'Import Video from Camera Roll',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
          ),
          const SizedBox(height: 24),

          // Pipeline Header
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'Active Video Queue',
                style: TextStyle(
                  fontSize: 17,
                  fontWeight: FontWeight.bold,
                  color: colors.textPrimary,
                ),
              ),
              GestureDetector(
                onTap: () => setState(() => _selectedBottomTab = 1),
                child: Text(
                  'See All',
                  style: TextStyle(
                    fontSize: 13,
                    color: colors.accent,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),

          // Dynamic Video Pipeline Items
          if (_projects.isNotEmpty) ...[
            ..._projects.take(3).map((p) {
              final ready = (p['readyVideos'] as int?) ?? 0;
              final processing = (p['processingVideos'] as int?) ?? 0;
              final total = (p['totalVideos'] as int?) ?? 0;

              String statusStr = 'QUEUED';
              Color statusClr = colors.warning;
              if (ready > 0) {
                statusStr = 'READY ($ready)';
                statusClr = colors.success;
              } else if (processing > 0) {
                statusStr = 'PROCESSING';
                statusClr = colors.accent;
              }

              return Padding(
                padding: const EdgeInsets.only(bottom: 10),
                child: _buildProjectItem(
                  title: p['name'] ?? 'Untitled Video Project',
                  channel: _activeChannelTitle,
                  duration: total > 0 ? '$total clips' : 'Auto Short',
                  status: statusStr,
                  statusColor: statusClr,
                ),
              );
            }),
          ] else ...[
            GlassContainer(
              padding: const EdgeInsets.all(20),
              borderRadius: 18,
              child: Column(
                children: [
                  Icon(CupertinoIcons.film, color: colors.accent, size: 34),
                  const SizedBox(height: 10),
                  Text(
                    'Queue is Empty',
                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: colors.textPrimary),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'Tap the + button below or import a talking-head video clip to start creating AI videos.',
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 13, color: colors.textSecondary, height: 1.4),
                  ),
                ],
              ),
            ),
          ],

        ],
      ),
    );
  }

  // TAB 2: GOALS
  Widget _buildGoalsTab() {
    final colors = context.colors;
    return SingleChildScrollView(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.fromLTRB(18, 16, 18, 110),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            'Channel Growth Targets',
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
              color: colors.textPrimary,
              letterSpacing: -0.5,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            'Live milestone velocity and pacing for YouTube',
            style: TextStyle(fontSize: 13, color: colors.textSecondary),
          ),
          const SizedBox(height: 20),

          if (!_hasGoals)
            _buildGoalsEmptyState()
          else if (!_hasLiveStats)
            _buildStatsUnavailableCard()
          else
            GlassContainer(
              borderRadius: 22,
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Expanded(
                        child: Text(
                          _activeChannelTitle,
                          style: TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                            color: colors.textPrimary,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      const SizedBox(width: 8),
                      _buildPacingBadge(),
                    ],
                  ),
                  const SizedBox(height: 18),
                  _buildGoalProgress(
                    label: 'Quarterly Views (Target: ${_formatNumber(_targetViews)})',
                    current: _currentViews ?? 0,
                    target: _targetViews,
                    color: colors.accent,
                  ),
                  const SizedBox(height: 16),
                  _buildGoalProgress(
                    label: 'Subscribers (Target: ${_formatNumber(_targetSubs)})',
                    current: _currentSubs ?? 0,
                    target: _targetSubs,
                    color: colors.accent,
                  ),
                  const SizedBox(height: 18),
                  Divider(color: colors.cardBorder),
                  const SizedBox(height: 12),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        'Deadline Target:',
                        style: TextStyle(fontSize: 13, color: colors.textSecondary),
                      ),
                      Text(
                        _targetDate != null ? _formatDate(_targetDate!) : '—',
                        style: TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.bold,
                          color: colors.accent,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),

          if (_hasGoals) ...[
            const SizedBox(height: 20),
            _buildTrendSection(),
          ],
        ],
      ),
    );
  }

  Widget _buildTrendSection() {
    final colors = context.colors;
    if (_history.length < 2) {
      return GlassContainer(
        padding: const EdgeInsets.all(20),
        borderRadius: 18,
        child: Column(
          children: [
            Icon(CupertinoIcons.graph_square, color: colors.accent, size: 34),
            const SizedBox(height: 10),
            Text(
              'Growth Trend',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: colors.textPrimary),
            ),
            const SizedBox(height: 4),
            Text(
              'Check back tomorrow — we started tracking your growth from today.',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 13, color: colors.textSecondary, height: 1.4),
            ),
          ],
        ),
      );
    }

    final views = _history.map((h) => ((h['views'] as num?) ?? 0).toDouble()).toList();
    final subs = _history.map((h) => ((h['subscribers'] as num?) ?? 0).toDouble()).toList();

    return GlassContainer(
      padding: const EdgeInsets.all(20),
      borderRadius: 18,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Growth Trend',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: colors.textPrimary),
          ),
          const SizedBox(height: 16),
          _buildTrendRow('Views', views, colors.accent),
          const SizedBox(height: 18),
          _buildTrendRow('Subscribers', subs, colors.accent),
        ],
      ),
    );
  }

  Widget _buildTrendRow(String label, List<double> series, Color color) {
    final colors = context.colors;
    final delta = series.last - series.first;
    final isUp = delta >= 0;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(label, style: TextStyle(fontSize: 13, color: colors.textSecondary)),
            Text(
              '${isUp ? '+' : ''}${_formatNumber(delta.toInt())}',
              style: TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.bold,
                color: isUp ? colors.success : colors.danger,
              ),
            ),
          ],
        ),
        const SizedBox(height: 6),
        TrendSparkline(values: series, color: color),
      ],
    );
  }


  // TAB 3: SETTINGS
  Widget _buildSettingsTab() {
    final colors = context.colors;
    final email = _user?['email'] ?? 'creator@example.com';
    final name = _user?['name'] ?? 'Creator';

    return SingleChildScrollView(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.fromLTRB(18, 16, 18, 110),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            'Settings & Account',
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
              color: colors.textPrimary,
              letterSpacing: -0.5,
            ),
          ),
          const SizedBox(height: 18),

          // User Card
          GlassContainer(
            borderRadius: 20,
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                CircleAvatar(
                  radius: 26,
                  backgroundColor: colors.accent.withValues(alpha: 0.18),
                  child: Text(
                    name.isNotEmpty ? name[0].toUpperCase() : 'C',
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                      color: colors.accent,
                    ),
                  ),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        name,
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                          color: colors.textPrimary,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        email,
                        style: TextStyle(fontSize: 13, color: colors.textSecondary),
                      ),
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: colors.accent,
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: const Text(
                    'PRO',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 18),

          // Settings Items
          GlassContainer(
            borderRadius: 20,
            padding: const EdgeInsets.symmetric(vertical: 6),
            child: Column(
              children: [
                ListTile(
                  leading: const Icon(CupertinoIcons.play_rectangle_fill, color: AppTheme.youtubeRed),
                  title: const Text('Connected Channels'),
                  subtitle: Text('$_activeChannelTitle • Active'),
                  trailing: Icon(CupertinoIcons.chevron_forward, color: colors.textMuted, size: 18),
                  onTap: () {},
                ),
                Divider(color: colors.cardBorder, height: 1),
                ListTile(
                  leading: Icon(CupertinoIcons.creditcard_fill, color: colors.success),
                  title: const Text('Subscription Plan'),
                  subtitle: const Text('Pro Creator Pass • \$49/month'),
                  trailing: Icon(CupertinoIcons.chevron_forward, color: colors.textMuted, size: 18),
                  onTap: () {},
                ),
                Divider(color: colors.cardBorder, height: 1),
                ListTile(
                  leading: Icon(CupertinoIcons.circle_lefthalf_fill, color: colors.accent),
                  title: const Text('Appearance'),
                  subtitle: Text(_themeModeLabel(themeModeNotifier.value)),
                  trailing: Icon(CupertinoIcons.chevron_forward, color: colors.textMuted, size: 18),
                  onTap: _pickThemeMode,
                ),
                Divider(color: colors.cardBorder, height: 1),
                ListTile(
                  leading: Icon(CupertinoIcons.lock_shield_fill, color: colors.accent),
                  title: const Text('Security & Privacy'),
                  trailing: Icon(CupertinoIcons.chevron_forward, color: colors.textMuted, size: 18),
                  onTap: () {},
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),

          // Logout Button
          OutlinedButton.icon(
            onPressed: _logout,
            style: OutlinedButton.styleFrom(
              side: BorderSide(color: colors.danger, width: 1.2),
              foregroundColor: colors.danger,
              minimumSize: const Size.fromHeight(50),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(16),
              ),
            ),
            icon: const Icon(CupertinoIcons.arrow_right_square, size: 18),
            label: const Text('Log Out', style: TextStyle(fontWeight: FontWeight.bold)),
          ),
        ],
      ),
    );
  }

  Widget _buildVelocityBadge() {
    final colors = context.colors;
    final velocity = _velocityPercent;
    if (velocity == null) return const SizedBox.shrink();
    final isAhead = velocity >= 0;
    final color = isAhead ? colors.success : colors.danger;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.18),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Text(
        'VELOCITY ${isAhead ? '+' : ''}${velocity.toStringAsFixed(0)}%',
        style: TextStyle(
          color: color,
          fontSize: 10,
          fontWeight: FontWeight.w800,
          letterSpacing: 0.4,
        ),
      ),
    );
  }

  Widget _buildPacingBadge() {
    final colors = context.colors;
    final label = _pacingLabel;
    if (label == null) return const SizedBox.shrink();
    final color = switch (label) {
      'Pacing Ahead' => colors.success,
      'Pacing Behind' => colors.danger,
      _ => colors.warning,
    };
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Text(
        label,
        style: TextStyle(color: color, fontSize: 11, fontWeight: FontWeight.bold),
      ),
    );
  }

  Widget _buildGoalsEmptyState() {
    final colors = context.colors;
    return GlassContainer(
      padding: const EdgeInsets.all(20),
      borderRadius: 18,
      child: Column(
        children: [
          Icon(CupertinoIcons.chart_pie, color: colors.accent, size: 34),
          const SizedBox(height: 10),
          Text(
            'No Growth Goals Set',
            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: colors.textPrimary),
          ),
          const SizedBox(height: 4),
          Text(
            'Set a views and subscriber target during onboarding to track your pacing here.',
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 13, color: colors.textSecondary, height: 1.4),
          ),
        ],
      ),
    );
  }

  Widget _buildStatsUnavailableCard() {
    final colors = context.colors;
    return GlassContainer(
      padding: const EdgeInsets.all(20),
      borderRadius: 18,
      child: Column(
        children: [
          Icon(CupertinoIcons.exclamationmark_triangle, color: colors.warning, size: 34),
          const SizedBox(height: 10),
          Text(
            'Stats Unavailable',
            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: colors.textPrimary),
          ),
          const SizedBox(height: 4),
          Text(
            'Reconnect your YouTube channel to pull in live view and subscriber counts.',
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 13, color: colors.textSecondary, height: 1.4),
          ),
        ],
      ),
    );
  }

  Widget _buildGoalProgress({
    required String label,
    required int current,
    required int target,
    required Color color,
  }) {
    final colors = context.colors;
    final progress = target > 0 ? (current / target).clamp(0.0, 1.0) : 0.0;
    final percent = (progress * 100).toInt();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Expanded(
              child: Text(
                label,
                style: TextStyle(fontSize: 13, color: colors.textSecondary),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ),
            const SizedBox(width: 8),
            Text(
              '${_formatNumber(current)} / ${_formatNumber(target)} ($percent%)',
              style: TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.bold,
                color: colors.textPrimary,
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        ClipRRect(
          borderRadius: BorderRadius.circular(6),
          child: LinearProgressIndicator(
            value: progress,
            backgroundColor: colors.cardBorder,
            valueColor: AlwaysStoppedAnimation<Color>(color),
            minHeight: 7,
          ),
        ),
      ],
    );
  }

  Widget _buildProjectItem({
    required String title,
    required String channel,
    required String duration,
    required String status,
    required Color statusColor,
  }) {
    final colors = context.colors;
    return GlassContainer(
      borderRadius: 16,
      padding: const EdgeInsets.all(14),
      child: Row(
        children: [
          Container(
            width: 46,
            height: 46,
            decoration: BoxDecoration(
              color: colors.accent.withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(CupertinoIcons.play_circle_fill, color: colors.accent, size: 26),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                    color: colors.textPrimary,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 4),
                Row(
                  children: [
                    Text(
                      channel,
                      style: TextStyle(fontSize: 11, color: colors.textSecondary),
                    ),
                    const SizedBox(width: 6),
                    Text('•', style: TextStyle(color: colors.textMuted, fontSize: 11)),
                    const SizedBox(width: 6),
                    Text(
                      duration,
                      style: TextStyle(fontSize: 11, color: colors.textSecondary),
                    ),
                  ],
                ),
              ],
            ),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            decoration: BoxDecoration(
              color: statusColor.withValues(alpha: 0.16),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: statusColor.withValues(alpha: 0.35)),
            ),
            child: Text(
              status,
              style: TextStyle(
                color: statusColor,
                fontSize: 10,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
