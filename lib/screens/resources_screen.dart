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
      appBar: AppBar(
        title: const Text('منابع استخدامی'),
        centerTitle: true,
      ),
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            const Icon(
              Icons.library_books_rounded,
              size: 80,
              color: Colors.blue,
            ),
            const SizedBox(height: 24),
            const Text(
              'ما تمامی منابع استخدامی رو با بهترین کیفیت و بیشترین آمار قبولی موجود داریم، اگه میخواید منابع رو تهیه کنین به ادمین پشتیبانی پیام بدین.',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
                height: 1.8,
              ),
            ),
            const SizedBox(height: 40),
            
            // دکمه پشتیبانی تلگرام
            SizedBox(
              width: double.infinity,
              height: 50,
              child: ElevatedButton.icon(
                onPressed: () => _launchUrl('https://t.me/omumikade_admin'),
                icon: const Icon(Icons.send),
                label: const Text('پشتیبانی تلگرام', style: TextStyle(fontSize: 16)),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF0088cc), // رنگ آیکون تلگرام
                  foregroundColor: Colors.white,
                ),
              ),
            ),
            const SizedBox(height: 16),
            
            // دکمه پشتیبانی روبیکا
            SizedBox(
              width: double.infinity,
              height: 50,
              child: ElevatedButton.icon(
                onPressed: () => _launchUrl('https://rubika.ir/omumikade'),
                icon: const Icon(Icons.chat_bubble_outline),
                label: const Text('پشتیبانی روبیکا', style: TextStyle(fontSize: 16)),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF9C27B0), // رنگ بنفش روبیکا
                  foregroundColor: Colors.white,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}