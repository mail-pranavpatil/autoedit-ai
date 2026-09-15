import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

/// Mirrors `apps/web/lib/stageCopy.ts`'s `PROCESS_STEPS` title strings —
/// kept in sync by hand (Dart can't import TS), not shared code.
const Map<String, String> kStageLabels = {
  'QUEUED': 'Queued',
  'DOWNLOADING': 'Download',
  'DOWNLOADED': 'Downloaded',
  'PROBING': 'Inspect',
  'TRANSCRIBING': 'Transcribe',
  'TRANSCRIBED': 'Transcript',
  'PLANNING': 'Thinking',
  'PLAN_READY': 'Edit plan',
  'SEARCHING_BROLL': 'Stock search',
  'BROLL_READY': 'Assets',
  'RENDERING': 'Render',
  'RENDERED': 'Written',
  'VALIDATING': 'Validate',
  'READY': 'Done',
  'FAILED': 'Failed',
  'DISCOVERED': 'Queued',
};

/// Friendly title for a raw backend stage/status string.
String stageTitle(String? stage) {
  if (stage == null || stage.isEmpty) return '';
  return kStageLabels[stage] ?? stage;
}

enum StatusBucket { queued, processing, ready, failed }

StatusBucket statusBucket(String? status) {
  switch (status) {
    case 'READY':
      return StatusBucket.ready;
    case 'FAILED':
      return StatusBucket.failed;
    case 'QUEUED':
    case 'DISCOVERED':
    case null:
      return StatusBucket.queued;
    default:
      return StatusBucket.processing;
  }
}

Color statusBucketColor(BuildContext context, StatusBucket bucket) {
  final colors = context.colors;
  return switch (bucket) {
    StatusBucket.ready => colors.success,
    StatusBucket.failed => colors.danger,
    StatusBucket.queued => colors.warning,
    StatusBucket.processing => colors.accent,
  };
}
