import 'package:flutter/material.dart';
import '../services/api_service.dart';
import 'package:flutter_application_1/services/settings.dart';

class HistoryScreen extends StatefulWidget {
  final AppSettings settings;
  final void Function(int)? onConversationSelected;

  const HistoryScreen({
    super.key,
    required this.settings,
    this.onConversationSelected,
  });

  @override
  // ignore: library_private_types_in_public_api
  _HistoryScreenState createState() => _HistoryScreenState(); 
}

class _HistoryScreenState extends State<HistoryScreen> {
  final ApiService api = ApiService();
  late Future<List<dynamic>> conversationsFuture;

  @override
  void initState() {
    super.initState();
    conversationsFuture = api.getConversations();
  }

  Future<void> _delete(int id) async {
    await api.deleteConversation(id);
    setState(() {
      conversationsFuture = api.getConversations();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('История диалогов')),
      body: FutureBuilder<List<dynamic>>(
        future: conversationsFuture,
        builder: (ctx, snapshot) {
          if (!snapshot.hasData) return Center(child: CircularProgressIndicator());
          final convs = snapshot.data!;
          if (convs.isEmpty) return Center(child: Text('Нет сохранённых диалогов'));
          return ListView.builder(
            itemCount: convs.length,
            itemBuilder: (ctx, i) {
              final c = convs[i];
              return ListTile(
                title: Text(c['title'] ?? 'Диалог ${c['id']}'),
                subtitle: Text(c['created_at']),
                onTap: () {
                  widget.onConversationSelected?.call(c['id']);
                },
                trailing: IconButton(
                  icon: Icon(Icons.delete),
                  onPressed: () => _delete(c['id']),
                ),
              );
            },
          );
        },
      ),
    );
  }
}