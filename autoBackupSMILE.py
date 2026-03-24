import time
import datetime
import os
from pywinauto import Application
from pywinauto.keyboard import send_keys

# ==================== CONFIG ====================
# Đường dẫn file chạy SMILE FO
SMILE_PATH = r"C:\Program Files (x86)\SMILE\SMILEFO.exe"
# Thông tin đăng nhập
USER = "IT"
PASS = "123@123a"
# ================================================

def get_main_window(app):
    """Lấy cửa sổ chính SMILE có diện tích lớn nhất"""
    try:
        all_wins = app.windows(title_re=".*SMILE.*")
        if not all_wins:
            return None
        return max(all_wins, key=lambda w: w.rectangle().width() * w.rectangle().height())
    except:
        return None

def clear_birthday_popup(app):
    """Đóng các bảng popup chặn màn hình (Sinh nhật/Thông báo)"""
    print("--> Đang kiểm tra và dọn dẹp popup...")
    try:
        # Danh sách các tiêu đề popup phổ biến
        popups = [".*Happy.*Birth.*Day.*", ".*Notice.*", ".*Thông báo.*", ".*Birthday.*"]
        for title in popups:
            try:
                win = app.window(title_re=title)
                if win.exists():
                    print(f"!!! PHÁT HIỆN BẢNG: '{title}'. Đang đóng...")
                    win.set_focus()
                    win.type_keys("{ESC}") # Ưu tiên dùng ESC để đóng nhanh
                    time.sleep(2)
            except:
                continue
    except Exception as e:
        print(f"--> Lỗi dọn popup: {e}")

def find_and_click_ok(app):
    """Tìm và bấm nút OK trên các bảng thông báo thành công"""
    try:
        # Kiểm tra cửa sổ trên cùng hiện tại
        top_win = app.top_window()
        # Thử tìm các nút có text là OK, Đồng ý, Yes, Close
        elements = top_win.descendants()
        for el in elements:
            txt = el.window_text()
            if txt and any(ok_txt in txt.upper() for ok_txt in ["OK", "ĐỒNG Ý", "YES", "CLOSE"]):
                print(f"   [+] Tìm thấy nút '{txt}'. Đang Click hoàn tất...")
                el.click_input()
                return True
        # Nếu không tìm thấy nút, thử nhấn phím Enter/Esc trên cửa sổ đó
        top_win.type_keys("{ENTER}")
        return True
    except:
        return False

def autoBackupSMILE():
    try:
        print(f"--- BẮT ĐẦU QUY TRÌNH BACKUP SMILE: {datetime.datetime.now()} ---")
        
        # BƯỚC 1: Khởi động/Kết nối
        print("Step 1: Khởi động SMILE...")
        try:
            app = Application(backend="win32").connect(path=SMILE_PATH)
        except:
            app = Application(backend="win32").start(SMILE_PATH)
        
        time.sleep(8)
        
        # Đăng nhập
        dlg_login = app.window(title_re=".*Log.*In.*")
        if dlg_login.exists():
            print("--> Đang đăng nhập...")
            dlg_login.set_focus()
            send_keys("^a{BACKSPACE}" + USER + "{TAB}" + PASS + "{ENTER}")
            time.sleep(15)

        # BƯỚC 2: Dọn dẹp Popup
        print("Step 2: Dọn dẹp màn hình...")
        clear_birthday_popup(app)

        # BƯỚC 3: Vào More Options (Phím 0)
        print("Step 3: Đang vào 'More Options' (Phím 0)...")
        main_win = get_main_window(app)
        if main_win:
            main_win.set_focus()
            # Click nhẹ vào thanh tiêu đề hoặc giữa màn hình để đảm bảo focus thực sự
            main_win.click_input(coords=(main_win.rectangle().width() // 2, 10))
            time.sleep(1)
            
            # Thử cả 2 cách gửi phím để chắc chắn
            print("--> Gửi phím '0'...")
            send_keys("0") 
            time.sleep(5) # Đợi menu More Options hiện ra
        else:
            print("!! Lỗi: Không thấy cửa sổ chính.")
            return

        # BƯỚC 4: Chạy Backup Database (Phím A)
        print("Step 4: Đang chọn 'Backup Database' (Phím A)...")
        # Lấy cửa sổ mới nhất sau khi bấm 0
        try:
            options_win = app.top_window()
            options_win.set_focus()
            print(f"--> Đang thao tác trên cửa sổ: '{options_win.window_text()}'")
            
            print("--> Gửi phím 'A'...")
            send_keys("a")
            time.sleep(3)
        except:
            print("!! Không tìm thấy cửa sổ More Options để bấm phím A.")

        # BƯỚC 5: Đợi hiện bảng OK (1-2 phút)
        print("Step 5: ĐANG CHẠY BACKUP... Đợi hiện nút OK (tầm 1-2 phút)...")
        start_time = time.time()
        found = False
        
        # Chờ tối đa 10 phút
        while time.time() - start_time < 600:
            if find_and_click_ok(app):
                print("--> THÀNH CÔNG: Đã xác nhận OK hoàn tất.")
                found = True
                break
            time.sleep(5)
            
        if not found:
            print("!! Quá thời gian chờ hoặc không thấy thông báo thành công.")

        print("--- KẾT THÚC QUY TRÌNH ---")
        time.sleep(2)
        # main_win.close() # Mở comment nếu muốn tự động tắt app

    except Exception as e:
        print(f"!! Lỗi: {e}")

if __name__ == "__main__":
    autoBackupSMILE()
