import 'dart:math';
import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import '../services/api_service.dart';

class RefugeScreen extends StatefulWidget {
  final double? currentLat;
  final double? currentLon;

  const RefugeScreen({super.key, this.currentLat, this.currentLon});

  @override
  State<RefugeScreen> createState() => _RefugeScreenState();
}

class _RefugeScreenState extends State<RefugeScreen> {
  List<Map<String, dynamic>> _features = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() { _loading = true; _error = null; });
    final data = await ApiService.getRefugePoints();
    if (!mounted) return;
    if (data.isEmpty && widget.currentLat == null) {
      setState(() { _loading = false; _error = 'Sin datos de refugios o sin token de API configurado.'; });
      return;
    }
    // Sort by distance if we have current position
    List<Map<String, dynamic>> sorted = data;
    if (widget.currentLat != null && widget.currentLon != null) {
      sorted = List.from(data)..sort((a, b) {
        final da = _dist(a);
        final db = _dist(b);
        return da.compareTo(db);
      });
    }
    setState(() { _features = sorted; _loading = false; });
  }

  double _dist(Map<String, dynamic> feature) {
    if (widget.currentLat == null) return double.infinity;
    final coords = (feature['geometry']?['coordinates'] as List?) ?? [];
    if (coords.length < 2) return double.infinity;
    final lon = (coords[0] as num).toDouble();
    final lat = (coords[1] as num).toDouble();
    return Geolocator.distanceBetween(widget.currentLat!, widget.currentLon!, lat, lon);
  }

  String _distLabel(Map<String, dynamic> feature) {
    final d = _dist(feature);
    if (d == double.infinity) return '— km';
    if (d < 1000) return '${d.toStringAsFixed(0)} m';
    return '${(d / 1000).toStringAsFixed(1)} km';
  }

  Color _distColor(Map<String, dynamic> feature) {
    final d = _dist(feature);
    if (d <= 500) return Colors.green;
    if (d <= 2000) return Colors.orange;
    return Colors.red;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Refugios Cercanos'),
        backgroundColor: const Color(0xFF16A34A),
        foregroundColor: Colors.white,
        actions: [
          IconButton(onPressed: _load, icon: const Icon(Icons.refresh)),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(Icons.warning_amber, color: Colors.orange, size: 48),
                        const SizedBox(height: 12),
                        Text(_error!, textAlign: TextAlign.center, style: const TextStyle(color: Colors.grey)),
                        const SizedBox(height: 16),
                        ElevatedButton(onPressed: _load, child: const Text('Reintentar')),
                      ],
                    ),
                  ),
                )
              : _features.isEmpty
                  ? const Center(child: Text('Sin puntos de refugio registrados.', style: TextStyle(color: Colors.grey)))
                  : ListView.separated(
                      padding: const EdgeInsets.all(16),
                      itemCount: _features.length,
                      separatorBuilder: (_, __) => const SizedBox(height: 8),
                      itemBuilder: (context, i) {
                        final props = _features[i]['properties'] as Map<String, dynamic>? ?? {};
                        return Card(
                          elevation: 2,
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                          child: Padding(
                            padding: const EdgeInsets.all(16),
                            child: Row(
                              children: [
                                Container(
                                  width: 48,
                                  height: 48,
                                  decoration: BoxDecoration(
                                    color: const Color(0xFF16A34A).withOpacity(0.1),
                                    borderRadius: BorderRadius.circular(12),
                                  ),
                                  child: const Icon(Icons.shield, color: Color(0xFF16A34A)),
                                ),
                                const SizedBox(width: 12),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        props['name'] ?? 'Refugio',
                                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                                      ),
                                      if ((props['description'] ?? '').isNotEmpty)
                                        Text(props['description'], style: const TextStyle(color: Colors.grey, fontSize: 12)),
                                      Row(
                                        children: [
                                          const Icon(Icons.people, size: 14, color: Colors.grey),
                                          const SizedBox(width: 4),
                                          Text('${props['capacity'] ?? '?'} pers.', style: const TextStyle(fontSize: 12, color: Colors.grey)),
                                        ],
                                      ),
                                    ],
                                  ),
                                ),
                                if (widget.currentLat != null)
                                  Column(
                                    children: [
                                      Text(
                                        _distLabel(_features[i]),
                                        style: TextStyle(
                                          fontWeight: FontWeight.bold,
                                          color: _distColor(_features[i]),
                                          fontSize: 13,
                                        ),
                                      ),
                                    ],
                                  ),
                              ],
                            ),
                          ),
                        );
                      },
                    ),
    );
  }
}
