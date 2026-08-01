class ExamModel {
  final int id;
  final String name;
  final String? examDate;
  final String? regStart;
  final String? regEnd;
  final String? description;
  final String? voiceUrl; // اضافه شدن فیلد ویس

  ExamModel({
    required this.id,
    required this.name,
    this.examDate,
    this.regStart,
    this.regEnd,
    this.description,
    this.voiceUrl,
  });

  factory ExamModel.fromJson(Map<String, dynamic> json) {
    return ExamModel(
      id: json['id'] is int ? json['id'] : int.parse(json['id'].toString()),
      name: json['name'] ?? '',
      examDate: json['exam_date'],
      regStart: json['reg_start'],
      regEnd: json['reg_end'],
      description: json['description'],
      // خواندن آدرس ویس از خروجی پایتون (voice_url)
      voiceUrl: json['voice_url'] ?? json['voice_file_id'], 
    );
  }
}