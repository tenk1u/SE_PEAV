import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class ApiClient {
  static const String baseUrl = 'http://10.0.2.2:8000/api/v1'; // Android emulator
  // static const String baseUrl = 'http://localhost:8000/api/v1'; // iOS simulator
  
  late final Dio _dio;
  final FlutterSecureStorage _storage = const FlutterSecureStorage();
  
  static final ApiClient _instance = ApiClient._internal();
  factory ApiClient() => _instance;
  
  ApiClient._internal() {
    _dio = Dio(BaseOptions(
      baseUrl: baseUrl,
      connectTimeout: const Duration(seconds: 30),
      receiveTimeout: const Duration(seconds: 30),
      headers: {
        'Content-Type': 'application/json',
      },
    ));
    
    _dio.interceptors.addAll([
      AuthInterceptor(_storage),
      LogInterceptor(requestBody: true, responseBody: true),
    ]);
  }
  
  Dio get dio => _dio;
  
  // Auth endpoints
  Future<Map<String, dynamic>> register({
    required String email,
    required String password,
    required String fullName,
    String? phone,
  }) async {
    final response = await _dio.post('/auth/register', data: {
      'email': email,
      'password': password,
      'full_name': fullName,
      'phone': phone,
    });
    return response.data;
  }
  
  Future<Map<String, dynamic>> login({
    required String email,
    required String password,
  }) async {
    final response = await _dio.post('/auth/login', data: {
      'email': email,
      'password': password,
    });
    
    // Save token
    await _storage.write(key: 'access_token', value: response.data['access_token']);
    await _storage.write(key: 'token_type', value: response.data['token_type']);
    
    return response.data;
  }
  
  Future<void> logout() async {
    await _storage.delete(key: 'access_token');
    await _storage.delete(key: 'token_type');
  }
  
  Future<bool> isLoggedIn() async {
    final token = await _storage.read(key: 'access_token');
    return token != null;
  }
  
  Future<Map<String, dynamic>> getCurrentUser() async {
    final response = await _dio.get('/auth/me');
    return response.data;
  }
  
  // Projects endpoints
  Future<List<dynamic>> getProjects() async {
    final response = await _dio.get('/projects/');
    return response.data;
  }
  
  Future<Map<String, dynamic>> createProject({
    required String name,
    String? description,
    String? address,
    double? latitude,
    double? longitude,
  }) async {
    final response = await _dio.post('/projects/', data: {
      'name': name,
      'description': description,
      'address': address,
      'latitude': latitude,
      'longitude': longitude,
    });
    return response.data;
  }
  
  Future<Map<String, dynamic>> getProject(int id) async {
    final response = await _dio.get('/projects/$id');
    return response.data;
  }
  
  // Inspections endpoints
  Future<List<dynamic>> getInspections({int? projectId}) async {
    final queryParams = projectId != null ? {'project_id': projectId} : null;
    final response = await _dio.get('/inspections/', queryParameters: queryParams);
    return response.data;
  }
  
  Future<Map<String, dynamic>> createInspection({
    required int projectId,
    required String captureSource,
  }) async {
    final response = await _dio.post('/inspections/', data: {
      'project_id': projectId,
      'capture_source': captureSource,
    });
    return response.data;
  }
  
  Future<Map<String, dynamic>> getInspectionStatus(int id) async {
    final response = await _dio.get('/inspections/$id/status');
    return response.data;
  }
  
  Future<void> triggerProcessing(int inspectionId) async {
    await _dio.post('/inspections/$inspectionId/process');
  }
  
  Future<List<dynamic>> getDetections(int inspectionId) async {
    final response = await _dio.get('/inspections/$inspectionId/detections');
    return response.data;
  }
  
  Future<List<dynamic>> getMetrics(int inspectionId) async {
    final response = await _dio.get('/inspections/$inspectionId/metrics');
    return response.data;
  }
  
  // Upload endpoints
  Future<Map<String, dynamic>> uploadVideo({
    required int inspectionId,
    required String filePath,
    required String fileName,
    Function(int, int)? onSendProgress,
  }) async {
    final formData = FormData.fromMap({
      'file': await MultipartFile.fromFile(filePath, filename: fileName),
    });
    
    final response = await _dio.post(
      '/inspections/$inspectionId/upload/dron',
      data: formData,
      onSendProgress: onSendProgress,
    );
    return response.data;
  }
  
  Future<Map<String, dynamic>> uploadImages({
    required int inspectionId,
    required List<String> filePaths,
    Function(int, int)? onSendProgress,
  }) async {
    final files = await Future.wait(
      filePaths.map((path) => MultipartFile.fromFile(path)),
    );
    
    final formData = FormData.fromMap({
      'files': files,
    });
    
    final response = await _dio.post(
      '/inspections/$inspectionId/upload/mobile',
      data: formData,
      onSendProgress: onSendProgress,
    );
    return response.data;
  }
  
  // Reports endpoints
  Future<List<dynamic>> getReports({int? inspectionId}) async {
    final queryParams = inspectionId != null ? {'inspection_id': inspectionId} : null;
    final response = await _dio.get('/reports/', queryParameters: queryParams);
    return response.data;
  }
  
  Future<Map<String, dynamic>> generateReport(int inspectionId) async {
    final response = await _dio.post('/reports/$inspectionId/generate');
    return response.data;
  }
  
  Future<String> getReportDownloadUrl(int reportId) async {
    final response = await _dio.get('/reports/$reportId/download');
    return response.data['download_url'];
  }
}

// Auth Interceptor
class AuthInterceptor extends Interceptor {
  final FlutterSecureStorage _storage;
  
  AuthInterceptor(this._storage);
  
  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) async {
    final token = await _storage.read(key: 'access_token');
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }
  
  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    if (err.response?.statusCode == 401) {
      // Token expired or invalid
      await _storage.delete(key: 'access_token');
      // Navigate to login (would need a global navigator key)
    }
    handler.next(err);
  }
}
