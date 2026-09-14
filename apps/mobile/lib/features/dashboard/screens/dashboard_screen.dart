import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import '../../../core/api/api_client.dart';
import '../../../core/storage/session_manager.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/widgets/glass_container.dart';
import '../../../core/widgets/ios_pill_navbar.dart';
import '../../auth/screens/login_screen.dart';
import '../../auth/services/auth_service.dart';
import '../../onboarding/models/onboarding_models.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  final ImagePicker _picker = ImagePicker();
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

      setState(() {
        _user = user;
        _channels = channelsRes is List ? channelsRes : [];
        _projects = projectsRes is List ? projectsRes : [];
        _isLoading = false;
      });

    } catch (_) {
      setState(() => _isLoading = false);
    }
  }

  void _showCreateActionSheet() {
    showCupertinoModalPopup(
      context: context,
      builder: (ctx) => CupertinoActionSheet(
        title: const Text('Add Video to Eren AI'),
        message: const Text('Choose a source to import talking-head footage for AI automated editing'),
        actions: [
          CupertinoActionSheetAction(
            onPressed: () {
              Navigator.of(ctx).pop();
              _pickVideo(ImageSource.gallery);
            },
            child: const Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(CupertinoIcons.photo_on_rectangle, size: 20),
                SizedBox(width: 8),
                Text('Choose from Photos / Camera Roll'),
              ],
            ),
          ),
          CupertinoActionSheetAction(
            onPressed: () {
              Navigator.of(ctx).pop();
              _pickVideo(ImageSource.camera);
            },
            child: const Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(CupertinoIcons.camera, size: 20),
                SizedBox(width: 8),
                Text('Record Video with Camera'),
              ],
            ),
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

  Future<void> _pickVideo(ImageSource source) async {
    try {
      final XFile? video = await _picker.pickVideo(
        source: source,
        maxDuration: const Duration(minutes: 10),
      );
      if (video != null) {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Selected video: ${video.name}. Uploading to AI pipeline...'),
            backgroundColor: AppTheme.success,
          ),
        );
        // Refresh project list after import
        _loadDashboardData();
      }
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Could not access video: $e'),
          backgroundColor: AppTheme.danger,
        ),
      );
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

  String get _activeChannelTitle {
    if (_channels.isNotEmpty && _channels.first['channelTitle'] != null) {
      return _channels.first['channelTitle'];
    }
    if (OnboardingState.instance.selectedChannels.isNotEmpty) {
      return OnboardingState.instance.selectedChannels.first.title;
    }
    return 'My YouTube Channel';
  }

  Map<String, dynamic> get _activeGoals {
    if (_channels.isNotEmpty && _channels.first['goals'] is Map) {
      return _channels.first['goals'] as Map<String, dynamic>;
    }
    return {};
  }

  int get _targetViews => (_activeGoals['targetViews'] as num?)?.toInt() ?? 50000;
  int get _targetSubs => (_activeGoals['targetSubs'] as num?)?.toInt() ?? 10000;
  String get _targetDate => (_activeGoals['targetDate'] as String?) ?? 'December 31, 2026';

  String _formatNumber(int n) {
    if (n >= 1000000) return '${(n / 1000000).toStringAsFixed(1)}M';
    if (n >= 1000) return '${(n / 1000).toStringAsFixed(1)}K';
    return n.toString();
  }


  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.background,
      extendBody: true, // Content flows behind floating glass pill bar
      appBar: PreferredSize(
        preferredSize: const Size.fromHeight(60),
        child: _buildHeaderGlassBar(),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _loadDashboardData,
              child: IndexedStack(
                index: _selectedBottomTab,
                children: [
                  _buildHomeTab(),
                  _buildVideosTab(),
                  _buildGoalsTab(),
                  _buildSettingsTab(),
                ],
              ),
            ),
      bottomNavigationBar: IOSPillNavBar(
        currentIndex: _selectedBottomTab,
        onTap: (idx) => setState(() => _selectedBottomTab = idx),
        items: _navItems,
        onAddTap: _showCreateActionSheet,
      ),
    );
  }


  // Apple Frosted Glass Top App Bar
  Widget _buildHeaderGlassBar() {
    return GlassContainer(
      borderRadius: 0,
      blur: 24,
      padding: EdgeInsets.only(
        top: MediaQuery.of(context).padding.top + 4,
        left: 18,
        right: 18,
        bottom: 10,
      ),
      color: AppTheme.background.withValues(alpha: 0.75),
      border: const Border(
        bottom: BorderSide(color: AppTheme.glassBorder, width: 0.8),
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
                  gradient: const LinearGradient(
                    colors: [AppTheme.primary, AppTheme.accent],
                  ),
                  borderRadius: BorderRadius.circular(10),
                  boxShadow: [
                    BoxShadow(
                      color: AppTheme.primary.withValues(alpha: 0.3),
                      blurRadius: 10,
                      offset: const Offset(0, 2),
                    ),
                  ],
                ),
                child: const Icon(CupertinoIcons.play_fill, size: 18, color: Colors.white),
              ),
              const SizedBox(width: 10),
              const Text(
                'Eren AI Studio',
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 18,
                  color: AppTheme.textPrimary,
                  letterSpacing: -0.4,
                ),
              ),
            ],
          ),
          // Channel Pill Badge
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.08),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: AppTheme.glassBorder),
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
                    style: const TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                      color: AppTheme.textPrimary,
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
    final userName = _user?['name'] ?? 'Creator';

    return SingleChildScrollView(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.fromLTRB(18, 16, 18, 110), // Bottom padding for pill navbar
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Greeting & Status
          Text(
            'Hey, $userName 👋',
            style: const TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
              color: AppTheme.textPrimary,
              letterSpacing: -0.5,
            ),
          ),
          const SizedBox(height: 4),
          const Text(
            'AI automation is active • Channel pipeline running',
            style: TextStyle(fontSize: 13, color: AppTheme.textSecondary),
          ),
          const SizedBox(height: 20),

          // Growth Goals Glass Card
          GlassContainer(
            padding: const EdgeInsets.all(18),
            borderRadius: 22,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Row(
                      children: [
                        Icon(CupertinoIcons.chart_pie_fill,
                            color: AppTheme.primaryLight, size: 20),
                        SizedBox(width: 8),
                        Text(
                          'Quarterly Goal Progress',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                            color: AppTheme.textPrimary,
                          ),
                        ),
                      ],
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: AppTheme.primary.withValues(alpha: 0.18),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: const Text(
                        'VELOCITY +24% 🚀',
                        style: TextStyle(
                          color: AppTheme.primaryLight,
                          fontSize: 10,
                          fontWeight: FontWeight.w800,
                          letterSpacing: 0.4,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),

                _buildGoalProgress(
                  label: 'Channel Views (Target: ${_formatNumber(_targetViews)})',
                  current: (_targetViews * 0.62).toInt(),
                  target: _targetViews,
                  color: AppTheme.primary,
                ),
                const SizedBox(height: 14),

                _buildGoalProgress(
                  label: 'Channel Subscribers (Target: ${_formatNumber(_targetSubs)})',
                  current: (_targetSubs * 0.74).toInt(),
                  target: _targetSubs,
                  color: AppTheme.accent,
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),

          // Primary Quick Action: Camera Roll Import
          ElevatedButton.icon(
            onPressed: () => _pickVideo(ImageSource.gallery),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppTheme.primary,
              minimumSize: const Size.fromHeight(54),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(18),
              ),
              shadowColor: AppTheme.primary.withValues(alpha: 0.4),
              elevation: 8,
            ),
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
              const Text(
                'Active Video Queue',
                style: TextStyle(
                  fontSize: 17,
                  fontWeight: FontWeight.bold,
                  color: AppTheme.textPrimary,
                ),
              ),
              GestureDetector(
                onTap: () => setState(() => _selectedBottomTab = 1),
                child: const Text(
                  'See All',
                  style: TextStyle(
                    fontSize: 13,
                    color: AppTheme.primaryLight,
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
              Color statusClr = AppTheme.warning;
              if (ready > 0) {
                statusStr = 'READY ($ready)';
                statusClr = AppTheme.success;
              } else if (processing > 0) {
                statusStr = 'PROCESSING';
                statusClr = AppTheme.primaryLight;
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
                  const Icon(CupertinoIcons.film, color: AppTheme.primaryLight, size: 34),
                  const SizedBox(height: 10),
                  const Text(
                    'Queue is Empty',
                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: AppTheme.textPrimary),
                  ),
                  const SizedBox(height: 4),
                  const Text(
                    'Tap the + button below or import a talking-head video clip to start creating AI videos.',
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 13, color: AppTheme.textSecondary, height: 1.4),
                  ),
                ],
              ),
            ),
          ],

        ],
      ),
    );
  }

  // TAB 1: VIDEOS / PROJECTS
  Widget _buildVideosTab() {
    return SingleChildScrollView(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.fromLTRB(18, 16, 18, 110),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const Text(
            'Your Video Projects',
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
              color: AppTheme.textPrimary,
              letterSpacing: -0.5,
            ),
          ),
          const SizedBox(height: 4),
          const Text(
            'All rendered and scheduled AI videos for distribution',
            style: TextStyle(fontSize: 13, color: AppTheme.textSecondary),
          ),
          const SizedBox(height: 18),

          // Filter Pills
          Row(
            children: [
              _buildFilterPill('All (8)', isSelected: true),
              const SizedBox(width: 8),
              _buildFilterPill('Scheduled (3)'),
              const SizedBox(width: 8),
              _buildFilterPill('In Progress (2)'),
            ],
          ),
          const SizedBox(height: 16),

          // Dynamic Video Project Items
          if (_projects.isNotEmpty) ...[
            ..._projects.map((p) {
              final ready = (p['readyVideos'] as int?) ?? 0;
              final processing = (p['processingVideos'] as int?) ?? 0;
              final total = (p['totalVideos'] as int?) ?? 0;

              String statusStr = 'QUEUED';
              Color statusClr = AppTheme.warning;
              if (ready > 0) {
                statusStr = 'READY';
                statusClr = AppTheme.success;
              } else if (processing > 0) {
                statusStr = 'PROCESSING';
                statusClr = AppTheme.primaryLight;
              }

              return Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: _buildProjectItem(
                  title: p['name'] ?? 'Untitled Video Project',
                  channel: _activeChannelTitle,
                  duration: '$total video${total == 1 ? "" : "s"}',
                  status: statusStr,
                  statusColor: statusClr,
                ),
              );
            }),
          ] else ...[
            Center(
              child: Padding(
                padding: const EdgeInsets.symmetric(vertical: 40),
                child: Column(
                  children: [
                    const Icon(CupertinoIcons.film_fill, size: 54, color: AppTheme.cardBorder),
                    const SizedBox(height: 14),
                    const Text(
                      'No Video Projects Yet',
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: AppTheme.textPrimary),
                    ),
                    const SizedBox(height: 6),
                    const Text(
                      'Create your first AI video project by importing footage.',
                      style: TextStyle(fontSize: 14, color: AppTheme.textSecondary),
                    ),
                    const SizedBox(height: 20),
                    ElevatedButton.icon(
                      onPressed: () => _pickVideo(ImageSource.gallery),
                      icon: const Icon(CupertinoIcons.add, size: 18),
                      label: const Text('Import First Video'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppTheme.primary,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }

  // TAB 2: GOALS
  Widget _buildGoalsTab() {
    return SingleChildScrollView(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.fromLTRB(18, 16, 18, 110),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const Text(
            'Channel Growth Targets',
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
              color: AppTheme.textPrimary,
              letterSpacing: -0.5,
            ),
          ),
          const SizedBox(height: 4),
          const Text(
            'Live milestone velocity and pacing for YouTube',
            style: TextStyle(fontSize: 13, color: AppTheme.textSecondary),
          ),
          const SizedBox(height: 20),

          GlassContainer(
            borderRadius: 22,
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      _activeChannelTitle,
                      style: const TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                        color: AppTheme.textPrimary,
                      ),
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: AppTheme.success.withValues(alpha: 0.15),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: const Text(
                        'Pacing Ahead',
                        style: TextStyle(
                          color: AppTheme.success,
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 18),
                _buildGoalProgress(
                  label: 'Quarterly Views (Target: ${_formatNumber(_targetViews)})',
                  current: (_targetViews * 0.62).toInt(),
                  target: _targetViews,
                  color: AppTheme.primary,
                ),
                const SizedBox(height: 16),
                _buildGoalProgress(
                  label: 'Subscribers (Target: ${_formatNumber(_targetSubs)})',
                  current: (_targetSubs * 0.74).toInt(),
                  target: _targetSubs,
                  color: AppTheme.accent,
                ),
                const SizedBox(height: 18),
                const Divider(color: AppTheme.glassBorder),
                const SizedBox(height: 12),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text(
                      'Deadline Target:',
                      style: TextStyle(fontSize: 13, color: AppTheme.textSecondary),
                    ),
                    Text(
                      _targetDate,
                      style: const TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.bold,
                        color: AppTheme.primaryLight,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }


  // TAB 3: SETTINGS
  Widget _buildSettingsTab() {
    final email = _user?['email'] ?? 'creator@example.com';
    final name = _user?['name'] ?? 'Creator';

    return SingleChildScrollView(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.fromLTRB(18, 16, 18, 110),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const Text(
            'Settings & Account',
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
              color: AppTheme.textPrimary,
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
                  backgroundColor: AppTheme.primary.withValues(alpha: 0.25),
                  child: Text(
                    name.isNotEmpty ? name[0].toUpperCase() : 'C',
                    style: const TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                      color: AppTheme.primaryLight,
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
                        style: const TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                          color: AppTheme.textPrimary,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        email,
                        style: const TextStyle(fontSize: 13, color: AppTheme.textSecondary),
                      ),
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(
                      colors: [AppTheme.primary, AppTheme.accent],
                    ),
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
                  leading: const Icon(CupertinoIcons.play_rectangle_fill,
                      color: AppTheme.youtubeRed),
                  title: const Text('Connected Channels'),
                  subtitle: Text('$_activeChannelTitle • Active'),
                  trailing: const Icon(CupertinoIcons.chevron_forward,
                      color: AppTheme.textMuted, size: 18),
                  onTap: () {},
                ),
                const Divider(color: AppTheme.glassBorder, height: 1),
                ListTile(
                  leading: const Icon(CupertinoIcons.creditcard_fill,
                      color: AppTheme.success),
                  title: const Text('Subscription Plan'),
                  subtitle: const Text('Pro Creator Pass • \$49/month'),
                  trailing: const Icon(CupertinoIcons.chevron_forward,
                      color: AppTheme.textMuted, size: 18),
                  onTap: () {},
                ),
                const Divider(color: AppTheme.glassBorder, height: 1),
                ListTile(
                  leading: const Icon(CupertinoIcons.lock_shield_fill,
                      color: AppTheme.primaryLight),
                  title: const Text('Security & Privacy'),
                  trailing: const Icon(CupertinoIcons.chevron_forward,
                      color: AppTheme.textMuted, size: 18),
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
              side: const BorderSide(color: AppTheme.danger, width: 1.2),
              foregroundColor: AppTheme.danger,
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

  Widget _buildFilterPill(String label, {bool isSelected = false}) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 7),
      decoration: BoxDecoration(
        color: isSelected
            ? AppTheme.primary.withValues(alpha: 0.25)
            : Colors.white.withValues(alpha: 0.06),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: isSelected ? AppTheme.primaryLight : AppTheme.glassBorder,
          width: 1,
        ),
      ),
      child: Text(
        label,
        style: TextStyle(
          fontSize: 12,
          fontWeight: isSelected ? FontWeight.bold : FontWeight.w500,
          color: isSelected ? AppTheme.primaryLight : AppTheme.textSecondary,
        ),
      ),
    );
  }

  Widget _buildGoalProgress({
    required String label,
    required int current,
    required int target,
    required Color color,
  }) {
    final progress = (current / target).clamp(0.0, 1.0);
    final percent = (progress * 100).toInt();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              label,
              style: const TextStyle(fontSize: 13, color: AppTheme.textSecondary),
            ),
            Text(
              '$current / $target ($percent%)',
              style: const TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.bold,
                color: AppTheme.textPrimary,
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        ClipRRect(
          borderRadius: BorderRadius.circular(6),
          child: LinearProgressIndicator(
            value: progress,
            backgroundColor: Colors.white.withValues(alpha: 0.08),
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
    return GlassContainer(
      borderRadius: 16,
      padding: const EdgeInsets.all(14),
      child: Row(
        children: [
          Container(
            width: 46,
            height: 46,
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.08),
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Icon(CupertinoIcons.play_circle_fill,
                color: AppTheme.primaryLight, size: 26),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                    color: AppTheme.textPrimary,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 4),
                Row(
                  children: [
                    Text(
                      channel,
                      style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary),
                    ),
                    const SizedBox(width: 6),
                    const Text('•', style: TextStyle(color: AppTheme.textMuted, fontSize: 11)),
                    const SizedBox(width: 6),
                    Text(
                      duration,
                      style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary),
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
