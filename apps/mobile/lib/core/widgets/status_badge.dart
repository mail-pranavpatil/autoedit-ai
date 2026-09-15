import 'package:flutter/material.dart';
import 'stage_labels.dart';

/// Small status pill driven by the real pipeline stage, replacing the
/// inline `Container`+`Text` pill code duplicated per screen.
class StatusBadge extends StatelessWidget {
  final String? status;

  const StatusBadge({super.key, required this.status});

  @override
  Widget build(BuildContext context) {
    final bucket = statusBucket(status);
    final color = statusBucketColor(context, bucket);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.16),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withValues(alpha: 0.35)),
      ),
      child: Text(
        stageTitle(status),
        style: TextStyle(color: color, fontSize: 10, fontWeight: FontWeight.bold),
      ),
    );
  }
}
