// فایل: lib/models/matched_job_model.dart

class MatchedDegreeBlock {
  final String degree;
  final String major;
  final List<dynamic> jobs;

  MatchedDegreeBlock({
    required this.degree,
    required this.major,
    required this.jobs,
  });

  factory MatchedDegreeBlock.fromJson(Map<String, dynamic> json) {
    return MatchedDegreeBlock(
      degree: json['degree'] ?? '',
      major: json['major'] ?? '',
      jobs: json['jobs'] ?? [],
    );
  }
}

class MatchedExamInfo {
  final int examId;
  final String examName;
  final String examDate;
  final List<MatchedDegreeBlock> matchedDegrees;

  MatchedExamInfo({
    required this.examId,
    required this.examName,
    required this.examDate,
    required this.matchedDegrees,
  });

  factory MatchedExamInfo.fromJson(Map<String, dynamic> json) {
    var degreeList = json['matched_degrees'] as List? ?? [];
    return MatchedExamInfo(
      examId: json['exam_id'] ?? 0,
      examName: json['exam_name'] ?? '',
      examDate: json['exam_date'] ?? '',
      matchedDegrees: degreeList.map((d) => MatchedDegreeBlock.fromJson(d)).toList(),
    );
  }
}

// خروجی کلی اندپوینت /user/matched-jobs/{user_id}
class MatchedJobsResponse {
  final List<MatchedExamInfo> activeExams;
  final List<MatchedExamInfo> pastExams;

  MatchedJobsResponse({
    required this.activeExams,
    required this.pastExams,
  });

  factory MatchedJobsResponse.fromJson(Map<String, dynamic> json) {
    var activeList = json['active_exams'] as List? ?? [];
    var pastList = json['past_exams'] as List? ?? [];

    return MatchedJobsResponse(
      activeExams: activeList.map((e) => MatchedExamInfo.fromJson(e)).toList(),
      pastExams: pastList.map((e) => MatchedExamInfo.fromJson(e)).toList(),
    );
  }
}