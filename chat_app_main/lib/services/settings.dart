import 'package:shared_preferences/shared_preferences.dart';

class AppSettings {
  static const _temperatureKey = 'temperature';
  static const _systemPromptKey = 'system_prompt';
  static const _maxTokensKey = 'max_tokens';
  static const _assistantNameKey = 'assistant_name';
  static const _themeKey = 'is_dark';

  late SharedPreferences _prefs;

  Future<void> init() async {
    _prefs = await SharedPreferences.getInstance();
  }

  double get temperature => _prefs.getDouble(_temperatureKey) ?? 0.7;
  set temperature(double v) => _prefs.setDouble(_temperatureKey, v);

  String get systemPrompt => _prefs.getString(_systemPromptKey) ?? "You are a helpful assistant.";
  set systemPrompt(String v) => _prefs.setString(_systemPromptKey, v);

  int get maxTokens => _prefs.getInt(_maxTokensKey) ?? 512;
  set maxTokens(int v) => _prefs.setInt(_maxTokensKey, v);

  String get assistantName => _prefs.getString(_assistantNameKey) ?? "Assistant";
  set assistantName(String v) => _prefs.setString(_assistantNameKey, v);

  bool get isDark => _prefs.getBool(_themeKey) ?? false;
  set isDark(bool v) => _prefs.setBool(_themeKey, v);
}