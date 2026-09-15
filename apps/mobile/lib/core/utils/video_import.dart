import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import '../theme/app_theme.dart';

final ImagePicker _picker = ImagePicker();

/// Shared "add video" entry point — used by the FAB and the Home tab's
/// import button so the action sheet isn't duplicated in two places.
void showVideoImportSheet(BuildContext context, {required VoidCallback onImported}) {
  showCupertinoModalPopup(
    context: context,
    builder: (ctx) => CupertinoActionSheet(
      title: const Text('Add Video to Eren AI'),
      message: const Text('Choose a source to import talking-head footage for AI automated editing'),
      actions: [
        CupertinoActionSheetAction(
          onPressed: () {
            Navigator.of(ctx).pop();
            pickAndUploadVideo(context, ImageSource.gallery, onImported: onImported);
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
            pickAndUploadVideo(context, ImageSource.camera, onImported: onImported);
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

Future<void> pickAndUploadVideo(
  BuildContext context,
  ImageSource source, {
  required VoidCallback onImported,
}) async {
  final colors = context.colors;
  try {
    final XFile? video = await _picker.pickVideo(
      source: source,
      maxDuration: const Duration(minutes: 10),
    );
    if (video != null) {
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Selected video: ${video.name}. Uploading to AI pipeline...'),
          backgroundColor: colors.success,
        ),
      );
      onImported();
    }
  } catch (e) {
    if (!context.mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Could not access video: $e'),
        backgroundColor: colors.danger,
      ),
    );
  }
}
