import 'dart:async';
import 'package:geolocator/geolocator.dart';

class LocationService {
  StreamController<Position>? _controller;
  StreamSubscription<Position>? _sub;

  Stream<Position> get positionStream => _controller!.stream;

  Future<bool> requestPermission() async {
    bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
    if (!serviceEnabled) return false;

    LocationPermission perm = await Geolocator.checkPermission();
    if (perm == LocationPermission.denied) {
      perm = await Geolocator.requestPermission();
      if (perm == LocationPermission.denied) return false;
    }
    if (perm == LocationPermission.deniedForever) return false;
    return true;
  }

  void start() {
    _controller = StreamController<Position>.broadcast();
    const settings = LocationSettings(
      accuracy: LocationAccuracy.high,
      distanceFilter: 10,  // meters
    );
    _sub = Geolocator.getPositionStream(locationSettings: settings)
        .listen((pos) => _controller!.add(pos));
  }

  void stop() {
    _sub?.cancel();
    _controller?.close();
    _sub = null;
    _controller = null;
  }
}
