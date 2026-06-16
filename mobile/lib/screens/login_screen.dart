import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'map_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _storage = const FlutterSecureStorage();
  final _tenantCtrl = TextEditingController();
  final _employeeIdCtrl = TextEditingController();
  final _nameCtrl = TextEditingController();
  bool _saving = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadSaved();
  }

  Future<void> _loadSaved() async {
    _tenantCtrl.text = await _storage.read(key: 'tenant_id') ?? '';
    _employeeIdCtrl.text = await _storage.read(key: 'employee_id') ?? '';
    _nameCtrl.text = await _storage.read(key: 'employee_name') ?? '';
  }

  Future<void> _enter() async {
    if (_tenantCtrl.text.isEmpty || _employeeIdCtrl.text.isEmpty || _nameCtrl.text.isEmpty) {
      setState(() => _error = 'Todos los campos son obligatorios.');
      return;
    }
    setState(() { _saving = true; _error = null; });
    await _storage.write(key: 'tenant_id', value: _tenantCtrl.text.trim());
    await _storage.write(key: 'employee_id', value: _employeeIdCtrl.text.trim());
    await _storage.write(key: 'employee_name', value: _nameCtrl.text.trim());
    if (!mounted) return;
    Navigator.of(context).pushReplacement(MaterialPageRoute(
      builder: (_) => MapScreen(
        tenantId: _tenantCtrl.text.trim(),
        employeeId: _employeeIdCtrl.text.trim(),
        employeeName: _nameCtrl.text.trim(),
      ),
    ));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF4F46E5),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: Column(
              children: [
                const Icon(Icons.shield_outlined, color: Colors.white, size: 64),
                const SizedBox(height: 12),
                const Text('Ximbra Campo', style: TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.bold)),
                const SizedBox(height: 4),
                const Text('Ingresa tus credenciales de empleado', style: TextStyle(color: Colors.white70, fontSize: 13)),
                const SizedBox(height: 32),
                Container(
                  padding: const EdgeInsets.all(24),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Column(
                    children: [
                      _field(_tenantCtrl, 'ID del Tenant (UUID)', Icons.business),
                      const SizedBox(height: 16),
                      _field(_employeeIdCtrl, 'ID de Empleado (UUID)', Icons.badge),
                      const SizedBox(height: 16),
                      _field(_nameCtrl, 'Tu nombre', Icons.person),
                      if (_error != null) ...[
                        const SizedBox(height: 12),
                        Text(_error!, style: const TextStyle(color: Colors.red, fontSize: 12)),
                      ],
                      const SizedBox(height: 20),
                      SizedBox(
                        width: double.infinity,
                        child: ElevatedButton(
                          onPressed: _saving ? null : _enter,
                          style: ElevatedButton.styleFrom(
                            backgroundColor: const Color(0xFF4F46E5),
                            foregroundColor: Colors.white,
                            padding: const EdgeInsets.symmetric(vertical: 14),
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                          ),
                          child: Text(_saving ? 'Conectando...' : 'Entrar'),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _field(TextEditingController ctrl, String label, IconData icon) {
    return TextField(
      controller: ctrl,
      decoration: InputDecoration(
        labelText: label,
        prefixIcon: Icon(icon, color: const Color(0xFF4F46E5)),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
        contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 14),
      ),
      style: const TextStyle(fontSize: 13),
    );
  }

  @override
  void dispose() {
    _tenantCtrl.dispose();
    _employeeIdCtrl.dispose();
    _nameCtrl.dispose();
    super.dispose();
  }
}
