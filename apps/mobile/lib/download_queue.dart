import 'dart:async';
import 'dart:io';

import 'package:http/http.dart' as http;
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';

/// WKWebView ignores `Content-Disposition: attachment` on
/// `/api/videos/{id}/download`, so a tapped download link never does
/// anything. Fetch it ourselves (carrying the session cookie) and hand it to
/// the share sheet instead.
///
/// "Download all ready videos" fires several downloads back to back; queue
/// them so the user gets one share sheet at a time instead of a stack.
class DownloadQueue {
  final List<Uri> _pending = [];
  bool _running = false;

  void enqueue(Uri url, String? cookieHeader) {
    _pending.add(url);
    _pump(cookieHeader);
  }

  Future<void> _pump(String? cookieHeader) async {
    if (_running || _pending.isEmpty) return;
    _running = true;
    final url = _pending.removeAt(0);
    try {
      final response = await http.get(
        url,
        headers: cookieHeader == null ? null : {'cookie': cookieHeader},
      );
      if (response.statusCode == 200) {
        final dir = await getTemporaryDirectory();
        final file = File('${dir.path}/${_filenameFor(response, url)}');
        await file.writeAsBytes(response.bodyBytes);
        await SharePlus.instance.share(ShareParams(files: [XFile(file.path)]));
      }
    } catch (_) {
      // A failed download must not crash the shell or wedge the queue.
    } finally {
      _running = false;
      unawaited(_pump(cookieHeader));
    }
  }

  static String _filenameFor(http.Response response, Uri url) {
    final disposition = response.headers['content-disposition'];
    if (disposition != null) {
      final match = RegExp('filename="?([^";]+)"?').firstMatch(disposition);
      if (match != null) return match.group(1)!;
    }
    // /api/videos/<id>/download -> "<id>-autoedit.mp4"
    final segments = url.pathSegments;
    final id = segments.length >= 2 ? segments[segments.length - 2] : 'video';
    return '$id-autoedit.mp4';
  }
}
