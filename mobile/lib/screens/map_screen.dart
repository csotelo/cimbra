import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:geolocator/geolocator.dart';
import 'package:latlong2/latlong.dart';
import '../services/location_service.dart';
import '../services/mqtt_service.dart';
import '../config/app_config.dart';
import 'refuge_screen.dart';

class MapScreen extends StatefulWidget {
  final String tenantId;
  final String employeeId;
  final String employeeName;

  const MapScreen({
    super.key,
    required this.tenantId,
    required this.employeeId,
    required this.employeeName,
  });

  @override
  State<MapScreen> createState() => _MapScreenState();
}

class _MapScreenState extends State<MapScreen> {
  final LocationService _locationService = LocationService();
  final MqttService _mqttService = MqttService();
  final MapController _mapController = MapController();

  LatLng? _currentPosition;
  bool _mqttConnected = false;
  String _statusMsg = 'Conectando...';
  Timer? _publishTimer;
  Position? _lastPosition;

  @override
  void initState() {
    super.initState();
    _init();
  }

  Future<void> _init() async {
    final hasPermission = await _locationService.requestPermission();
    if (!hasPermission) {
      setState(() => _statusMsg = 'Sin permiso de ubicación');
      return;
    }

    _locationService.start();
    _locationService.positionStream.listen((pos) {
      _lastPosition = pos;
      final ll = LatLng(pos.latitude, pos.longitude);
      setState(() => _currentPosition = ll);
      try {
        _mapController.move(ll, _mapController.camera.zoom);
      } catch (_) {}
    });

    final clientId = 'ximbra-${widget.employeeId.substring(0, 8)}';
    _mqttConnected = await _mqttService.connect(clientId);
    setState(() {
      _statusMsg = _mqttConnected ? 'En vivo — enviando GPS' : 'Sin conexión MQTT';
    });

    // Publish every N seconds regardless of movement
    _publishTimer = Timer.periodic(
      const Duration(seconds: AppConfig.publishIntervalSec),
      (_) => _publishPosition(),
    );
  }

  void _publishPosition() {
    if (_lastPosition == null || !_mqttConnected) return;
    _mqttService.publish(
      widget.tenantId,
      widget.employeeId,
      _lastPosition!.latitude,
      _lastPosition!.longitude,
      _lastPosition!.accuracy,
    );
  }

  @override
  void dispose() {
    _publishTimer?.cancel();
    _locationService.stop();
    _mqttService.disconnect();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.employeeName),
        backgroundColor: const Color(0xFF4F46E5),
        foregroundColor: Colors.white,
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 12),
            child: Row(
              children: [
                Icon(
                  _mqttConnected ? Icons.wifi : Icons.wifi_off,
                  color: _mqttConnected ? Colors.greenAccent : Colors.redAccent,
                  size: 20,
                ),
                const SizedBox(width: 4),
                Text(
                  _mqttConnected ? 'En vivo' : 'Offline',
                  style: const TextStyle(fontSize: 12),
                ),
              ],
            ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => Navigator.push(
          context,
          MaterialPageRoute(
            builder: (_) => RefugeScreen(
              currentLat: _currentPosition?.latitude,
              currentLon: _currentPosition?.longitude,
            ),
          ),
        ),
        backgroundColor: const Color(0xFF16A34A),
        foregroundColor: Colors.white,
        icon: const Icon(Icons.shield_outlined),
        label: const Text('Refugios'),
      ),
      body: Stack(
        children: [
          FlutterMap(
            mapController: _mapController,
            options: MapOptions(
              initialCenter: _currentPosition ?? const LatLng(-9.19, -75.01),
              initialZoom: _currentPosition != null ? 15.0 : 6.0,
            ),
            children: [
              TileLayer(
                urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                userAgentPackageName: 'com.ximbra.field',
              ),
              if (_currentPosition != null)
                MarkerLayer(
                  markers: [
                    Marker(
                      point: _currentPosition!,
                      width: 40,
                      height: 40,
                      child: const Icon(
                        Icons.my_location,
                        color: Color(0xFF4F46E5),
                        size: 32,
                      ),
                    ),
                  ],
                ),
            ],
          ),
          Positioned(
            bottom: 16,
            left: 16,
            right: 16,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(12),
                boxShadow: const [BoxShadow(color: Colors.black26, blurRadius: 8)],
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(_statusMsg, style: const TextStyle(fontSize: 12, color: Colors.grey)),
                  if (_currentPosition != null)
                    Text(
                      '${_currentPosition!.latitude.toStringAsFixed(5)}, '
                      '${_currentPosition!.longitude.toStringAsFixed(5)}',
                      style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
                    ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
