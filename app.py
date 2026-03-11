import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
from streamlit_autorefresh import st_autorefresh
import pandas as pd

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(
    page_title="IoT Home Control",
    page_icon="🏠",
    layout="wide"
)

# --- 2. KẾT NỐI FIREBASE ---
# Kiểm tra nếu App chưa khởi tạo thì mới khởi tạo
if not firebase_admin._apps:
    # Lấy thông tin từ mục Secrets của Streamlit Cloud
    firebase_secrets = dict(st.secrets["firebase"])

    # Xử lý lỗi ký tự xuống dòng của Private Key (thường gặp khi copy-paste)
    if "private_key" in firebase_secrets:
        firebase_secrets["private_key"] = firebase_secrets["private_key"].replace("\\n", "\n")

    cred = credentials.Certificate(firebase_secrets)
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://iothome-e7d29-default-rtdb.asia-southeast1.firebasedatabase.app'
    })

# --- 3. TỰ ĐỘNG REFRESH ---
# Cứ mỗi 5 giây web sẽ tự load lại để cập nhật số liệu mới nhất từ thiết bị
st_autorefresh(interval=5000, key="datarefresh")

# --- 4. GIAO DIỆN CHÍNH ---
st.title("🏠 Hệ thống Giám sát & Điều khiển IoT")
st.markdown("---")

# Tham chiếu tới các node dữ liệu trên Firebase
# (Bạn hãy đảm bảo code ESP32 gửi đúng vào các đường dẫn này)
ref_temp = db.reference('devices/sensor1/temp')
ref_humi = db.reference('devices/sensor1/humi')
ref_led = db.reference('devices/led1/status')

# Chia cột hiển thị thông số
col1, col2, col3 = st.columns(3)

with col1:
    temp_val = ref_temp.get() or 0
    st.metric(label="🌡️ Nhiệt độ", value=f"{temp_val} °C")

with col2:
    humi_val = ref_humi.get() or 0
    st.metric(label="💧 Độ ẩm", value=f"{humi_val} %")

with col3:
    status = ref_led.get() or "OFF"
    st.subheader("💡 Thiết bị")

    # Nút bấm đổi trạng thái
    if st.button('Đổi trạng thái Đèn'):
        new_status = "OFF" if status == "ON" else "ON"
        ref_led.set(new_status)
        st.rerun()  # Load lại ngay để thấy sự thay đổi

    color = "green" if status == "ON" else "red"
    st.markdown(f"Trạng thái: <b style='color:{color}'>{status}</b>", unsafe_allow_html=True)

st.markdown("---")

# --- 5. BIỂU ĐỒ (Nếu bạn có lưu lịch sử) ---
# Phần này dành cho việc nâng cấp sau này để vẽ biểu đồ đường
st.subheader("📊 Lịch sử dữ liệu")
st.info("Dữ liệu đang được cập nhật Realtime từ Firebase.")

# Ví dụ tạo dữ liệu giả lập để bạn thấy giao diện biểu đồ
# Sau này bạn có thể thay bằng db.reference('history').get()
chart_data = pd.DataFrame({
    "Nhiệt độ": [25, 26, 25.5, 27, temp_val],
})
st.line_chart(chart_data)

# --- FOOTER ---
st.caption("Developed with Streamlit & Firebase Admin SDK")