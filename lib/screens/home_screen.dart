import 'package:flutter/material.dart';
import 'package:audioplayers/audioplayers.dart';
import '../services/api_service.dart';
import '../models/matched_job_model.dart';
import '../models/exam_model.dart';

// این Enum برای تشخیص اینکه کدام دکمه در داشبورد کلیک شده اضافه شد
enum ExamPageType { matchedJobs, activeExams, upcomingExams }

class HomeScreen extends StatefulWidget {
  final int userId;
  final ExamPageType pageType; // دریافت نوع صفحه از داشبورد

  const HomeScreen({super.key, required this.userId, required this.pageType});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  bool _isLoading = true;

  List<ExamModel> _exams = [];
  MatchedJobsResponse? _matchedData;

  // --- متغیرهای مربوط به پخش ویس ---
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

  // لود کردن اطلاعات فقط برای همان صفحه‌ای که کلیک شده
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

  // تغییر نام اپ‌بار بر اساس دکمه کلیک شده
  String get _pageTitle {
    switch (widget.pageType) {
      case ExamPageType.matchedJobs: return 'پیشنهاد رشته من';
      case ExamPageType.activeExams: return 'آزمون‌های فعال';
      case ExamPageType.upcomingExams: return 'آزمون‌های پیش‌رو';
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_pageTitle, style: const TextStyle(fontWeight: FontWeight.bold)),
        centerTitle: true,
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _buildBodyContent(),
    );
  }

  Widget _buildBodyContent() {
    switch (widget.pageType) {
      case ExamPageType.matchedJobs:
        return _buildMatchedJobsTab();
      case ExamPageType.activeExams:
        return _buildActiveExamList(_exams, 'هیچ آزمون فعالی یافت نشد.');
      case ExamPageType.upcomingExams:
        return _buildUpcomingExamList(_exams);
    }
  }

  // ================= بخش ۱: پیشنهاد رشته من =================
  Widget _buildMatchedJobsTab() {
    if (_matchedData == null) {
      return const Center(child: Text('درحال بارگذاری اطلاعات...'));
    }

    final active = _matchedData!.activeExams;
    final past = _matchedData!.pastExams;
    final allExams = [...active, ...past];

    if (allExams.isEmpty) {
      return const Center(child: Text('هیچ شغل یا آزمون متناسب با رشته شما یافت نشد.'));
    }

    return ListView.builder(
      padding: const EdgeInsets.all(12),
      itemCount: allExams.length,
      itemBuilder: (context, index) {
        final examInfo = allExams[index];
        final isActive = active.contains(examInfo);

        return Card(
          elevation: 3,
          margin: const EdgeInsets.symmetric(vertical: 8),
          child: Padding(
            padding: const EdgeInsets.all(12.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Expanded(
                      child: Text(
                        examInfo.examName,
                        style: TextStyle(
                          fontSize: 16, fontWeight: FontWeight.bold,
                          color: isActive ? Colors.blue : Colors.grey.shade700,
                        ),
                      ),
                    ),
                    if (!isActive)
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(color: Colors.red.shade50, borderRadius: BorderRadius.circular(4)),
                        child: const Text('منقضی شده', style: TextStyle(color: Colors.red, fontSize: 12)),
                      ),
                  ],
                ),
                const SizedBox(height: 6),
                Text('تاریخ برگزاری: ${examInfo.examDate}'),
                const Divider(),
                ...examInfo.matchedDegrees.map((deg) {
                  return Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(color: Colors.blue.shade50, borderRadius: BorderRadius.circular(8)),
                        child: Text('تطبیق با: ${deg.degree} ${deg.major}', style: const TextStyle(color: Colors.blue, fontWeight: FontWeight.bold)),
                      ),
                      const SizedBox(height: 8),
                      ...deg.jobs.map((job) => Padding(
                        padding: const EdgeInsets.only(bottom: 4.0, right: 8.0),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Icon(Icons.check_circle, size: 16, color: isActive ? Colors.green : Colors.grey),
                            const SizedBox(width: 8),
                            Expanded(child: Text(job.toString())),
                          ],
                        ),
                      )).toList(),
                      const SizedBox(height: 8),
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
  Widget _buildActiveExamList(List<ExamModel> exams, String emptyMessage) {
    if (exams.isEmpty) return Center(child: Text(emptyMessage));

    return ListView.builder(
      padding: const EdgeInsets.all(12),
      itemCount: exams.length,
      itemBuilder: (context, index) {
        final exam = exams[index];
        final deadline = exam.regEnd ?? 'نامشخص';

        return Card(
          elevation: 2,
          margin: const EdgeInsets.symmetric(vertical: 6),
          child: ListTile(
            title: Text(exam.name, style: const TextStyle(fontWeight: FontWeight.bold)),
            subtitle: Text('مهلت ثبت‌نام: $deadline'),
            trailing: const Icon(Icons.arrow_forward_ios, size: 16),
          ),
        );
      },
    );
  }

  // ================= بخش ۳: آزمون‌های پیش‌رو (همراه با پخش ویس) =================
  Widget _buildUpcomingExamList(List<ExamModel> exams) {
    if (exams.isEmpty) return const Center(child: Text('هیچ آزمون پیش‌رویی یافت نشد.'));

    return RefreshIndicator(
      onRefresh: _loadData,
      child: ListView.builder(
        padding: const EdgeInsets.all(12),
        itemCount: exams.length,
        itemBuilder: (context, index) {
          final exam = exams[index];
          final voiceUrl = exam.voiceUrl;
          final bool hasVoice = voiceUrl != null && voiceUrl.trim().isNotEmpty;
          final bool isThisPlaying = _isPlaying && _playingVoiceUrl == voiceUrl;

          return Card(
            elevation: 3,
            margin: const EdgeInsets.symmetric(vertical: 8),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            child: Padding(
              padding: const EdgeInsets.all(12.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Expanded(
                        child: Text(exam.name, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.blue)),
                      ),
                      IconButton(
                        icon: Icon(
                          isThisPlaying ? Icons.pause_circle_filled : (hasVoice ? Icons.play_circle_fill : Icons.volume_off),
                          color: hasVoice ? Colors.purple : Colors.grey,
                          size: 40,
                        ),
                        onPressed: () async {
                         if (!hasVoice) {
                           ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('ویسی برای این آزمون ثبت نشده است.')));
                           return;
                         }
                         try {
                          if (isThisPlaying) {
                            await _audioPlayer.pause();
                            if (mounted) setState(() => _isPlaying = false);
                          } else {
      // تغییر مهم: اول وضعیت دکمه را تغییر می‌دهیم تا کاربر بلافاصله متوجه شود
                            if (mounted) {
                              setState(() {
                                _playingVoiceUrl = voiceUrl;
                                _isPlaying = true;
                              });
                            }
      
      // سپس در پس‌زمینه ویس را لود و پخش می‌کنیم
                            await _audioPlayer.stop();
                            await _audioPlayer.play(UrlSource(voiceUrl!));
                          }
                          } catch (e) {
                            debugPrint("Error playing audio: $e");
                            if (mounted) {
      // اگر خطایی رخ داد، دکمه را به حالت اول برمی‌گردانیم
                              setState(() => _isPlaying = false);
                              ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('خطا در پخش ویس: $e')));
                            }
                          }
                        },
                      ),
                    ],
                  ),
                  if (exam.description != null && exam.description!.isNotEmpty) ...[
                    const SizedBox(height: 8),
                    Text(exam.description!, style: TextStyle(color: Colors.grey.shade800, height: 1.4)),
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