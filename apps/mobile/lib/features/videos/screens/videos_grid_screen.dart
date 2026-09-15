import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import '../../../core/api/api_client.dart';
import '../../../core/models/video_summary.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/utils/video_import.dart';
import '../../../core/widgets/empty_state.dart';
import '../../../core/widgets/video_thumbnail_card.dart';

enum _SortOrder { newest, oldest }

/// Flat grid of the user's videos across all projects — replaces the old
/// project-aggregate row list. Fed by `GET /api/projects/videos`.
class VideosGridScreen extends StatefulWidget {
  final String userInitial;
  final VoidCallback onAvatarTap;

  const VideosGridScreen({super.key, required this.userInitial, required this.onAvatarTap});

  @override
  State<VideosGridScreen> createState() => _VideosGridScreenState();
}

class _VideosGridScreenState extends State<VideosGridScreen> {
  List<VideoSummary>? _videos;
  bool _loading = true;
  String? _error;
  bool _searchOpen = false;
  final _searchController = TextEditingController();
  _SortOrder _sort = _SortOrder.newest;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final res = await ApiClient.get('/api/projects/videos');
      final list = (res as List).map((e) => VideoSummary.fromJson(e as Map<String, dynamic>)).toList();
      if (!mounted) return;
      setState(() {
        _videos = list;
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.toString();
        _loading = false;
      });
    }
  }

  List<VideoSummary> get _visible {
    var list = _videos ?? [];
    final query = _searchController.text.trim().toLowerCase();
    if (query.isNotEmpty) {
      list = list
          .where((v) =>
              v.filename.toLowerCase().contains(query) || v.projectName.toLowerCase().contains(query))
          .toList();
    }
    list = [...list];
    if (_sort == _SortOrder.oldest) {
      list = list.reversed.toList();
    }
    return list;
  }

  void _pickSort() {
    showCupertinoModalPopup(
      context: context,
      builder: (ctx) => CupertinoActionSheet(
        title: const Text('Sort by'),
        actions: [
          CupertinoActionSheetAction(
            onPressed: () {
              Navigator.of(ctx).pop();
              setState(() => _sort = _SortOrder.newest);
            },
            child: const Text('Newest first'),
          ),
          CupertinoActionSheetAction(
            onPressed: () {
              Navigator.of(ctx).pop();
              setState(() => _sort = _SortOrder.oldest);
            },
            child: const Text('Oldest first'),
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

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;

    return SafeArea(
      bottom: false,
      child: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(18, 8, 18, 8),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Videos',
                  style: TextStyle(
                    fontSize: 28,
                    fontWeight: FontWeight.bold,
                    color: colors.textPrimary,
                    letterSpacing: -0.6,
                  ),
                ),
                Row(
                  children: [
                    IconButton(
                      onPressed: () => setState(() => _searchOpen = !_searchOpen),
                      icon: Icon(CupertinoIcons.search, color: colors.textPrimary),
                      constraints: const BoxConstraints(minWidth: 44, minHeight: 44),
                    ),
                    IconButton(
                      onPressed: _pickSort,
                      icon: Icon(CupertinoIcons.arrow_up_arrow_down, color: colors.textPrimary),
                      constraints: const BoxConstraints(minWidth: 44, minHeight: 44),
                    ),
                    GestureDetector(
                      onTap: widget.onAvatarTap,
                      child: CircleAvatar(
                        radius: 18,
                        backgroundColor: colors.accent.withValues(alpha: 0.2),
                        child: Text(
                          widget.userInitial,
                          style: TextStyle(color: colors.accent, fontWeight: FontWeight.bold),
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          if (_searchOpen)
            Padding(
              padding: const EdgeInsets.fromLTRB(18, 0, 18, 8),
              child: TextField(
                controller: _searchController,
                autofocus: true,
                onChanged: (_) => setState(() {}),
                decoration: const InputDecoration(
                  hintText: 'Search videos...',
                  prefixIcon: Icon(CupertinoIcons.search, size: 18),
                ),
              ),
            ),
          Expanded(child: _buildBody(context)),
        ],
      ),
    );
  }

  Widget _buildBody(BuildContext context) {
    if (_loading) {
      return _buildGrid(context, List.generate(6, (_) => null));
    }
    if (_error != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: EmptyState(
            icon: CupertinoIcons.exclamationmark_triangle,
            title: 'Could not load videos',
            message: _error!,
            actionLabel: 'Retry',
            onAction: _load,
            iconColor: context.colors.warning,
          ),
        ),
      );
    }
    final visible = _visible;
    if (visible.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: EmptyState(
            icon: CupertinoIcons.film,
            title: 'No Videos Yet',
            message: 'Tap the + button to import your first talking-head clip.',
            actionLabel: 'Import Video',
            onAction: () => showVideoImportSheet(context, onImported: _load),
          ),
        ),
      );
    }
    return RefreshIndicator(
      onRefresh: _load,
      child: _buildGrid(context, visible),
    );
  }

  Widget _buildGrid(BuildContext context, List<VideoSummary?> items) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final crossAxisCount = constraints.maxWidth > 600 ? 3 : 2;
        return GridView.builder(
          padding: const EdgeInsets.fromLTRB(18, 8, 18, 110),
          physics: const AlwaysScrollableScrollPhysics(),
          gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: crossAxisCount,
            crossAxisSpacing: 12,
            mainAxisSpacing: 16,
            childAspectRatio: 0.62,
          ),
          itemCount: items.length,
          itemBuilder: (context, i) {
            final v = items[i];
            if (v == null) return const VideoThumbnailCard.skeleton();
            return VideoThumbnailCard(video: v);
          },
        );
      },
    );
  }
}
