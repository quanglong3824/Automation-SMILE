import time
import datetime
import os
from pywinauto import Application

# ==================== CONFIG ====================
SMILE_PATH = r"C:\Program Files (x86)\SMILE\SMILEFO.exe"
USER = "IT"
PASS = "123@123a"
# ================================================

def find_and_click_text(window, target_text):
    """Hàm quét toàn bộ UI để tìm và click vào text mong muốn"""
    print(f"--> Đang truy tìm chữ: '{target_text}'...")
    try:
        # Lấy tất cả các thành phần con của cửa sổ
        elements = window.descendants()
        for el in elements:
            # Kiểm tra nếu text của element chứa chữ mình cần (không phân biệt hoa thường)
            if target_text.lower() in el.window_text().lower():
                print(f"   [+] Đã tìm thấy '{target_text}'. Đang Click...")
                el.click_input()
                return True
        print(f"   [-] Không tìm thấy chữ '{target_text}' trên màn hình hiện tại.")
        return False
    except Exception as e:
        print(f"   [!] Lỗi khi quét text: {e}")
        return False

def run_backup_by_text_scan():
    try:
        print(f"--- BẮT ĐẦU QUY TRÌNH QUÉT TEXT: {datetime.datetime.now()} ---")
        
        # 1. Khởi động SMILE
        app = Application(backend="win32").start(SMILE_PATH)
        time.sleep(5)
        
        # 2. Đăng nhập (Màn hình Login)
        dlg_login = app.window(title_re=".*Log.*In.*")
        if dlg_login.exists():
            dlg_login.set_focus()
            # Login Name 'IT' đã có sẵn, chỉ cần Tab sang Pass
            dlg_login.type_keys("{TAB}" + PASS + "{ENTER}")
            print("--> Đã gửi lệnh Đăng nhập. Đợi 15s...")
            time.sleep(15)

        # 3. Xử lý bảng Sinh nhật (image_2.png)
        # Nếu bảng sinh nhật hiện ra, nó sẽ là cửa sổ trên cùng (Top Window)
        top_win = app.top_window()
        if "Happy" in top_win.window_text() or "Birth" in top_win.window_text():
            print("!!! Phát hiện bảng Sinh nhật. Đang tìm nút 'Close' để đóng...")
            if not find_and_click_text(top_win, "Close"):
                top_win.type_keys("{ESC}") # Backup bằng phím ESC nếu không tìm thấy chữ Close
            time.sleep(3)

        # 4. Tìm và Click "More Options" (image_4.png)
        # Lấy cửa sổ chính SMILE
        all_wins = app.windows(title_re=".*SMILE.*")
        main_win = max(all_wins, key=lambda w: w.rectangle().width() * w.rectangle().height())
        main_win.set_focus()
        
        if not find_and_click_text(main_win, "More Options"):
            print("!! Không tìm thấy chữ 'More Options'. Thử gửi phím '0' dự phòng...")
            main_win.type_keys("0")
        time.sleep(5)

        # 5. Xác thực mật khẩu lần 2 (nếu có hiện bảng Login tiếp)
        auth_dlg = app.top_window()
        if "Log" in auth_dlg.window_text() or "Password" in auth_dlg.window_text():
            print("--> Xác thực mật khẩu lần 2...")
            auth_dlg.set_focus()
            auth_dlg.type_keys(USER + "{TAB}" + PASS + "{ENTER}")
            time.sleep(5)

        # 6. Tìm và Click "Backup Database" (image_5.png)
        # Quét trên cửa sổ More Options hiện tại
        options_win = app.top_window()
        if not find_and_click_text(options_win, "Backup Database"):
            print("!! Không tìm thấy chữ 'Backup Database'. Thử gửi phím 'A' dự phòng...")
            options_win.type_keys("a")
            
        # 7. Treo máy đợi nút OK (Kết thúc backup)
        print("--> ĐANG CHẠY BACKUP... Đợi hiện nút OK (tầm 1-2 phút)...")
        start_wait = time.time()
        while True:
            try:
                popup = app.top_window()
                # Quét xem có chữ OK trên màn hình không
                if find_and_click_text(popup, "OK"):
                    print("--> THÀNH CÔNG! Đã bấm nút OK hoàn tất.")
                    break
            except:
                pass
            
            # Timeout 10 phút
            if time.time() - start_wait > 600:
                print("!! Quá thời gian chờ 10 phút.")
                break
            time.sleep(5) # 5 giây quét 1 lần cho nhẹ máy

        # 8. Thoát app
        print("--> Đóng SMILE. Hoàn tất công việc.")
        main_win.close()

    except Exception as e:
        print(f"!! Lỗi hệ thống: {e}")

if __name__ == "__main__":
    run_backup_by_text_scan()