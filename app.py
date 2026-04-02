import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
from streamlit_autorefresh import st_autorefresh
import pandas as pd

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(page_title="IoT Home Monitoring", layout="wide", page_icon="🏠")


@st.cache_resource
def init_firebase():
    if not firebase_admin._apps:
        try:
            fb_dict = dict(st.secrets["firebase"])
            fb_dict["private_key"] = fb_dict["private_key"].replace("\\n", "\n")
            cred = credentials.Certificate(fb_dict)
            firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://iothome-e7d29-default-rtdb.asia-southeast1.firebasedatabase.app'
            })
            return True
        except Exception as e:
            st.error(f"Lỗi kết nối Firebase: {e}")
            return False
    return True


if init_firebase():
    st_autorefresh(interval=5000, key="f5_clean")

    # Giao diện chính với 3 Tabs
    tab1, tab2, tab3 = st.tabs(["🔴 TRẠNG THÁI HIỆN TẠI", "📜 LỊCH SỬ HỆ THỐNG", "🚨 NHẬT KÝ KHẨN CẤP"])

    # Truy vấn dữ liệu gốc
    smart_home = db.reference('SmartHome').get()
    if not smart_home:
        st.warning("Đang kết nối tới database...")
        st.stop()

    # --- TAB 1: HIỆN TẠI (DASHBOARD) ---
    with tab1:
        ht = smart_home.get('HienTai', {})
        mt = ht.get('MoiTruong', {})
        at = ht.get('AnToan', {}).get('Gas', {})
        tb = ht.get('ThietBi', {})
    
        st.subheader("📊 Thông số môi trường & Thiết bị")
        c1, c2, c3, c4 = st.columns(4)
    
        # 1. Nhiệt độ
        temp_data = mt.get('NhietDo', {})
        c1.metric(
            label="🌡️ Nhiệt độ", 
            value=f"{temp_data.get('Val', '--')}°C",
            delta=temp_data.get('Status') # Hiện: "Binh thuong", "Nong",...
        )
    
        # 2. Độ ẩm
        hum_data = mt.get('DoAm', {})
        c2.metric(
            label="💧 Độ ẩm", 
            value=f"{hum_data.get('Val', '--')}%",
            delta=hum_data.get('Status') # Hiện: "Thoai mai" như trong ảnh
        )
    
        # 3. Ánh sáng
        light_data = mt.get('AnhSang', {})
        c3.metric(
            label="☀️ Ánh sáng", 
            value=f"{light_data.get('Pct', '--')}%",
            delta=light_data.get('Status') # Hiện: "Rat sang" như trong ảnh
        )
    
        # 4. Gas (Giữ nguyên hoặc tối ưu màu sắc)
        gas_val = at.get('Val', 0)
        c4.metric("💨 Gas", gas_val, delta=at.get('Status'), delta_color="inverse")

        st.divider()
        col_l, col_r = st.columns(2)
        with col_l:
            st.write(f"🏃 Hiện diện: **{ht.get('HienDien', 'N/A')}**")
            st.write(f"🕒 Cập nhật: {ht.get('SyncTime', 'N/A')}")
        with col_r:
            st.write("### 🎮 Điều khiển")
            
            # Lấy trạng thái hiện tại từ Firebase
            current_den = tb.get('Den', 'OFF')
            current_quat = smart_home.get('Command', {}).get('Quat', 'OFF')
    
            # Nút Đèn
            if st.button(f"💡 ĐÈN: {current_den}", use_container_width=True, type="primary" if current_den=="ON" else "secondary"):
                new_st = "ON" if current_den == "OFF" else "OFF"
                db.reference('SmartHome/HienTai/ThietBi/Den').set(new_st)
                st.rerun() # Reload ngay lập tức để gửi lệnh đi nhanh nhất
    
            # Nút Quạt
            if st.button(f"🌀 QUẠT: {current_quat}", use_container_width=True, type="primary" if current_quat=="ON" else "secondary"):
                new_st = "ON" if current_quat == "OFF" else "OFF"
                db.reference('SmartHome/Command/Quat').set(new_st)
                st.rerun()

           
            # --- TAB 2: LỊCH SỬ HỆ THỐNG (LichSuHeThong) ---
    with tab2:
                st.subheader("📜 Nhật ký hệ thống toàn thời gian")

                # 1. Trỏ đến nhánh LichSu để lấy toàn bộ danh sách các ngày
                ref_lich_su = db.reference('SmartHome/LichSu')
                data_toan_bo = ref_lich_su.get()
                
                if data_toan_bo:
                    all_records = []
                    
                    # 2. Duyệt qua từng ngày (2026-03-20, 2026-03-23, 2026-03-26...)
                    for ngay, danh_sach_ban_ghi in data_toan_bo.items():
                        if isinstance(danh_sach_ban_ghi, dict):
                            # 3. Duyệt qua từng bản ghi cụ thể trong ngày đó
                            for push_id, val in danh_sach_ban_ghi.items():
                                # Tạo một dictionary chuẩn hóa dữ liệu
                                # Lưu ý: Cấu trúc của bạn có sự thay đổi giữa các ngày (G/H/L/T và Gas/Humid/Light/Temp)
                                record = {
                                    "Ngày": ngay,
                                    "Thời gian": val.get('Gio') or val.get('Time') or "--",
                                    "Nhiệt độ (°C)": val.get('T') or val.get('Temp') or "--",
                                    "Độ ẩm (%)": val.get('H') or val.get('Humid') or "--",
                                    "Ánh sáng": val.get('L') or val.get('Light') or "--",
                                    "Khí Gas": val.get('G') or val.get('Gas') or "0"
                                }
                                all_records.append(record)
                
                    if all_records:
                        # 4. Chuyển thành DataFrame để hiển thị
                        df = pd.DataFrame(all_records)
                        
                        # Sắp xếp theo thời gian mới nhất lên đầu
                        # Chuyển cột 'Thời gian' sang định dạng datetime để sort chính xác nếu cần
                        df = df.iloc[::-1] 
                        
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.warning("Không có dữ liệu chi tiết trong các ngày.")
                else:
                    st.info("Hiện tại chưa có dữ liệu lịch sử trên hệ thống.")
    # --- TAB 3: NHẬT KÝ KHẨN CẤP (History_Safe) ---
    with tab3:
        st.subheader("⚠️ Nhật ký cảnh báo an ninh")
        
        # 1. Trỏ đến đúng nhánh trong file JSON của bạn
        ref_khan_cap = db.reference('SmartHome/NhatKy_KhanCap')
        data_khan_cap = ref_khan_cap.get()
    
        if data_khan_cap:
            all_alerts = []
            
            # 2. Duyệt qua danh sách phẳng các mã ID
            for alert_id, val in data_khan_cap.items():
                # Xử lý linh hoạt cho cả 2 kiểu đặt tên key (mới và cũ) trong file của bạn
                time_val = val.get('ThoiGian') or val.get('Time') or "--"
                event_val = val.get('Loai') or val.get('Event') or "--"
                detail_val = val.get('ChiTiet') or val.get('Detail') or "--"
                
                alert_record = {
                    "Thời Gian": time_val,
                    "Loại Sự Kiện": event_val,
                    "Chi Tiết Hệ Thống": detail_val
                }
                all_alerts.append(alert_record)
    
            if all_alerts:
                # 3. Tạo DataFrame
                df_alerts = pd.DataFrame(all_alerts)
                
                # Đảo ngược để sự cố mới nhất hiện lên trên cùng
                df_alerts = df_alerts.iloc[::-1]
                
                # 4. Hiển thị bảng
                st.error("Các tình huống bất thường đã ghi nhận:")
                st.dataframe(df_alerts, use_container_width=True)
                
                # Nút xóa lịch sử nếu cần
                if st.button("🗑️ Xóa sạch nhật ký khẩn cấp", key="del_alert"):
                    ref_khan_cap.delete()
                    st.rerun()
            else:
                st.info("Chưa có dữ liệu cảnh báo.")
        else:
            st.success("✅ Hiện tại không có cảnh báo nguy hiểm nào.")
