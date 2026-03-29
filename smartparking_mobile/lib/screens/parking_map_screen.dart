import 'dart:convert';
import 'package:flutter/material.dart';
import '../services/api_service.dart';

class ParkingMapScreen extends StatefulWidget {
  const ParkingMapScreen({super.key});

  @override
  State<ParkingMapScreen> createState() => _ParkingMapScreenState();
}

class _ParkingMapScreenState extends State<ParkingMapScreen> {
  List<dynamic> _spaces = [];
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadParkingStatus();
  }

  Future<void> _loadParkingStatus() async {
    try {
      setState(() {
        _isLoading = true;
        _error = null;
      });
      final data = await ApiService.getParkingStatus();
      setState(() {
        _spaces = data['spaces'] ?? [];
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0D1B2A),
      appBar: AppBar(
        backgroundColor: const Color(0xFF0D1B2A),
        foregroundColor: Colors.white,
        title: const Text(
          'Park Haritası',
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadParkingStatus,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(
              child: CircularProgressIndicator(color: Colors.blue))
          : _error != null
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.error_outline,
                          color: Colors.red, size: 48),
                      const SizedBox(height: 12),
                      Text(
                        'Bağlantı hatası',
                        style: TextStyle(color: Colors.grey.shade400),
                      ),
                      const SizedBox(height: 12),
                      ElevatedButton(
                        onPressed: _loadParkingStatus,
                        child: const Text('Tekrar Dene'),
                      ),
                    ],
                  ),
                )
              : Column(
                  children: [
                    _buildLegend(),
                    Expanded(
                      child: _buildMap(),
                    ),
                  ],
                ),
    );
  }

  Widget _buildLegend() {
    final total = _spaces.length;
    final occupied =
        _spaces.where((s) => s['isOccupied'] == true).length;
    final available = total - occupied;

    return Container(
      margin: const EdgeInsets.all(16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF1A2D3F),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _buildLegendItem(
              Colors.green.shade400, 'Boş', available.toString()),
          _buildLegendItem(
              Colors.red.shade400, 'Dolu', occupied.toString()),
          _buildLegendItem(Colors.blue.shade300, 'Toplam', total.toString()),
        ],
      ),
    );
  }

  Widget _buildLegendItem(Color color, String label, String count) {
    return Row(
      children: [
        Container(
          width: 14,
          height: 14,
          decoration: BoxDecoration(
            color: color.withOpacity(0.4),
            border: Border.all(color: color, width: 2),
            borderRadius: BorderRadius.circular(3),
          ),
        ),
        const SizedBox(width: 8),
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              count,
              style: TextStyle(
                color: color,
                fontWeight: FontWeight.bold,
                fontSize: 16,
              ),
            ),
            Text(
              label,
              style: TextStyle(color: Colors.grey.shade400, fontSize: 12),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildMap() {
    // Sectionlara göre grupla
    final Map<String, List<dynamic>> sections = {};
    for (final space in _spaces) {
      final section = space['section'] ?? space['spaceNumber']?.substring(0, 1) ?? '?';
      sections.putIfAbsent(section, () => []);
      sections[section]!.add(space);
    }

    return RefreshIndicator(
      onRefresh: _loadParkingStatus,
      child: SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.symmetric(horizontal: 16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Giriş göstergesi
            Center(
              child: Container(
                margin: const EdgeInsets.only(bottom: 20),
                padding:
                    const EdgeInsets.symmetric(horizontal: 24, vertical: 8),
                decoration: BoxDecoration(
                  color: Colors.orange.shade700,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.arrow_downward, color: Colors.white, size: 16),
                    SizedBox(width: 8),
                    Text(
                      'GİRİŞ',
                      style: TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                        letterSpacing: 2,
                      ),
                    ),
                  ],
                ),
              ),
            ),

            // Her section için satır
            ...sections.entries.map((entry) {
              final sectionName = entry.key;
              final sectionSpaces = entry.value;
              // spaceNumber'a göre sırala
              sectionSpaces
                  .sort((a, b) => (a['spaceNumber'] ?? '').compareTo(b['spaceNumber'] ?? ''));

              return Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 8),
                    child: Text(
                      'Bölüm $sectionName',
                      style: TextStyle(
                        color: Colors.grey.shade400,
                        fontSize: 13,
                        letterSpacing: 1.5,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ),
                  Row(
                    children: sectionSpaces
                        .map((space) => _buildParkingSpaceCard(space))
                        .toList(),
                  ),
                  const SizedBox(height: 16),
                ],
              );
            }).toList(),

            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }

  Widget _buildParkingSpaceCard(Map<String, dynamic> space) {
    final isOccupied = space['isOccupied'] == true;
    final spaceNumber = space['spaceNumber'] ?? '?';
    final color = isOccupied ? Colors.red.shade400 : Colors.green.shade400;

    return Expanded(
      child: GestureDetector(
        onTap: () => _showSpaceDetail(space),
        child: Container(
          margin: const EdgeInsets.symmetric(horizontal: 4),
          height: 90,
          decoration: BoxDecoration(
            color: color.withOpacity(0.15),
            border: Border.all(color: color, width: 2),
            borderRadius: BorderRadius.circular(10),
          ),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                isOccupied ? Icons.directions_car : Icons.local_parking,
                color: color,
                size: 28,
              ),
              const SizedBox(height: 6),
              Text(
                spaceNumber,
                style: TextStyle(
                  color: color,
                  fontWeight: FontWeight.bold,
                  fontSize: 14,
                ),
              ),
              Text(
                isOccupied ? 'Dolu' : 'Boş',
                style: TextStyle(
                  color: color.withOpacity(0.8),
                  fontSize: 11,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _showSpaceDetail(Map<String, dynamic> space) {
    final isOccupied = space['isOccupied'] == true;
    final spaceNumber = space['spaceNumber'] ?? '?';
    final section = space['section'] ?? spaceNumber.substring(0, 1);

    // Yön tarifi oluştur
    String directions = _getDirections(spaceNumber);

    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF1A2D3F),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) => Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: (isOccupied ? Colors.red : Colors.green)
                        .withOpacity(0.2),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Icon(
                    isOccupied
                        ? Icons.directions_car
                        : Icons.local_parking,
                    color:
                        isOccupied ? Colors.red.shade400 : Colors.green.shade400,
                    size: 32,
                  ),
                ),
                const SizedBox(width: 16),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Park Yeri $spaceNumber',
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    Text(
                      isOccupied ? '🔴 Dolu' : '🟢 Boş',
                      style: TextStyle(
                        color: Colors.grey.shade400,
                        fontSize: 14,
                      ),
                    ),
                  ],
                ),
              ],
            ),
            const SizedBox(height: 24),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: const Color(0xFF0D1B2A),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Row(
                    children: [
                      Icon(Icons.navigation, color: Colors.orange, size: 18),
                      SizedBox(width: 8),
                      Text(
                        'Yön Tarifi',
                        style: TextStyle(
                          color: Colors.orange,
                          fontWeight: FontWeight.bold,
                          fontSize: 14,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 10),
                  Text(
                    directions,
                    style: TextStyle(
                      color: Colors.grey.shade300,
                      fontSize: 14,
                      height: 1.6,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Icon(Icons.info_outline,
                    color: Colors.grey.shade500, size: 14),
                const SizedBox(width: 6),
                Text(
                  'Bölüm: $section',
                  style:
                      TextStyle(color: Colors.grey.shade500, fontSize: 12),
                ),
              ],
            ),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }

  String _getDirections(String spaceNumber) {
    // Spacelar A1-A4 (Kamera 1) ve C1-C3 (Kamera 2) olarak bölünmüş
    // Yön tariflerini space numarasına göre üret
    final section = spaceNumber.isNotEmpty ? spaceNumber[0] : '?';
    final num = spaceNumber.length > 1
        ? int.tryParse(spaceNumber.substring(1)) ?? 1
        : 1;

    if (section == 'A') {
      switch (num) {
        case 1:
          return '📍 Girişten içeri girin\n➡️ Sağa dönün\n🅿️ Karşınızdaki ilk park yeri';
        case 2:
          return '📍 Girişten içeri girin\n➡️ Sağa dönün\n🅿️ İkinci park yeri';
        case 3:
          return '📍 Girişten içeri girin\n➡️ Sağa dönün\n🅿️ Üçüncü park yeri';
        case 4:
          return '📍 Girişten içeri girin\n➡️ Sağa dönün\n🅿️ Dördüncü park yeri (son)';
        default:
          return '📍 Girişten içeri girin, $spaceNumber bölümünü takip edin';
      }
    } else if (section == 'C') {
      switch (num) {
        case 1:
          return '📍 Girişten içeri girin\n⬆️ Düz ilerleyin\n⬅️ Sola dönün\n🅿️ İlk park yeri';
        case 2:
          return '📍 Girişten içeri girin\n⬆️ Düz ilerleyin\n⬅️ Sola dönün\n🅿️ İkinci park yeri';
        case 3:
          return '📍 Girişten içeri girin\n⬆️ Düz ilerleyin\n⬅️ Sola dönün\n🅿️ Üçüncü park yeri (son)';
        default:
          return '📍 Girişten içeri girin, $spaceNumber bölümünü takip edin';
      }
    }

    return '📍 Girişten içeri girin\n🅿️ $spaceNumber numaralı park yerini bulun';
  }
}