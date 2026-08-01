import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/user_model.dart';
import '../models/exam_model.dart';
import '../models/matched_job_model.dart';

class ApiService {
  static const String baseUrl = 'http://136.243.30.219:8000';

  static Future<bool> checkServerStatus() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/'));
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }

  static Future<Map<String, dynamic>> registerUser(RegisterModel user) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/register'),
        headers: {'Content-Type': 'application/json; charset=utf-8'},
        body: jsonEncode(user.toJson()),
      );

      final body = jsonDecode(utf8.decode(response.bodyBytes));

      if (response.statusCode == 200) {
        return {'success': true, 'message': body['message']};
      } else {
        return {'success': false, 'message': body['detail'] ?? 'خطایی در ثبت اطلاعات رخ داد'};
      }
    } catch (e) {
      return {'success': false, 'message': 'ارتباط با سرور برقرار نشد: $e'};
    }
  }

  static Future<UserProfile?> getProfile(int userId) async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/profile/$userId'));
      if (response.statusCode == 200) {
        final data = jsonDecode(utf8.decode(response.bodyBytes));
        return UserProfile.fromJson(data);
      }
      return null;
    } catch (e) {
      return null;
    }
  }

  static Future<List<ExamModel>> getActiveExams() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/exams/active'));
      if (response.statusCode == 200) {
        final List list = jsonDecode(utf8.decode(response.bodyBytes));
        return list.map((item) => ExamModel.fromJson(item)).toList();
      }
      return [];
    } catch (e) {
      return [];
    }
  }

  static Future<List<ExamModel>> getUpcomingExams() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/exams/upcoming'));
      if (response.statusCode == 200) {
        final List list = jsonDecode(utf8.decode(response.bodyBytes));
        return list.map((item) => ExamModel.fromJson(item)).toList();
      }
      return [];
    } catch (e) {
      return [];
    }
  }

  // اصلاح شده بر اساس ساختار جدید MatchedJobsResponse
  static Future<MatchedJobsResponse?> getMatchedJobs(int userId) async {
    try {
      final url = '$baseUrl/user/matched-jobs/$userId';
      
      final response = await http.get(
        Uri.parse(url),
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json; charset=utf-8',
        },
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(utf8.decode(response.bodyBytes));
        return MatchedJobsResponse.fromJson(data);
      }
    } catch (e) {
      print(">>> CATCH ERROR: $e");
    }
    return null;
  }
}