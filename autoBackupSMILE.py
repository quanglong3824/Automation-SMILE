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
        # Chọn cửa sổ có diện tích lớn nhất (thường là main win)
        main_win = max(all_wins, key=lambda w: w.rectangle().width() * w.rectangle().height())
        return main_win
    except:
        return None

def clear_birthday_popup(app):
    """Đóng bảng Happy Birth Day hoặc các bảng thông báo chặn màn hình"""
    print("--> Đang kiểm tra bảng chặn (Sinh nhật/Thông báo)...")
    try:
        # Tìm các cửa sổ popup phổ biến
        for title in [".*Happy.*Birth.*Day.*", ".*Notice.*", ".*Thông báo.*"]:
            bd_win = app.window(title_re=title)
            if bd_win.exists():
                print(f"!!! PHÁT HIỆN BẢNG: {title}. Đang đóng...")
                bd_win.set_focus()
                # Thử tìm nút Close
                try:
                    btn_close = bd_win.child_window(title="Close", control_type="Button")
                    if btn_close.exists():
                        btn_close.click_input()
                    else:
                        bd_win.type_keys("{ESC}")
                except:
                    bd_win.type_keys("{ESC}")
                time.sleep(2)
    except Exception as e:
        print(f"--> Lỗi khi đóng popup: {e}")

def find_and_click_ok(app):
    """Tìm và bấm nút OK trên các bảng popup thông báo thành công"""
    try:
        # Lấy cửa sổ trên cùng hiện tại
        top_win = app.top_window()
        elements = top_win.descendants()
        for el in elements:
            txt = el.window_text()
            # Tìm nút có chữ OK hoặc Đồng ý
            if txt and any(ok_txt in txt.upper() for ok_txt in ["OK", "ĐỒNG Ý", "YES"]):
                print(f"   [+] Đã tìm thấy nút '{txt}'. Đang Click...")
                el.click_input()
                return True
        return False
    except:
        return False

def autoBackupSMILE():
    try:
        print(f"--- BẮT ĐẦU QUY TRÌNH BACKUP SMILE: {datetime.datetime.now()} ---")
        
        # BƯỚC 1: Khởi động/Kết nối và Đăng nhập
        print("Step 1: Khởi động/Kết nối SMILE...")
        try:
            app = Application(backend="win32").connect(path=SMILE_PATH)
        except:
            app = Application(backend="win32").start(SMILE_PATH)
        
        time.sleep(10)
        
        dlg_login = app.window(title_re=".*Log.*In.*")
        if dlg_login.exists():
            print("--> Đang thực hiện đăng nhập...")
            dlg_login.set_focus()
            # Xóa trắng ô User và nhập lại cho chắc
            dlg_login.type_keys("^a{BACKSPACE}" + USER + "{TAB}" + PASS + "{ENTER}")
            time.sleep(15)

        # BƯỚC 2: Xử lý popup Sinh nhật/Thông báo
        print("Step 2: Kiểm tra và dọn dẹp popup...")
        clear_birthday_popup(app)

        # BƯỚC 3: Vào More Options (Phím 0)
        print("Step 3: Đang vào 'More Options' (Nhấn phím 0)...")
        main_win = get_main_window(app)
        if main_win:
            main_win.set_focus()
            main_win.type_keys("0") # Nhấn phím 0
            time.sleep(5)
        else:
            print("!! Lỗi: Không thấy cửa sổ chính để nhấn phím 0.")
            return

        # BƯỚC 4: Chạy Backup Database (Phím A)
        print("Step 4: Đang chọn 'Backup Database' (Nhấn phím A)...")
        # Sau khi bấm 0, thường sẽ hiện ra một menu hoặc cửa sổ mới
        options_win = app.top_window()
        options_win.set_focus()
        options_win.type_keys("a") # Nhấn phím A
        
        # BƯỚC 5: Đợi 1-2 phút và bấm OK kết thúc
        print("Step 5: ĐANG CHẠY BACKUP... Đang đợi bảng thông báo thành công (1-2 phút)...")
        start_wait = time.time()
        
        # Chờ tối đa 10 phút cho chắc chắn
        while time.time() - start_wait < 600:
            if find_and_click_ok(app):
                print("--> THÀNH CÔNG! Đã bấm nút OK hoàn tất.")
                break
            time.sleep(5)
        
        # Kết thúc
        print("--- HOÀN TẤT QUY TRÌNH ---")
        time.sleep(2)
        # Tắt app sau khi xong (nếu cần)
        # main_win.close() 

    except Exception as e:
        print(f"!! Lỗi hệ thống: {e}")

if __name__ == "__main__":
    autoBackupSMILE()
