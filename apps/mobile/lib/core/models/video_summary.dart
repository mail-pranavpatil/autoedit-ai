/// One video from `GET /api/projects/videos` — scoped to the Videos grid
/// screen only. The rest of the app still consumes raw `Map<String, dynamic>`
/// as it does today; not retrofitting typed models app-wide.
class VideoSummary {
  final String id;
  final String filename;
  final String? thumbnailUrl;
  final String status;
  final String? currentStage;
  final double? duration;
  final DateTime? createdAt;
  final String projectId;
  final String projectName;

  const VideoSummary({
    required this.id,
    required this.filename,
    required this.thumbnailUrl,
    required this.status,
    required this.currentStage,
    required this.duration,
    required this.createdAt,
    required this.projectId,
    required this.projectName,
  });

  factory VideoSummary.fromJson(Map<String, dynamic> json) {
    return VideoSummary(
      id: json['id'] as String,
      filename: json['filename'] as String? ?? 'Untitled',
      thumbnailUrl: json['thumbnailUrl'] as String?,
      status: json['status'] as String? ?? 'QUEUED',
      currentStage: json['currentStage'] as String?,
      duration: (json['duration'] as num?)?.toDouble(),
      createdAt: DateTime.tryParse(json['createdAt'] as String? ?? ''),
      projectId: json['projectId'] as String? ?? '',
      projectName: json['projectName'] as String? ?? '',
    );
  }
}
