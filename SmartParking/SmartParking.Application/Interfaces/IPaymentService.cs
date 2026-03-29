using SmartParking.Application.DTOs;
using SmartParking.Domain.Entities;
using System;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace SmartParking.Application.Interfaces
{
    /// <summary>
    /// Ödeme servisi interface
    /// </summary>
    public interface IPaymentService
    {
        /// <summary>
        /// Ödeme işle (Session için)
        /// </summary>
        /// <param name="sessionId">Session ID</param>
        /// <param name="userId">Kullanıcı ID</param>
        /// <param name="paymentMethod">Ödeme yöntemi (cash, credit_card, debit_card, qr_code)</param>
        /// <param name="transactionId">İşlem ID (opsiyonel)</param>
        /// <returns>Payment entity</returns>
        Task<Payment> ProcessPaymentAsync(Guid sessionId, Guid userId, string paymentMethod, string? transactionId = null);

        /// <summary>
        /// Session ödemesini getir
        /// </summary>
        Task<Payment?> GetPaymentBySessionIdAsync(Guid sessionId);

        /// <summary>
        /// Kullanıcının tüm ödemelerini getir
        /// </summary>
        Task<IEnumerable<Payment>> GetUserPaymentsAsync(Guid userId);

        /// <summary>
        /// Ödeme detayını getir
        /// </summary>
        Task<Payment?> GetPaymentByIdAsync(Guid paymentId);

        /// <summary>
        /// Ödeme iptal et
        /// </summary>
        Task<bool> CancelPaymentAsync(Guid paymentId);
    }
}