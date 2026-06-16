import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'screens/login_screen.dart';
import 'screens/map_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  // FCM init will be added in Sprint 4 (firebase_messaging setup)
  runApp(const XimbraFieldApp());
}

class XimbraFieldApp extends StatelessWidget {
  const XimbraFieldApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Ximbra Campo',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF4F46E5)),
        useMaterial3: true,
      ),
      home: const _SplashRouter(),
    );
  }
}

class _SplashRouter extends StatefulWidget {
  const _SplashRouter();

  @override
  State<_SplashRouter> createState() => _SplashRouterState();
}

class _SplashRouterState extends State<_SplashRouter> {
  @override
  void initState() {
    super.initState();
    _route();
  }

  Future<void> _route() async {
    const storage = FlutterSecureStorage();
    final tenantId = await storage.read(key: 'tenant_id');
    final employeeId = await storage.read(key: 'employee_id');
    final employeeName = await storage.read(key: 'employee_name');

    if (!mounted) return;
    if (tenantId != null && employeeId != null && employeeName != null) {
      Navigator.of(context).pushReplacement(MaterialPageRoute(
        builder: (_) => MapScreen(
          tenantId: tenantId,
          employeeId: employeeId,
          employeeName: employeeName,
        ),
      ));
    } else {
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (_) => const LoginScreen()),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      backgroundColor: Color(0xFF4F46E5),
      body: Center(child: CircularProgressIndicator(color: Colors.white)),
    );
  }
}
