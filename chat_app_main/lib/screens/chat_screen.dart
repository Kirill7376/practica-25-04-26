import 'dart:convert';
import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:file_picker/file_picker.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:url_launcher/url_launcher.dart';
import '../services/api_service.dart';
import '../models/message.dart';
import 'package:flutter_application_1/services/settings.dart';
import '../services/cancel_token.dart';

class ChatScreen extends StatefulWidget {
  final AppSettings settings;
  final int? conversationId;
  final Function(int?)? onConversationChanged;

  const ChatScreen({
    super.key,
    required this.settings,
    this.conversationId,
    this.onConversationChanged,
  });

  @override
  ChatScreenState createState() => ChatScreenState();
}

class ChatScreenState extends State<ChatScreen> {
  final ApiService api = ApiService();
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  List<Message> _messages = [];
  int? _currentConversationId;
  bool _isLoading = false;
  CancelToken? _cancelToken;

  @override
  void initState() {
    super.initState();
    if (widget.conversationId != null) {
      loadConversation(widget.conversationId!);
    }
  }

  void startNewChat() {
    setState(() {
      _currentConversationId = null;
      _messages.clear();
      _controller.clear();
      _cancelToken?.cancel();
      _isLoading = false;
    });
    widget.onConversationChanged?.call(null);
  }

  void loadConversation(int id) {
    _currentConversationId = id;
    _loadConversation(id);
  }

  Future<void> _loadConversation(int id) async {
    try {
      final conv = await api.getConversation(id);
      setState(() {
        _currentConversationId = conv['id'];
        _messages = (conv['messages'] as List)
            .map((m) => Message(
                  role: m['role'],
                  content: m['content'],
                  timestamp: m['timestamp'] != null
                      ? DateTime.tryParse(m['timestamp'])
                      : null,
                ))
            .toList();
      });
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Ошибка загрузки диалога: $e')),
      );
    }
  }

  Future<void> _pickFile() async {
    final result = await FilePicker.pickFiles(type: FileType.any, allowMultiple: false);
    if (result != null && result.files.isNotEmpty) {
      final file = result.files.single;
      if (file.bytes != null) {
        try {
          final textContent = utf8.decode(file.bytes!);
          _controller.text += '\n\nСодержимое файла ${file.name}:\n```\n$textContent\n```';
        } catch (e) {
          if (!mounted) return;
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Не удалось прочитать файл: $e')),
          );
        }
      }
    }
  }

  Future<void> _sendMessage({String? overrideMessage}) async {
    final text = overrideMessage ?? _controller.text.trim();
    if (text.isEmpty) return;

    if (!_isLoading) {
      setState(() {
        _messages.add(Message(role: 'user', content: text));
      });
    }
    _controller.clear();

    _cancelToken = CancelToken();
    final token = _cancelToken!;

    setState(() => _isLoading = true);

    try {
      Map<String, dynamic> response;
      if (text.startsWith('/search ')) {
        final query = text.substring(8).trim();
        response = await api.searchMessage(
          query: query,
          conversationId: _currentConversationId,
          temperature: widget.settings.temperature,
          cancelToken: token,
        );
      } else {
        response = await api.sendMessage(
          message: text,
          conversationId: _currentConversationId,
          temperature: widget.settings.temperature,
          systemPrompt: widget.settings.systemPrompt,
          maxTokens: widget.settings.maxTokens,
          assistantName: widget.settings.assistantName,
          cancelToken: token,
        );
      }

      if (!mounted || token.isCancelled) return;

      setState(() {
        _currentConversationId = response['conversation_id'];
        _messages.add(Message(role: 'assistant', content: response['assistant_message']));
        _isLoading = false;
      });
      widget.onConversationChanged?.call(_currentConversationId);
    } catch (e) {
      if (e is CancelledException || e is TimeoutException) {
        if (!mounted) return;
        setState(() => _isLoading = false);
        return;
      }
      if (!mounted) return;
      setState(() => _isLoading = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Ошибка: $e')),
      );
    } finally {
      _scrollToBottom();
    }
  }

  Future<void> _regenerateMessage(int messageIndex) async {
    final assistantMsg = _messages[messageIndex];
    if (assistantMsg.role != 'assistant') return;

    int userIndex = messageIndex - 1;
    while (userIndex >= 0 && _messages[userIndex].role != 'user') {
      userIndex--;
    }
    if (userIndex < 0) return;

    final userMessage = _messages[userIndex].content;
    setState(() {
      _messages.removeAt(messageIndex);
    });
    await _sendMessage(overrideMessage: userMessage);
  }

  void _cancelRequest() {
    _cancelToken?.cancel();
    setState(() => _isLoading = false);
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('LLM Chat')),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              itemCount: _messages.length,
              itemBuilder: (ctx, i) {
                final msg = _messages[i];
                final isUser = msg.role == 'user';
                return _buildMessageBubble(msg, isUser, i);
              },
            ),
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
            child: Container(
              decoration: BoxDecoration(
                border: Border.all(color: Colors.grey.shade400),
                borderRadius: BorderRadius.circular(12),
              ),
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                  Expanded(
                    child: ConstrainedBox(
                      constraints: const BoxConstraints(minHeight: 50, maxHeight: 150),
                      child: TextField(
                        controller: _controller,
                        maxLines: null,
                        minLines: 3,
                        decoration: const InputDecoration(
                          hintText: 'Введите сообщение...',
                          border: InputBorder.none,
                          contentPadding: EdgeInsets.symmetric(vertical: 8),
                        ),
                        onSubmitted: (_) => _sendMessage(),
                      ),
                    ),
                  ),
                  const SizedBox(width: 4),
                  IconButton(
                    icon: const Icon(Icons.attach_file),
                    onPressed: _pickFile,
                    tooltip: 'Прикрепить файл',
                  ),
                  _isLoading
                      ? IconButton(
                          icon: const Icon(Icons.stop),
                          onPressed: _cancelRequest,
                          tooltip: 'Остановить',
                        )
                      : IconButton(
                          icon: const Icon(Icons.send),
                          onPressed: () => _sendMessage(),
                          tooltip: 'Отправить',
                        ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMessageBubble(Message msg, bool isUser, int index) {
    final maxWidth = MediaQuery.of(context).size.width * 0.75;

    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: EdgeInsets.symmetric(horizontal: 12, vertical: 4),
        padding: const EdgeInsets.all(8),
        constraints: BoxConstraints(maxWidth: maxWidth),
        decoration: BoxDecoration(
          color: isUser
              ? Colors.blue[100]
              : Theme.of(context).brightness == Brightness.dark
                  ? Colors.grey[700]
                  : Colors.grey[300],
          borderRadius: BorderRadius.circular(12),
        ),
        child: SelectionArea(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              if (isUser)
                Text(
                  msg.content,
                  style: TextStyle(color: Colors.black87, fontSize: 16),
                )
              else
                MarkdownBody(
                  data: msg.content,
                  onTapLink: (text, href, title) {
                    if (href != null) {
                      final uri = Uri.tryParse(href);
                      if (uri != null && (uri.isScheme('http') || uri.isScheme('https'))) {
                        launchUrl(uri, mode: LaunchMode.externalApplication);
                      }
                    }
                  },
                  styleSheet: MarkdownStyleSheet(
                    p: TextStyle(
                      color: Theme.of(context).brightness == Brightness.dark
                          ? Colors.white
                          : Colors.black87,
                      fontSize: 16,
                    ),
                    strong: TextStyle(fontWeight: FontWeight.bold),
                  ),
                ),
              const SizedBox(height: 4),
              Row(
                mainAxisAlignment: MainAxisAlignment.end,
                mainAxisSize: MainAxisSize.min,
                children: [
                  InkWell(
                    onTap: () {
                      Clipboard.setData(ClipboardData(text: msg.content));
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('Текст скопирован')),
                      );
                    },
                    child: const Padding(
                      padding: EdgeInsets.all(4),
                      child: Icon(Icons.copy, size: 18),
                    ),
                  ),
                  if (!isUser)
                    InkWell(
                      onTap: () => _regenerateMessage(index),
                      child: const Padding(
                        padding: EdgeInsets.all(4),
                        child: Icon(Icons.refresh, size: 18),
                      ),
                    ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}