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


# --- 2. KẾT NỐI FIREBASE (Sửa lỗi JWT tại đây) ---
@st.cache_resource
def init_firebase():
    if not firebase_admin._apps:
        try:
            # 1. Chuyển secrets sang dict
            fb_dict = dict(st.secrets["firebase"])

            # 2. Xử lý ký tự xuống dòng (Cực kỳ quan trọng)
            if "private_key" in fb_dict:
                # Thay thế chuỗi "\n" văn bản thành ký tự xuống dòng thực sự
                fb_dict["private_key"] = fb_dict["private_key"].replace("\\n", "\n")

            # 3. Khởi tạo Firebase
            cred = credentials.Certificate(fb_dict)
            firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://iothome-e7d29-default-rtdb.asia-southeast1.firebasedatabase.app'
            })
            return True
        except Exception as e:
            st.error(f"Lỗi khởi tạo Firebase: {e}")
            return False
    return True


# Gọi hàm khởi tạo
if init_firebase():
    st.success("🔥 Kết nối Firebase thành công!")
    # --- 3. TỰ ĐỘNG REFRESH ---
    # Giảm xuống 10 giây để tránh bị Firebase "chặn" vì gửi request quá dày đặc
    st_autorefresh(interval=5000, key="datarefresh")

    # --- 4. GIAO DIỆN CHÍNH ---
    st.title("🏠 Hệ thống Giám sát & Điều khiển IoT")
    st.markdown("---")

    try:
        # Tham chiếu tới các node
        ref_temp = db.reference('devices/sensor1/temp')
        ref_humi = db.reference('devices/sensor1/humi')
        ref_led = db.reference('devices/led1/status')

        # Lấy dữ liệu
        temp_val = ref_temp.get()
        humi_val = ref_humi.get()
        status = ref_led.get()

        # Chia cột hiển thị
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(label="🌡️ Nhiệt độ", value=f"{temp_val if temp_val is not None else '--'} °C")

        with col2:
            st.metric(label="💧 Độ ẩm", value=f"{humi_val if humi_val is not None else '--'} %")

        with col3:
            st.subheader("💡 Thiết bị")
            # Nút bấm đổi trạng thái
            btn_label = "BẬT ĐÈN" if status != "ON" else "TẮT ĐÈN"
            if st.button(btn_label, use_container_width=True):
                new_status = "OFF" if status == "ON" else "ON"
                ref_led.set(new_status)
                st.rerun()

            color = "green" if status == "ON" else "red"
            st.markdown(f"Trạng thái: <b style='color:{color}'>{status}</b>", unsafe_allow_html=True)

        st.markdown("---")

        # --- 5. BIỂU ĐỒ ---
        st.subheader("📊 Lịch sử dữ liệu")
        # Giả lập dữ liệu dựa trên giá trị thực để biểu đồ không bị trống
        chart_data = pd.DataFrame({
            "Nhiệt độ": [24, 25, 24.5, 26, temp_val if temp_val else 25],
        })
        st.line_chart(chart_data)

    except Exception as e:
        st.error(f"Lỗi khi đọc/ghi dữ liệu: {e}")

else:
    st.warning("Ứng dụng chưa thể kết nối với Firebase. Vui lòng kiểm tra lại cấu hình Secrets.")

# --- FOOTER ---
st.caption("Developed with Streamlit & Firebase Admin SDK")