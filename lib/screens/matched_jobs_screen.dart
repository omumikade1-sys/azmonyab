import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/matched_job_model.dart';

class MatchedJobsScreen extends StatefulWidget {
  final int userId;

  const MatchedJobsScreen({Key? key, required this.userId}) : super(key: key);

  @override
  _MatchedJobsScreenState createState() => _MatchedJobsScreenState();
}

class _MatchedJobsScreenState extends State<MatchedJobsScreen> {
  late Future<MatchedJobsResponse?> _matchedJobsFuture;

  @override
  void initState() {
    super.initState();
    _matchedJobsFuture = ApiService.getMatchedJobs(widget.userId);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('مشاغل و آزمون‌های متناسب'),
      ),
      body: FutureBuilder<MatchedJobsResponse?>(
        future: _matchedJobsFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }

          if (snapshot.hasError || snapshot.data == null) {
            return Center(
              child: Text('خطا در دریافت اطلاعات: ${snapshot.error ?? "داده‌ای یافت نشد"}'),
            );
          }

          final responseData = snapshot.data!;
          final activeExams = responseData.activeExams;

          if (activeExams.isEmpty) {
            return const Center(
              child: Text('هیچ آزمون یا شغلی متناسب با شرایط شما یافت نشد.'),
            );
          }

          return ListView.builder(
            itemCount: activeExams.length,
            itemBuilder: (context, index) {
              final examInfo = activeExams[index];
              return Card(
                margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                elevation: 3,
                child: Padding(
                  padding: const EdgeInsets.all(12.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        examInfo.examName,
                        style: const TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                          color: Colors.blue,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text('تاریخ آزمون: ${examInfo.examDate}'),
                      const Divider(),
                      ...examInfo.matchedDegrees.map((degBlock) {
                        return Padding(
                          padding: const EdgeInsets.symmetric(vertical: 4.0),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                'مقطع: ${degBlock.degree} - رشته: ${degBlock.major}',
                                style: const TextStyle(fontWeight: FontWeight.w600),
                              ),
                              const SizedBox(height: 4),
                              ...degBlock.jobs.map((job) {
                                return ListTile(
                                  dense: true,
                                  title: Text(job.toString()),
                                );
                              }),
                            ],
                          ),
                        );
                      }),
                    ],
                  ),
                ),
              );
            },
          );
        },
      ),
    );
  }
}