import MetaTrader5 as mt5
from binance.client import Client
from atr_check import atr_stop_loss_finder  # Hàm tính ATR từ Binance

# Thông tin tài khoản MT5
MT5_ACCOUNT = 7510016
MT5_PASSWORD = '7lTa+zUw'
MT5_SERVER = 'VantageInternational-Demo'

# Thông tin API Binance
BINANCE_API_KEY = "your_binance_api_key"
BINANCE_SECRET_KEY = "your_binance_secret_key"

# Hàm kết nối với MT5
def connect_mt5():
    if not mt5.initialize():
        print("Lỗi khi khởi động MT5:", mt5.last_error())
        return False
    
    authorized = mt5.login(MT5_ACCOUNT, password=MT5_PASSWORD, server=MT5_SERVER)
    if not authorized:
        error_code, error_message = mt5.last_error()
        print(f"Lỗi kết nối đến MT5: Mã lỗi {error_code} - {error_message}")
        mt5.shutdown()
        return False
    
    print("Kết nối thành công đến MT5 với tài khoản:", MT5_ACCOUNT)
    return True

# Hàm lấy giá mark từ MT5
def get_realtime_price_mt5(symbol="BTCUSD"):
    tick = mt5.symbol_info_tick(symbol)
    if tick:
        return tick.ask  # Giá mua (ask)
    else:
        print(f"Không thể lấy giá hiện tại cho {symbol}.")
        return None

# Hàm tính khối lượng giao dịch dựa trên mức rủi ro mong muốn
def calculate_volume_based_on_risk(symbol, risk_amount, market_price, stop_loss_price):
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print(f"Không thể lấy thông tin cho {symbol}")
        return None

    # Kích thước hợp đồng giao dịch
    contract_size = symbol_info.trade_contract_size

    # Khoảng cách từ giá vào lệnh đến Stop Loss
    distance = abs(market_price - stop_loss_price)

    # Tính khối lượng giao dịch (Volume)
    volume = risk_amount / (distance * contract_size)

    # Làm tròn volume theo bước lot tối thiểu của broker
    volume_step_decimal_places = len(str(symbol_info.volume_step).split(".")[-1])
    volume = max(symbol_info.volume_min, round(volume, volume_step_decimal_places))
    
    print(f"Volume tính toán: {volume} lots cho rủi ro {risk_amount} USD")
    return volume

# Hàm thực hiện lệnh Market trên MT5 với tính toán volume dựa trên mức rủi ro
def place_order_mt5(client, order_type, symbol="BTCUSD", risk_amount=100):
    global last_order_status
    
    # Lấy giá mark hiện tại từ MT5 để đặt lệnh
    mark_price = get_realtime_price_mt5(symbol="BTCUSD")
    if mark_price is None:
        return

    # Sử dụng hàm ATR để lấy stop_loss dựa trên ATR từ Binance
    atr_symbol = "BTCUSDT"  # Đổi thành BTCUSDT cho Binance API
    atr_short_stop_loss, atr_long_stop_loss = atr_stop_loss_finder(client, atr_symbol)
    stop_loss_price = atr_long_stop_loss if order_type == "buy" else atr_short_stop_loss

    # Tính khối lượng giao dịch dựa trên mức rủi ro và giá trị ATR
    volume = calculate_volume_based_on_risk("BTCUSD", risk_amount, mark_price, stop_loss_price)
    if volume is None or volume <= 0:
        print("Số lượng giao dịch không hợp lệ. Hủy giao dịch.")
        return

    # In các giá trị để kiểm tra
    print(f"Giá hiện tại từ MT5: {mark_price}")
    print(f"Stop Loss dựa trên ATR: {stop_loss_price}")
    print(f"Khối lượng giao dịch: {volume} lots")

    # Thiết lập và gửi lệnh Market trên MT5 với IOC filling mode
    order = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": "BTCUSD",
        "volume": volume,
        "type": mt5.ORDER_TYPE_BUY if order_type == "buy" else mt5.ORDER_TYPE_SELL,
        "price": mark_price,
        "deviation": 20,
        "magic": 234000,
        "type_filling": mt5.ORDER_FILLING_IOC,  # Chọn IOC làm chế độ khớp lệnh mặc định
    }

    # Gửi lệnh và kiểm tra lỗi
    result = mt5.order_send(order)
    if result is None:
        print("Gửi lệnh thất bại. Kiểm tra các thông số lệnh:")
        print("Order:", order)
        print("Lỗi:", mt5.last_error())
    elif result.retcode != mt5.TRADE_RETCODE_DONE:
        print("Lệnh không thành công. Mã lỗi:", result.retcode)
        print("Thông tin chi tiết:", result)
    else:
        last_order_status = f"Đã {order_type} {volume} lots BTC ở giá {mark_price:.2f}."
        print(last_order_status)

# Chương trình chính để kiểm tra
if __name__ == "__main__":
    # Khởi tạo Binance client
    client = Client(BINANCE_API_KEY, BINANCE_SECRET_KEY)
    
    # Kết nối MT5 và thực hiện lệnh Market mẫu
    if connect_mt5():
        print("Thực hiện lệnh Market với tính toán volume từ mức rủi ro và ATR stop loss.")
        place_order_mt5(client, "buy", "BTCUSD", risk_amount=60)  # Truyền risk_amount trực tiếp
        mt5.shutdown()
    else:
        print("Không thể kết nối đến MT5.")
