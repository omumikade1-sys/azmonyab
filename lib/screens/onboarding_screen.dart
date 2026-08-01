import 'package:flutter/material.dart';
import 'register_screen.dart'; // مطمئن شو مسیر فایل ثبت نامت درست است

class OnboardingScreen extends StatefulWidget {
  const OnboardingScreen({super.key});

  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  final PageController _controller = PageController();
  int _currentIndex = 0;

  final List<Map<String, String>> _pages = [
    {
      'title': 'هیچ فرصت استخدامی را از دست نده!',
      'description':
          'فقط کافیست سن، مدرک و رشته تحصیلی‌ات را به ما بگویی تا دقیقاً به تو بگوییم در کدام آزمون‌ها می‌توانی شرکت کنی. هر زمان هم که آزمون جدیدی متناسب با شرایطت منتشر شود، فوراً با یک اعلان به تو خبر می‌دهیم تا هرگز جا نمانی!',
      'icon': 'search',
    },
    {
      'title': 'پیشنهادهای کاملاً شخصی‌سازی‌شده',
      'description':
          'شرایط پذیرش در آزمون‌های استخدامی بر اساس سن، رشته تحصیلی، وضعیت تأهل و نظام وظیفه متفاوت است. ما این اطلاعات را می‌گیریم تا فقط آزمون‌هایی را نشان دهیم که واجد شرایط شرکت در آن‌ها هستید!',
      'icon': 'school',
    },
    {
      'title': 'محاسبه امتیازات قانونی و سهمیه‌ها',
      'description':
          'تعداد فرزندان و وضعیت تأهل در امتیاز نهایی شما تأثیر مستقیم دارند. اطلاعات شما با بالاترین سطح امنیت ذخیره شده و صرفاً برای محاسبه دقیق شرایط استخدامی شما استفاده خواهد شد.',
      'icon': 'security',
    },
  ];

  void _goToRegister() {
    Navigator.pushReplacement(
      context,
      MaterialPageRoute(builder: (context) => const RegisterScreen()),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            // دکمه رد شدن (Skip)
            Align(
              alignment: Alignment.topLeft,
              child: TextButton(
                onPressed: _goToRegister,
                child: const Text('رد شدن', style: TextStyle(color: Colors.grey)),
              ),
            ),
            
            // بخش اسلایدر
            Expanded(
              child: PageView.builder(
                controller: _controller,
                itemCount: _pages.length,
                onPageChanged: (index) {
                  setState(() => _currentIndex = index);
                },
                itemBuilder: (context, index) {
                  final page = _pages[index];
                  return Padding(
                    padding: const EdgeInsets.all(24.0),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(
                          index == 0
                              ? Icons.manage_search_rounded
                              : index == 1
                                  ? Icons.school_rounded
                                  : Icons.verified_user_rounded,
                          size: 100,
                          color: Colors.blue,
                        ),
                        const SizedBox(height: 32),
                        Text(
                          page['title']!,
                          style: const TextStyle(
                            fontSize: 20,
                            fontWeight: FontWeight.bold,
                          ),
                          textAlign: TextAlign.center,
                        ),
                        const SizedBox(height: 16),
                        Text(
                          page['description']!,
                          style: const TextStyle(
                            fontSize: 14,
                            color: Colors.grey,
                            height: 1.6,
                          ),
                          textAlign: TextAlign.center,
                        ),
                      ],
                    ),
                  );
                },
              ),
            ),

            // نقطه نمایش صفحه فعال (Dots)
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: List.generate(
                _pages.length,
                (index) => AnimatedContainer(
                  duration: const Duration(milliseconds: 300),
                  margin: const EdgeInsets.symmetric(horizontal: 4),
                  width: _currentIndex == index ? 24 : 8,
                  height: 8,
                  decoration: BoxDecoration(
                    color: _currentIndex == index ? Colors.blue : Colors.grey.shade300,
                    borderRadius: BorderRadius.circular(4),
                  ),
                ),
              ),
            ),

            // دکمه بعدی / شروع ثبت نام
            Padding(
              padding: const EdgeInsets.all(24.0),
              child: SizedBox(
                width: double.infinity,
                height: 50,
                child: ElevatedButton(
                  onPressed: () {
                    if (_currentIndex == _pages.length - 1) {
                      _goToRegister();
                    } else {
                      _controller.nextPage(
                        duration: const Duration(milliseconds: 300),
                        curve: Curves.easeInOut,
                      );
                    }
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.blue,
                    foregroundColor: Colors.white,
                  ),
                  child: Text(
                    _currentIndex == _pages.length - 1 ? 'شروع و ثبت‌نام' : 'بعدی',
                    style: const TextStyle(fontSize: 16),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}