import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class ApiService {
  static const _storage = FlutterSecureStorage();

  static Future<String?> _baseUrl() => _storage.read(key: 'api_base_url');
  static Future<String?> _token() => _storage.read(key: 'api_token');

  static Future<Map<String, String>> _headers() async {
    final token = await _token();
    return {
      'Content-Type': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
    };
  }

  static Future<List<Map<String, dynamic>>> getRefugePoints() async {
    final base = await _baseUrl();
    if (base == null) return [];
    try {
      final headers = await _headers();
      final res = await http
          .get(Uri.parse('$base/api/field/points/geojson/?is_active=true'), headers: headers)
          .timeout(const Duration(seconds: 10));
      if (res.statusCode != 200) return [];
      final data = jsonDecode(res.body) as Map<String, dynamic>;
      final features = (data['features'] as List? ?? []);
      return features.cast<Map<String, dynamic>>();
    } catch (_) {
      return [];
    }
  }
}
