import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import 'home_screen.dart';
import 'profile_screen.dart';
import 'resources_screen.dart';

class DashboardScreen extends StatelessWidget {
  final int userId;

  const DashboardScreen({super.key, required this.userId});

  Future<void> _launchUrl(String urlString) async {
    final Uri url = Uri.parse(urlString);
    try {
      await launchUrl(url, mode: LaunchMode.externalApplication);
    } catch (e) {
      debugPrint('خطا در باز کردن لینک: $e');
    }
  }

  void _showSupportBottomSheet(BuildContext context) {
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 20.0, horizontal: 16.0),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 40,
                height: 4,
                margin: const EdgeInsets.only(bottom: 16),
                decoration: BoxDecoration(
                  color: Colors.grey.shade300,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
              const Text(
                'ارتباط با پشتیبانی',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 16),
              ListTile(
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                tileColor: Colors.blue.shade50,
                leading: const Icon(Icons.telegram, color: Color(0xFF0088cc), size: 32),
                title: const Text('پشتیبانی در تلگرام', style: TextStyle(fontWeight: FontWeight.bold)),
                trailing: const Icon(Icons.arrow_forward_ios, size: 16),
                onTap: () {
                  Navigator.pop(context);
                  _launchUrl('https://t.me/omumikade_admin');
                },
              ),
              const SizedBox(height: 10),
              ListTile(
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                tileColor: Colors.purple.shade50,
                leading: const Icon(Icons.support_agent, color: Color(0xFF9C27B0), size: 32),
                title: const Text('پشتیبانی در روبیکا', style: TextStyle(fontWeight: FontWeight.bold)),
                trailing: const Icon(Icons.arrow_forward_ios, size: 16),
                onTap: () {
                  Navigator.pop(context);
                  _launchUrl('https://rubika.ir/omumikade');
                },
              ),
            ],
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey.shade100,
      appBar: AppBar(
        title: const Text('آزمون‌یاب استخدامی', style: TextStyle(fontWeight: FontWeight.bold)),
        centerTitle: true,
        elevation: 0,
        backgroundColor: Colors.white,
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            children: [
              Expanded(
                child: GridView.count(
                  crossAxisCount: 2,
                  crossAxisSpacing: 16,
                  mainAxisSpacing: 16,
                  children: [
                    _buildSquareCard(
                      context,
                      title: 'پروفایل کاربری',
                      icon: Icons.person_rounded,
                      color: Colors.blue,
                      onTap: () => Navigator.push(
                        context,
                        MaterialPageRoute(builder: (_) => ProfileScreen(userId: userId)),
                      ),
                    ),
                    _buildSquareCard(
                      context,
                      title: 'آزمون‌های مناسب رشته من',
                      icon: Icons.work_rounded,
                      color: Colors.indigo,
                      onTap: () => Navigator.push(
                        context,
                        MaterialPageRoute(builder: (_) => HomeScreen(userId: userId, pageType: ExamPageType.matchedJobs)),
                      ),
                    ),
                    _buildSquareCard(
                      context,
                      title: 'آزمون‌های فعال',
                      icon: Icons.event_available_rounded,
                      color: Colors.teal,
                      onTap: () => Navigator.push(
                        context,
                        MaterialPageRoute(builder: (_) => HomeScreen(userId: userId, pageType: ExamPageType.activeExams)),
                      ),
                    ),
                    _buildSquareCard(
                      context,
                      title: 'آزمون‌های آینده',
                      icon: Icons.event_note_rounded,
                      color: Colors.orange.shade800,
                      onTap: () => Navigator.push(
                        context,
                        MaterialPageRoute(builder: (_) => HomeScreen(userId: userId, pageType: ExamPageType.upcomingExams)),
                      ),
                    ),
                    // 🟢 کارت مربعی جدید: منابع استخدامی
                    _buildSquareCard(
                      context,
                      title: 'منابع استخدامی',
                      icon: Icons.menu_book_rounded, // آیکون کتاب/منابع استخدامی
                      color: Colors.purple.shade700,
                      onTap: () => Navigator.push(
                        context,
                        MaterialPageRoute(builder: (_) => const ResourcesScreen()),
                      ),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 16),

              // دکمه بزرگ پشتیبانی زیر کارت‌های مربعی
              InkWell(
                onTap: () => _showSupportBottomSheet(context),
                borderRadius: BorderRadius.circular(20),
                child: Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(18),
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: [Colors.purple.shade600, Colors.deepPurple.shade800],
                      begin: Alignment.topRight,
                      end: Alignment.bottomLeft,
                    ),
                    borderRadius: BorderRadius.circular(20),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.purple.withOpacity(0.3),
                        blurRadius: 10,
                        offset: const Offset(0, 4),
                      ),
                    ],
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: const [
                      Icon(Icons.headset_mic_rounded, color: Colors.white, size: 28),
                      SizedBox(width: 12),
                      Text(
                        'ارتباط با پشتیبانی',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildSquareCard(
    BuildContext context, {
    required String title,
    required IconData icon,
    required Color color,
    required VoidCallback onTap,
  }) {
    return Material(
      color: Colors.white,
      borderRadius: BorderRadius.circular(20),
      elevation: 2,
      shadowColor: color.withOpacity(0.2),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(20),
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: color.withOpacity(0.1),
                  shape: BoxShape.circle,
                ),
                child: Icon(icon, size: 36, color: color),
              ),
              const SizedBox(height: 12),
              Text(
                title,
                textAlign: TextAlign.center,
                style: const TextStyle(
                  fontSize: 15,
                  fontWeight: FontWeight.bold,
                  color: Colors.black87,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}