class Vehicle {
  final String id;
  final String userId;
  final String licensePlate;
  final String brand;
  final String model;
  final String color;
  final int? year;
  final DateTime createdAt;

  Vehicle({
    required this.id,
    required this.userId,
    required this.licensePlate,
    required this.brand,
    required this.model,
    required this.color,
    this.year,
    required this.createdAt,
  });

  factory Vehicle.fromJson(Map<String, dynamic> json) {
    return Vehicle(
      id: json['id'].toString(),
      userId: json['userId']?.toString() ?? '',
      licensePlate: json['plateNumber'] ?? json['licensePlate'] ?? '',  // Backend'den plateNumber geliyor
      brand: json['label'] ?? json['brand'] ?? '',                       // Backend'den label geliyor
      model: json['model'] ?? '',
      color: json['color'] ?? '',
      year: json['year'],
      createdAt: json['createdAt'] != null 
          ? DateTime.parse(json['createdAt']) 
          : DateTime.now(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'userId': userId,
      'plateNumber': licensePlate,  // Backend plateNumber bekliyor
      'label': brand,               // Backend label bekliyor
      'model': model,
      'color': color,
      if (year != null) 'year': year,
    };
  }
}