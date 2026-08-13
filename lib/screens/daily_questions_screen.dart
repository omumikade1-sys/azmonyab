import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:http/http.dart' as http;

class DailyQuestionsScreen extends StatefulWidget {
  final int userId;

  const DailyQuestionsScreen({super.key, required this.userId});

  @override
  State<DailyQuestionsScreen> createState() => _DailyQuestionsScreenState();
}

class _DailyQuestionsScreenState extends State<DailyQuestionsScreen> {
  List<dynamic> _questions = [];
  bool _isLoading = true;
  String? _errorMessage;

  int _currentIndex = 0;
  final Map<int, String> _selectedAnswers = {};
  bool _showResults = false;

  @override
  void initState() {
    super.initState();
    _fetchDailyQuestions();
  }

  void _playClickSound() {
    SystemSound.play(SystemSoundType.click);
    HapticFeedback.selectionClick();
  }

  Future<void> _fetchDailyQuestions() async {
    try {
      // محاسبه شماره روز بین ۱ و ۲ (بر اساس روز جاری ماه)
      int currentDay = (DateTime.now().day % 2) + 1; 

      final url = Uri.parse('http://136.243.30.219:8000/questions/daily?day=$currentDay');
      final response = await http.get(url);

      if (response.statusCode == 200) {
        final data = json.decode(utf8.decode(response.bodyBytes));
        if (data['status'] == 'success' && data['questions'].isNotEmpty) {
          setState(() {
            _questions = data['questions'];
            _isLoading = false;
          });
        } else {
          setState(() {
            _errorMessage = 'سوالاتی برای امروز یافت نشد.';
            _isLoading = false;
          });
        }
      } else {
        setState(() {
          _errorMessage = 'خطا در برقراری ارتباط با سرور.';
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        _errorMessage = 'خطای شبکه‌ای: لطفاً اتصال اینترنت خود را بررسی کنید.';
        _isLoading = false;
      });
    }
  }

  int _calculateCorrectCount() {
    int correct = 0;
    for (int i = 0; i < _questions.length; i++) {
      final selected = _selectedAnswers[i];
      final correctOpt = _questions[i]['correct_option'].toString().trim().toLowerCase();
      if (selected == correctOpt) {
        correct++;
      }
    }
    return correct;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF1F5F9),
      appBar: AppBar(
        title: const Text(
          'نمونه سوالات روزانه استخدامی',
          style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold, color: Color(0xFF0F172A)),
        ),
        centerTitle: true,
        backgroundColor: Colors.white,
        elevation: 0.5,
        iconTheme: const IconThemeData(color: Color(0xFF0F172A)),
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return const Center(
        child: CircularProgressIndicator(color: Color(0xFF2563EB)),
      );
    }

    if (_errorMessage != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.wifi_off_rounded, color: Colors.redAccent, size: 56),
              const SizedBox(height: 12),
              Text(_errorMessage!, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600)),
              const SizedBox(height: 16),
              ElevatedButton.icon(
                onPressed: () {
                  _playClickSound();
                  setState(() {
                    _isLoading = true;
                    _errorMessage = null;
                  });
                  _fetchDailyQuestions();
                },
                icon: const Icon(Icons.refresh_rounded),
                label: const Text('تلاش مجدد'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF2563EB),
                  padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                ),
              )
            ],
          ),
        ),
      );
    }

    if (_questions.isEmpty) {
      return const Center(child: Text('هیچ سوالی برای امروز ثبت نشده است.'));
    }

    if (_showResults) {
      return _buildResultAndReviewView();
    }

    final currentQuestion = _questions[_currentIndex];
    final Map<String, dynamic> options = currentQuestion['options'] != null
        ? Map<String, dynamic>.from(currentQuestion['options'])
        : {'a': '', 'b': '', 'c': '', 'd': ''};

    final hasAnswered = _selectedAnswers.containsKey(_currentIndex);
    final String explanation = currentQuestion['explanation'] ?? '';

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 12.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // بخش فشرده نوار پیشرفت
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(12),
              boxShadow: [
                BoxShadow(color: Colors.black.withOpacity(0.02), blurRadius: 6, offset: const Offset(0, 2))
              ],
            ),
            child: Row(
              children: [
                Text(
                  'سوال ${_currentIndex + 1}/${_questions.length}',
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Color(0xFF2563EB)),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(6),
                    child: LinearProgressIndicator(
                      value: (_currentIndex + 1) / _questions.length,
                      backgroundColor: Colors.grey.shade200,
                      color: const Color(0xFF2563EB),
                      minHeight: 6,
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: const Color(0xFF2563EB).withOpacity(0.1),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Text(
                    'روز ۱',
                    style: TextStyle(color: Color(0xFF2563EB), fontWeight: FontWeight.bold, fontSize: 11),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 10),

          // صورت سوال
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(14),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.03),
                  blurRadius: 8,
                  offset: const Offset(0, 3),
                )
              ],
            ),
            child: Text(
              currentQuestion['question'] ?? '',
              style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: Color(0xFF0F172A), height: 1.45),
            ),
          ),
          const SizedBox(height: 10),

          // گزینه‌ها + پاسخ تشریحی
          Expanded(
            child: ListView(
              padding: EdgeInsets.zero,
              physics: const BouncingScrollPhysics(),
              children: [
                _buildOptionTile('a', options['a'] ?? '', currentQuestion),
                _buildOptionTile('b', options['b'] ?? '', currentQuestion),
                _buildOptionTile('c', options['c'] ?? '', currentQuestion),
                _buildOptionTile('d', options['d'] ?? '', currentQuestion),

                // نمایش پاسخ تشریحی بلافاصله پس از پاسخ کاربر (در صورت وجود متن)
                if (hasAnswered && explanation.trim().isNotEmpty) ...[
                  const SizedBox(height: 12),
                  Container(
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      color: Colors.blue.shade50,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: Colors.blue.shade200, width: 1.2),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Row(
                          children: [
                            Icon(Icons.lightbulb_rounded, color: Color(0xFF2563EB), size: 20),
                            SizedBox(width: 6),
                            Text(
                              'پاسخ تشریحی:',
                              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13.5, color: Color(0xFF1E40AF)),
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        Text(
                          explanation,
                          style: const TextStyle(fontSize: 13, color: Color(0xFF334155), height: 1.5),
                        ),
                      ],
                    ),
                  ),
                ],
              ],
            ),
          ),
          const SizedBox(height: 8),

          // دکمه‌های قبلی / بعدی
          Row(
            children: [
              if (_currentIndex > 0)
                Expanded(
                  child: OutlinedButton(
                    onPressed: () {
                      _playClickSound();
                      setState(() {
                        _currentIndex--;
                      });
                    },
                    style: OutlinedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 12),
                      side: const BorderSide(color: Color(0xFFCBD5E1)),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                    child: const Text('سوال قبلی', style: TextStyle(color: Color(0xFF475569), fontWeight: FontWeight.bold, fontSize: 13)),
                  ),
                ),
              if (_currentIndex > 0) const SizedBox(width: 10),
              Expanded(
                child: ElevatedButton(
                  onPressed: hasAnswered
                      ? () {
                          _playClickSound();
                          if (_currentIndex < _questions.length - 1) {
                            setState(() {
                              _currentIndex++;
                            });
                          } else {
                            HapticFeedback.heavyImpact();
                            setState(() {
                              _showResults = true;
                            });
                          }
                        }
                      : null, // تا زمان عدم انتخاب گزینه، دکمه بعدی غیرفعال است
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF2563EB),
                    disabledBackgroundColor: Colors.grey.shade300,
                    padding: const EdgeInsets.symmetric(vertical: 12),
                    elevation: 1,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                  child: Text(
                    _currentIndex == _questions.length - 1 ? 'مشاهده کارنامه و کلید' : 'سوال بعدی',
                    style: TextStyle(
                      color: hasAnswered ? Colors.white : Colors.grey.shade600,
                      fontWeight: FontWeight.bold,
                      fontSize: 14,
                    ),
                  ),
                ),
              ),
            ],
          )
        ],
      ),
    );
  }

  Widget _buildOptionTile(String key, String text, dynamic currentQuestion) {
    final userSelected = _selectedAnswers[_currentIndex];
    final hasAnswered = userSelected != null;
    final correctOpt = currentQuestion['correct_option'].toString().trim().toLowerCase();

    final isCorrectOption = key == correctOpt;
    final isSelectedByUser = key == userSelected;

    Color bgColor = Colors.white;
    Color borderColor = Colors.grey.shade200;
    Color textColor = const Color(0xFF334155);
    Color circleColor = const Color(0xFFF1F5F9);
    Color circleTextColor = const Color(0xFF64748B);

    if (hasAnswered) {
      if (isCorrectOption) {
        bgColor = Colors.green.shade50;
        borderColor = Colors.green;
        textColor = Colors.green.shade900;
        circleColor = Colors.green;
        circleTextColor = Colors.white;
      } else if (isSelectedByUser && !isCorrectOption) {
        bgColor = Colors.red.shade50;
        borderColor = Colors.red;
        textColor = Colors.red.shade900;
        circleColor = Colors.red;
        circleTextColor = Colors.white;
      }
    }

    final Map<String, String> keyToPersian = {
      'a': 'الف',
      'b': 'ب',
      'c': 'ج',
      'd': 'د',
    };

    return AnimatedContainer(
      duration: const Duration(milliseconds: 200),
      margin: const EdgeInsets.only(bottom: 8),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: borderColor,
          width: (hasAnswered && (isCorrectOption || isSelectedByUser)) ? 1.8 : 1,
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.02),
            blurRadius: 5,
            offset: const Offset(0, 2),
          )
        ],
      ),
      child: Material(
        color: Colors.transparent,
        child: ListTile(
          onTap: hasAnswered
              ? null
              : () {
                  _playClickSound();
                  setState(() {
                    _selectedAnswers[_currentIndex] = key;
                  });
                },
          dense: true,
          contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 2),
          leading: Container(
            width: 30,
            height: 30,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: circleColor,
              shape: BoxShape.circle,
            ),
            child: Text(
              keyToPersian[key] ?? key.toUpperCase(),
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.bold,
                color: circleTextColor,
              ),
            ),
          ),
          title: Text(
            text,
            style: TextStyle(
              fontSize: 13.5,
              fontWeight: (hasAnswered && (isCorrectOption || isSelectedByUser)) ? FontWeight.bold : FontWeight.w500,
              color: textColor,
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildResultAndReviewView() {
    final correctCount = _calculateCorrectCount();
    final total = _questions.length;
    final percentage = total > 0 ? ((correctCount / total) * 100).round() : 0;

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        children: [
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [Color(0xFF1E3A8A), Color(0xFF2563EB)],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: BorderRadius.circular(20),
              boxShadow: [
                BoxShadow(
                  color: const Color(0xFF2563EB).withOpacity(0.25),
                  blurRadius: 12,
                  offset: const Offset(0, 5),
                )
              ],
            ),
            child: Column(
              children: [
                const Icon(Icons.emoji_events_rounded, color: Color(0xFFFBBF24), size: 52),
                const SizedBox(height: 8),
                const Text(
                  'کارنامه آزمون امروز',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white),
                ),
                const SizedBox(height: 14),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceAround,
                  children: [
                    _buildStatBadge('پاسخ صحیح', '$correctCount', Colors.greenAccent),
                    _buildStatBadge('درصد عملکرد', '%$percentage', Colors.amberAccent),
                    _buildStatBadge('کل سوالات', '$total', Colors.white),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),

          const Align(
            alignment: Alignment.centerRight,
            child: Text(
              'مرور پاسخ‌ها و کلید صحیح سوالات',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Color(0xFF0F172A)),
            ),
          ),
          const SizedBox(height: 12),

          ListView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: _questions.length,
            itemBuilder: (context, index) {
              final q = _questions[index];
              final userSelected = _selectedAnswers[index];
              final correctOpt = q['correct_option'].toString().trim().toLowerCase();
              final isUserCorrect = userSelected == correctOpt;
              final String exp = q['explanation'] ?? '';

              final Map<String, dynamic> options = q['options'] != null
                  ? Map<String, dynamic>.from(q['options'])
                  : {'a': '', 'b': '', 'c': '', 'd': ''};

              return Container(
                margin: const EdgeInsets.only(bottom: 14),
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(
                    color: isUserCorrect ? Colors.green.shade300 : Colors.red.shade300,
                    width: 1.2,
                  ),
                  boxShadow: [
                    BoxShadow(color: Colors.black.withOpacity(0.02), blurRadius: 6, offset: const Offset(0, 3))
                  ],
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(
                          isUserCorrect ? Icons.check_circle_rounded : Icons.cancel_rounded,
                          color: isUserCorrect ? Colors.green : Colors.red,
                          size: 20,
                        ),
                        const SizedBox(width: 8),
                        Text(
                          'سوال ${index + 1}',
                          style: TextStyle(
                            fontWeight: FontWeight.bold,
                            fontSize: 13,
                            color: isUserCorrect ? Colors.green.shade800 : Colors.red.shade800,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Text(
                      q['question'] ?? '',
                      style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Color(0xFF0F172A), height: 1.4),
                    ),
                    const SizedBox(height: 12),
                    ...['a', 'b', 'c', 'd'].map((key) {
                      final optionText = options[key] ?? '';
                      final isCorrectOption = key == correctOpt;
                      final isSelectedByUser = key == userSelected;

                      Color bgColor = Colors.transparent;
                      Border border = Border.all(color: Colors.grey.shade200);
                      Widget? badge;

                      if (isCorrectOption) {
                        bgColor = Colors.green.shade50;
                        border = Border.all(color: Colors.green, width: 1.2);
                        badge = const Text('(پاسخ صحیح ✔)', style: TextStyle(color: Colors.green, fontWeight: FontWeight.bold, fontSize: 11));
                      } else if (isSelectedByUser && !isUserCorrect) {
                        bgColor = Colors.red.shade50;
                        border = Border.all(color: Colors.red, width: 1.2);
                        badge = const Text('(انتخاب شما ✖)', style: TextStyle(color: Colors.red, fontWeight: FontWeight.bold, fontSize: 11));
                      }

                      return Container(
                        margin: const EdgeInsets.only(bottom: 6),
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                        decoration: BoxDecoration(
                          color: bgColor,
                          borderRadius: BorderRadius.circular(10),
                          border: border,
                        ),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.center,
                          children: [
                            Expanded(
                              child: Text(
                                '${_getOptionLabel(key)}: $optionText',
                                style: TextStyle(
                                  fontSize: 12.5,
                                  fontWeight: (isCorrectOption || isSelectedByUser) ? FontWeight.bold : FontWeight.normal,
                                  color: isCorrectOption ? Colors.green.shade900 : (isSelectedByUser ? Colors.red.shade900 : const Color(0xFF475569)),
                                  height: 1.4,
                                ),
                              ),
                            ),
                            if (badge != null) ...[
                              const SizedBox(width: 6),
                              badge,
                            ],
                          ],
                        ),
                      );
                    }),
                    if (exp.trim().isNotEmpty) ...[
                      const SizedBox(height: 10),
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.all(10),
                        decoration: BoxDecoration(
                          color: Colors.blue.shade50,
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Text(
                          '💡 پاسخ تشریحی: $exp',
                          style: const TextStyle(fontSize: 12, color: Color(0xFF1E3A8A), height: 1.4),
                        ),
                      ),
                    ]
                  ],
                ),
              );
            },
          ),

          const SizedBox(height: 10),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: () {
                _playClickSound();
                if (Navigator.canPop(context)) {
                  Navigator.pop(context);
                } else {
                  setState(() {
                    _showResults = false;
                    _currentIndex = 0;
                    _selectedAnswers.clear();
                  });
                }
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF2563EB),
                padding: const EdgeInsets.symmetric(vertical: 14),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
              child: const Text('بازگشت به داشبورد', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 15)),
            ),
          )
        ],
      ),
    );
  }

  Widget _buildStatBadge(String title, String value, Color color) {
    return Column(
      children: [
        Text(value, style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: color)),
        const SizedBox(height: 2),
        Text(title, style: TextStyle(fontSize: 11, color: Colors.white.withOpacity(0.85))),
      ],
    );
  }

  String _getOptionLabel(String key) {
    switch (key) {
      case 'a':
        return 'الف';
      case 'b':
        return 'ب';
      case 'c':
        return 'ج';
      case 'd':
        return 'د';
      default:
        return key;
    }
  }
}