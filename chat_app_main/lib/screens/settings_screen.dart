import 'package:flutter/material.dart';
import 'package:flutter_application_1/services/settings.dart';
import 'package:flutter_application_1/services/api_service.dart';

class SettingsScreen extends StatefulWidget {
  final AppSettings settings;
  final VoidCallback onSettingsChanged;
  const SettingsScreen({super.key, required this.settings, required this.onSettingsChanged});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  late TextEditingController _systemPromptCtrl;
  late TextEditingController _assistantNameCtrl;
  late double _temperature;
  late int _maxTokens;
  late bool _isDark;
  late bool _useNativeDb;
  final ApiService _api = ApiService();

  @override
  void initState() {
    super.initState();
    _systemPromptCtrl = TextEditingController(text: widget.settings.systemPrompt);
    _assistantNameCtrl = TextEditingController(text: widget.settings.assistantName);
    _temperature = widget.settings.temperature;
    _maxTokens = widget.settings.maxTokens;
    _isDark = widget.settings.isDark;
    _useNativeDb = false; // временно, потом загрузим

    _loadDbMode();
    _systemPromptCtrl.addListener(_save);
    _assistantNameCtrl.addListener(_save);
  }

  Future<void> _loadDbMode() async {
    try {
      final mode = await _api.getDbMode();
      if (mounted) {
        setState(() {
          _useNativeDb = (mode == 'native');
        });
      }
    } catch (e) {
      debugPrint('Ошибка загрузки режима БД: $e');
    }
  }

  @override
  void dispose() {
    _systemPromptCtrl.removeListener(_save);
    _assistantNameCtrl.removeListener(_save);
    _systemPromptCtrl.dispose();
    _assistantNameCtrl.dispose();
    super.dispose();
  }

  void _save() {
    widget.settings.systemPrompt = _systemPromptCtrl.text;
    widget.settings.assistantName = _assistantNameCtrl.text;
    widget.settings.temperature = _temperature;
    widget.settings.maxTokens = _maxTokens;
    widget.settings.isDark = _isDark;
    widget.onSettingsChanged();
  }

  Future<void> _toggleDbMode(bool value) async {
  setState(() => _useNativeDb = value);
  try {
    await _api.setDbMode(value ? 'native' : 'orm');
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Режим БД переключен на ${value ? "нативный SQL" : "ORM"}')),
      );
    }
  } catch (e) {
    if (mounted) {
      setState(() => _useNativeDb = !value);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Ошибка переключения: $e'), backgroundColor: Colors.red),
      );
    }
  }
}

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Настройки')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          SwitchListTile(
            title: const Text('Тёмная тема'),
            value: _isDark,
            onChanged: (v) {
              setState(() => _isDark = v);
              _save();
            },
          ),
          SwitchListTile(
            title: const Text('Использовать нативный SQL (вместо ORM)'),
            subtitle: const Text('Переключение требует перезагрузки страницы после сохранения'),
            value: _useNativeDb,
            onChanged: _toggleDbMode,
          ),
          TextField(
            controller: _assistantNameCtrl,
            decoration: const InputDecoration(labelText: 'Имя ассистента'),
          ),
          const SizedBox(height: 16),
          Text('Температура: ${_temperature.toStringAsFixed(2)}'),
          Slider(
            value: _temperature,
            min: 0.0,
            max: 1.5,
            onChanged: (v) {
              setState(() => _temperature = v);
              _save();
            },
          ),
          Text('Макс. токенов: $_maxTokens'),
          Slider(
            value: _maxTokens.toDouble(),
            min: 100,
            max: 2000,
            divisions: 19,
            label: _maxTokens.toString(),
            onChanged: (v) {
              setState(() => _maxTokens = v.toInt());
              _save();
            },
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _systemPromptCtrl,
            maxLines: 4,
            decoration: const InputDecoration(labelText: 'Системный промпт', border: OutlineInputBorder()),
          ),
        ],
      ),
    );
  }
}
