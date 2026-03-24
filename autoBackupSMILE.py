import time
import json
import os
import datetime
from pywinauto import Application, mouse
from pywinauto.keyboard import send_keys
import keyboard

# ==================== CONFIG ====================
SMILE_PATH = r"C:\Program Files (x86)\SMILE\SMILEFO.exe"
USER = "IT"
PASS = "123@123a"
CONFIG_FILE = "smile_config.json"
# ================================================

class autoBackupSMILE:
    def __init__(self):
        self.app = None
        self.config = self.load_config()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        return {"more_options": None, "backup_db": None, "ok_btn": None}

    def save_config(self):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=4)
        print(f"--> Đã lưu tọa độ vào {CONFIG_FILE}")

    def get_user_click(self, label):
        """Dừng lại để người dùng di chuyển chuột và nhấn 'S' để lấy tọa độ"""
        print(f"\n[!] YÊU CẦU CHỈ ĐIỂM: {label.upper()}")
        print(f"--> Hãy di chuyển chuột đến đúng vị trí nút '{label}' trên màn hình SMILE.")
        print("--> Sau đó nhấn phím 'S' (Save) trên bàn phím để bot ghi nhớ.")
        
        while True:
            if keyboard.is_pressed('s'):
                pos = mouse.position()
                print(f"   [+] Đã ghi nhớ tọa độ {label}: {pos}")
                time.sleep(1)
                return [pos[0], pos[1]]
            time.sleep(0.1)

    def run(self):
        try:
            print(f"--- BẮT ĐẦU: {datetime.datetime.now()} ---")
            
            # BƯỚC 1: Khởi động & Đăng nhập (Auto)
            print("Step 1: Khởi động và Đăng nhập lần 1...")
            self.app = Application(backend="win32").start(SMILE_PATH)
            time.sleep(10)
            
            dlg = self.app.window(title_re=".*Log.*In.*")
            if dlg.exists():
                dlg.set_focus()
                send_keys("^a{BACKSPACE}" + USER + "{TAB}" + PASS + "{ENTER}")
                time.sleep(15)

            # BƯỚC 2: Xóa Popup (Auto)
            print("Step 2: Đang dọn dẹp Popup thông báo...")
            send_keys("{ESC}") # Thử đóng bảng sinh nhật bằng ESC
            time.sleep(3)

            # BƯỚC 3: More Options (Hybrid - Chỉ điểm nếu chưa có tọa độ)
            if not self.config.get("more_options"):
                print("\n[CHẾ ĐỘ CÀI ĐẶT] Lần đầu tiên chạy, bot cần bạn chỉ vị trí.")
                self.config["more_options"] = self.get_user_click("More Options")
                self.save_config()
            
            print("Step 3: Click 'More Options' theo tọa độ...")
            x, y = self.config["more_options"]
            mouse.click(button='left', coords=(x, y))
            time.sleep(5)

            # BƯỚC 4: Đăng nhập lần 2 (Auto)
            print("Step 4: Kiểm tra xác thực mật khẩu lần 2...")
            auth_dlg = self.app.top_window()
            if any(word in auth_dlg.window_text() for word in ["Log", "Pass", "Mật khẩu"]):
                auth_dlg.set_focus()
                send_keys("^a{BACKSPACE}" + USER + "{TAB}" + PASS + "{ENTER}")
                time.sleep(5)

            # BƯỚC 5: Backup Database (Hybrid)
            if not self.config.get("backup_db"):
                self.config["backup_db"] = self.get_user_click("Backup Database")
                self.save_config()

            print("Step 5: Click 'Backup Database' theo tọa độ...")
            x, y = self.config["backup_db"]
            mouse.click(button='left', coords=(x, y))
            
            # BƯỚC 6: Đợi nút OK (Hybrid)
            print("Step 6: ĐANG CHẠY BACKUP... Đợi hiện thông báo thành công.")
            if not self.config.get("ok_btn"):
                print("--> Khi nào hiện bảng OK, hãy di chuột vào nút OK và nhấn 'S'.")
                self.config["ok_btn"] = self.get_user_click("Nút OK Hoàn tất")
                self.save_config()
            
            # Chờ đợi thực sự cho đến khi nút OK có thể click được (hoặc chờ 1 phút)
            print("--> Đang chờ 60 giây cho chắc chắn database được backup xong...")
            time.sleep(60)
            x, y = self.config["ok_btn"]
            mouse.click(button='left', coords=(x, y))
            
            print("\n[+] TẤT CẢ HOÀN TẤT! Lần sau bot sẽ tự chạy 100%.")

        except Exception as e:
            print(f"!! Lỗi: {e}")

if __name__ == "__main__":
    # Nếu muốn reset tọa độ để chọn lại, hãy xóa file smile_config.json
    bot = autoBackupSMILE()
    bot.run()
