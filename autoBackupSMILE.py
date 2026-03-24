import time
import datetime
from pywinauto import Application, mouse
from pywinauto.keyboard import send_keys

# ==================== CONFIG (BẠN CÓ THỂ CHỈNH Ở ĐÂY) ====================
SMILE_PATH = r"C:\Program Files (x86)\SMILE\SMILEFO.exe"
USER = "IT"
PASS = "123@123a"

# Tọa độ dự phòng nếu không quét được chữ (X, Y)
# Bạn có thể lấy tọa độ này bằng cách mở Paint, di chuột vào nút và nhìn góc dưới
MORE_OPTIONS_COORDS = (50, 680) # Ví dụ: Góc dưới bên trái
BACKUP_DB_COORDS = (300, 400)   # Ví dụ: Giữa màn hình menu
# ========================================================================

def force_focus_and_click(window, coords=None, target_text=None):
    """Kích hoạt cửa sổ và Click bằng mọi giá"""
    try:
        window.set_focus()
        time.sleep(1)
        
        # Cách 1: Thử tìm theo chữ (Dùng backend 'uia' mạnh hơn)
        if target_text:
            print(f"--> Đang lùng sục chữ: '{target_text}'...")
            for el in window.descendants():
                try:
                    if target_text.lower() in el.window_text().lower():
                        print(f"   [+] Đã thấy '{target_text}'. Click chuột ngay!")
                        el.click_input()
                        return True
                except: continue

        # Cách 2: Nếu không thấy chữ, click theo tọa độ dự phòng
        if coords:
            print(f"   [-] Không thấy chữ, dùng 'Tuyệt chiêu' Click tọa độ: {coords}")
            # Click vào tọa độ tương đối trong cửa sổ
            window.click_input(coords=coords)
            return True
            
        return False
    except Exception as e:
        print(f"   [!] Lỗi khi click: {e}")
        return False

def autoBackupSMILE():
    try:
        print(f"--- BẮT ĐẦU QUY TRÌNH (BẢN TỌA ĐỘ CHÍNH XÁC): {datetime.datetime.now()} ---")
        
        # 1. Khởi động với Backend UIA (Hiện đại hơn, dễ quét chữ hơn)
        print("Bước 1: Khởi động SMILE...")
        app = Application(backend="uia").start(SMILE_PATH)
        time.sleep(10)

        # 2. Đăng nhập
        try:
            dlg = app.window(title_re=".*Log.*In.*")
            if dlg.exists():
                print("--> Đăng nhập...")
                dlg.set_focus()
                send_keys("^a{BACKSPACE}" + USER + "{TAB}" + PASS + "{ENTER}")
                time.sleep(15)
        except:
            print("--> Bỏ qua đăng nhập (có thể đã vào sẵn).")

        # 3. Dọn dẹp Popup (Bắt buộc click để lấy lại Focus)
        print("Bước 2: Dọn dẹp Popup & Lấy lại Focus...")
        top_win = app.top_window()
        # Thử bấm phím ESC để đóng nhanh
        send_keys("{ESC}")
        time.sleep(2)
        # Click vào một khoảng trống trên cửa sổ chính để lấy lại quyền kiểm soát
        top_win.click_input(coords=(100, 10)) 

        # 4. Click 'More Options'
        print("Bước 3: Mở 'More Options'...")
        # Thử quét chữ trước, nếu xịt thì bấm vào tọa độ (50, 680)
        if not force_focus_and_click(top_win, target_text="More Options", coords=MORE_OPTIONS_COORDS):
            print("   [!] Không thể kích hoạt More Options.")

        time.sleep(5)

        # 5. Đăng nhập lần 2
        print("Bước 4: Xác thực mật khẩu...")
        auth_dlg = app.top_window()
        if "Log" in auth_dlg.window_text() or "Pass" in auth_dlg.window_text():
            auth_dlg.set_focus()
            send_keys("^a{BACKSPACE}" + USER + "{TAB}" + PASS + "{ENTER}")
            time.sleep(5)

        # 6. Click 'Backup Database'
        print("Bước 5: Chạy Backup...")
        options_win = app.top_window()
        if not force_focus_and_click(options_win, target_text="Backup Database", coords=BACKUP_DB_COORDS):
            send_keys("a") # Cuối cùng mới dùng phím tắt

        # 7. Đợi bảng OK
        print("--> ĐANG CHẠY... Đợi hiện nút OK (1-2 phút)...")
        start_wait = time.time()
        while time.time() - start_wait < 600:
            final_popup = app.top_window()
            # Quét tìm nút OK hoặc Đồng ý
            found = False
            for el in final_popup.descendants():
                if any(ok in el.window_text().upper() for ok in ["OK", "ĐỒNG Ý", "YES"]):
                    el.click_input()
                    print("--> THÀNH CÔNG!")
                    found = True
                    break
            if found: break
            time.sleep(5)

    except Exception as e:
        print(f"!! Lỗi: {e}")

if __name__ == "__main__":
    autoBackupSMILE()
