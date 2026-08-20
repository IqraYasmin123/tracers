import 'dart:convert';
import 'dart:typed_data';
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../models/models.dart';

/// The backend strictly allowlists image/jpeg, image/png, image/webp (see
/// backend/app/api/routes/inference.py and cases.py's ALLOWED_CONTENT_TYPES) — a
/// MultipartFile built from raw bytes defaults to application/octet-stream unless told
/// otherwise, which the backend would correctly reject with a 422. This infers the real
/// content type from the filename extension so uploads actually carry a type the backend
/// will accept.
MediaType _mediaTypeForFilename(String filename) {
  final lower = filename.toLowerCase();
  if (lower.endsWith('.png')) return MediaType('image', 'png');
  if (lower.endsWith('.webp')) return MediaType('image', 'webp');
  return MediaType('image', 'jpeg'); // covers .jpg/.jpeg, and is a reasonable default
}

class ApiException implements Exception {
  final String message;
  final int status;
  ApiException(this.message, this.status);
  @override
  String toString() => message;
}

/// Thin wrapper around the same TRACER backend the React frontend talks to (Module 9,
/// extended by 13/14). Every method mirrors a function in frontend/src/api/client.js —
/// same endpoints, same request/response shapes, so behavior stays consistent across
/// clients rather than the mobile app inventing its own contract.
class ApiClient {
  static const _baseUrlPrefsKey = 'tracer.api_base_url';
  static const _tokenPrefsKey = 'tracer.auth_token';
  static const _defaultBaseUrl = 'http://10.0.2.2:8000'; // Android emulator's alias for
  // the host machine's localhost. iOS simulator and physical devices need a real LAN IP —
  // see docs/module15_mobile.md for how to change this from the Settings screen.

  String baseUrl;
  String? _token;
  ApiClient._(this.baseUrl, this._token);

  static Future<ApiClient> create() async {
    final prefs = await SharedPreferences.getInstance();
    final savedUrl = prefs.getString(_baseUrlPrefsKey);
    final savedToken = prefs.getString(_tokenPrefsKey);
    return ApiClient._(savedUrl ?? _defaultBaseUrl, savedToken);
  }

  Future<void> setBaseUrl(String url) async {
    baseUrl = url;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_baseUrlPrefsKey, url);
  }

  bool get isAuthenticated => _token != null;

  Map<String, String> _authHeaders() =>
      _token != null ? {'Authorization': 'Bearer $_token'} : {};

  /// Real authentication (Module 16). Mirrors frontend/src/api/client.js's login() exactly
  /// — the backend's /auth/login expects application/x-www-form-urlencoded
  /// (FastAPI's OAuth2PasswordRequestForm), which `http.post` produces automatically when
  /// `body` is a plain Map<String, String>, not JSON.
  Future<void> login(String usernameOrEmail, String password) async {
    http.Response response;
    try {
      response = await http
          .post(
            Uri.parse('$baseUrl/api/v1/auth/login'),
            body: {'username': usernameOrEmail, 'password': password},
          )
          .timeout(const Duration(seconds: 15));
    } on Exception catch (e) {
      throw ApiException('Could not reach the TRACER backend at $baseUrl. ($e)', 0);
    }
    final body = _decodeOrThrow(response);
    _token = body['access_token'] as String;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_tokenPrefsKey, _token!);
  }

  Future<void> logout() async {
    _token = null;
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_tokenPrefsKey);
  }

  /// Validates the stored token against the backend — a token can be expired or its
  /// account deleted since it was issued, so "a token is stored locally" isn't the same
  /// as "the session is actually still valid". Returns null (not throwing) on any
  /// failure, since the caller (main.dart's bootstrap) just needs a yes/no to decide
  /// whether to show Login or the app shell.
  Future<UserProfile?> getCurrentUserOrNull() async {
    if (_token == null) return null;
    try {
      final response = await http
          .get(Uri.parse('$baseUrl/api/v1/auth/me'), headers: _authHeaders())
          .timeout(const Duration(seconds: 10));
      if (response.statusCode != 200) {
        await logout(); // stale/invalid token — don't keep sending it on every request
        return null;
      }
      return UserProfile.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
    } catch (_) {
      return null;
    }
  }

  Map<String, dynamic> _decodeOrThrow(http.Response response) {
    if (response.statusCode >= 200 && response.statusCode < 300) {
      return jsonDecode(response.body) as Map<String, dynamic>;
    }
    String detail = 'Request failed with status ${response.statusCode}';
    try {
      final body = jsonDecode(response.body) as Map<String, dynamic>;
      if (body['detail'] is String) detail = body['detail'] as String;
    } catch (_) {
      // response body wasn't JSON — keep the generic message above
    }
    throw ApiException(detail, response.statusCode);
  }

  Future<bool> checkHealth() async {
    try {
      final response = await http
          .get(Uri.parse('$baseUrl/api/v1/health'))
          .timeout(const Duration(seconds: 5));
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  Future<AnalysisResult> analyzeImage(Uint8List imageBytes, String filename, {String? caption}) async {
    final uri = Uri.parse('$baseUrl/api/v1/analyze');
    final request = http.MultipartRequest('POST', uri)
      ..files.add(http.MultipartFile.fromBytes('file', imageBytes,
          filename: filename, contentType: _mediaTypeForFilename(filename)));
    if (caption != null && caption.isNotEmpty) {
      request.fields['caption'] = caption;
    }

    final streamed = await _send(request);
    final response = await http.Response.fromStream(streamed);
    return AnalysisResult.fromJson(_decodeOrThrow(response));
  }

  Future<List<CaseSummary>> listCases({String? status}) async {
    final uri = Uri.parse('$baseUrl/api/v1/cases').replace(
      queryParameters: status != null ? {'status': status} : null,
    );
    final response = await _get(uri);
    final list = jsonDecode(response.body) as List;
    return list.map((e) => CaseSummary.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<CaseDetail> getCase(String caseId) async {
    final response = await _get(Uri.parse('$baseUrl/api/v1/cases/$caseId'));
    return CaseDetail.fromJson(_decodeOrThrow(response));
  }

  Future<CaseSummary> createCase({required String title, String? description}) async {
    final response = await _post(
      Uri.parse('$baseUrl/api/v1/cases'),
      body: {'title': title, 'description': description},
    );
    return CaseSummary.fromJson(_decodeOrThrow(response));
  }

  Future<CaseSummary> updateCaseStatus(String caseId, String status) async {
    final response = await _patch(
      Uri.parse('$baseUrl/api/v1/cases/$caseId'),
      body: {'status': status},
    );
    return CaseSummary.fromJson(_decodeOrThrow(response));
  }

  Future<EvidenceSummary> attachEvidenceToCase(
    String caseId,
    Uint8List imageBytes,
    String filename, {
    String? caption,
  }) async {
    final uri = Uri.parse('$baseUrl/api/v1/cases/$caseId/evidence');
    final request = http.MultipartRequest('POST', uri)
      ..files.add(http.MultipartFile.fromBytes('file', imageBytes,
          filename: filename, contentType: _mediaTypeForFilename(filename)));
    if (caption != null && caption.isNotEmpty) {
      request.fields['caption'] = caption;
    }
    final streamed = await _send(request);
    final response = await http.Response.fromStream(streamed);
    return EvidenceSummary.fromJson(_decodeOrThrow(response));
  }

  Future<CaseStats> getCaseStats() async {
    final response = await _get(Uri.parse('$baseUrl/api/v1/cases/stats'));
    return CaseStats.fromJson(_decodeOrThrow(response));
  }

  Future<List<ReportSummary>> listReports(String caseId) async {
    final response = await _get(Uri.parse('$baseUrl/api/v1/cases/$caseId/reports'));
    final list = jsonDecode(response.body) as List;
    return list.map((e) => ReportSummary.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<ReportSummary> generateReport(String caseId, {String format = 'pdf'}) async {
    final response = await _post(
      Uri.parse('$baseUrl/api/v1/cases/$caseId/reports'),
      body: {'format': format},
    );
    return ReportSummary.fromJson(_decodeOrThrow(response));
  }

  /// Fetches the report file with the auth header the download endpoint now requires
  /// (Module 16) — a bare URL opened externally (e.g. via url_launcher) can't carry an
  /// Authorization header, so that approach silently breaks once auth is required.
  Future<Uint8List> downloadReportBytes(String caseId, String reportId) async {
    http.Response response;
    try {
      response = await http
          .get(
            Uri.parse('$baseUrl/api/v1/cases/$caseId/reports/$reportId/download'),
            headers: _authHeaders(),
          )
          .timeout(const Duration(seconds: 30));
    } on Exception catch (e) {
      throw ApiException('Could not reach the TRACER backend at $baseUrl. ($e)', 0);
    }
    if (response.statusCode != 200) {
      String detail = 'Failed to download report (status ${response.statusCode}).';
      try {
        final body = jsonDecode(response.body) as Map<String, dynamic>;
        if (body['detail'] is String) detail = body['detail'] as String;
      } catch (_) {}
      throw ApiException(detail, response.statusCode);
    }
    return response.bodyBytes;
  }

  // --- internal helpers: consistent timeouts + a clear error when the backend is simply
  // unreachable, rather than an opaque SocketException bubbling up to the UI. The real
  // exception's message is included (not swallowed) so unexpected errors stay diagnosable
  // instead of every failure looking identical. ---

  Future<http.Response> _get(Uri uri) async {
    try {
      return await http.get(uri, headers: _authHeaders()).timeout(const Duration(seconds: 15));
    } on Exception catch (e) {
      throw ApiException('Could not reach the TRACER backend at $baseUrl. ($e)', 0);
    }
  }

  Future<http.Response> _post(Uri uri, {required Map<String, dynamic> body}) async {
    try {
      return await http
          .post(
            uri,
            headers: {'Content-Type': 'application/json', ..._authHeaders()},
            body: jsonEncode(body),
          )
          .timeout(const Duration(seconds: 60)); // report generation can take a few seconds
    } on Exception catch (e) {
      throw ApiException('Could not reach the TRACER backend at $baseUrl. ($e)', 0);
    }
  }

  Future<http.Response> _patch(Uri uri, {required Map<String, dynamic> body}) async {
    try {
      return await http
          .patch(
            uri,
            headers: {'Content-Type': 'application/json', ..._authHeaders()},
            body: jsonEncode(body),
          )
          .timeout(const Duration(seconds: 15));
    } on Exception catch (e) {
      throw ApiException('Could not reach the TRACER backend at $baseUrl. ($e)', 0);
    }
  }

  Future<http.StreamedResponse> _send(http.MultipartRequest request) async {
    try {
      request.headers.addAll(_authHeaders());
      return await request.send().timeout(const Duration(seconds: 60));
    } on Exception catch (e) {
      throw ApiException('Could not reach the TRACER backend at $baseUrl. ($e)', 0);
    }
  }
}
