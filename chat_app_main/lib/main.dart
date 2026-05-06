import 'package:flutter/material.dart';
import 'screens/chat_screen.dart';
import 'screens/history_screen.dart';
import 'screens/settings_screen.dart';
import 'package:flutter_application_1/services/settings.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final settings = AppSettings();
  await settings.init();
  runApp(MyApp(settings: settings));
}

class MyApp extends StatefulWidget {
  final AppSettings settings;
  const MyApp({super.key, required this.settings});
  @override
  State<MyApp> createState() => _MyAppState();
}

class _MyAppState extends State<MyApp> {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'LLM Chat',
      themeMode: widget.settings.isDark ? ThemeMode.dark : ThemeMode.light,
      darkTheme: ThemeData.dark(),
      theme: ThemeData.light(),
      home: HomePage(settings: widget.settings, onThemeChanged: () => setState(() {})),
    );
  }
}

class HomePage extends StatefulWidget {
  final AppSettings settings;
  final VoidCallback onThemeChanged;
  const HomePage({super.key, required this.settings, required this.onThemeChanged});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  int _currentIndex = 0;
  int? _activeConversationId;
  final GlobalKey<ChatScreenState> _chatKey = GlobalKey();

  void _onConversationSelected(int conversationId) {
    setState(() {
      _activeConversationId = conversationId;
      _currentIndex = 0;
    });
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _chatKey.currentState?.loadConversation(conversationId);
    });
  }

  void _startNewChat() {
    setState(() {
      _activeConversationId = null;
      _currentIndex = 0;
    });
    _chatKey.currentState?.startNewChat();
  }

  @override
  Widget build(BuildContext context) {
    final screens = [
      ChatScreen(
        key: _chatKey,
        settings: widget.settings,
        conversationId: _activeConversationId,
        onConversationChanged: (id) => setState(() => _activeConversationId = id),
      ),
      HistoryScreen(
        settings: widget.settings,
        onConversationSelected: _onConversationSelected,
      ),
      SettingsScreen(
        settings: widget.settings,
        onSettingsChanged: widget.onThemeChanged,
      ),
    ];

    return Scaffold(
      body: Row(
        children: [
          NavigationRail(
            selectedIndex: _currentIndex,
            onDestinationSelected: (index) => setState(() => _currentIndex = index),
            labelType: NavigationRailLabelType.all,
            destinations: const [
              NavigationRailDestination(icon: Icon(Icons.chat), label: Text('Чат')),
              NavigationRailDestination(icon: Icon(Icons.history), label: Text('История')),
              NavigationRailDestination(icon: Icon(Icons.settings), label: Text('Настройки')),
            ],
            trailing: IconButton(
              icon: const Icon(Icons.add),
              onPressed: _startNewChat,
              tooltip: 'Новый чат',
            ),
          ),
          const VerticalDivider(thickness: 1, width: 1),
          Expanded(child: screens[_currentIndex]),
        ],
      ),
    );
  }
}