import 'package:flutter/material.dart';
import 'package:flutter_application_1/services/settings.dart';

class SettingsScreen extends StatefulWidget {
  final AppSettings settings;
  final VoidCallback onSettingsChanged;
  const SettingsScreen({super.key, required this.settings, required this.onSettingsChanged});
  @override
  // ignore: library_private_types_in_public_api
  _SettingsScreenState createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  late TextEditingController _systemPromptCtrl;
  late TextEditingController _assistantNameCtrl;
  late double _temperature;
  late int _maxTokens;
  late bool _isDark;

  @override
  void initState() {
    super.initState();
    _systemPromptCtrl = TextEditingController(text: widget.settings.systemPrompt);
    _assistantNameCtrl = TextEditingController(text: widget.settings.assistantName);
    _temperature = widget.settings.temperature;
    _maxTokens = widget.settings.maxTokens;
    _isDark = widget.settings.isDark;

    _systemPromptCtrl.addListener(_save);
    _assistantNameCtrl.addListener(_save);
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Настройки')),
      body: ListView(
        padding: EdgeInsets.all(16),
        children: [
          SwitchListTile(
            title: Text('Тёмная тема'),
            value: _isDark,
            onChanged: (v) {
              setState(() => _isDark = v);
              _save();
            },
          ),
          TextField(
            controller: _assistantNameCtrl,
            decoration: InputDecoration(labelText: 'Имя ассистента'),
          ),
          SizedBox(height: 16),
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
          SizedBox(height: 16),
          TextField(
            controller: _systemPromptCtrl,
            maxLines: 4,
            decoration: InputDecoration(labelText: 'Системный промпт', border: OutlineInputBorder()),
          ),
        ],
      ),
    );
  }
}