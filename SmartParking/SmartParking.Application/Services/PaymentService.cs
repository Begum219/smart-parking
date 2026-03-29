using SmartParking.Application.Interfaces;
using SmartParking.Domain.Entities;
using SmartParking.Domain.Interfaces;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace SmartParking.Application.Services
{
    public class PaymentService : IPaymentService
    {
        private readonly IUnitOfWork _unitOfWork;

        public PaymentService(IUnitOfWork unitOfWork)
        {
            _unitOfWork = unitOfWork;
        }

        /// <summary>
        /// Ödeme işle (Session için)
        /// </summary>
        public async Task<Payment> ProcessPaymentAsync(
            Guid sessionId,
            Guid userId,
            string paymentMethod,
            string? transactionId = null)
        {
            // 1. Session'ı kontrol et
            var session = await _unitOfWork.ParkingSessions.GetByIdAsync(sessionId);

            if (session == null)
                throw new Exception("Session bulunamadı");

            if (session.SessionStatus != "completed")
                throw new Exception("Session henüz tamamlanmamış");

            // ✅ DÜZELTME: TotalFee decimal (nullable değil), direkt karşılaştır
            if (session.TotalFee <= 0)
                throw new Exception("Ücret henüz hesaplanmamış");

            if (session.PaymentStatus == "paid")
                throw new Exception("Bu session için ödeme zaten yapılmış");

            // 2. Önceden ödeme var mı kontrol et
            var existingPayment = await _unitOfWork.Payments.GetBySessionIdAsync(sessionId);
            if (existingPayment != null)
                throw new Exception("Bu session için zaten ödeme kaydı var");

            // 3. Payment yöntemi validasyonu
            var validMethods = new[] { "cash", "credit_card", "debit_card", "qr_code" };
            if (!validMethods.Contains(paymentMethod.ToLower()))
                throw new Exception("Geçersiz ödeme yöntemi. Kabul edilenler: cash, credit_card, debit_card, qr_code");

            // 4. Payment kaydı oluştur
            var payment = new Payment
            {
                SessionId = sessionId,
                UserId = userId,
                Amount = session.TotalFee,  // ✅ .Value kaldırıldı (decimal nullable değil)
                PaymentMethod = paymentMethod.ToLower(),
                PaymentStatus = "completed",
                TransactionId = transactionId ?? Guid.NewGuid().ToString(),
                PaymentTime = DateTime.UtcNow
            };

            // 5. Payment'ı kaydet
            await _unitOfWork.Payments.AddAsync(payment);

            // 6. Session'ın PaymentStatus'unu güncelle
            session.PaymentStatus = "paid";
            await _unitOfWork.ParkingSessions.UpdateAsync(session);

            // 7. Değişiklikleri kaydet
            await _unitOfWork.SaveChangesAsync();

            return payment;
        }

        /// <summary>
        /// Session ödemesini getir
        /// </summary>
        public async Task<Payment?> GetPaymentBySessionIdAsync(Guid sessionId)
        {
            return await _unitOfWork.Payments.GetBySessionIdAsync(sessionId);
        }

        /// <summary>
        /// Kullanıcının tüm ödemelerini getir
        /// </summary>
        public async Task<IEnumerable<Payment>> GetUserPaymentsAsync(Guid userId)
        {
            return await _unitOfWork.Payments.GetByUserIdAsync(userId);
        }

        /// <summary>
        /// Ödeme detayını getir
        /// </summary>
        public async Task<Payment?> GetPaymentByIdAsync(Guid paymentId)
        {
            return await _unitOfWork.Payments.GetByIdAsync(paymentId);
        }

        /// <summary>
        /// Ödeme iptal et (nadir kullanılır - yönetici işlemi)
        /// </summary>
        public async Task<bool> CancelPaymentAsync(Guid paymentId)
        {
            var payment = await _unitOfWork.Payments.GetByIdAsync(paymentId);

            if (payment == null)
                return false;

            if (payment.PaymentStatus == "failed" || payment.PaymentStatus == "cancelled")
                return false;

            // Payment'ı iptal et
            payment.PaymentStatus = "cancelled";
            await _unitOfWork.Payments.UpdateAsync(payment);

            // Session'ı geri pending yap
            var session = await _unitOfWork.ParkingSessions.GetByIdAsync(payment.SessionId);
            if (session != null)
            {
                session.PaymentStatus = "pending";
                await _unitOfWork.ParkingSessions.UpdateAsync(session);
            }

            await _unitOfWork.SaveChangesAsync();

            return true;
        }
    }
}