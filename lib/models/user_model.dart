// مدل برای هر مدرک تحصیلی (مطابق با DegreeItem در FastAPI)
class DegreeItem {
  final String degree;
  final String major;

  DegreeItem({
    required this.degree,
    required this.major,
  });

  // تبدیل به JSON برای ارسال به API
  Map<String, dynamic> toJson() {
    return {
      'degree': degree,
      'major': major,
    };
  }

  // ساخت آبجکت از روی JSON دریافتی از API
  factory DegreeItem.fromJson(Map<String, dynamic> json) {
    return DegreeItem(
      degree: json['degree'] ?? '',
      major: json['major'] ?? '',
    );
  }
}

// مدل ثبت‌نام کاربر (مطابق با RegisterModel در FastAPI)
class RegisterModel {
  final int userId;
  final String name;
  final String phone;
  final int bYear;
  final int bMonth;
  final int bDay;
  final int isMarried;
  final int childrenCount;
  final List<DegreeItem> degrees;

  RegisterModel({
    required this.userId,
    required this.name,
    required this.phone,
    required this.bYear,
    required this.bMonth,
    required this.bDay,
    required this.isMarried,
    required this.childrenCount,
    required this.degrees,
  });

  Map<String, dynamic> toJson() {
    return {
      'user_id': userId,
      'name': name,
      'phone': phone,
      'b_year': bYear,
      'b_month': bMonth,
      'b_day': bDay,
      'is_married': isMarried,
      'children_count': childrenCount,
      'degrees': degrees.map((d) => d.toJson()).toList(),
    };
  }
}

// مدل دریافت اطلاعات پروفایل کاربر (مطابق با خروجی اندپوینت /profile/{user_id})
class UserProfile {
  final String name;
  final String phone;
  final int ageYears;
  final int ageMonths;
  final int ageDays;
  final bool isMarried;
  final int childrenCount;
  final List<DegreeItem> degrees;

  UserProfile({
    required this.name,
    required this.phone,
    required this.ageYears,
    required this.ageMonths,
    required this.ageDays,
    required this.isMarried,
    required this.childrenCount,
    required this.degrees,
  });

  factory UserProfile.fromJson(Map<String, dynamic> json) {
    var degreesList = json['degrees'] as List? ?? [];
    return UserProfile(
      name: json['name'] ?? '',
      phone: json['phone'] ?? '',
      ageYears: json['age_years'] ?? 0,
      ageMonths: json['age_months'] ?? 0,
      ageDays: json['age_days'] ?? 0,
      isMarried: json['is_married'] ?? false,
      childrenCount: json['children_count'] ?? 0,
      degrees: degreesList.map((d) => DegreeItem.fromJson(d)).toList(),
    );
  }
}