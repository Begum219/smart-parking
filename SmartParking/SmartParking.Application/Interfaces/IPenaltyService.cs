using SmartParking.Application.DTOs;
using SmartParking.Domain.Entities;
using System;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace SmartParking.Application.Interfaces 
{
    public interface IPenaltyService
    {
        Task<Penalty> IssuePenaltyAsync(Guid sessionId, string violationType, decimal amount, string description, string? imageUrl = null);
        Task<bool> PayPenaltyAsync(Guid penaltyId);
        Task<List<Penalty>> GetSessionPenaltiesAsync(Guid sessionId);
        Task<List<Penalty>> GetUnpaidPenaltiesAsync();
        Task<List<Penalty>> GetUserPenaltiesAsync(Guid userId);
        // ========== ✨ YENİ METODLAR ✨ ==========
        /// <summary>
        /// Yol ihlali cezası kes
        /// </summary>
        Task<Penalty> IssueRoadViolationAsync(RoadViolationDto dto);

        /// <summary>
        /// Yamuk park (birden fazla park yeri) cezası kes
        /// </summary>
        Task<Penalty> IssueMultiSpaceViolationAsync(MultiSpaceViolationDto dto);
        
    }
}