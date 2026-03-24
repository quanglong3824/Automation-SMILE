import time
import datetime
import os
from pywinauto import Application

# ==================== CONFIG ====================
# Đường dẫn file chạy SMILE FO
SMILE_PATH = r"C:\Program Files (x86)\SMILE\SMILEFO.exe"
# Thông tin đăng nhập
USER = "IT"
PASS = "123@123a"
# ================================================

def find_and_click_text(window, target_text):
    """Quét toàn bộ UI để tìm và click vào text mong muốn"""
    try:
        # Lấy tất cả các thành phần con của cửa sổ
        elements = window.descendants()
        for el in elements:
            txt = el.window_text()
            if txt and target_text.lower() in txt.lower():
                print(f"   [+] Đã tìm thấy '{target_text}'. Đang Click...")
                el.click_input()
                return True
        return False
    except Exception as e:
        print(f"   [!] Lỗi khi quét text '{target_text}': {e}")
        return False

def autoBackupSMILE():
    try:
        print(f"--- BẮT ĐẦU QUY TRÌNH BACKUP SMILE: {datetime.datetime.now()} ---")
        
        # BƯỚC 1: Khởi động SMILE và Đăng nhập
        print("Step 1: Đang khởi động SMILE...")
        app = Application(backend="win32").start(SMILE_PATH)
        time.sleep(10) # Chờ app load
        
        try:
            dlg_login = app.window(title_re=".*Log.*In.*")
            if dlg_login.exists():
                dlg_login.set_focus()
                # Giả định cursor đang ở ô Username, Tab sang Pass
                dlg_login.type_keys("{TAB}" + PASS + "{ENTER}")
                print("--> Đã gửi thông tin đăng nhập. Đợi vào màn hình chính...")
                time.sleep(15)
        except:
            print("--> Không thấy cửa sổ Login, bỏ qua...")

        # BƯỚC 2: Xử lý các popup phiền phức (nếu có)
        try:
            top_win = app.top_window()
            # Đóng bảng sinh nhật hoặc thông báo nếu nó hiện lên che màn hình
            if any(word in top_win.window_text() for word in ["Happy", "Birth", "Notice", "Sinh nhật"]):
                print("Step 2: Đang đóng popup thông báo...")
                top_win.type_keys("{ESC}")
                time.sleep(3)
        except:
            pass

        # BƯỚC 3: Vào More Options (Phím 0)
        print("Step 3: Đang truy cập 'More Options' (Phím 0)...")
        all_wins = app.windows(title_re=".*SMILE.*")
        if all_wins:
            # Lấy cửa sổ có diện tích lớn nhất (thường là main win)
            main_win = max(all_wins, key=lambda w: w.rectangle().width() * w.rectangle().height())
            main_win.set_focus()
            main_win.type_keys("0")
            time.sleep(5)
        else:
            print("!! Không tìm thấy cửa sổ chính của SMILE.")
            return

        # BƯỚC 4: Chạy Backup Database (Phím A)
        print("Step 4: Đang chọn 'Backup Database' (Phím A)...")
        options_win = app.top_window()
        
        # Thử quét text trước cho chắc chắn, nếu không thấy thì bấm phím A
        if not find_and_click_text(options_win, "Backup Database"):
            print("--> Không quét được text, gửi phím 'A' trực tiếp...")
            options_win.type_keys("a")
            
        # BƯỚC 5: Đợi 1-2 phút và bấm OK kết thúc
        print("Step 5: ĐANG CHẠY BACKUP... Vui lòng đợi 1-2 phút...")
        start_wait = time.time()
        found_ok = False
        
        # Chờ tối đa 10 phút (đề phòng database lớn)
        while time.time() - start_wait < 600:
            try:
                popup = app.top_window()
                # Tìm chữ OK hoặc nút Đồng ý trên popup kết thúc
                if find_and_click_text(popup, "OK") or find_and_click_text(popup, "Đồng ý"):
                    print("--> THÀNH CÔNG! Đã bấm nút OK hoàn tất quy trình.")
                    found_ok = True
                    break
            except:
                pass
            time.sleep(5) # Quét lại mỗi 5 giây
        
        if not found_ok:
            print("!! Quá thời gian chờ hoặc không thấy bảng thông báo thành công.")

        # Hoàn tất và thoát
        print("--- KẾT THÚC: Đóng ứng dụng ---")
        time.sleep(2)
        app.kill()

    except Exception as e:
        print(f"!! Lỗi hệ thống: {e}")

if __name__ == "__main__":
    autoBackupSMILE()
