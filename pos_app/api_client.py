import requests
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

# C# .NET 8 Web API Base URL
CSHARP_API_URL = "http://localhost:5000/api"

class CSharpApiClient:
    @staticmethod
    def _url(path):
        return f"{CSHARP_API_URL}/{path.lstrip('/')}"

    @classmethod
    def search_barcode(cls, barcode):
        try:
            res = requests.get(cls._url(f"products/barcode/{barcode}"), timeout=3)
            if res.status_code == 200:
                data = res.json()
                p = data.get('product', {})
                return {
                    'success': True,
                    'product': {
                        'id': p.get('id'),
                        'name': p.get('name'),
                        'barcode': p.get('barcode', ''),
                        'sell_price': float(p.get('sellPrice', 0)),
                        'vat_rate': float(p.get('vatRate', 0)),
                        'unit': p.get('unit', 'Adet'),
                        'is_weighted': p.get('isWeighted', False),
                        'stock_quantity': float(p.get('stockQuantity', 0)),
                    },
                    'quantity': float(data.get('quantity', 1.0)),
                    'is_weighted_barcode': data.get('isWeightedBarcode', False)
                }
            return {'success': False, 'message': 'Ürün bulunamadı'}
        except Exception as e:
            logger.warning(f"C# API offline, falling back: {e}")
            return None

    @classmethod
    def get_quick_buttons(cls):
        try:
            res = requests.get(cls._url("products/quick-buttons"), timeout=3)
            if res.status_code == 200:
                return res.json()
        except Exception:
            pass
        return None

    @classmethod
    def process_sale(cls, shift_id, payment_type, cash_paid, discount_amount, items):
        try:
            # PaymentType enum: Cash = 1, CreditCard = 2
            pay_type = 1 if payment_type == 'NAKIT' else 2
            payload = {
                'shiftId': shift_id,
                'paymentType': pay_type,
                'cashPaid': float(cash_paid),
                'discountAmount': float(discount_amount),
                'items': [
                    {
                        'productId': item.get('product_id'),
                        'quantity': float(item.get('quantity', 1)),
                        'unitPrice': float(item.get('unit_price', 0))
                    } for item in items
                ]
            }
            res = requests.post(cls._url("sales"), json=payload, timeout=5)
            if res.status_code == 200:
                return res.json()
        except Exception as e:
            logger.error(f"C# API Process Sale Error: {e}")
        return None

    @classmethod
    def close_shift(cls, shift_id, actual_cash, note=""):
        try:
            payload = {
                'shiftId': shift_id,
                'actualCash': float(actual_cash),
                'note': note
            }
            res = requests.post(cls._url("shifts/close"), json=payload, timeout=5)
            if res.status_code == 200:
                return res.json()
        except Exception as e:
            logger.error(f"C# API Close Shift Error: {e}")
        return None
