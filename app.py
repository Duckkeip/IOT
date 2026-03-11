import firebase_admin
from firebase_admin import credentials, db

# Kiểm tra nếu chưa khởi tạo thì mới khởi tạo (tránh lỗi app đã tồn tại)
if not firebase_admin._apps:
    cred = credentials.Certificate("secret.json") # Đường dẫn tới file JSON bạn vừa tải
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://iothome-e7d29-default-rtdb.asia-southeast1.firebasedatabase.app'
    })

# Ví dụ đọc thử dữ liệu
ref = db.reference('devices/sensor1')
print(ref.get())