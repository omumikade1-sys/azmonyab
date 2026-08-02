import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/user_model.dart';
import '../services/api_service.dart';
import 'dashboard_screen.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  int _currentStep = 0;
  final _step1FormKey = GlobalKey<FormState>();
  final _step2FormKey = GlobalKey<FormState>();

  // کنترلرهای متنی
  final _nameController = TextEditingController();
  final _phoneController = TextEditingController();
  final _bYearController = TextEditingController();
  final _bMonthController = TextEditingController();
  final _bDayController = TextEditingController();
  final _childrenController = TextEditingController(text: '0');

  int _isMarried = 0;
  bool _isLoading = false;

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
    if (!_step2FormKey.currentState!.validate()) return;

    setState(() => _isLoading = true);

    // تولید آیدی کاملاً عددی و خودمختار
    final int generatedUserId = DateTime.now().millisecondsSinceEpoch % 1000000;

    final registerData = RegisterModel(
      userId: generatedUserId,
      name: _nameController.text.trim(),
      phone: _phoneController.text.trim(),
      bYear: int.parse(_bYearController.text.trim()),
      bMonth: int.parse(_bMonthController.text.trim()),
      bDay: int.parse(_bDayController.text.trim()),
      isMarried: _isMarried,
      childrenCount: int.tryParse(_childrenController.text.trim()) ?? 0,
      degrees: _degrees,
    );

    final result = await ApiService.registerUser(registerData);

    setState(() => _isLoading = false);

    if (!mounted) return;

    if (result['success']) {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setBool('isRegistered', true);
      await prefs.setInt('userId', generatedUserId);

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(result['message']),
          backgroundColor: Colors.green,
        ),
      );

      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (context) => DashboardScreen(userId: generatedUserId),
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

  InputDecoration _customInputDecoration(String label, IconData icon) {
    return InputDecoration(
      labelText: label,
      prefixIcon: Icon(icon, color: const Color(0xFF2563EB), size: 22),
      filled: true,
      fillColor: Colors.white,
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(16),
        borderSide: const BorderSide(color: Color(0xFFE2E8F0)),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(16),
        borderSide: const BorderSide(color: Color(0xFFE2E8F0)),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(16),
        borderSide: const BorderSide(color: Color(0xFF2563EB), width: 2),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        title: const Text(
          'تکمیل شناسنامه استخدامی',
          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
        ),
        centerTitle: true,
        backgroundColor: Colors.white,
        elevation: 0,
        foregroundColor: const Color(0xFF0F172A),
      ),
      body: Theme(
        data: Theme.of(context).copyWith(
          colorScheme: const ColorScheme.light(primary: Color(0xFF2563EB)),
        ),
        child: Stepper(
          type: StepperType.horizontal,
          elevation: 0,
          currentStep: _currentStep,
          onStepTapped: (step) {
            if (step < _currentStep) {
              setState(() => _currentStep = step);
            }
          },
          onStepContinue: () {
            if (_currentStep == 0) {
              if (_step1FormKey.currentState != null && _step1FormKey.currentState!.validate()) {
                setState(() => _currentStep = 1);
              }
            } else if (_currentStep == 1) {
              _submitForm();
            }
          },
          onStepCancel: () {
            if (_currentStep > 0) {
              setState(() => _currentStep = 0);
            }
          },
          controlsBuilder: (context, details) {
            return Padding(
              padding: const EdgeInsets.only(top: 24.0),
              child: Row(
                children: [
                  Expanded(
                    child: ElevatedButton(
                      onPressed: _isLoading ? null : details.onStepContinue,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF2563EB),
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(16),
                        ),
                        elevation: 2,
                      ),
                      child: _isLoading
                          ? const SizedBox(
                              height: 20,
                              width: 20,
                              child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                            )
                          : Text(
                              _currentStep == 1 ? 'ثبت نهایی اطلاعات' : 'مرحله بعدی',
                              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                            ),
                    ),
                  ),
                  if (_currentStep > 0) ...[
                    const SizedBox(width: 12),
                    OutlinedButton(
                      onPressed: details.onStepCancel,
                      style: OutlinedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 20),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(16),
                        ),
                      ),
                      child: const Text('قبلی'),
                    ),
                  ],
                ],
              ),
            );
          },
          steps: [
            // گام اول: اطلاعات فردی
            Step(
              title: const Text('اطلاعات فردی'),
              isActive: _currentStep >= 0,
              state: _currentStep > 0 ? StepState.complete : StepState.indexed,
              content: Form(
                key: _step1FormKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const SizedBox(height: 8),
                    TextFormField(
                      controller: _nameController,
                      decoration: _customInputDecoration('نام و نام خانوادگی', Icons.person_outline),
                      validator: (v) => v == null || v.trim().isEmpty ? 'لطفاً نام را وارد کنید' : null,
                    ),
                    const SizedBox(height: 16),
                    TextFormField(
                      controller: _phoneController,
                      keyboardType: TextInputType.phone,
                      decoration: _customInputDecoration('شماره همراه', Icons.phone_android_outlined),
                      validator: (v) => v == null || v.trim().isEmpty ? 'لطفاً شماره را وارد کنید' : null,
                    ),
                    const SizedBox(height: 20),
                    const Text('تاریخ تولد (شمسی):', style: TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF334155))),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        Expanded(
                          child: TextFormField(
                            controller: _bYearController,
                            keyboardType: TextInputType.number,
                            decoration: _customInputDecoration('سال', Icons.calendar_today_outlined),
                            validator: (v) => v == null || v.trim().isEmpty ? 'سال' : null,
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: TextFormField(
                            controller: _bMonthController,
                            keyboardType: TextInputType.number,
                            decoration: _customInputDecoration('ماه', Icons.date_range_outlined),
                            validator: (v) => v == null || v.trim().isEmpty ? 'ماه' : null,
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: TextFormField(
                            controller: _bDayController,
                            keyboardType: TextInputType.number,
                            decoration: _customInputDecoration('روز', Icons.today_outlined),
                            validator: (v) => v == null || v.trim().isEmpty ? 'روز' : null,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 20),
                    Row(
                      children: [
                        const Text('وضعیت تأهل:', style: TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF334155))),
                        const SizedBox(width: 16),
                        ChoiceChip(
                          label: const Text('مجرد'),
                          selected: _isMarried == 0,
                          selectedColor: const Color(0xFF2563EB).withOpacity(0.15),
                          labelStyle: TextStyle(
                            color: _isMarried == 0 ? const Color(0xFF2563EB) : Colors.black87,
                            fontWeight: _isMarried == 0 ? FontWeight.bold : FontWeight.normal,
                          ),
                          onSelected: (val) => setState(() => _isMarried = 0),
                        ),
                        const SizedBox(width: 8),
                        ChoiceChip(
                          label: const Text('متأهل'),
                          selected: _isMarried == 1,
                          selectedColor: const Color(0xFF2563EB).withOpacity(0.15),
                          labelStyle: TextStyle(
                            color: _isMarried == 1 ? const Color(0xFF2563EB) : Colors.black87,
                            fontWeight: _isMarried == 1 ? FontWeight.bold : FontWeight.normal,
                          ),
                          onSelected: (val) => setState(() => _isMarried = 1),
                        ),
                      ],
                    ),
                    if (_isMarried == 1) ...[
                      const SizedBox(height: 16),
                      TextFormField(
                        controller: _childrenController,
                        keyboardType: TextInputType.number,
                        decoration: _customInputDecoration('تعداد فرزندان', Icons.child_friendly_outlined),
                      ),
                    ],
                  ],
                ),
              ),
            ),

            // گام دوم: سوابق تحصیلی
            Step(
              title: const Text('تحصیلات'),
              isActive: _currentStep >= 1,
              state: StepState.indexed,
              content: Form(
                key: _step2FormKey,
                child: Column(
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text(
                          'مدارک تحصیلی',
                          style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Color(0xFF0F172A)),
                        ),
                        TextButton.icon(
                          icon: const Icon(Icons.add_circle_outline, color: Color(0xFF2563EB)),
                          label: const Text('مدرک جدید'),
                          onPressed: _addDegreeField,
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    ListView.builder(
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      itemCount: _degrees.length,
                      itemBuilder: (context, index) {
                        final currentDegree = _degrees[index].degree;

                        return Card(
                          elevation: 0,
                          color: Colors.white,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(16),
                            side: const BorderSide(color: Color(0xFFE2E8F0)),
                          ),
                          margin: const EdgeInsets.symmetric(vertical: 6),
                          child: Padding(
                            padding: const EdgeInsets.all(12.0),
                            child: Column(
                              children: [
                                Row(
                                  children: [
                                    Expanded(
                                      child: DropdownButtonFormField<String>(
                                        value: _degrees[index].degree,
                                        decoration: _customInputDecoration('مقطع', Icons.school_outlined),
                                        items: _degreeOptions.map((String deg) {
                                          return DropdownMenuItem<String>(
                                            value: deg,
                                            child: Text(deg, style: const TextStyle(fontSize: 14)),
                                          );
                                        }).toList(),
                                        onChanged: (val) {
                                          if (val != null) {
                                            setState(() {
                                              _degrees[index] = DegreeItem(degree: val, major: '');
                                            });
                                          }
                                        },
                                      ),
                                    ),
                                    if (_degrees.length > 1)
                                      IconButton(
                                        icon: const Icon(Icons.delete_outline, color: Colors.red),
                                        onPressed: () => _removeDegreeField(index),
                                      ),
                                  ],
                                ),
                                const SizedBox(height: 12),
                                Builder(
                                  builder: (context) {
                                    if (currentDegree == 'حافظ قرآن') {
                                      return DropdownButtonFormField<String>(
                                        value: quranDegrees.contains(_degrees[index].major)
                                            ? _degrees[index].major
                                            : null,
                                        decoration: _customInputDecoration('درجه مدرک', Icons.workspace_premium_outlined),
                                        items: quranDegrees.map((deg) {
                                          return DropdownMenuItem(value: deg, child: Text(deg));
                                        }).toList(),
                                        onChanged: (val) {
                                          setState(() {
                                            _degrees[index] = DegreeItem(degree: currentDegree, major: val ?? '');
                                          });
                                        },
                                        validator: (v) => v == null || v.isEmpty ? 'درجه را انتخاب کنید' : null,
                                      );
                                    } else if (currentDegree == 'حوزوی') {
                                      return DropdownButtonFormField<String>(
                                        value: hawzahDegrees.contains(_degrees[index].major)
                                            ? _degrees[index].major
                                            : null,
                                        decoration: _customInputDecoration('سطح مدرک', Icons.auto_stories_outlined),
                                        items: hawzahDegrees.map((deg) {
                                          return DropdownMenuItem(value: deg, child: Text(deg));
                                        }).toList(),
                                        onChanged: (val) {
                                          setState(() {
                                            _degrees[index] = DegreeItem(degree: currentDegree, major: val ?? '');
                                          });
                                        },
                                        validator: (v) => v == null || v.isEmpty ? 'سطح را انتخاب کنید' : null,
                                      );
                                    } else {
                                      return TextFormField(
                                        key: ValueKey('text_$index'),
                                        initialValue: _degrees[index].major,
                                        decoration: _customInputDecoration('رشته تحصیلی', Icons.book_outlined),
                                        onChanged: (val) {
                                          _degrees[index] = DegreeItem(degree: _degrees[index].degree, major: val);
                                        },
                                        validator: (v) => v == null || v.trim().isEmpty ? 'رشته را وارد کنید' : null,
                                      );
                                    }
                                  },
                                ),
                              ],
                            ),
                          ),
                        );
                      },
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}