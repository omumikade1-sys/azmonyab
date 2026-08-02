import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import 'home_screen.dart';
import 'profile_screen.dart';
import 'resources_screen.dart';

class DashboardScreen extends StatefulWidget {
  final int userId;

  const DashboardScreen({super.key, required this.userId});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  int _currentIndex = 0;

  // صفحات برنامه برای Bottom Navigation
  late final List<Widget> _pages;

  @override
  void initState() {
    super.initState();
    // ارتباط صفحات به تب‌های پایین صفحه
    _pages = [
      _buildHomeContent(),
      HomeScreen(userId: widget.userId, pageType: ExamPageType.activeExams),
      const ResourcesScreen(),
      ProfileScreen(userId: widget.userId),
    ];
  }

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
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (context) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 24.0, horizontal: 20.0),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 50,
                height: 5,
                margin: const EdgeInsets.only(bottom: 24),
                decoration: BoxDecoration(
                  color: Colors.grey.shade300,
                  borderRadius: BorderRadius.circular(10),
                ),
              ),
              const Text(
                'ارتباط با پشتیبانی عمومی کده',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Color(0xFF0F172A)), 
              ),
              const SizedBox(height: 24),
              _buildSupportTile(
                title: 'پشتیبانی در تلگرام',
                icon: Icons.telegram,
                color: const Color(0xFF0088cc),
                onTap: () {
                  Navigator.pop(context);
                  _launchUrl('https://t.me/omumikade_admin');
                },
              ),
              const SizedBox(height: 12),
              _buildSupportTile(
                title: 'پشتیبانی در روبیکا',
                icon: Icons.support_agent,
                color: const Color(0xFF9C27B0),
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

  Widget _buildSupportTile({required String title, required IconData icon, required Color color, required VoidCallback onTap}) {
    return ListTile(
      contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      tileColor: color.withOpacity(0.05),
      leading: Container(
        padding: const EdgeInsets.all(10),
        decoration: BoxDecoration(
          color: color.withOpacity(0.1),
          shape: BoxShape.circle,
        ),
        child: Icon(icon, color: color, size: 28),
      ),
      title: Text(title, style: TextStyle(fontWeight: FontWeight.bold, color: color.withOpacity(0.9))),
      trailing: Icon(Icons.arrow_forward_ios, size: 16, color: color.withOpacity(0.5)),
      onTap: onTap,
    );
  }

  // محتوای اصلی داشبورد (صفحه خانه)
  Widget _buildHomeContent() {
    return SafeArea(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // هدر بالای صفحه با دکمه پشتیبانی
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'خوش آمدید 👋',
                      style: TextStyle(fontSize: 14, color: Colors.grey, fontWeight: FontWeight.w600),
                    ),
                    const SizedBox(height: 4),
                    const Text(
                      'سامانه جامع آزمون‌یاب',
                      style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Color(0xFF0F172A)),
                    ),
                  ],
                ),
                Container(
                  decoration: BoxDecoration(
                    color: Colors.white,
                    shape: BoxShape.circle,
                    boxShadow: [
                      BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 10, spreadRadius: 1)
                    ],
                  ),
                  child: IconButton(
                    icon: const Icon(Icons.headset_mic_rounded, color: Color(0xFF2563EB)),
                    onPressed: () => _showSupportBottomSheet(context),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 32),

            // بنر اصلی مدرن با رنگ سازمانی 
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFF2563EB), Color(0xFF1D4ED8)], // آبی سازمانی زیبا
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(24),
                boxShadow: [
                  BoxShadow(
                    color: const Color(0xFF2563EB).withOpacity(0.3),
                    blurRadius: 15,
                    offset: const Offset(0, 8),
                  ),
                ],
              ),
              child: Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'موفقیت در استخدامی',
                          style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          'با جامع‌ترین منابع و جدیدترین آزمون‌های عمومی‌کده استخدام شوید.',
                          style: TextStyle(color: Colors.white.withOpacity(0.9), fontSize: 13, height: 1.5),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 16),
                  const Icon(Icons.menu_book_rounded, color: Colors.white, size: 48),
                ],
              ),
            ),
            const SizedBox(height: 32),

            // بخش دسترسی سریع
            const Text(
              'دسترسی سریع',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Color(0xFF0F172A)),
            ),
            const SizedBox(height: 16),
            
            GridView.count(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              crossAxisCount: 2,
              crossAxisSpacing: 16,
              mainAxisSpacing: 16,
              childAspectRatio: 1.1,
              children: [
                _buildModernCard(
                  title: 'مناسب رشته من',
                  icon: Icons.work_outline_rounded,
                  color: const Color(0xFF3B82F6),
                  onTap: () => Navigator.push(
                    context,
                    MaterialPageRoute(builder: (_) => HomeScreen(userId: widget.userId, pageType: ExamPageType.matchedJobs)),
                  ),
                ),
                _buildModernCard(
                  title: 'آزمون‌های آینده',
                  icon: Icons.event_note_rounded,
                  color: const Color(0xFFF59E0B), // طلایی/نارنجی ملایم
                  onTap: () => Navigator.push(
                    context,
                    MaterialPageRoute(builder: (_) => HomeScreen(userId: widget.userId, pageType: ExamPageType.upcomingExams)),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildModernCard({required String title, required IconData icon, required Color color, required VoidCallback onTap}) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: color.withOpacity(0.08),
            blurRadius: 15,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(20),
          child: Padding(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: color.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(14),
                  ),
                  child: Icon(icon, size: 32, color: color),
                ),
                const SizedBox(height: 16),
                Text(
                  title,
                  textAlign: TextAlign.center,
                  style: const TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.bold,
                    color: Color(0xFF334155),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC), // پس‌زمینه بسیار روشن و چشم‌نواز
      body: _pages[_currentIndex], // نمایش صفحه‌ای که در نوار پایین انتخاب شده
      bottomNavigationBar: Container(
        decoration: BoxDecoration(
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.05),
              blurRadius: 20,
              offset: const Offset(0, -5),
            ),
          ],
        ),
        child: ClipRRect(
          borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
          child: BottomNavigationBar(
            currentIndex: _currentIndex,
            onTap: (index) => setState(() => _currentIndex = index),
            backgroundColor: Colors.white,
            selectedItemColor: const Color(0xFF2563EB), 
            unselectedItemColor: const Color(0xFF94A3B8),
            selectedLabelStyle: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
            unselectedLabelStyle: const TextStyle(fontWeight: FontWeight.normal, fontSize: 12),
            type: BottomNavigationBarType.fixed,
            elevation: 0,
            items: const [
              BottomNavigationBarItem(
                icon: Padding(padding: EdgeInsets.only(bottom: 4), child: Icon(Icons.home_rounded)),
                label: 'داشبورد',
              ),
              BottomNavigationBarItem(
                icon: Padding(padding: EdgeInsets.only(bottom: 4), child: Icon(Icons.event_available_rounded)),
                label: 'آزمون‌ها',
              ),
              BottomNavigationBarItem(
                icon: Padding(padding: EdgeInsets.only(bottom: 4), child: Icon(Icons.menu_book_rounded)),
                label: 'منابع',
              ),
              BottomNavigationBarItem(
                icon: Padding(padding: EdgeInsets.only(bottom: 4), child: Icon(Icons.person_rounded)),
                label: 'پروفایل',
              ),
            ],
          ),
        ),
      ),
    );
  }
}