import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/cupertino.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import '../api/api_client.dart';
import '../models/video_summary.dart';
import '../theme/app_theme.dart';
import 'status_badge.dart';

/// 9:16 grid card for the Videos screen — thumbnail + status badge overlay
/// + relative-time/duration caption. Also doubles as a loading skeleton via
/// [VideoThumbnailCard.skeleton].
class VideoThumbnailCard extends StatelessWidget {
  final VideoSummary? video;
  final VoidCallback? onTap;

  const VideoThumbnailCard({super.key, required this.video, this.onTap});

  const VideoThumbnailCard.skeleton({super.key})
      : video = null,
        onTap = null;

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    final v = video;

    return GestureDetector(
      onTap: onTap,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          AspectRatio(
            aspectRatio: 9 / 16,
            child: ClipRRect(
              borderRadius: BorderRadius.circular(14),
              child: Stack(
                fit: StackFit.expand,
                children: [
                  if (v == null)
                    _ShimmerBox(color: colors.card)
                  else if (v.thumbnailUrl == null)
                    Container(
                      color: colors.card,
                      child: Icon(CupertinoIcons.film, color: colors.textMuted, size: 32),
                    )
                  else
                    CachedNetworkImage(
                      imageUrl: '${ApiClient.baseUrl}${v.thumbnailUrl}',
                      httpHeaders: {
                        'Authorization':
                            'Bearer ${Supabase.instance.client.auth.currentSession?.accessToken ?? ''}',
                      },
                      fit: BoxFit.cover,
                      placeholder: (_, _) => _ShimmerBox(color: colors.card),
                      errorWidget: (_, _, _) => Container(
                        color: colors.card,
                        child: Icon(CupertinoIcons.film, color: colors.textMuted, size: 32),
                      ),
                    ),
                  if (v != null && v.status != 'READY')
                    Positioned(
                      top: 8,
                      left: 8,
                      child: StatusBadge(status: v.status),
                    ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 6),
          if (v != null) ...[
            Text(
              _relativeTime(v.createdAt),
              style: TextStyle(fontSize: 12, color: colors.textPrimary, fontWeight: FontWeight.w500),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
            Text(
              _durationLabel(v.duration),
              style: TextStyle(fontSize: 11, color: colors.textSecondary),
            ),
          ] else ...[
            _ShimmerBox(color: colors.card, height: 12, width: 60, radius: 4),
            const SizedBox(height: 4),
            _ShimmerBox(color: colors.card, height: 10, width: 40, radius: 4),
          ],
        ],
      ),
    );
  }

  static String _durationLabel(double? seconds) {
    if (seconds == null || seconds <= 0) return '--:--';
    final total = seconds.round();
    final m = total ~/ 60;
    final s = total % 60;
    return '$m:${s.toString().padLeft(2, '0')}';
  }

  static String _relativeTime(DateTime? dt) {
    if (dt == null) return '';
    final diff = DateTime.now().difference(dt);
    if (diff.inMinutes < 1) return 'Just now';
    if (diff.inHours < 1) return '${diff.inMinutes}m';
    if (diff.inDays < 1) return '${diff.inHours}h';
    if (diff.inDays < 7) return '${diff.inDays}d';
    return '${(diff.inDays / 7).floor()}w';
  }
}

/// Minimal pulsing placeholder — stdlib animation, no shimmer package.
class _ShimmerBox extends StatefulWidget {
  final Color color;
  final double? height;
  final double? width;
  final double radius;

  const _ShimmerBox({required this.color, this.height, this.width, this.radius = 0});

  @override
  State<_ShimmerBox> createState() => _ShimmerBoxState();
}

class _ShimmerBoxState extends State<_ShimmerBox> with SingleTickerProviderStateMixin {
  late final AnimationController _controller = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 900),
  )..repeat(reverse: true);

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, _) {
        return Container(
          height: widget.height,
          width: widget.width,
          decoration: BoxDecoration(
            color: widget.color.withValues(alpha: 0.5 + _controller.value * 0.5),
            borderRadius: BorderRadius.circular(widget.radius),
          ),
        );
      },
    );
  }
}
