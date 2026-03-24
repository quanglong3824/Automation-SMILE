import time
import datetime
import os
from pywinauto import Application
from pywinauto.keyboard import send_keys

# ==================== CONFIG ====================
SMILE_PATH = r"C:\Program Files (x86)\SMILE\SMILEFO.exe"
USER = "IT"
PASS = "123@123a"

class autoBackupSMILE:
    def __init__(self):
        self.app = None
        self.main_win = None

    def start_and_login(self):
        """MODULE 1: Khởi động và Đăng nhập lần đầu"""
        print("--> [Module 1] Đang khởi động/kết nối SMILE...")
        try:
            self.app = Application(backend="win32").connect(path=SMILE_PATH)
        except:
            self.app = Application(backend="win32").start(SMILE_PATH)
        
        time.sleep(10)
        dlg = self.app.window(title_re=".*Log.*In.*")
        if dlg.exists():
            print("   [+] Đang thực hiện đăng nhập...")
            dlg.set_focus()
            send_keys("^a{BACKSPACE}" + USER + "{TAB}" + PASS + "{ENTER}")
            time.sleep(15)
        return True

    def close_annoying_popups(self):
        """MODULE 2: Tìm và đóng các bảng chặn (Popup Sinh nhật/Thông báo)"""
        print("--> [Module 2] Đang quét dọn các bảng Popup...")
        try:
            # Thử tìm các cửa sổ trên cùng không phải cửa sổ chính
            top_win = self.app.top_window()
            title = top_win.window_text()
            
            # Nếu thấy các từ khóa popup
            if any(word in title for word in ["Happy", "Birth", "Notice", "Thông báo", "Sinh nhật"]):
                print(f"   [!] Phát hiện bảng: '{title}'. Đang đóng bằng ESC...")
                top_win.set_focus()
                top_win.type_keys("{ESC}")
                time.sleep(3)
                
            # Quét thêm lần nữa tìm nút 'Close' bên trong nếu ESC không ăn
            for el in top_win.descendants():
                if "close" in el.window_text().lower() or "đóng" in el.window_text().lower():
                    print(f"   [+] Tìm thấy nút '{el.window_text()}'. Click để đóng...")
                    el.click_input()
                    time.sleep(2)
                    break
        except:
            print("   [-] Không thấy popup nào.")
        return True

    def trigger_more_options(self):
        """MODULE 3: Click chuột vào 'More Options' (Bắt buộc dùng chuột)"""
        print("--> [Module 3] Đang truy tìm nút 'More Options' để CLICK CHUỘT...")
        try:
            # 1. Lấy cửa sổ chính và focus
            all_wins = self.app.windows(title_re=".*SMILE.*")
            self.main_win = max(all_wins, key=lambda w: w.rectangle().width() * w.rectangle().height())
            self.main_win.set_focus()
            time.sleep(2) # Chờ 1 chút sau khi đóng popup ở Module 2
            
            # 2. Quét tìm chữ 'More Options' (hoặc '0. More Options')
            found = False
            elements = self.main_win.descendants()
            for el in elements:
                txt = el.window_text()
                # Kiểm tra nếu text chứa "More Options"
                if txt and "more options" in txt.lower():
                    print(f"   [+] ĐÃ TÌM THẤY: '{txt}'. Đang CLICK CHUỘT trực tiếp...")
                    # Lấy tọa độ và click vào giữa element đó
                    el.click_input()
                    found = True
                    break
            
            # 3. Phương án dự phòng: Tìm nút có số '0'
            if not found:
                print("   [-] Không tìm thấy chữ 'More Options', thử quét tìm nút có số '0'...")
                for el in elements:
                    if el.window_text() == "0":
                        print("   [+] Tìm thấy nút '0'. Click chuột...")
                        el.click_input()
                        found = True
                        break
            
            if not found:
                print("   [!] CẢNH BÁO: Không tìm thấy mục 'More Options' trên màn hình để click.")
                return False

            time.sleep(5) # Đợi bảng đăng nhập lần 2 hiện ra
            return True
        except Exception as e:
            print(f"   [!] Lỗi Module 3: {e}")
            return False

    def handle_second_login(self):
        """MODULE 4: Đăng nhập lần 2 (Sau khi click More Options)"""
        print("--> [Module 4] Đăng nhập xác thực lần 2...")
        try:
            auth_dlg = self.app.top_window()
            if any(word in auth_dlg.window_text() for word in ["Log", "Pass", "Mật khẩu", "Xác nhận"]):
                print("   [+] Đang nhập User/Pass lần 2...")
                auth_dlg.set_focus()
                send_keys("^a{BACKSPACE}" + USER + "{TAB}" + PASS + "{ENTER}")
                time.sleep(5)
        except:
            print("   [-] Không thấy yêu cầu đăng nhập lần 2.")
        return True

    def run_backup_process(self):
        """MODULE 5: Chạy Backup và đợi bảng OK"""
        print("--> [Module 5] Đang thực hiện Backup Database...")
        try:
            # Thử click chữ "Backup Database" trước
            top = self.app.top_window()
            found_backup = False
            for el in top.descendants():
                if "backup database" in el.window_text().lower():
                    print("   [+] Đã thấy chữ 'Backup Database'. Click chuột...")
                    el.click_input()
                    found_backup = True
                    break
            
            # Nếu không thấy chữ, nhấn phím A
            if not found_backup:
                print("   [-] Không quét được chữ, gửi phím 'A'...")
                send_keys("a")
            
            print("   [+] Đang đợi bảng OK (1-2 phút)...")
            start_wait = time.time()
            while time.time() - start_wait < 600:
                final_popup = self.app.top_window()
                for el in final_popup.descendants():
                    txt = el.window_text().upper()
                    if any(ok_txt in txt for ok_txt in ["OK", "ĐỒNG Ý", "SUCCESS", "HOÀN TẤT"]):
                        print(f"   [+] THÀNH CÔNG! Đã bấm nút '{el.window_text()}'.")
                        el.click_input()
                        return True
                time.sleep(5)
        except Exception as e:
            print(f"   [!] Lỗi Module 5: {e}")
        return False

if __name__ == "__main__":
    bot = autoBackupSMILE()
    if bot.start_and_login():
        bot.close_annoying_popups()
        if bot.trigger_more_options():
            bot.handle_second_login()
            bot.run_backup_process()
    print(f"\n--- KẾT THÚC QUY TRÌNH ---")
