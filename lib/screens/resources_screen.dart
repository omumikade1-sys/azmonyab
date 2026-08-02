import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

class ResourcesScreen extends StatelessWidget {
  const ResourcesScreen({super.key});

  // تابع باز کردن لینک در پس‌زمینه گوشی
  Future<void> _launchUrl(String urlString) async {
    final Uri url = Uri.parse(urlString);
    try {
      await launchUrl(url, mode: LaunchMode.externalApplication);
    } catch (e) {
      debugPrint('خطا در باز کردن لینک: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        title: const Text(
          'منابع استخدامی',
          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
        ),
        centerTitle: true,
        backgroundColor: Colors.white,
        elevation: 0,
        foregroundColor: const Color(0xFF0F172A),
      ),
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20.0),
          child: Container(
            padding: const EdgeInsets.all(24.0),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(24),
              border: Border.all(color: const Color(0xFFE2E8F0)),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.04),
                  blurRadius: 16,
                  offset: const Offset(0, 6),
                ),
              ],
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                // آیکون بنری زیبا
                Container(
                  padding: const EdgeInsets.all(18),
                  decoration: BoxDecoration(
                    color: const Color(0xFF2563EB).withOpacity(0.1),
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(
                    Icons.library_books_rounded,
                    size: 60,
                    color: Color(0xFF2563EB),
                  ),
                ),
                const SizedBox(height: 20),

                // متن راهنمای اصلی
                const Text(
                  'ما تمامی منابع استخدامی رو با بهترین کیفیت و بیشترین آمار قبولی موجود داریم، اگه میخواید منابع رو تهیه کنین به ادمین پشتیبانی پیام بدین.',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.bold,
                    color: Color(0xFF1E293B),
                    height: 1.8,
                  ),
                ),
                const SizedBox(height: 32),

                // دکمه پشتیبانی تلگرام
                SizedBox(
                  width: double.infinity,
                  height: 52,
                  child: ElevatedButton.icon(
                    onPressed: () => _launchUrl('https://t.me/omumikade_admin'),
                    icon: const Icon(Icons.send_rounded, size: 20),
                    label: const Text(
                      'پشتیبانی تلگرام',
                      style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold),
                    ),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF0088CC),
                      foregroundColor: Colors.white,
                      elevation: 0,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(14),
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 12),

                // دکمه پشتیبانی روبیکا
                SizedBox(
                  width: double.infinity,
                  height: 52,
                  child: ElevatedButton.icon(
                    onPressed: () => _launchUrl('https://rubika.ir/omumikade'),
                    icon: const Icon(Icons.chat_bubble_rounded, size: 20),
                    label: const Text(
                      'پشتیبانی روبیکا',
                      style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold),
                    ),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF8E24AA),
                      foregroundColor: Colors.white,
                      elevation: 0,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(14),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}