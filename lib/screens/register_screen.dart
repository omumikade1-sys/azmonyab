import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/user_model.dart';
import '../services/api_service.dart';
import 'home_screen.dart';
import 'dashboard_screen.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _formKey = GlobalKey<FormState>();

  // کنترلرهای فرم
  final _userIdController = TextEditingController();
  final _nameController = TextEditingController();
  final _phoneController = TextEditingController();
  final _bYearController = TextEditingController();
  final _bMonthController = TextEditingController();
  final _bDayController = TextEditingController();
  final _childrenController = TextEditingController(text: '0');

  int _isMarried = 0; // 0 = مجرد، 1 = متأهل
  bool _isLoading = false;

  // لیست مدارک تحصیلی کاربر
  final List<DegreeItem> _degrees = [
    DegreeItem(degree: 'کارشناسی', major: ''),
  ];

  final List<String> _degreeOptions = [
    'دیپلم',
    'کاردانی',
    'کارشناسی',
    'کارشناسی ارشد',
    'دکتری',
    'حوزوی',
    'دانشنامه تخصصی',
    'حافظ قرآن',
  ];

  final List<String> quranDegrees = [
    'درجه 1',
    'درجه 2',
    'درجه 3',
    'درجه 4',
    'درجه 5',
  ];

  final List<String> hawzahDegrees = [
    'سطح 1',
    'سطح 2',
    'سطح 3',
    'سطح 4',
  ];

  void _addDegreeField() {
    setState(() {
      _degrees.add(DegreeItem(degree: 'کارشناسی', major: ''));
    });
  }

  void _removeDegreeField(int index) {
    if (_degrees.length > 1) {
      setState(() {
        _degrees.removeAt(index);
      });
    }
  }

  Future<void> _submitForm() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isLoading = true);

    final registerData = RegisterModel(
      userId: int.parse(_userIdController.text.trim()),
      name: _nameController.text.trim(),
      phone: _phoneController.text.trim(),
      bYear: int.parse(_bYearController.text.trim()),
      bMonth: int.parse(_bMonthController.text.trim()),
      bDay: int.parse(_bDayController.text.trim()),
      isMarried: _isMarried,
      childrenCount: int.parse(_childrenController.text.trim()),
      degrees: _degrees,
    );

    final result = await ApiService.registerUser(registerData);

    setState(() => _isLoading = false);

    // بررسی اینکه آیا صفحه هنوز باز است تا خطای کانتکست ندهد
    if (!mounted) return;

    if (result['success']) {
      // 🟢 تغییر مهم: ذخیره در حافظه گوشی بعد از ثبت‌نام موفق
      final prefs = await SharedPreferences.getInstance();
      await prefs.setBool('isRegistered', true); // ثبت اینکه کاربر ثبت‌نام کرده
      await prefs.setInt('userId', int.parse(_userIdController.text.trim())); // ذخیره آیدی برای دفعات بعدی

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(result['message']),
          backgroundColor: Colors.green,
        ),
      );

      // انتقال کاربر به صفحه داشبورد اصلی
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (context) => DashboardScreen(
            userId: int.parse(_userIdController.text.trim()),
          ),
        ),
      );
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(result['message']),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('ثبت‌نام در سامانه آزمون‌یاب'),
        centerTitle: true,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.only(left: 16.0, right: 16.0, top: 16.0, bottom: 80.0),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'اطلاعات فردی',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _userIdController, // اگر خواستی می‌تونی اسم این کنترلر رو به _usernameController تغییر بدی
                keyboardType: TextInputType.text,
                textDirection: TextDirection.ltr, // برای اینکه چپ‌چین و انگلیسی تایپ بشه
                decoration: const InputDecoration(
                  labelText: 'نام کاربری (فقط حروف انگلیسی و عدد)',
                  border: OutlineInputBorder(),
                ),
                validator: (v) {
                  if (v == null || v.isEmpty) return 'لطفاً نام کاربری را وارد کنید';
                  // بررسی با Regex برای حروف انگلیسی و عدد
                  if (!RegExp(r'^[a-zA-Z0-9]+$').hasMatch(v)) {
                    return 'نام کاربری فقط باید شامل حروف انگلیسی و عدد باشد';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _nameController,
                decoration: const InputDecoration(
                  labelText: 'نام و نام خانوادگی',
                  border: OutlineInputBorder(),
                ),
                validator: (v) => v!.isEmpty ? 'لطفاً نام را وارد کنید' : null,
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _phoneController,
                keyboardType: TextInputType.phone,
                decoration: const InputDecoration(
                  labelText: 'شماره همراه',
                  border: OutlineInputBorder(),
                ),
                validator: (v) => v!.isEmpty ? 'لطفاً شماره را وارد کنید' : null,
              ),
              const SizedBox(height: 16),
              const Text('تاریخ تولد (شمسی):'),
              const SizedBox(height: 8),
              Row(
                children: [
                  Expanded(
                    child: TextFormField(
                      controller: _bYearController,
                      keyboardType: TextInputType.number,
                      decoration: const InputDecoration(
                        labelText: 'سال (۱۳۷۵)',
                        border: OutlineInputBorder(),
                      ),
                      validator: (v) => v!.isEmpty ? 'سال' : null,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: TextFormField(
                      controller: _bMonthController,
                      keyboardType: TextInputType.number,
                      decoration: const InputDecoration(
                        labelText: 'ماه (۱-۱۲)',
                        border: OutlineInputBorder(),
                      ),
                      validator: (v) => v!.isEmpty ? 'ماه' : null,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: TextFormField(
                      controller: _bDayController,
                      keyboardType: TextInputType.number,
                      decoration: const InputDecoration(
                        labelText: 'روز (۱-۳۱)',
                        border: OutlineInputBorder(),
                      ),
                      validator: (v) => v!.isEmpty ? 'روز' : null,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              Row(
                children: [
                  const Text('وضعیت تأهل:'),
                  const SizedBox(width: 16),
                  ChoiceChip(
                    label: const Text('مجرد'),
                    selected: _isMarried == 0,
                    onSelected: (val) => setState(() => _isMarried = 0),
                  ),
                  const SizedBox(width: 8),
                  ChoiceChip(
                    label: const Text('متأهل'),
                    selected: _isMarried == 1,
                    onSelected: (val) => setState(() => _isMarried = 1),
                  ),
                ],
              ),
              if (_isMarried == 1) ...[
                const SizedBox(height: 12),
                TextFormField(
                  controller: _childrenController,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(
                    labelText: 'تعداد فرزندان',
                    border: OutlineInputBorder(),
                  ),
                ),
              ],
              const Divider(height: 32, thickness: 1.5),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text(
                    'مدارک تحصیلی',
                    style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                  ),
                  IconButton(
                    icon: const Icon(Icons.add_circle, color: Colors.blue),
                    onPressed: _addDegreeField,
                  ),
                ],
              ),
              ListView.builder(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                itemCount: _degrees.length,
                itemBuilder: (context, index) {
                  final currentDegree = _degrees[index].degree;

                  return Card(
                    margin: const EdgeInsets.symmetric(vertical: 6),
                    child: Padding(
                      padding: const EdgeInsets.all(8.0),
                      child: Row(
                        children: [
                          DropdownButton<String>(
                            value: _degrees[index].degree,
                            items: _degreeOptions.map((String deg) {
                              return DropdownMenuItem<String>(
                                value: deg,
                                child: Text(deg),
                              );
                            }).toList(),
                            onChanged: (val) {
                              if (val != null) {
                                setState(() {
                                  // هنگام تغییر نوع مقطع، مقدار رشته/درجه قبلی ریست می‌شود
                                  _degrees[index] = DegreeItem(
                                    degree: val,
                                    major: '',
                                  );
                                });
                              }
                            },
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Builder(
                              builder: (context) {
                                // ۱. اگر مقطع «حافظ قرآن» بود
                                if (currentDegree == 'حافظ قرآن') {
                                  return DropdownButtonFormField<String>(
                                    value: quranDegrees.contains(_degrees[index].major)
                                        ? _degrees[index].major
                                        : null,
                                    decoration: const InputDecoration(
                                      labelText: 'درجه مدرک',
                                      border: OutlineInputBorder(),
                                    ),
                                    items: quranDegrees.map((deg) {
                                      return DropdownMenuItem(
                                        value: deg,
                                        child: Text(deg),
                                      );
                                    }).toList(),
                                    onChanged: (val) {
                                      setState(() {
                                        _degrees[index] = DegreeItem(
                                          degree: currentDegree,
                                          major: val ?? '',
                                        );
                                      });
                                    },
                                    validator: (v) =>
                                        v == null || v.isEmpty ? 'درجه را انتخاب کنید' : null,
                                  );
                                }
                                // ۲. اگر مقطع «حوزوی» بود
                                else if (currentDegree == 'حوزوی') {
                                  return DropdownButtonFormField<String>(
                                    value: hawzahDegrees.contains(_degrees[index].major)
                                        ? _degrees[index].major
                                        : null,
                                    decoration: const InputDecoration(
                                      labelText: 'سطح مدرک',
                                      border: OutlineInputBorder(),
                                    ),
                                    items: hawzahDegrees.map((deg) {
                                      return DropdownMenuItem(
                                        value: deg,
                                        child: Text(deg),
                                      );
                                    }).toList(),
                                    onChanged: (val) {
                                      setState(() {
                                        _degrees[index] = DegreeItem(
                                          degree: currentDegree,
                                          major: val ?? '',
                                        );
                                      });
                                    },
                                    validator: (v) =>
                                        v == null || v.isEmpty ? 'سطح را انتخاب کنید' : null,
                                  );
                                }
                                // ۳. سایر مقاطع (ورودی متنی معمولی)
                                else {
                                  return TextFormField(
                                    key: ValueKey('text_$index'),
                                    initialValue: _degrees[index].major,
                                    decoration: const InputDecoration(
                                      labelText: 'رشته تحصیلی',
                                      border: OutlineInputBorder(),
                                    ),
                                    onChanged: (val) {
                                      _degrees[index] = DegreeItem(
                                        degree: _degrees[index].degree,
                                        major: val,
                                      );
                                    },
                                    validator: (v) =>
                                        v!.isEmpty ? 'رشته را وارد کنید' : null,
                                  );
                                }
                              },
                            ),
                          ),
                          if (_degrees.length > 1)
                            IconButton(
                              icon: const Icon(Icons.delete, color: Colors.red),
                              onPressed: () => _removeDegreeField(index),
                            ),
                        ],
                      ),
                    ),
                  );
                },
              ),
              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                height: 50,
                child: ElevatedButton(
                  onPressed: _isLoading ? null : _submitForm,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.blue,
                    foregroundColor: Colors.white,
                  ),
                  child: _isLoading
                      ? const CircularProgressIndicator(color: Colors.white)
                      : const Text(
                          'ثبت اطلاعات',
                          style: TextStyle(fontSize: 16),
                        ),
                ),
              ),
              const SizedBox(height: 40), // ایجاد فاصله کافی در انتهای صفحه برای اسکرول راحت
            ],
          ),
        ),
      ),
    );
  }
}