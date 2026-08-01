import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'screens/register_screen.dart';
import 'screens/onboarding_screen.dart';
import 'screens/dashboard_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized(); 
  
  final prefs = await SharedPreferences.getInstance();
  final bool isRegistered = prefs.getBool('isRegistered') ?? false;
  final int userId = prefs.getInt('userId') ?? 0;

  // پاس دادن دقیق پارامترهای اجباری به MyApp
  runApp(MyApp(isRegistered: isRegistered, userId: userId));
}

class MyApp extends StatelessWidget {
  final bool isRegistered;
  final int userId;

  const MyApp({
    super.key, 
    required this.isRegistered, 
    required this.userId,
  });

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'آزمون‌یاب استخدامی',
      debugShowCheckedModeBanner: false,
      
      locale: const Locale('fa', 'IR'),
      supportedLocales: const [
        Locale('fa', 'IR'),
      ],
      localizationsDelegates: const [
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],

      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: Colors.blue,
          primary: Colors.blue,
        ),
        fontFamily: 'Tahoma',
      ),

      home: isRegistered 
          ? DashboardScreen(userId: userId) 
          : const OnboardingScreen(),
    );
  }
}