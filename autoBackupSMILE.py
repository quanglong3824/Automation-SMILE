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
        """MODULE 2: Tìm và đóng các bảng chặn (Close button / ESC)"""
        print("--> [Module 2] Đang quét tìm các bảng Popup để đóng...")
        try:
            # Thử tìm cửa sổ trên cùng hiện tại
            top_win = self.app.top_window()
            # Danh sách các chữ có thể có trên nút Close/Đóng
            close_keywords = ["Close", "Đóng", "Thoát", "Cancel", "X"]
            
            elements = top_win.descendants()
            for el in elements:
                txt = el.window_text()
                if txt and any(k.lower() in txt.lower() for k in close_keywords):
                    print(f"   [+] Đã tìm thấy nút '{txt}'. Đang Click để dọn dẹp...")
                    el.click_input()
                    time.sleep(2)
                    return True
            
            # Nếu không tìm thấy nút bằng chữ, thử nhấn ESC làm phương án dự phòng
            print("   [-] Không thấy nút Close rõ ràng, gửi lệnh ESC dự phòng...")
            top_win.type_keys("{ESC}")
            time.sleep(2)
        except:
            print("   [-] Không phát hiện popup nào chặn màn hình.")
        return True

    def trigger_more_options(self):
        """MODULE 3: Nhấn phím 0 hoặc Click chữ 'More Options'"""
        print("--> [Module 3] Đang kích hoạt 'More Options'...")
        try:
            # Xác định cửa sổ chính
            all_wins = self.app.windows(title_re=".*SMILE.*")
            self.main_win = max(all_wins, key=lambda w: w.rectangle().width() * w.rectangle().height())
            self.main_win.set_focus()
            
            # Click vào giữa thanh tiêu đề để chắc chắn focus
            self.main_win.click_input(coords=(self.main_win.rectangle().width() // 2, 5))
            
            # THỬ CÁCH 1: Tìm chữ More Options để Click
            found_text = False
            for el in self.main_win.descendants():
                if "more options" in el.window_text().lower():
                    print("   [+] Đã tìm thấy chữ 'More Options'. Click chuột...")
                    el.click_input()
                    found_text = True
                    break
            
            # THỬ CÁCH 2: Nếu không thấy chữ, nhấn phím 0
            if not found_text:
                print("   [-] Không thấy chữ, gửi lệnh phím '0'...")
                send_keys("0")
            
            time.sleep(5)
            return True
        except Exception as e:
            print(f"   [!] Lỗi ở Module 3: {e}")
            return False

    def handle_second_login(self):
        """MODULE 4: Xử lý đăng nhập lần 2 (nếu có)"""
        print("--> [Module 4] Kiểm tra xác thực lần 2...")
        try:
            auth_dlg = self.app.top_window()
            if any(word in auth_dlg.window_text() for word in ["Log", "Pass", "Mật khẩu"]):
                print("   [+] Phát hiện bảng đăng nhập lần 2. Đang nhập...")
                auth_dlg.set_focus()
                send_keys("^a{BACKSPACE}" + USER + "{TAB}" + PASS + "{ENTER}")
                time.sleep(5)
        except:
            pass
        return True

    def run_backup_process(self):
        """MODULE 5: Bấm phím A và đợi OK"""
        print("--> [Module 5] Đang thực hiện Backup Database...")
        try:
            # Nhấn phím A
            send_keys("a")
            print("   [+] Đã nhấn 'A'. Vui lòng đợi 1-2 phút...")
            
            start_wait = time.time()
            while time.time() - start_wait < 600: # Max 10 phút
                top = self.app.top_window()
                # Tìm bất kỳ nút nào có chữ OK hoặc Đồng ý
                for el in top.descendants():
                    if any(ok_txt in el.window_text().upper() for ok_txt in ["OK", "ĐỒNG Ý", "YES"]):
                        print(f"   [+] THÀNH CÔNG! Đã thấy nút '{el.window_text()}'. Click hoàn tất.")
                        el.click_input()
                        return True
                time.sleep(5)
        except Exception as e:
            print(f"   [!] Lỗi ở Module 5: {e}")
        return False

if __name__ == "__main__":
    bot = autoBackupSMILE()
    
    # Chạy tuần tự từng module
    if bot.start_and_login():
        bot.close_annoying_popups()
        if bot.trigger_more_options():
            bot.handle_second_login()
            bot.run_backup_process()
    
    print(f"\n--- KẾT THÚC QUY TRÌNH: {datetime.datetime.now()} ---")
