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
    #st_autorefresh(interval=5000, key="f5_clean")

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
            # --- ĐIỀU KHIỂN ĐÈN ---
            den_status = tb.get('Den', 'OFF')
            if st.button(f"💡 ĐÈN: {den_status}", use_container_width=True, type="secondary" if den_status=="OFF" else "primary"):
                new_den = "ON" if den_status == "OFF" else "OFF"
                db.reference('SmartHome/HienTai/ThietBi/Den').set(new_den)
                st.rerun()

            st.write("") # Tạo khoảng cách nhỏ

            # --- ĐIỀU KHIỂN QUẠT (MỚI) ---
            quat_status = tb.get('Quat', 'OFF')
            # Nút bấm này sẽ gửi lệnh ON/OFF xuống Firebase
            # ESP32 sẽ đọc lệnh này và kết hợp với logic cảm biến
            if st.button(f"🌀 QUẠT: {quat_status}", use_container_width=True, type="secondary" if quat_status=="OFF" else "primary"):
                new_quat = "ON" if quat_status == "OFF" else "OFF"
                db.reference('SmartHome/HienTai/ThietBi/Quat').set(new_quat)
                st.rerun()
            
            # Hiển thị chú thích nhỏ để người dùng hiểu cơ chế Hybrid
            st.caption("ℹ️ Quạt sẽ tự bật nếu Gas nguy hiểm hoặc quá nóng dù bạn tắt ở đây.")

           
            # --- TAB 2: LỊCH SỬ HỆ THỐNG (LichSuHeThong) ---
            with tab2:
                st.subheader("📜 Nhật ký thiết bị (Đã sửa lỗi kiểu dữ liệu)")

                ls_he_thong = smart_home.get('LichSuHeThong', {})

                if ls_he_thong:
                    rows = []

                    if isinstance(ls_he_thong, dict):
                        for key, val in ls_he_thong.items():
                            if not isinstance(val, dict):
                                continue


                            def get_smart(field_data, sub_key):
                                if isinstance(field_data, dict):
                                    return field_data.get(sub_key, '--')
                                return field_data if field_data is not None else '--'


                            row = {
                                "Thời Gian": str(val.get('ThoiGian', '--')),
                                "Nhiệt Độ": str(get_smart(val.get('NhietDo'), 'GiaTri')),
                                "Độ Ẩm": str(get_smart(val.get('DoAm'), 'GiaTri')),
                                "Ánh Sáng": str(get_smart(val.get('AnhSang'), 'TiLe')),
                                "Chỉ số Gas": str(get_smart(val.get('KhiGas'), 'DiemSo') if 'DiemSo' in str(
                                    val.get('KhiGas')) else get_smart(val.get('KhiGas'), 'ChiSo')),
                                "Trạng Thái Gas": str(get_smart(val.get('KhiGas'), 'TrangThai')),
                                "An Ninh": str(get_smart(val.get('AnNinh'), 'HienTrang') if 'HienTrang' in str(
                                    val.get('AnNinh')) else get_smart(val.get('AnNinh'), 'Nguoi')),
                                "Quạt": str(get_smart(val.get('HeThong'), 'Quat'))
                            }
                            rows.append(row)

                    if rows:
                        df_ls = pd.DataFrame(rows)

                        # --- BƯỚC QUAN TRỌNG NHẤT ĐỂ HẾT LỖI ---
                        # Ép toàn bộ DataFrame thành kiểu String để pyarrow không bắt lỗi
                        df_ls = df_ls.astype(str)

                        # Đảo ngược để dữ liệu mới nhất lên đầu
                        df_ls = df_ls.iloc[::-1]

                        # Hiển thị bảng
                        st.dataframe(df_ls, width='stretch')
                    else:
                        st.info("Chưa có dữ liệu hợp lệ.")
                else:
                    st.info("Mục LichSuHeThong trống.")
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
