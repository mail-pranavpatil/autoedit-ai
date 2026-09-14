import 'dart:convert';
import 'dart:io';

import 'package:file_picker/file_picker.dart';
import 'package:http/http.dart' as http;
import 'package:image_picker/image_picker.dart';

import 'app_config.dart';

/// Picks a video from the Photos library or the Files app and uploads it to
/// the project. `POST /api/projects/{id}/videos/upload` lands the bytes
/// straight into the new video's local_path, so process_video() skips its
/// normal Drive-download step entirely (see services/api/routes/projects.py).
class NativeUpload {
  final ImagePicker _imagePicker = ImagePicker();

  Future<Map<String, dynamic>?> pickAndUpload({
    required String projectId,
    required bool fromFiles,
    required Future<String?> Function() cookieHeader,
  }) async {
    final path = fromFiles ? await _pickFromFiles() : await _pickFromPhotos();
    if (path == null) return null;
    return _upload(File(path), projectId, await cookieHeader());
  }

  Future<String?> _pickFromPhotos() async {
    final file = await _imagePicker.pickVideo(source: ImageSource.gallery);
    return file?.path;
  }

  Future<String?> _pickFromFiles() async {
    final file = await FilePicker.pickFile(type: FileType.video);
    return file?.path;
  }

  Future<Map<String, dynamic>?> _upload(File file, String projectId, String? cookieHeader) async {
    try {
      final uri = Uri.parse('$serverUrl/api/projects/$projectId/videos/upload');
      final request = http.MultipartRequest('POST', uri);
      if (cookieHeader != null) request.headers['cookie'] = cookieHeader;
      request.files.add(await http.MultipartFile.fromPath('file', file.path));
      final response = await http.Response.fromStream(await request.send());
      if (response.statusCode != 200) {
        return {'error': 'Upload failed (${response.statusCode})'};
      }
      return jsonDecode(response.body) as Map<String, dynamic>;
    } catch (_) {
      return {'error': 'Upload failed'};
    }
  }
}
