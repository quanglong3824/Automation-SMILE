import time
import datetime
import os
from pywinauto import Application
from pywinauto.keyboard import send_keys

# ==================== CONFIG ====================
SMILE_PATH = r"C:\Program Files (x86)\SMILE\SMILEFO.exe"
USER = "IT"
PASS = "123@123a"
# ================================================

def find_and_click_text(window, target_text):
    """Quét toàn bộ UI để tìm và click vào text mong muốn"""
    try:
        elements = window.descendants()
        for el in elements:
            txt = el.window_text()
            if txt and target_text.lower() in txt.lower():
                print(f"   [+] Đã tìm thấy '{target_text}'. Đang Click chuột...")
                el.click_input()
                return True
        return False
    except:
        return False

def autoBackupSMILE():
    try:
        print(f"--- BẮT ĐẦU: {datetime.datetime.now()} ---")
        
        # BƯỚC 1: Khởi động & Đăng nhập lần 1
        try:
            app = Application(backend="win32").connect(path=SMILE_PATH)
        except:
            app = Application(backend="win32").start(SMILE_PATH)
        
        time.sleep(10)
        dlg_login = app.window(title_re=".*Log.*In.*")
        if dlg_login.exists():
            print("--> Đăng nhập hệ thống...")
            dlg_login.set_focus()
            send_keys("^a{BACKSPACE}" + USER + "{TAB}" + PASS + "{ENTER}")
            time.sleep(15)

        # BƯỚC 2: Vào More Options (Ưu tiên Click chữ -> Sau đó mới nhấn phím 0)
        print("Step 2: Đang truy tìm 'More Options'...")
        all_wins = app.windows(title_re=".*SMILE.*")
        main_win = max(all_wins, key=lambda w: w.rectangle().width() * w.rectangle().height())
        main_win.set_focus()
        
        # Cách A: Quét tìm chữ "More Options" để click chuột
        if not find_and_click_text(main_win, "More Options"):
            print("--> Không quét được chữ, gửi phím '0' dự phòng...")
            # Cách B: Nhấn phím 0
            main_win.click_input(coords=(main_win.rectangle().width() // 2, 10)) # Click để chắc chắn focus
            send_keys("0")
        
        time.sleep(5)

        # BƯỚC 3: Xử lý Đăng nhập lần 2 (Bắt buộc để vào Backup)
        print("Step 3: Kiểm tra xác thực mật khẩu lần 2...")
        auth_dlg = app.top_window()
        # Nếu tiêu đề cửa sổ chứa chữ Log In hoặc Password
        if any(word in auth_dlg.window_text() for word in ["Log", "Pass", "Mật khẩu"]):
            print("--> Đang nhập mật khẩu xác thực lần 2...")
            auth_dlg.set_focus()
            send_keys("^a{BACKSPACE}" + USER + "{TAB}" + PASS + "{ENTER}")
            time.sleep(5)

        # BƯỚC 4: Chọn Backup Database (Phím A)
        print("Step 4: Đang chọn 'Backup Database'...")
        options_win = app.top_window()
        if not find_and_click_text(options_win, "Backup Database"):
            print("--> Gửi phím 'A' trực tiếp...")
            send_keys("a")
        
        # BƯỚC 5: Đợi bảng OK kết thúc (1-2 phút)
        print("Step 5: ĐANG BACKUP... Đợi hiện nút OK (1-2 phút)...")
        start_wait = time.time()
        while time.time() - start_wait < 600:
            top = app.top_window()
            # Quét tìm nút OK, Đồng ý, Yes trên popup kết thúc
            if find_and_click_text(top, "OK") or find_and_click_text(top, "Đồng ý"):
                print("--> THÀNH CÔNG: Đã bấm OK hoàn tất.")
                break
            time.sleep(5)

        print("--- HOÀN TẤT ---")
        time.sleep(2)

    except Exception as e:
        print(f"!! Lỗi: {e}")

if __name__ == "__main__":
    autoBackupSMILE()
