class Message {
  final String role;
  final String content;
  final DateTime? timestamp;

  Message({
    required this.role,
    required this.content,
    this.timestamp,
  });

  factory Message.fromJson(Map<String, dynamic> json) =>
      Message(
        role: json['role'],
        content: json['content'],
        timestamp: json['timestamp'] != null ? DateTime.parse(json['timestamp']) : null,
      );
}