import 'dart:async';
import 'dart:convert';
import 'package:mqtt_client/mqtt_client.dart';
import 'package:mqtt_client/mqtt_server_client.dart';
import '../config/app_config.dart';

class MqttService {
  late MqttServerClient _client;
  bool _connected = false;

  bool get isConnected => _connected;

  Future<bool> connect(String clientId) async {
    _client = MqttServerClient(AppConfig.mqttHost, clientId)
      ..port = AppConfig.mqttPort
      ..keepAlivePeriod = 60
      ..logging(on: false)
      ..onDisconnected = _onDisconnected;

    final connMsg = MqttConnectMessage()
        .withClientIdentifier(clientId)
        .startClean()
        .withWillQos(MqttQos.atLeastOnce);
    _client.connectionMessage = connMsg;

    try {
      await _client.connect();
      _connected = _client.connectionStatus?.state == MqttConnectionState.connected;
      return _connected;
    } catch (_) {
      _connected = false;
      return false;
    }
  }

  void publish(String tenantId, String employeeId, double lat, double lon, double accuracy) {
    if (!_connected) return;
    final topic = AppConfig.positionTopic(tenantId, employeeId);
    final payload = jsonEncode({
      'lat': lat,
      'lon': lon,
      'accuracy': accuracy,
      'ts': DateTime.now().toUtc().toIso8601String(),
    });
    final builder = MqttClientPayloadBuilder()..addString(payload);
    _client.publishMessage(topic, MqttQos.atLeastOnce, builder.payload!);
  }

  void _onDisconnected() {
    _connected = false;
  }

  void disconnect() {
    _client.disconnect();
    _connected = false;
  }
}
