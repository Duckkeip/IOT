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
            current_quat = tb.get('Quat', 'OFF')
    
            # Nút Đèn
            if st.button(f"💡 ĐÈN: {current_den}", use_container_width=True, type="primary" if current_den=="ON" else "secondary"):
                new_st = "ON" if current_den == "OFF" else "OFF"
                db.reference('SmartHome/HienTai/ThietBi/Den').set(new_st)
                st.rerun() # Reload ngay lập tức để gửi lệnh đi nhanh nhất
    
            # Nút Quạt
            if st.button(f"🌀 QUẠT: {current_quat}", use_container_width=True, type="primary" if current_quat=="ON" else "secondary"):
                new_st = "ON" if current_quat == "OFF" else "OFF"
                db.reference('SmartHome/HienTai/ThietBi/Quat').set(new_st)
                st.rerun()

           
            # --- TAB 2: LỊCH SỬ HỆ THỐNG (LichSuHeThong) ---
    with tab2:
                st.subheader("📜 Nhật ký hệ thống (Cập nhật cấu trúc mới)")
            
                # 1. Truy vấn nhánh LichSu
                # Lưu ý: Bạn có thể thêm .limit_to_last(1) để chỉ lấy ngày gần nhất 
                # hoặc lấy cả để duyệt tất cả các ngày.
                ls_data = db.reference('SmartHome/LichSu').get()
            
                if ls_data:
                    all_rows = []
                    
                    # 2. Duyệt qua từng Ngày (ví dụ: "2026-03-20")
                    for date_key, entries in ls_data.items():
                        if isinstance(entries, dict):
                            # 3. Duyệt qua từng bản ghi (Push ID) trong ngày đó
                            for push_id, val in entries.items():
                                # Trích xuất dữ liệu dựa trên key viết tắt trong ảnh của bạn
                                row = {
                                    "Thời Gian": val.get('Gio', '--'),
                                    "Nhiệt Độ (T)": val.get('T', '--'),
                                    "Độ Ẩm (H)": val.get('H', '--'),
                                    "Ánh Sáng (L)": val.get('L', '--'),
                                    "Chỉ số Gas (G)": val.get('G', '--'),
                                    "Ngày Log": date_key # Thêm cột này để dễ quản lý
                                }
                                all_rows.append(row)
            
                    if all_rows:
                        # 4. Tạo DataFrame và xử lý hiển thị
                        df_ls = pd.DataFrame(all_rows)
                        
                        # Ép kiểu string để tránh lỗi PyArrow
                        df_ls = df_ls.astype(str)
                        
                        # Sắp xếp để bản ghi mới nhất (thường là cuối danh sách) lên đầu
                        # Nếu 'Gio' định dạng chuẩn, bạn có thể sort theo 'Gio'
                        df_ls = df_ls.iloc[::-1]
            
                        st.dataframe(df_ls, use_container_width=True)
                    else:
                        st.info("Không tìm thấy bản ghi nào trong các thư mục ngày.")
                else:
                    st.info("Nhánh 'LichSu' hiện đang trống.")
    # --- TAB 3: NHẬT KÝ KHẨN CẤP (History_Safe) ---
    with tab3:
        st.subheader("⚠️ Cảnh báo an ninh & khẩn cấp")
        h_safe = smart_home.get('History_Safe', {})
        if h_safe:
            df_safe = pd.DataFrame.from_dict(h_safe, orient='index')
            df_safe = df_safe.loc[:, ~df_safe.columns.duplicated()]
            df_safe = df_safe.sort_index(ascending=False)

            # Hiển thị với định dạng cảnh báo
            st.error("Danh sách các sự kiện bất thường được ghi nhận:")
            st.table(df_safe)
        else:
            st.success("Hệ thống an toàn. Chưa ghi nhận sự cố khẩn cấp.")

else:
    st.error("Vui lòng kiểm tra lại cấu hình Secrets trên Streamlit Cloud.")
