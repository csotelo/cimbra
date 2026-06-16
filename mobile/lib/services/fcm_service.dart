import 'dart:async';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/material.dart';
import 'package:vibration/vibration.dart';

/// Buzzer patterns by alert level.
/// Level 4 = Rojo: continuous (repeat short bursts)
/// Level 3 = Naranja: fast intermittent
/// Level 2 = Amarillo: slow intermittent
/// Level 1 / off: stop
const _patterns = {
  4: [500, 200, 500, 200, 500, 200], // continuous buzzer
  3: [300, 400, 300, 400],            // fast intermittent
  2: [200, 800, 200, 800],            // slow intermittent
};

class FcmService {
  static final FcmService _instance = FcmService._();
  factory FcmService() => _instance;
  FcmService._();

  final _alertController = StreamController<Map<String, dynamic>>.broadcast();
  Stream<Map<String, dynamic>> get alertStream => _alertController.stream;

  int _currentLevel = 0;
  Timer? _buzzerTimer;

  Future<void> init() async {
    final messaging = FirebaseMessaging.instance;

    // Request permission (Android 13+ / iOS)
    await messaging.requestPermission(alert: true, badge: true, sound: true);

    // Foreground messages
    FirebaseMessaging.onMessage.listen(_handleMessage);

    // Background tap (app was in background)
    FirebaseMessaging.onMessageOpenedApp.listen(_handleMessage);

    // App was terminated — check initial message
    final initial = await messaging.getInitialMessage();
    if (initial != null) _handleMessage(initial);
  }

  Future<String?> getToken() async {
    return FirebaseMessaging.instance.getToken();
  }

  void _handleMessage(RemoteMessage msg) {
    final data = msg.data;
    final level = int.tryParse(data['alert_level'] ?? '0') ?? 0;
    _alertController.add({
      'level': level,
      'level_label': data['alert_level_label'] ?? '',
      'distance_km': data['distance_km'] ?? '',
      'station': data['station'] ?? '',
      'buzzer_pattern': data['buzzer_pattern'] ?? 'off',
      'title': msg.notification?.title ?? '',
      'body': msg.notification?.body ?? '',
    });
    _triggerBuzzer(level);
  }

  void _triggerBuzzer(int level) async {
    final canVibrate = await Vibration.hasVibrator() ?? false;
    if (!canVibrate) return;

    if (level <= 1) {
      stopBuzzer();
      return;
    }

    if (level == _currentLevel) return; // same level — don't restart
    _currentLevel = level;

    _buzzerTimer?.cancel();
    _repeatBuzz(level);
  }

  void _repeatBuzz(int level) {
    final pattern = _patterns[level];
    if (pattern == null) return;
    Vibration.vibrate(pattern: pattern, repeat: 0);
    // Re-trigger every 8s to keep buzzing (vibration repeat param unreliable cross-platform)
    _buzzerTimer = Timer.periodic(const Duration(seconds: 8), (_) {
      if (_currentLevel == level) {
        Vibration.vibrate(pattern: pattern, repeat: 0);
      }
    });
  }

  void stopBuzzer() {
    _buzzerTimer?.cancel();
    _buzzerTimer = null;
    _currentLevel = 0;
    Vibration.cancel();
  }

  void dispose() {
    _buzzerTimer?.cancel();
    _alertController.close();
  }
}

/// Alert overlay widget displayed on top of the map when danger is detected.
class AlertBanner extends StatelessWidget {
  final Map<String, dynamic> alert;
  final VoidCallback onDismiss;

  const AlertBanner({super.key, required this.alert, required this.onDismiss});

  Color get _bgColor {
    final level = alert['level'] as int? ?? 0;
    if (level >= 4) return const Color(0xFFEF4444);
    if (level >= 3) return const Color(0xFFF97316);
    if (level >= 2) return const Color(0xFFEAB308);
    return Colors.grey;
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.all(12),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: _bgColor,
        borderRadius: BorderRadius.circular(12),
        boxShadow: const [BoxShadow(color: Colors.black38, blurRadius: 10)],
      ),
      child: Row(
        children: [
          const Icon(Icons.warning_amber_rounded, color: Colors.white, size: 28),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  alert['title'] ?? '⚡ Alerta de tormenta',
                  style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 14),
                ),
                if ((alert['body'] ?? '').isNotEmpty)
                  Text(
                    alert['body'],
                    style: const TextStyle(color: Colors.white70, fontSize: 12),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
              ],
            ),
          ),
          IconButton(
            icon: const Icon(Icons.close, color: Colors.white, size: 20),
            onPressed: onDismiss,
            padding: EdgeInsets.zero,
            constraints: const BoxConstraints(),
          ),
        ],
      ),
    );
  }
}
