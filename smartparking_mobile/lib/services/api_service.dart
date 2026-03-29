import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter/foundation.dart';
import 'storage_service.dart';

class ApiService {
  // Platform bazlı URL
  static String get baseUrl {
    if (kIsWeb) {
      // Chrome için
      return 'https://localhost:7044/api';
    } else {
      // Android Emulator için
      return 'http://10.25.157.189:5197/api';
    }
  }
  
  static Future<Map<String, dynamic>> login(String email, String password) async {
    try {
      debugPrint('🔵 Login isteği gönderiliyor...');
      debugPrint('🔵 URL: $baseUrl/Auth/login');
      debugPrint('🔵 Email: $email');
      
      final response = await http.post(
        Uri.parse('$baseUrl/Auth/login'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'email': email,
          'password': password,
        }),
      );

      debugPrint('🔵 Status Code: ${response.statusCode}');
      debugPrint('🔵 Response Body: ${response.body}');

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Giriş başarısız: ${response.body}');
      }
    } catch (e) {
      debugPrint('🔴 HATA: $e');
      throw Exception('Bağlantı hatası: $e');
    }
  }

  static Future<Map<String, dynamic>> register(
    String name,
    String email,
    String password,
    String phone,
  ) async {
    try {
      debugPrint('🔵 Register isteği gönderiliyor...');
      debugPrint('🔵 URL: $baseUrl/Auth/register');
      
      final response = await http.post(
        Uri.parse('$baseUrl/Auth/register'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'name': name,
          'email': email,
          'password': password,
          'phone': phone,
        }),
      );

      debugPrint('🔵 Status Code: ${response.statusCode}');
      debugPrint('🔵 Response Body: ${response.body}');

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Kayıt başarısız: ${response.body}');
      }
    } catch (e) {
      debugPrint('🔴 HATA: $e');
      throw Exception('Bağlantı hatası: $e');
    }
  }

  // Profil güncelle
  static Future<Map<String, dynamic>> updateProfile(
    String userId,
    String name,
    String email,
    String phone,
  ) async {
    try {
      debugPrint('🔵 Profil güncelleniyor...');
      debugPrint('🔵 URL: $baseUrl/User/$userId');
      
      final response = await http.put(
        Uri.parse('$baseUrl/User/$userId'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'name': name,
          'email': email,
          'phone': phone,
        }),
      );

      debugPrint('🔵 Status Code: ${response.statusCode}');
      debugPrint('🔵 Response: ${response.body}');

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Profil güncellenemedi: ${response.body}');
      }
    } catch (e) {
      debugPrint('🔴 HATA: $e');
      throw Exception('Bağlantı hatası: $e');
    }
  }

  // Şifre değiştir
  static Future<void> changePassword(
    String userId,
    String currentPassword,
    String newPassword,
  ) async {
    try {
      debugPrint('🔵 Şifre değiştiriliyor...');
      debugPrint('🔵 URL: $baseUrl/User/$userId/change-password');
      
      final response = await http.post(
        Uri.parse('$baseUrl/User/$userId/change-password'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'currentPassword': currentPassword,
          'newPassword': newPassword,
        }),
      );

      debugPrint('🔵 Status Code: ${response.statusCode}');
      debugPrint('🔵 Response: ${response.body}');

      if (response.statusCode != 200) {
        var errorMessage = 'Şifre değiştirilemedi';
        try {
          var errorBody = jsonDecode(response.body);
          errorMessage = errorBody['message'] ?? errorMessage;
        } catch (e) {
          // JSON parse hatası
        }
        throw Exception(errorMessage);
      }
    } catch (e) {
      debugPrint('🔴 HATA: $e');
      rethrow;
    }
  }

// ========== VEHICLE ENDPOINTS ==========

// Kullanıcının araçlarını getir
static Future<List<dynamic>> getUserVehicles(String userId) async {
  debugPrint('🚗 Araçlar getiriliyor...');
  debugPrint('🔵 URL: $baseUrl/Vehicle/user/$userId');

  final response = await http.get(
    Uri.parse('$baseUrl/Vehicle/user/$userId'),
    headers: {'Content-Type': 'application/json'},
  );

  debugPrint('🔵 Status Code: ${response.statusCode}');
  debugPrint('🔵 Response: ${response.body}');

  if (response.statusCode == 200) {
    return jsonDecode(response.body);
  } else {
    throw Exception('Araçlar getirilemedi');
  }
}

// Yeni araç ekle
static Future<Map<String, dynamic>> addVehicle(
  String userId,
  String plateNumber,
  String label,
  String model,
  String color,
) async {
  debugPrint('🚗 Yeni araç ekleniyor...');
  debugPrint('🔵 URL: $baseUrl/Vehicle/user/$userId');

  final response = await http.post(
    Uri.parse('$baseUrl/Vehicle/user/$userId'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({
      'plateNumber': plateNumber,
      'label': label,
      'model': model,
      'color': color,
    }),
  );

  debugPrint('🔵 Status Code: ${response.statusCode}');
  debugPrint('🔵 Response: ${response.body}');

  if (response.statusCode == 200 || response.statusCode == 201) {
    return jsonDecode(response.body);
  } else {
    final error = jsonDecode(response.body);
    throw Exception(error['message'] ?? 'Araç eklenemedi');
  }
}

// Araç güncelle
static Future<Map<String, dynamic>> updateVehicle(
  String vehicleId,
  String plateNumber,
  String label,
  String model,
  String color,
) async {
  debugPrint('🚗 Araç güncelleniyor...');
  debugPrint('🔵 URL: $baseUrl/Vehicle/$vehicleId');

  final response = await http.put(
    Uri.parse('$baseUrl/Vehicle/$vehicleId'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({
      'plateNumber': plateNumber,
      'label': label,
      'model': model,
      'color': color,
    }),
  );

  debugPrint('🔵 Status Code: ${response.statusCode}');

  if (response.statusCode == 200) {
    return jsonDecode(response.body);
  } else {
    final error = jsonDecode(response.body);
    throw Exception(error['message'] ?? 'Araç güncellenemedi');
  }
}
// Araç sil
static Future<void> deleteVehicle(String vehicleId) async {
  debugPrint('🚗 Araç siliniyor...');
  debugPrint('🔵 URL: $baseUrl/Vehicle/$vehicleId');

  final response = await http.delete(
    Uri.parse('$baseUrl/Vehicle/$vehicleId'),
    headers: {'Content-Type': 'application/json'},
  );

  debugPrint('🔵 Status Code: ${response.statusCode}');

  if (response.statusCode != 200 && response.statusCode != 204) {
    throw Exception('Araç silinemedi');
  }
}
// Park durumu getir
static Future<Map<String, dynamic>> getParkingStatus() async {
  try {
    final response = await http.get(
      Uri.parse('$baseUrl/parking/status'),
      headers: {'Content-Type': 'application/json'},
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Park durumu alınamadı');
    }
  } catch (e) {
    throw Exception('Bağlantı hatası: $e');
  }
}
static Future<Map<String, dynamic>?> getActiveSession(String vehicleId) async {
  try {
    final response = await http.get(
      Uri.parse('$baseUrl/parking/vehicle/$vehicleId/active-session'),
      headers: {'Content-Type': 'application/json'},
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    return null;
  } catch (e) {
    return null;
  }
}
// Cezalarımı getir
static Future<List<dynamic>> getMyPenalties() async {
  try {
    final token = await StorageService.getToken();
    final response = await http.get(
      Uri.parse('$baseUrl/Penalty/my-penalties'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    return [];
  } catch (e) {
    return [];
  }
}
}