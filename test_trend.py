from binance.client import Client
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, f1_score
import numpy as np
import random

# Hàm giả định kết quả xu hướng ngẫu nhiên
def random_trend():
    return random.choice([1, 0, -1])  # 1: Tăng, 0: Giảm, -1: Không rõ ràng

def combined_probability(p1, p2):
    return random.random()  # Trả về giá trị ngẫu nhiên cho xác suất kết hợp

# Hàm phân tích xu hướng (không thực hiện tính toán, chỉ trả về giá trị ngẫu nhiên)
def analyze_trend(client, interval, name, end_time=None):
    trend = random_trend()  # Xu hướng ngẫu nhiên
    accuracy = random.uniform(60, 100)  # Ngẫu nhiên trong khoảng 60% - 100%
    f1 = random.uniform(60, 100)  # Ngẫu nhiên trong khoảng 60% - 100%
    return trend, accuracy, f1

# Hàm xác định xu hướng cuối cùng
def get_final_trend(client):
    trend_h1, accuracy_h1, f1_h1 = analyze_trend(client, Client.KLINE_INTERVAL_1HOUR, "H1")
    trend_h4, accuracy_h4, f1_h4 = analyze_trend(client, Client.KLINE_INTERVAL_4HOUR, "H4")

    combined_acc = combined_probability(accuracy_h1 / 100, accuracy_h4 / 100)

    if (trend_h1 == 1 and trend_h4 == 1 and combined_acc >= 0.88) or \
       (trend_h1 == 1 and accuracy_h1 > 71 and f1_h1 > 71) or \
       (trend_h4 == 1 and accuracy_h4 > 69 and f1_h4 > 69):
        return "Xu hướng tăng"
    elif (trend_h1 == 0 and trend_h4 == 0 and combined_acc >= 0.88) or \
         (trend_h1 == 0 and accuracy_h1 > 71 and f1_h1 > 71) or \
         (trend_h4 == 0 and accuracy_h4 > 69 and f1_h4 > 69):
        return "Xu hướng giảm"
    elif trend_h1 == -1 or trend_h4 == -1:
        return "Xu hướng tăng"
    else:
        return "Xu hướng giảm"
