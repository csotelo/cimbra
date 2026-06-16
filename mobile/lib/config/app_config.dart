/// Runtime configuration loaded from secure storage.
/// Fields are written on first login and persist across app restarts.
class AppConfig {
  /// MQTT broker host (production: ximbra.creativa2b.pe)
  static const String mqttHost = String.fromEnvironment(
    'MQTT_HOST',
    defaultValue: 'ximbra.creativa2b.pe',
  );
  static const int mqttPort = int.fromEnvironment('MQTT_PORT', defaultValue: 1883);

  /// MQTT topic template — fill in tenantId and employeeId at runtime.
  static String positionTopic(String tenantId, String employeeId) =>
      'ximbra/$tenantId/tracking/employee/$employeeId/position';

  /// How often to publish GPS (seconds).
  static const int publishIntervalSec = 30;
}
