from flask import Flask, render_template, jsonify, request
import time
import threading
import MetaTrader5 as mt5
from binance.client import Client
from Entry_Super import get_final_trend
from TPO_POC import calculate_poc_value
from place_order import place_order_mt5

# Khởi tạo ứng dụng Flask
app = Flask(__name__)

# Thông tin tài khoản MT5 và Binance API
MT5_ACCOUNT = 24407647
MT5_PASSWORD = 'awzfDGFB-.96'
MT5_SERVER = 'FivePercentOnline-Real'
BINANCE_API_KEY = "your_binance_api_key"
BINANCE_SECRET_KEY = "your_binance_secret_key"
RISK_AMOUNT = 70  # USD

# Biến lưu trữ trạng thái giao dịch và điều khiển bot
trade_status = {
    "position_type": None,
    "profit": 0.0,
    "balance": 0.0,
    "status": "Chưa có vị thế",
    "trend": "N/A"
}
bot_running = False  # Biến để điều khiển trạng thái bot

# Kết nối MT5
def connect_mt5():
    if not mt5.initialize():
        print("Lỗi khi khởi động MT5:", mt5.last_error())
        return False
    authorized = mt5.login(MT5_ACCOUNT, password=MT5_PASSWORD, server=MT5_SERVER)
    if not authorized:
        print("Lỗi kết nối đến MT5")
        mt5.shutdown()
        return False
    print("Kết nối thành công đến MT5")
    return True

# Hàm lấy số dư tài khoản từ MT5
def get_account_balance():
    account_info = mt5.account_info()
    return account_info.balance if account_info else None

# Lấy thông tin vị thế hiện tại
def get_position_info():
    positions = mt5.positions_get(symbol="BTCUSD")
    if positions:
        position = positions[0]
        return {
            "type": "Buy" if position.type == mt5.ORDER_TYPE_BUY else "Sell",
            "profit": position.profit
        }
    return None

# Hàm cập nhật trạng thái giao dịch
def update_trade_status():
    balance = get_account_balance()
    position_info = get_position_info()
    trade_status["balance"] = balance
    trade_status["trend"] = get_trend() if bot_running else "Bot đang tạm dừng"
    if position_info:
        trade_status["position_type"] = position_info["type"]
        trade_status["profit"] = position_info["profit"]
        trade_status["status"] = "Đang có vị thế"
    else:
        trade_status["position_type"] = None
        trade_status["profit"] = 0.0
        trade_status["status"] = "Chưa có vị thế"

# Hàm lấy xu hướng hiện tại từ hàm phân tích `get_final_trend`
def get_trend():
    client = Client(BINANCE_API_KEY, BINANCE_SECRET_KEY)
    trend = get_final_trend(client)
    print(f"Kết quả xu hướng hiện tại: {trend}")
    return trend

# Kiểm tra giá POC và thực hiện lệnh
def check_poc_and_place_order(client, final_trend, symbol="BTCUSD"):
    position = get_position_info()
    if position:
        print("Đã có một vị thế mở. Theo dõi vị thế hiện tại và không mở thêm lệnh.")
        close_position_if_needed(position)
        return

    mark_price = get_realtime_price_mt5(symbol)
    if mark_price is None:
        return

    poc_value = calculate_poc_value(client)
    price_difference_percent = abs((poc_value - mark_price) / mark_price) * 100
    print(f"Chênh lệch giữa POC và mark price: {price_difference_percent:.2f}%")

    if price_difference_percent <= 0.5:
        if final_trend == "Xu hướng tăng":
            print("Xu hướng tăng. POC value gần mark price. Thực hiện lệnh mua.")
            place_order_mt5(client, "buy", symbol, risk_amount=RISK_AMOUNT)
        elif final_trend == "Xu hướng giảm":
            print("Xu hướng giảm. POC value gần mark price. Thực hiện lệnh bán.")
            place_order_mt5(client, "sell", symbol, risk_amount=RISK_AMOUNT)
    else:
        print("Không thực hiện lệnh vì chênh lệch vượt quá 0.5%.")

# Đóng lệnh nếu đạt mức lãi/lỗ đặt trước
def close_position_if_needed(position):
    profit = position["profit"]
    if profit <= -RISK_AMOUNT:
        print(f"Lỗ đạt ngưỡng {RISK_AMOUNT}. Đóng lệnh.")
        close_position(position)
    elif profit >= 1.75 * RISK_AMOUNT:
        print(f"Lợi nhuận đạt ngưỡng {1.75 * RISK_AMOUNT}. Đóng lệnh.")
        close_position(position)

# Hàm đóng lệnh
def close_position(position):
    order_type = mt5.ORDER_TYPE_SELL if position["type"] == "Buy" else mt5.ORDER_TYPE_BUY
    close_request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": "BTCUSD",
        "volume": position["volume"],
        "type": order_type,
        "position": position["ticket"],
        "deviation": 20,
        "magic": 234000,
        "comment": "Đóng lệnh do đạt ngưỡng lãi/lỗ",
    }
    result = mt5.order_send(close_request)
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        print("Đóng lệnh thành công.")
    else:
        print(f"Đóng lệnh thất bại. Mã lỗi: {result.retcode}, Thông tin chi tiết: {result}")

# Lấy giá real-time từ MT5
def get_realtime_price_mt5(symbol):
    tick = mt5.symbol_info_tick(symbol)
    return tick.ask if tick else None

# Vòng lặp kiểm tra xu hướng và vị thế
def trading_loop():
    client = Client(BINANCE_API_KEY, BINANCE_SECRET_KEY)
    while bot_running:
        final_trend = get_trend()
        if final_trend == "Xu hướng không rõ ràng":
            print("Xu hướng không rõ ràng. Nghỉ 600 giây trước khi kiểm tra lại.")
            time.sleep(600)  # Nghỉ 600 giây
        else:
            check_poc_and_place_order(client, final_trend)
            print("Xu hướng rõ ràng. Nghỉ 60 giây trước khi kiểm tra lại.")
            time.sleep(60)  # Nghỉ 60 giây nếu có xu hướng tăng/giảm

# Hàm để bắt đầu bot
def start_bot():
    global bot_running
    if not bot_running:
        bot_running = True
        threading.Thread(target=trading_loop).start()

# Hàm để tạm dừng bot
def pause_bot():
    global bot_running
    bot_running = False

# Route chính hiển thị giao diện
@app.route('/')
def index():
    update_trade_status()
    return render_template('index.html', trade_status=trade_status)

# Route để lấy trạng thái dưới dạng JSON
@app.route('/status')
def status():
    update_trade_status()
    return jsonify(trade_status)

# Route để bắt đầu bot
@app.route('/start_bot', methods=['POST'])
def start_bot_route():
    start_bot()
    return jsonify({"message": "Bot đã bắt đầu chạy"})

# Route để tạm dừng bot
@app.route('/pause_bot', methods=['POST'])
def pause_bot_route():
    pause_bot()
    return jsonify({"message": "Bot đã dừng"})

# Chạy Flask server và vòng lặp kiểm tra giao dịch song song
if __name__ == '__main__':
    if connect_mt5():
        print("Khởi động bot giao dịch trên server Flask.")
        app.run(debug=True, use_reloader=False)
    else:
        print("Không thể kết nối đến MT5.")
        mt5.shutdown()
