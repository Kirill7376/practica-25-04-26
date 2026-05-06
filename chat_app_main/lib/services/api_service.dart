import 'dart:convert';
import 'dart:async';
import 'package:http/http.dart' as http;
import 'package:flutter_application_1/services/cancel_token.dart';

class ApiService {
  static const String baseUrl = 'http://localhost:8000';

  Future<Map<String, dynamic>> sendMessage({
    required String message,
    int? conversationId,
    double temperature = 0.7,
    String systemPrompt = "Ты — вежливый русскоязычный ассистент.",
    int maxTokens = 150,
    String assistantName = "Assistant",
    CancelToken? cancelToken,
  }) async {
    final uri = Uri.parse('$baseUrl/chat');
    final request = http.Request('POST', uri)
      ..headers['Content-Type'] = 'application/json'
      ..body = jsonEncode({
        'conversation_id': conversationId,
        'message': message,
        'temperature': temperature,
        'system_prompt': systemPrompt,
        'max_tokens': maxTokens,
        'assistant_name': assistantName,
      });
    final response = await _executeWithCancellation(request, cancelToken);
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Failed to send message');
    }
  }

  Future<Map<String, dynamic>> searchMessage({
    required String query,
    int? conversationId,
    double temperature = 0.7,
    String systemPrompt = "Ты — полезный ассистент. На основе результатов поиска дай развёрнутый ответ.",
    int maxTokens = 300,
    CancelToken? cancelToken,
  }) async {
    final uri = Uri.parse('$baseUrl/search');
    final request = http.Request('POST', uri)
      ..headers['Content-Type'] = 'application/json'
      ..body = jsonEncode({
        'query': query,
        'conversation_id': conversationId,
        'temperature': temperature,
        'system_prompt': systemPrompt,
        'max_tokens': maxTokens,
      });
    final response = await _executeWithCancellation(request, cancelToken);
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Search failed');
    }
  }

  Future<http.Response> _executeWithCancellation(http.Request request, CancelToken? cancelToken) async {
    final client = http.Client();
    try {
      final streamedResponse = await client.send(request).timeout(Duration(seconds: 30));
      if (cancelToken != null && cancelToken.isCancelled) {
        throw CancelledException();
      }
      return await http.Response.fromStream(streamedResponse);
    } finally {
      client.close();
    }
  }

  Future<List<dynamic>> getConversations() async {
    final response = await http.get(Uri.parse('$baseUrl/conversations'));
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Failed to load conversations');
    }
  }

  Future<Map<String, dynamic>> getConversation(int id) async {
    final response = await http.get(Uri.parse('$baseUrl/conversations/$id'));
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Failed to load conversation');
    }
  }

  Future<void> deleteConversation(int id) async {
    await http.delete(Uri.parse('$baseUrl/conversations/$id'));
  }
}