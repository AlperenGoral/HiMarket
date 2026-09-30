using HiMarket.Application.DTOs;

namespace HiMarket.Application.Interfaces;

public interface ISaleService
{
    Task<SaleDto> ProcessSaleAsync(int cashierId, CreateSaleDto dto);
    Task<SaleDto?> GetSaleByReceiptNumberAsync(string receiptNumber);
    Task<bool> CancelSaleAsync(int saleId, int supervisorId, string reason);
}
