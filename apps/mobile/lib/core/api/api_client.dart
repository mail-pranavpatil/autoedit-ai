import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import '../../app_config.dart';
import '../storage/session_manager.dart';

class ApiException implements Exception {
  final int statusCode;
  final String message;
  ApiException(this.statusCode, this.message);

  @override
  String toString() => message;
}

class ApiClient {
  static String get baseUrl => serverUrl;

  static Future<Map<String, String>> _headers({bool requiresAuth = true}) async {
    final headers = <String, String>{
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
    if (requiresAuth) {
      final token = await SessionManager.getToken();
      if (token != null && token.isNotEmpty) {
        headers['Authorization'] = 'Bearer $token';
      }
    }
    return headers;
  }

  static dynamic _handleResponse(http.Response response) {
    dynamic body;
    try {
      body = jsonDecode(response.body);
    } catch (_) {
      body = response.body;
    }

    if (response.statusCode >= 200 && response.statusCode < 300) {
      return body;
    }

    String errorMsg = 'An error occurred (${response.statusCode})';
    if (body is Map && body.containsKey('detail')) {
      errorMsg = body['detail'].toString();
    } else if (body is Map && body.containsKey('message')) {
      errorMsg = body['message'].toString();
    }
    throw ApiException(response.statusCode, errorMsg);
  }

  static Future<dynamic> get(String path, {bool requiresAuth = true}) async {
    final url = Uri.parse('$baseUrl$path');
    final headers = await _headers(requiresAuth: requiresAuth);
    try {
      final response = await http.get(url, headers: headers).timeout(const Duration(seconds: 20));
      return _handleResponse(response);
    } on SocketException {
      throw ApiException(503, 'Network connection failed. Please check your internet.');
    }
  }

  static Future<dynamic> post(
    String path, {
    Map<String, dynamic>? body,
    bool requiresAuth = true,
  }) async {
    final url = Uri.parse('$baseUrl$path');
    final headers = await _headers(requiresAuth: requiresAuth);
    try {
      final response = await http
          .post(url, headers: headers, body: body != null ? jsonEncode(body) : null)
          .timeout(const Duration(seconds: 25));
      return _handleResponse(response);
    } on SocketException {
      throw ApiException(503, 'Network connection failed. Please check your internet.');
    }
  }

  static Future<dynamic> put(
    String path, {
    Map<String, dynamic>? body,
    bool requiresAuth = true,
  }) async {
    final url = Uri.parse('$baseUrl$path');
    final headers = await _headers(requiresAuth: requiresAuth);
    try {
      final response = await http
          .put(url, headers: headers, body: body != null ? jsonEncode(body) : null)
          .timeout(const Duration(seconds: 25));
      return _handleResponse(response);
    } on SocketException {
      throw ApiException(503, 'Network connection failed. Please check your internet.');
    }
  }
}
