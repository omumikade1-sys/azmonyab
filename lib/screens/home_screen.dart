import 'package:flutter/material.dart';
import 'package:audioplayers/audioplayers.dart';
import '../services/api_service.dart';
import '../models/matched_job_model.dart';
import '../models/exam_model.dart';

enum ExamPageType { matchedJobs, activeExams, upcomingExams }

class HomeScreen extends StatefulWidget {
  final int userId;
  final ExamPageType pageType;

  const HomeScreen({super.key, required this.userId, required this.pageType});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  bool _isLoading = true;

  List<ExamModel> _exams = [];
  MatchedJobsResponse? _matchedData;

  // متغیرهای پخش ویس
  final AudioPlayer _audioPlayer = AudioPlayer();
  String? _playingVoiceUrl;
  bool _isPlaying = false;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  @override
  void dispose() {
    _audioPlayer.dispose();
    super.dispose();
  }

  Future<void> _loadData() async {
    setState(() => _isLoading = true);

    try {
      if (widget.pageType == ExamPageType.matchedJobs) {
        final matched = await ApiService.getMatchedJobs(widget.userId);
        if (!mounted) return;
        setState(() => _matchedData = matched);
      } else if (widget.pageType == ExamPageType.activeExams) {
        final active = await ApiService.getActiveExams();
        if (!mounted) return;
        setState(() => _exams = active);
      } else if (widget.pageType == ExamPageType.upcomingExams) {
        final upcoming = await ApiService.getUpcomingExams();
        if (!mounted) return;
        setState(() => _exams = upcoming);
      }
    } catch (e) {
      debugPrint("Error loading data: $e");
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  String get _pageTitle {
    switch (widget.pageType) {
      case ExamPageType.matchedJobs:
        return 'پیشنهادهای متناسب با رشته من';
      case ExamPageType.activeExams:
        return 'آزمون‌های فعال و در حال ثبت‌نام';
      case ExamPageType.upcomingExams:
        return 'آزمون‌های پیش‌رو و اطلاعات';
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        title: Text(_pageTitle, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 17)),
        centerTitle: true,
        backgroundColor: Colors.white,
        elevation: 0,
        foregroundColor: const Color(0xFF0F172A),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: Color(0xFF2563EB)))
          : _buildBodyContent(),
    );
  }

  Widget _buildBodyContent() {
    switch (widget.pageType) {
      case ExamPageType.matchedJobs:
        return _buildMatchedJobsTab();
      case ExamPageType.activeExams:
        return _buildActiveExamList(_exams);
      case ExamPageType.upcomingExams:
        return _buildUpcomingExamList(_exams);
    }
  }

  // ================= بخش ۱: پیشنهاد رشته من =================
  // ================= بخش ۱: پیشنهاد رشته من =================
  Widget _buildMatchedJobsTab() {
    if (_matchedData == null) {
      return const Center(child: Text('درحال بارگذاری اطلاعات...'));
    }

    final active = _matchedData!.activeExams;
    final past = _matchedData!.pastExams;
    final allExams = [...active, ...past];

    if (allExams.isEmpty) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(24.0),
          child: Text(
            'هیچ شغل یا آزمون متناسب با رشته شما یافت نشد.',
            textAlign: TextAlign.center,
            style: TextStyle(color: Color(0xFF64748B), height: 1.6),
          ),
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: allExams.length + 1, // +1 برای اضافه کردن کارت راهنمای بالای صفحه
      itemBuilder: (context, index) {
        // ردیف اول: بنر راهنما و انگیزه بخش
        if (index == 0) {
          return Container(
            margin: const EdgeInsets.only(bottom: 20),
            padding: const EdgeInsets.all(18),
            decoration: BoxDecoration(
              color: const Color(0xFF2563EB).withOpacity(0.08),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: const Color(0xFF2563EB).withOpacity(0.2)),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: const Color(0xFF2563EB).withOpacity(0.15),
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(
                    Icons.info_outline_rounded,
                    color: Color(0xFF2563EB),
                    size: 24,
                  ),
                ),
                const SizedBox(width: 14),
                const Expanded(
                  child: Text(
                    'آزمون‌های این بخش بر اساس مقطع، رشته تحصیلی و شرایط سنی شما تطبیق داده شده‌اند. اگرچه مهلت ثبت‌نام این موارد به پایان رسیده، اما بررسی آن‌ها به شما کمک می‌کند تا با ارگان‌ها، سازمان‌ها و فرصت‌های شغلی مرتبط با رشته خود آشنا شده و برای آزمون‌های بعدی آماده‌تر شوید.',
                    style: TextStyle(
                      fontSize: 13,
                      height: 1.8,
                      color: Color(0xFF1E293B),
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ),
              ],
            ),
          );
        }

        // کارت‌های آزمون (ایندکس - ۱ به خاطر کارت راهنما)
        final examInfo = allExams[index - 1];

        return Container(
          margin: const EdgeInsets.only(bottom: 16),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: const Color(0xFFE2E8F0)),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.04),
                blurRadius: 12,
                offset: const Offset(0, 4),
              ),
            ],
          ),
          child: Padding(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  examInfo.examName,
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                    color: Color(0xFF0F172A),
                  ),
                ),
                const SizedBox(height: 8),
                Row(
                  children: [
                    const Icon(Icons.calendar_month_outlined, size: 16, color: Color(0xFF64748B)),
                    const SizedBox(width: 6),
                    Text(
                      'تاریخ برگزاری: ${examInfo.examDate}',
                      style: const TextStyle(color: Color(0xFF64748B), fontSize: 13),
                    ),
                  ],
                ),
                const Divider(height: 24, color: Color(0xFFF1F5F9)),
                ...examInfo.matchedDegrees.map((deg) {
                  return Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                        decoration: BoxDecoration(
                          color: const Color(0xFF2563EB).withOpacity(0.08),
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: Text(
                          'تطبیق با: ${deg.degree} ${deg.major}',
                          style: const TextStyle(color: Color(0xFF2563EB), fontWeight: FontWeight.bold, fontSize: 13),
                        ),
                      ),
                      const SizedBox(height: 10),
                      ...deg.jobs.map((job) => Padding(
                        padding: const EdgeInsets.only(bottom: 6.0, right: 8.0),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Icon(Icons.check_circle_rounded, size: 18, color: Color(0xFF2563EB)),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                job.toString(),
                                style: const TextStyle(fontSize: 13, color: Color(0xFF334155), height: 1.4),
                              ),
                            ),
                          ],
                        ),
                      )).toList(),
                      const SizedBox(height: 10),
                    ],
                  );
                }).toList(),
              ],
            ),
          ),
        );
      },
    );
  }

  // ================= بخش ۲: لیست آزمون‌های فعال =================
  Widget _buildActiveExamList(List<ExamModel> exams) {
    if (exams.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: const Color(0xFF2563EB).withOpacity(0.1),
                  shape: BoxShape.circle,
                ),
                child: const Icon(
                  Icons.find_in_page_rounded,
                  size: 48,
                  color: Color(0xFF2563EB),
                ),
              ),
              const SizedBox(height: 20),
              const Text(
                'ما در حال تطبیق شرایط شما با تمامی آزمون های استخدامی هستیم ، در صورتی که آزمون فعالی برای شما منتشر شود در این بخش اطلاع رسانی میکنیم',
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: Color(0xFF334155),
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                  height: 1.8,
                ),
              ),
            ],
          ),
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: exams.length,
      itemBuilder: (context, index) {
        final exam = exams[index];
        final deadline = exam.regEnd ?? 'نامشخص';

        return Container(
          margin: const EdgeInsets.only(bottom: 12),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: const Color(0xFFE2E8F0)),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.03),
                blurRadius: 10,
                offset: const Offset(0, 3),
              ),
            ],
          ),
          child: ListTile(
            contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            leading: Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: const Color(0xFF2563EB).withOpacity(0.1),
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.assignment_turned_in_rounded, color: Color(0xFF2563EB)),
            ),
            title: Text(
              exam.name,
              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: Color(0xFF0F172A)),
            ),
            subtitle: Padding(
              padding: const EdgeInsets.only(top: 4.0),
              child: Text(
                'مهلت ثبت‌نام: $deadline',
                style: const TextStyle(color: Color(0xFF64748B), fontSize: 13),
              ),
            ),
            trailing: const Icon(Icons.arrow_forward_ios_rounded, size: 16, color: Color(0xFF94A3B8)),
          ),
        );
      },
    );
  }

  // ================= بخش ۳: آزمون‌های پیش‌رو (با پخش ویس) =================
  Widget _buildUpcomingExamList(List<ExamModel> exams) {
    if (exams.isEmpty) {
      return const Center(
        child: Text('هیچ آزمون پیش‌رویی یافت نشد.', style: TextStyle(color: Color(0xFF64748B))),
      );
    }

    return RefreshIndicator(
      onRefresh: _loadData,
      color: const Color(0xFF2563EB),
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: exams.length,
        itemBuilder: (context, index) {
          final exam = exams[index];
          final voiceUrl = exam.voiceUrl;
          final bool hasVoice = voiceUrl != null && voiceUrl.trim().isNotEmpty;
          final bool isThisPlaying = _isPlaying && _playingVoiceUrl == voiceUrl;

          return Container(
            margin: const EdgeInsets.only(bottom: 16),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: const Color(0xFFE2E8F0)),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.04),
                  blurRadius: 12,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Expanded(
                        child: Text(
                          exam.name,
                          style: const TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                            color: Color(0xFF2563EB),
                          ),
                        ),
                      ),
                      IconButton(
                        icon: Icon(
                          isThisPlaying ? Icons.pause_circle_filled : (hasVoice ? Icons.play_circle_fill : Icons.volume_off_rounded),
                          color: hasVoice ? const Color(0xFF8B5CF6) : const Color(0xFFCBD5E1),
                          size: 42,
                        ),
                        onPressed: () async {
                          if (!hasVoice) {
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(content: Text('ویسی برای این آزمون ثبت نشده است.')),
                            );
                            return;
                          }
                          try {
                            if (isThisPlaying) {
                              await _audioPlayer.pause();
                              if (mounted) setState(() => _isPlaying = false);
                            } else {
                              if (mounted) {
                                setState(() {
                                  _playingVoiceUrl = voiceUrl;
                                  _isPlaying = true;
                                });
                              }
                              await _audioPlayer.stop();
                              await _audioPlayer.play(UrlSource(voiceUrl!));
                            }
                          } catch (e) {
                            debugPrint("Error playing audio: $e");
                            if (mounted) {
                              setState(() => _isPlaying = false);
                              ScaffoldMessenger.of(context).showSnackBar(
                                SnackBar(content: Text('خطا در پخش ویس: $e')),
                              );
                            }
                          }
                        },
                      ),
                    ],
                  ),
                  if (exam.description != null && exam.description!.isNotEmpty) ...[
                    const SizedBox(height: 8),
                    Text(
                      exam.description!,
                      style: const TextStyle(color: Color(0xFF475569), height: 1.5, fontSize: 13),
                    ),
                  ],
                ],
              ),
            ),
          );
        },
      ),
    );
  }
}