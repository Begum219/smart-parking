using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using SmartParking.Application.Interfaces;
using System;
using System.Threading.Tasks;

namespace SmartParking.API.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class PaymentController : ControllerBase
    {
        private readonly IPaymentService _paymentService;

        public PaymentController(IPaymentService paymentService)
        {
            _paymentService = paymentService;
        }

        /// <summary>
        /// Ödeme işle (Session için)
        /// </summary>
        /// <param name="request">Ödeme bilgileri</param>
        /// <returns>Ödeme sonucu</returns>
        [HttpPost("process")]
        [Authorize]
        public async Task<IActionResult> ProcessPayment([FromBody] ProcessPaymentRequest request)
        {
            try
            {
                // Kullanıcı ID'sini token'dan al
                var userIdClaim = User.FindFirst("UserId")?.Value;
                if (string.IsNullOrEmpty(userIdClaim) || !Guid.TryParse(userIdClaim, out var userId))
                {
                    return Unauthorized(new { message = "Geçersiz kullanıcı" });
                }

                var payment = await _paymentService.ProcessPaymentAsync(
                    request.SessionId,
                    userId,
                    request.PaymentMethod,
                    request.TransactionId
                );

                return Ok(new
                {
                    success = true,
                    message = "Ödeme başarıyla tamamlandı",
                    payment = new
                    {
                        id = payment.Id,
                        sessionId = payment.SessionId,
                        amount = payment.Amount,
                        paymentMethod = payment.PaymentMethod,
                        paymentStatus = payment.PaymentStatus,
                        transactionId = payment.TransactionId,
                        paymentTime = payment.PaymentTime
                    }
                });
            }
            catch (Exception ex)
            {
                return BadRequest(new
                {
                    success = false,
                    message = ex.Message
                });
            }
        }

        /// <summary>
        /// Session ödemesini getir
        /// </summary>
        [HttpGet("session/{sessionId}")]
        [Authorize]
        public async Task<IActionResult> GetPaymentBySession(Guid sessionId)
        {
            try
            {
                var payment = await _paymentService.GetPaymentBySessionIdAsync(sessionId);

                if (payment == null)
                {
                    return NotFound(new
                    {
                        success = false,
                        message = "Bu session için ödeme bulunamadı"
                    });
                }

                return Ok(new
                {
                    success = true,
                    payment = new
                    {
                        id = payment.Id,
                        sessionId = payment.SessionId,
                        userId = payment.UserId,
                        amount = payment.Amount,
                        paymentMethod = payment.PaymentMethod,
                        paymentStatus = payment.PaymentStatus,
                        transactionId = payment.TransactionId,
                        paymentTime = payment.PaymentTime
                    }
                });
            }
            catch (Exception ex)
            {
                return BadRequest(new { success = false, message = ex.Message });
            }
        }

        /// <summary>
        /// Kullanıcının tüm ödemelerini getir
        /// </summary>
        [HttpGet("user/{userId}")]
        [Authorize]
        public async Task<IActionResult> GetUserPayments(Guid userId)
        {
            try
            {
                // Kullanıcı sadece kendi ödemelerini görebilir (veya admin)
                var currentUserIdClaim = User.FindFirst("UserId")?.Value;
                var currentUserRole = User.FindFirst("Role")?.Value;

                if (string.IsNullOrEmpty(currentUserIdClaim) || !Guid.TryParse(currentUserIdClaim, out var currentUserId))
                {
                    return Unauthorized(new { message = "Geçersiz kullanıcı" });
                }

                // Kendisi değilse ve admin değilse
                if (currentUserId != userId && currentUserRole != "Admin")
                {
                    return Forbid();
                }

                var payments = await _paymentService.GetUserPaymentsAsync(userId);

                return Ok(new
                {
                    success = true,
                    payments = payments.Select(p => new
                    {
                        id = p.Id,
                        sessionId = p.SessionId,
                        amount = p.Amount,
                        paymentMethod = p.PaymentMethod,
                        paymentStatus = p.PaymentStatus,
                        transactionId = p.TransactionId,
                        paymentTime = p.PaymentTime
                    })
                });
            }
            catch (Exception ex)
            {
                return BadRequest(new { success = false, message = ex.Message });
            }
        }

        /// <summary>
        /// Ödeme detayını getir
        /// </summary>
        [HttpGet("{id}")]
        [Authorize]
        public async Task<IActionResult> GetPaymentById(Guid id)
        {
            try
            {
                var payment = await _paymentService.GetPaymentByIdAsync(id);

                if (payment == null)
                {
                    return NotFound(new
                    {
                        success = false,
                        message = "Ödeme bulunamadı"
                    });
                }

                return Ok(new
                {
                    success = true,
                    payment = new
                    {
                        id = payment.Id,
                        sessionId = payment.SessionId,
                        userId = payment.UserId,
                        amount = payment.Amount,
                        paymentMethod = payment.PaymentMethod,
                        paymentStatus = payment.PaymentStatus,
                        transactionId = payment.TransactionId,
                        paymentTime = payment.PaymentTime
                    }
                });
            }
            catch (Exception ex)
            {
                return BadRequest(new { success = false, message = ex.Message });
            }
        }

        /// <summary>
        /// Ödeme iptal et (Sadece Admin)
        /// </summary>
        [HttpPost("cancel/{id}")]
        [Authorize(Roles = "Admin")]
        public async Task<IActionResult> CancelPayment(Guid id)
        {
            try
            {
                var result = await _paymentService.CancelPaymentAsync(id);

                if (!result)
                {
                    return NotFound(new
                    {
                        success = false,
                        message = "Ödeme bulunamadı veya iptal edilemez"
                    });
                }

                return Ok(new
                {
                    success = true,
                    message = "Ödeme başarıyla iptal edildi"
                });
            }
            catch (Exception ex)
            {
                return BadRequest(new { success = false, message = ex.Message });
            }
        }
    }

    /// <summary>
    /// Ödeme işleme request modeli
    /// </summary>
    public class ProcessPaymentRequest
    {
        public Guid SessionId { get; set; }
        public string PaymentMethod { get; set; } = string.Empty; // "cash", "credit_card", "debit_card", "qr_code"
        public string? TransactionId { get; set; } // Opsiyonel - kredi kartı işlemleri için
    }
}