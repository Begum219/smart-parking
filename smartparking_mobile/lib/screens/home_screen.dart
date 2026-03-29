import 'dart:async';
import 'package:flutter/material.dart';
import 'profile/profile_info_screen.dart';
import 'profile/change_password_screen.dart';
import '../services/storage_service.dart';
import '../services/api_service.dart';
import 'vehicles_screen.dart';
import 'parking_map_screen.dart';

class HomeScreen extends StatefulWidget {
  final String userName;
  final String userEmail;
  final String userId;

  const HomeScreen({
    super.key,
    required this.userName,
    required this.userEmail,
    required this.userId,
  });

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _currentIndex = 0;
  late String _userName;
  late String _userEmail;

  // Park durumu
  int _totalSpaces = 0;
  int _availableSpaces = 0;
  int _occupiedSpaces = 0;
  double _occupancyRate = 0;
  bool _statusLoading = true;

  // Aktif park session
  Map<String, dynamic>? _activeSession;
  bool _sessionLoading = true;
  Timer? _sessionTimer;
  int _elapsedSeconds = 0;

  // Cezalar
  List<dynamic> _penalties = [];
  bool _penaltiesLoading = true;

  @override
  void initState() {
    super.initState();
    _userName = widget.userName;
    _userEmail = widget.userEmail;
    _loadUserData();
    _loadParkingStatus();
    _loadActiveSession();
    _loadPenalties();
  }

  @override
  void dispose() {
    _sessionTimer?.cancel();
    super.dispose();
  }

  Future<void> _loadUserData() async {
    final user = await StorageService.getUser();
    if (user != null && mounted) {
      setState(() {
        _userName = user['name'] ?? widget.userName;
        _userEmail = user['email'] ?? widget.userEmail;
      });
    }
  }

  Future<void> _loadParkingStatus() async {
    try {
      final data = await ApiService.getParkingStatus();
      debugPrint('📦 Park data: $data');
      if (mounted) {
        setState(() {
          _totalSpaces = data['totalSpaces'] ?? 0;
          _availableSpaces = data['availableSpaces'] ?? 0;
          _occupiedSpaces = data['occupiedSpaces'] ?? 0;
          _occupancyRate = double.tryParse(data['occupancyRate'].toString()) ?? 0;
          _statusLoading = false;
        });
      }
    } catch (e) {
      debugPrint('❌ Park durumu hatası: $e');
      if (mounted) setState(() => _statusLoading = false);
    }
  }

  Future<void> _loadActiveSession() async {
    try {
      final vehicles = await ApiService.getUserVehicles(widget.userId);

      for (final vehicle in vehicles) {
        final vehicleId = vehicle['id']?.toString();
        if (vehicleId == null) continue;

        final session = await ApiService.getActiveSession(vehicleId);
        if (session != null) {
          final rawTime = session['entryTime'] as String;
          final entryTime = DateTime.parse(
            rawTime.endsWith('Z') ? rawTime : rawTime + 'Z',
          );
          final now = DateTime.now().toUtc();
          final elapsed = now.difference(entryTime).inSeconds;

          if (mounted) {
            setState(() {
              _activeSession = {
                ...session,
                'vehiclePlate': vehicle['plateNumber'] ?? '',
                'vehicleLabel': vehicle['label'] ?? '',
              };
              _elapsedSeconds = elapsed < 0 ? 0 : elapsed;
              _sessionLoading = false;
            });
            if (_sessionTimer == null || !_sessionTimer!.isActive) {
              _startTimer();
            }
          }
          return;
        }
      }

      if (mounted) setState(() => _sessionLoading = false);
    } catch (e) {
      debugPrint('❌ Session yükleme hatası: $e');
      if (mounted) setState(() => _sessionLoading = false);
    }
  }

  Future<void> _loadPenalties() async {
    try {
      final penalties = await ApiService.getMyPenalties();
      if (mounted) {
        setState(() {
          _penalties = penalties;
          _penaltiesLoading = false;
        });
      }
    } catch (e) {
      debugPrint('❌ Ceza yükleme hatası: $e');
      if (mounted) setState(() => _penaltiesLoading = false);
    }
  }

  void _startTimer() {
    _sessionTimer?.cancel();
    _sessionTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (mounted) setState(() => _elapsedSeconds++);
    });
  }

  String _formatDuration(int seconds) {
    final h = seconds ~/ 3600;
    final m = (seconds % 3600) ~/ 60;
    final s = seconds % 60;
    if (h > 0) return '${h}s ${m}dk ${s}sn';
    if (m > 0) return '${m}dk ${s}sn';
    return '${s}sn';
  }

  double _calculateFee(int seconds) {
    final minutes = seconds / 60;
    if (minutes <= 60) return 10.0;
    final additionalHours = ((minutes - 60) / 60).ceil();
    return 10.0 + (additionalHours * 8.0);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Akıllı Park Sistemi'),
        backgroundColor: Colors.blue.shade700,
        foregroundColor: Colors.white,
      ),
      body: _getBody(),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentIndex,
        onTap: (index) => setState(() => _currentIndex = index),
        type: BottomNavigationBarType.fixed,
        selectedItemColor: Colors.blue.shade700,
        unselectedItemColor: Colors.grey,
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.home), label: 'Ana Sayfa'),
          BottomNavigationBarItem(icon: Icon(Icons.directions_car), label: 'Araçlarım'),
          BottomNavigationBarItem(icon: Icon(Icons.history), label: 'Geçmiş'),
          BottomNavigationBarItem(icon: Icon(Icons.person), label: 'Profil'),
        ],
      ),
    );
  }

  Widget _getBody() {
    switch (_currentIndex) {
      case 0: return _buildHomeTab();
      case 1: return _buildVehiclesTab();
      case 2: return _buildHistoryTab();
      case 3: return _buildProfileTab();
      default: return _buildHomeTab();
    }
  }

  Widget _buildHomeTab() {
    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [Colors.blue.shade50, Colors.white],
        ),
      ),
      child: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Kullanıcı kartı
              Card(
                elevation: 4,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Row(
                    children: [
                      CircleAvatar(
                        radius: 28,
                        backgroundColor: Colors.blue.shade700,
                        child: Text(
                          _userName.isNotEmpty ? _userName[0].toUpperCase() : 'U',
                          style: const TextStyle(fontSize: 24, color: Colors.white, fontWeight: FontWeight.bold),
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text('Hoş Geldiniz,', style: TextStyle(fontSize: 13, color: Colors.grey)),
                            Text(_userName, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                          ],
                        ),
                      ),
                      Icon(Icons.check_circle, color: Colors.green.shade400, size: 28),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),

              // Aktif Park Kartı
              if (_sessionLoading)
                const Center(child: Padding(
                  padding: EdgeInsets.symmetric(vertical: 12),
                  child: CircularProgressIndicator(),
                ))
              else if (_activeSession != null)
                _buildActiveSessionCard()
              else
                _buildNoActiveSessionCard(),

              const SizedBox(height: 16),

              // Park Durumu başlığı
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text('Park Durumu', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
                  IconButton(
                    icon: const Icon(Icons.refresh),
                    onPressed: () {
                      setState(() {
                        _statusLoading = true;
                        _sessionLoading = true;
                      });
                      _sessionTimer?.cancel();
                      _loadParkingStatus();
                      _loadActiveSession();
                    },
                  ),
                ],
              ),
              const SizedBox(height: 12),

              _statusLoading
                  ? const Center(child: Padding(padding: EdgeInsets.all(32), child: CircularProgressIndicator()))
                  : GridView.count(
                      crossAxisCount: 2,
                      crossAxisSpacing: 12,
                      mainAxisSpacing: 12,
                      shrinkWrap: true,
                      childAspectRatio: 1.2,
                      physics: const NeverScrollableScrollPhysics(),
                      children: [
                        _buildStatCard(icon: Icons.local_parking, title: 'Toplam Park', value: _totalSpaces.toString(), color: Colors.blue),
                        _buildStatCard(icon: Icons.check_circle_outline, title: 'Boş Alan', value: _availableSpaces.toString(), color: Colors.green),
                        _buildStatCard(icon: Icons.block, title: 'Dolu Alan', value: _occupiedSpaces.toString(), color: Colors.red),
                        _buildStatCard(icon: Icons.pie_chart, title: 'Doluluk', value: '${_occupancyRate.toStringAsFixed(0)}%', color: Colors.orange),
                      ],
                    ),

              const SizedBox(height: 20),

              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: () => Navigator.push(
                    context,
                    MaterialPageRoute(builder: (context) => const ParkingMapScreen()),
                  ),
                  icon: const Icon(Icons.map),
                  label: const Text('Park Haritasını Görüntüle', style: TextStyle(fontSize: 15)),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.blue.shade700,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildActiveSessionCard() {
    final fee = _calculateFee(_elapsedSeconds);
    final plate = _activeSession!['vehiclePlate'] ?? _activeSession!['detectedPlateNumber'] ?? '';
    final spaceNumber = _activeSession!['spaceNumber'] ?? 'Tespit ediliyor...';

    return Card(
      elevation: 6,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Container(
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(16),
          gradient: LinearGradient(
            colors: [Colors.blue.shade700, Colors.blue.shade900],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
        ),
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.directions_car, color: Colors.white, size: 20),
                const SizedBox(width: 8),
                const Text('Aktif Parkım',
                    style: TextStyle(color: Colors.white70, fontSize: 13, fontWeight: FontWeight.w500)),
                const Spacer(),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: Colors.green.shade400,
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: const Text('AKTİF',
                      style: TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.bold)),
                ),
              ],
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('Plaka', style: TextStyle(color: Colors.white60, fontSize: 12)),
                      Text(plate.isNotEmpty ? plate : '-',
                          style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
                    ],
                  ),
                ),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('Park Yeri', style: TextStyle(color: Colors.white60, fontSize: 12)),
                      Text(spaceNumber,
                          style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Row(
                children: [
                  Expanded(
                    child: Column(
                      children: [
                        const Icon(Icons.timer, color: Colors.white70, size: 20),
                        const SizedBox(height: 4),
                        Text(
                          _formatDuration(_elapsedSeconds),
                          style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold),
                        ),
                        const Text('Süre', style: TextStyle(color: Colors.white60, fontSize: 11)),
                      ],
                    ),
                  ),
                  Container(width: 1, height: 50, color: Colors.white24),
                  Expanded(
                    child: Column(
                      children: [
                        const Icon(Icons.payments_outlined, color: Colors.white70, size: 20),
                        const SizedBox(height: 4),
                        Text(
                          '${fee.toStringAsFixed(2)} ₺',
                          style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold),
                        ),
                        const Text('Ücret', style: TextStyle(color: Colors.white60, fontSize: 11)),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildNoActiveSessionCard() {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: Colors.grey.shade100,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(Icons.local_parking, color: Colors.grey.shade400, size: 28),
            ),
            const SizedBox(width: 16),
            const Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Aktif Parkım', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                  SizedBox(height: 4),
                  Text('Şu anda park edilmiş aracınız yok',
                      style: TextStyle(color: Colors.grey, fontSize: 13)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildVehiclesTab() {
    return VehiclesScreen(userId: widget.userId);
  }

  // ✅ GÜNCELLENDİ: Cezalar gösteriliyor
  Widget _buildHistoryTab() {
    return Container(
      color: Colors.grey.shade50,
      child: SafeArea(
        child: _penaltiesLoading
            ? const Center(child: CircularProgressIndicator())
            : RefreshIndicator(
                onRefresh: _loadPenalties,
                child: _penalties.isEmpty
                    ? ListView(
                        children: [
                          SizedBox(
                            height: 400,
                            child: Center(
                              child: Column(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  Icon(Icons.check_circle_outline,
                                      size: 80, color: Colors.green.shade300),
                                  const SizedBox(height: 16),
                                  Text('Ceza Yok',
                                      style: TextStyle(
                                          fontSize: 22,
                                          fontWeight: FontWeight.bold,
                                          color: Colors.grey.shade700)),
                                  const SizedBox(height: 8),
                                  Text('Herhangi bir cezanız bulunmuyor',
                                      style: TextStyle(
                                          fontSize: 15, color: Colors.grey.shade500)),
                                ],
                              ),
                            ),
                          ),
                        ],
                      )
                    : ListView(
                        padding: const EdgeInsets.all(16),
                        children: [
                          // Toplam ceza özeti
                          _buildPenaltySummary(),
                          const SizedBox(height: 16),
                          const Text('Ceza Geçmişi',
                              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                          const SizedBox(height: 12),
                          ..._penalties.map((p) => _buildPenaltyCard(p)).toList(),
                        ],
                      ),
              ),
      ),
    );
  }

  Widget _buildPenaltySummary() {
    final unpaid = _penalties.where((p) => p['isPaid'] == false || p['paymentStatus'] == 'unpaid').length;
    final totalAmount = _penalties.fold<double>(
        0, (sum, p) => sum + (double.tryParse(p['amount'].toString()) ?? 0));

    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Container(
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(16),
          gradient: LinearGradient(
            colors: unpaid > 0
                ? [Colors.red.shade600, Colors.red.shade800]
                : [Colors.green.shade600, Colors.green.shade800],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
        ),
        padding: const EdgeInsets.all(20),
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Toplam Ceza', style: TextStyle(color: Colors.white70, fontSize: 13)),
                  Text('${_penalties.length} adet',
                      style: const TextStyle(
                          color: Colors.white, fontSize: 22, fontWeight: FontWeight.bold)),
                ],
              ),
            ),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Ödenmemiş', style: TextStyle(color: Colors.white70, fontSize: 13)),
                  Text('$unpaid adet',
                      style: const TextStyle(
                          color: Colors.white, fontSize: 22, fontWeight: FontWeight.bold)),
                ],
              ),
            ),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Toplam Tutar', style: TextStyle(color: Colors.white70, fontSize: 13)),
                  Text('${totalAmount.toStringAsFixed(0)} ₺',
                      style: const TextStyle(
                          color: Colors.white, fontSize: 22, fontWeight: FontWeight.bold)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPenaltyCard(Map<String, dynamic> penalty) {
    final isPaid = penalty['isPaid'] == true || penalty['paymentStatus'] == 'paid';
    final amount = double.tryParse(penalty['amount'].toString()) ?? 0;
    final violationType = penalty['violationType'] ?? 'Bilinmiyor';
    final plate = penalty['plateNumber'] ?? penalty['qrCode'] ?? '-';
    final issuedAt = penalty['issuedAt'] ?? penalty['createdAt'] ?? '';

    String formattedDate = '';
    if (issuedAt.isNotEmpty) {
      try {
        final dt = DateTime.parse(issuedAt);
        formattedDate = '${dt.day}.${dt.month}.${dt.year} ${dt.hour}:${dt.minute.toString().padLeft(2, '0')}';
      } catch (_) {
        formattedDate = issuedAt;
      }
    }

    String typeLabel;
    IconData typeIcon;
    Color typeColor;
    if (violationType.contains('road') || violationType.contains('yol')) {
      typeLabel = 'Yol İhlali';
      typeIcon = Icons.warning_amber;
      typeColor = Colors.orange;
    } else if (violationType.contains('multi') || violationType.contains('yamuk')) {
      typeLabel = 'Yamuk Park';
      typeIcon = Icons.crop_free;
      typeColor = Colors.purple;
    } else {
      typeLabel = violationType;
      typeIcon = Icons.gavel;
      typeColor = Colors.red;
    }

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: typeColor.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Icon(typeIcon, color: typeColor, size: 22),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(typeLabel,
                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                      Text(formattedDate,
                          style: TextStyle(color: Colors.grey.shade500, fontSize: 12)),
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: isPaid ? Colors.green.shade50 : Colors.red.shade50,
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(
                        color: isPaid ? Colors.green.shade300 : Colors.red.shade300),
                  ),
                  child: Text(
                    isPaid ? 'Ödendi' : 'Ödenmedi',
                    style: TextStyle(
                      color: isPaid ? Colors.green.shade700 : Colors.red.shade700,
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Icon(Icons.directions_car, size: 16, color: Colors.grey.shade400),
                const SizedBox(width: 4),
                Text(plate, style: TextStyle(color: Colors.grey.shade600, fontSize: 13)),
                const Spacer(),
                Text('${amount.toStringAsFixed(2)} ₺',
                    style: TextStyle(
                        color: typeColor,
                        fontSize: 18,
                        fontWeight: FontWeight.bold)),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildProfileTab() {
    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [Colors.blue.shade50, Colors.white],
        ),
      ),
      child: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            children: [
              const SizedBox(height: 40),
              CircleAvatar(
                radius: 60,
                backgroundColor: Colors.blue.shade700,
                child: Text(
                  _userName.isNotEmpty ? _userName[0].toUpperCase() : 'U',
                  style: const TextStyle(fontSize: 48, color: Colors.white, fontWeight: FontWeight.bold),
                ),
              ),
              const SizedBox(height: 24),
              Text(_userName, style: const TextStyle(fontSize: 28, fontWeight: FontWeight.bold)),
              const SizedBox(height: 40),
              _buildProfileOption(
                icon: Icons.person_outline,
                title: 'Profil Bilgileri',
                onTap: () => Navigator.push(context, MaterialPageRoute(
                  builder: (context) => ProfileInfoScreen(
                      userName: _userName, userEmail: _userEmail, userId: widget.userId),
                )),
              ),
              _buildProfileOption(
                icon: Icons.lock_outline,
                title: 'Şifre Değiştir',
                onTap: () => Navigator.push(context, MaterialPageRoute(
                  builder: (context) => ChangePasswordScreen(userId: widget.userId),
                )),
              ),
              _buildProfileOption(
                icon: Icons.help_outline,
                title: 'Yardım',
                onTap: () => showDialog(
                  context: context,
                  builder: (context) => AlertDialog(
                    title: const Text('Yardım'),
                    content: const Text(
                        'Akıllı Park Yönetim Sistemi\n\nSorularınız için:\nEmail: begumcetinkaya@akillpark.com\nTel: 0850 123 45 67'),
                    actions: [
                      TextButton(onPressed: () => Navigator.pop(context), child: const Text('Tamam'))
                    ],
                  ),
                ),
              ),
              _buildProfileOption(
                icon: Icons.logout,
                title: 'Çıkış Yap',
                color: Colors.red,
                onTap: () async {
                  await StorageService.clearUser();
                  if (mounted) Navigator.pushNamedAndRemoveUntil(context, '/login', (route) => false);
                },
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildStatCard({
    required IconData icon,
    required String title,
    required String value,
    required MaterialColor color,
  }) {
    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(12.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 36, color: color.shade700),
            const SizedBox(height: 8),
            Text(value,
                style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold, color: color.shade700)),
            const SizedBox(height: 4),
            Text(title,
                textAlign: TextAlign.center,
                style: const TextStyle(fontSize: 12, color: Colors.grey)),
          ],
        ),
      ),
    );
  }

  Widget _buildProfileOption({
    required IconData icon,
    required String title,
    required VoidCallback onTap,
    Color? color,
  }) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: ListTile(
        leading: Icon(icon, color: color ?? Colors.blue.shade700),
        title: Text(title, style: TextStyle(color: color, fontWeight: FontWeight.w500)),
        trailing: Icon(Icons.chevron_right, color: Colors.grey.shade400),
        onTap: onTap,
      ),
    );
  }
}