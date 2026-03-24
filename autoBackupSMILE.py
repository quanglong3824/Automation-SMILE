import time
import datetime
from pywinauto import Application
from pywinauto.keyboard import send_keys

# ==================== CONFIG ====================
SMILE_PATH = r"C:\Program Files (x86)\SMILE\SMILEFO.exe"
USER = "IT"
PASS = "123@123a"
# ================================================

def deep_scan_and_click(window, target_text):
    """Quét cực sâu toàn bộ các thành phần để tìm chữ và CLICK"""
    print(f"--> Đang quét tìm chữ: '{target_text}'...")
    try:
        # Lấy tất cả các thành phần (kể cả những thành phần bị ẩn hoặc lồng sâu)
        elements = window.descendants()
        for el in elements:
            try:
                content = el.window_text()
                # Nếu thấy chữ cần tìm trong text của thành phần đó
                if content and target_text.lower() in content.lower():
                    print(f"   [+] ĐÃ THẤY '{content}'! Đang click chuột...")
                    # Đưa chuột đến và click (dùng click_input để giả lập chuột thật)
                    el.click_input()
                    return True
            except:
                continue
        return False
    except Exception as e:
        print(f"   [!] Lỗi khi quét: {e}")
        return False

def autoBackupSMILE():
    try:
        print(f"--- BẮT ĐẦU QUY TRÌNH (BẢN QUÉT TEXT): {datetime.datetime.now()} ---")
        
        # 1. Khởi động
        print("Bước 1: Khởi động SMILE...")
        app = Application(backend="win32").start(SMILE_PATH)
        time.sleep(10)

        # 2. Đăng nhập lần 1
        dlg = app.window(title_re=".*Log.*In.*")
        if dlg.exists():
            print("--> Đang đăng nhập lần 1...")
            dlg.set_focus()
            send_keys("^a{BACKSPACE}" + USER + "{TAB}" + PASS + "{ENTER}")
            time.sleep(15)

        # 3. Quét và Đóng Popup Sinh nhật/Thông báo
        print("Bước 2: Dọn dẹp Popup...")
        top_win = app.top_window()
        # Tìm bất kỳ nút nào có chữ Đóng, Close, Thoát để click
        if not deep_scan_and_click(top_win, "Close"):
            deep_scan_and_click(top_win, "Đóng")
            # Nếu vẫn không thấy, nhấn ESC dự phòng
            send_keys("{ESC}")
        time.sleep(3)

        # 4. Bước then chốt: Quét tìm "More Options"
        print("Bước 3: Truy tìm 'More Options' trên toàn màn hình...")
        main_win = app.top_window() # Lấy cửa sổ đang hiện hữu
        if not deep_scan_and_click(main_win, "More Options"):
            print("   [-] Không thấy chữ 'More Options', thử quét phím '0'...")
            if not deep_scan_and_click(main_win, "0"):
                # Nếu quét không ra, gửi phím 0 mù
                send_keys("0")
        
        time.sleep(5)

        # 5. Đăng nhập lần 2 (Nếu có bảng hiện ra)
        print("Bước 4: Xác thực lần 2...")
        auth_dlg = app.top_window()
        if "Log" in auth_dlg.window_text() or "Pass" in auth_dlg.window_text():
            auth_dlg.set_focus()
            send_keys("^a{BACKSPACE}" + USER + "{TAB}" + PASS + "{ENTER}")
            time.sleep(5)

        # 6. Quét tìm "Backup Database"
        print("Bước 5: Chạy Backup...")
        options_win = app.top_window()
        if not deep_scan_and_click(options_win, "Backup Database"):
            send_keys("a") # Phím tắt dự phòng
        
        # 7. Đợi bảng OK hoàn tất
        print("--> ĐANG CHẠY BACKUP... Đợi hiện nút OK (1-2 phút)...")
        start_wait = time.time()
        while time.time() - start_wait < 600:
            final_popup = app.top_window()
            if deep_scan_and_click(final_popup, "OK") or deep_scan_and_click(final_popup, "Đồng ý"):
                print("--> THÀNH CÔNG! Đã hoàn tất sao lưu.")
                break
            time.sleep(5)

        print("--- KẾT THÚC ---")

    except Exception as e:
        print(f"!! Lỗi: {e}")

if __name__ == "__main__":
    autoBackupSMILE()
