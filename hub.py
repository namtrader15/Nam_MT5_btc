import MetaTrader5 as mt5

# Thông tin tài khoản MT5 của anh
MT5_ACCOUNT = 7510016  # Số tài khoản MT5
MT5_PASSWORD = '7lTa+zUw'  # Mật khẩu tài khoản
MT5_SERVER = 'VantageInternational-Demo'  # Tên server của broker, ví dụ 'MetaQuotes-Demo'

# Hàm kết nối với MT5
def connect_mt5():
    # Khởi động MetaTrader 5
    if not mt5.initialize():
        print("Lỗi khi khởi động MT5:", mt5.last_error())
        return False
    
    # Đăng nhập vào tài khoản
    authorized = mt5.login(MT5_ACCOUNT, password=MT5_PASSWORD, server=MT5_SERVER)
    if not authorized:
        print("Lỗi kết nối đến MT5:", mt5.last_error())
        mt5.shutdown()  # Đóng MT5 nếu kết nối thất bại
        return False
    
    print("Kết nối thành công đến MT5 với tài khoản:", MT5_ACCOUNT)
    return True

# Thực hiện kết nối
if __name__ == "__main__":
    if connect_mt5():
        print("Kết nối hoàn tất.")
        # Đóng MT5 khi không còn sử dụng để giải phóng tài nguyên
        mt5.shutdown()
    else:
        print("Không thể kết nối đến MT5.")
