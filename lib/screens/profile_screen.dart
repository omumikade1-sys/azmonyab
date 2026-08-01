import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/user_model.dart';
import 'register_screen.dart'; // اضافه شدن ایمپورت صفحه ثبت‌نام

class ProfileScreen extends StatefulWidget {
  final int userId;
  const ProfileScreen({super.key, required this.userId});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  late Future<UserProfile?> _profileFuture;

  @override
  void initState() {
    super.initState();
    _profileFuture = ApiService.getProfile(widget.userId);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('پروفایل کاربری')),
      body: FutureBuilder<UserProfile?>(
        future: _profileFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError || snapshot.data == null) {
            return const Center(child: Text('خطا در بارگذاری اطلاعات کاربری'));
          }

          final user = snapshot.data!;
          return ListView(
            padding: const EdgeInsets.all(16.0),
            children: [
              ListTile(
                leading: const Icon(Icons.person),
                title: const Text('نام و نام خانوادگی'),
                subtitle: Text(user.name),
              ),
              const Divider(),
              ListTile(
                leading: const Icon(Icons.phone),
                title: const Text('شماره تماس'),
                subtitle: Text(user.phone),
              ),
              const Divider(),
              ListTile(
                leading: const Icon(Icons.cake),
                title: const Text('سن دقیق'),
                subtitle: Text('${user.ageYears} سال و ${user.ageMonths} ماه و ${user.ageDays} روز'),
              ),
              const Divider(),
              ListTile(
                leading: const Icon(Icons.family_restroom),
                title: const Text('وضعیت تاهل و فرزندان'),
                subtitle: Text('${user.isMarried ? "متاهل" : "مجرد"} - ${user.childrenCount} فرزند'),
              ),
              const Divider(),
              const Padding(
                padding: EdgeInsets.only(top: 16.0, bottom: 8.0),
                child: Text('مدارک تحصیلی ثبت شده:', style: TextStyle(fontWeight: FontWeight.bold)),
              ),
              ...user.degrees.map((deg) => Card(
                elevation: 1,
                child: ListTile(
                  leading: const Icon(Icons.school, color: Colors.blue),
                  title: Text(deg.major),
                  subtitle: Text(deg.degree),
                ),
              )).toList(),
              
              const SizedBox(height: 32), // فاصله دادن از مدارک تحصیلی
              
              // دکمه ویرایش اطلاعات
              SizedBox(
                width: double.infinity,
                height: 50,
                child: ElevatedButton.icon(
                  onPressed: () {
                    // هدایت به صفحه ثبت نام برای ویرایش اطلاعات
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) => const RegisterScreen(),
                      ),
                    );
                  },
                  icon: const Icon(Icons.edit_document),
                  label: const Text(
                    'ویرایش اطلاعات',
                    style: TextStyle(fontSize: 16),
                  ),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.orange,
                    foregroundColor: Colors.white,
                  ),
                ),
              ),
              const SizedBox(height: 16),
            ],
          );
        },
      ),
    );
  }
}