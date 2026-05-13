import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class AuthService {
  final FlutterSecureStorage _storage = const FlutterSecureStorage();
  
  static final AuthService _instance = AuthService._internal();
  factory AuthService() => _instance;
  AuthService._internal();
  
  Future<String?> getToken() async {
    return await _storage.read(key: 'access_token');
  }
  
  Future<void> saveToken(String token) async {
    await _storage.write(key: 'access_token', value: token);
  }
  
  Future<void> deleteToken() async {
    await _storage.delete(key: 'access_token');
  }
  
  Future<bool> isLoggedIn() async {
    final token = await getToken();
    return token != null;
  }
}
