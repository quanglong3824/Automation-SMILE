import time
import json
import os
import shutil
import datetime
import tkinter as tk
import gdown  # Cài đặt: pip install gdown
from pywinauto import Application, mouse
from pywinauto.keyboard import send_keys

# ==================== CONFIG ====================
SMILE_PATH = r"C:\Program Files (x86)\SMILE\SMILEFO.exe"
USER = "IT"
PASS = "123@123a"
CONFIG_FILE = "smile_config.json"

# Cấu hình Google Drive (Tải cả thư mục bằng gdown)
GD_FOLDER_URL = "https://drive.google.com/drive/folders/15dTWt2vgwOtFDLXrz9GU8vJ-7m9k9gkC?usp=sharing"
DOWNLOAD_DEST_DIR = r"C:\SMILE_Setup"

# Cấu hình ĐƯỜNG DẪN REMOTE (Đưa file backup về từ đây)
SOURCE_DIR = r"\\192.168.1.2\smile$"
# Thư mục Google Drive trên máy để lưu trữ
DRIVE_DIR = r"C:\Users\YourUser\Google Drive\SMILE_Backup" 
# ================================================

class VisualPicker:
    """Lớp tạo màn hình trong suốt để người dùng click chọn tọa độ"""
    def __init__(self, label):
        self.root = tk.Tk()
        self.root.attributes("-alpha", 0.3) 
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)
        self.root.config(cursor="cross")
        self.label_text = f"HÃY CLICK VÀO NÚT: [{label.upper()}]"
        self.canvas = tk.Canvas(self.root, cursor="cross", bg="blue")
        self.canvas.pack(fill="both", expand=True)
        self.text_id = self.canvas.create_text(
            self.root.winfo_screenwidth() // 2, 
            self.root.winfo_screenheight() // 2,
            text=self.label_text, font=("Arial", 30, "bold"), fill="white"
        )
        self.blink()
        self.selected_coords = None
        self.canvas.bind("<Button-1>", self.on_click)
        self.root.mainloop()

    def blink(self):
        current_color = self.canvas.itemcget(self.text_id, "fill")
        next_color = "yellow" if current_color == "white" else "white"
        self.canvas.itemconfig(self.text_id, fill=next_color)
        self.root.after(500, self.blink)

    def on_click(self, event):
        self.selected_coords = [event.x_root, event.y_root]
        self.root.destroy()

class autoBackupSMILE:
    def __init__(self):
        self.app = None
        self.config = self.load_config()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except: pass
        return {"more_options": None, "backup_db": None}

    def save_config(self):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=4)

    def download_folder_from_drive(self):
        print(f"\n[Step 0] Đang đồng bộ thư mục từ Google Drive...")
        try:
            os.makedirs(DOWNLOAD_DEST_DIR, exist_ok=True)
            gdown.download_folder(url=GD_FOLDER_URL, output=DOWNLOAD_DEST_DIR, quiet=False, use_cookies=False)
            print(f"   [+] Đã tải/cập nhật dữ liệu từ Drive vào: {DOWNLOAD_DEST_DIR}")
            return True
        except Exception as e:
            print(f"   [!] Lỗi khi tải Drive: {e}")
            return False

    def pre_check_remote(self):
        """Mở và kiểm tra ổ mạng trước khi bắt đầu SMILE"""
        print(f"\n[Step 0.5] Đang kiểm tra kết nối tới ổ mạng: {SOURCE_DIR}...")
        try:
            # Thử liệt kê file để kích hoạt kết nối
            if os.path.exists(SOURCE_DIR):
                print(f"   [OK] Đã kết nối tới ổ mạng thành công.")
                return True
            else:
                print(f"   [!] CẢNH BÁO: Không thể truy cập {SOURCE_DIR}. Hãy đảm bảo ổ mạng đã được đăng nhập.")
                return False
        except Exception as e:
            print(f"   [!] Lỗi kết nối ổ mạng: {e}")
            return False

    def sync_to_drive(self):
        """Quét file backup mới nhất từ 192.168.1.2/smile$ và đưa về Drive"""
        print(f"\n[Step 7] Đang quét file backup mới nhất tại: {SOURCE_DIR}")
        try:
            if not os.path.exists(SOURCE_DIR):
                print(f"   [!] LỖI: Không thể truy cập ổ mạng {SOURCE_DIR}.")
                return

            files = [os.path.join(SOURCE_DIR, f) for f in os.listdir(SOURCE_DIR) if os.path.isfile(os.path.join(SOURCE_DIR, f))]
            if not files:
                print("   [-] Không có file để đưa về.")
                return

            latest_file = max(files, key=os.path.getmtime)
            file_name = os.path.basename(latest_file)
            print(f"   [+] Đã phát hiện file mới nhất: {file_name}")

            os.makedirs(DRIVE_DIR, exist_ok=True)
            shutil.copy2(latest_file, os.path.join(DRIVE_DIR, file_name))
            print(f"   [OK] Đã đưa file về Drive thành công!")
        except Exception as e:
            print(f"   [!] Lỗi khi đồng bộ file: {e}")

    def run(self):
        try:
            # Step 0: Tải dữ liệu từ Drive
            self.download_folder_from_drive() 
            
            # Step 0.5: Mở file remote trước
            self.pre_check_remote()

            print(f"\n--- BẮT ĐẦU QUY TRÌNH SMILE: {datetime.datetime.now()} ---")
            
            # Step 1: Khởi động SMILE
            self.app = Application(backend="win32").start(SMILE_PATH)
            time.sleep(10)
            dlg = self.app.window(title_re=".*Log.*In.*")
            if dlg.exists():
                dlg.set_focus()
                send_keys("^a{BACKSPACE}" + USER + "{TAB}" + PASS + "{ENTER}")
                time.sleep(15)

            # Step 2: Xóa Popup
            send_keys("{ESC}")
            time.sleep(3)

            # Step 3: More Options
            if not self.config.get("more_options"):
                self.config["more_options"] = VisualPicker("More Options").selected_coords
                self.save_config()
            mouse.click(button='left', coords=tuple(self.config["more_options"]))
            time.sleep(3)

            # Step 4: Login 2
            auth_wait_start = time.time()
            while time.time() - auth_wait_start < 10:
                try:
                    top_win = self.app.top_window()
                    if any(word in top_win.window_text() for word in ["Log", "Pass", "Mật khẩu"]):
                        top_win.set_focus()
                        send_keys(PASS + "{ENTER}")
                        time.sleep(5)
                        break
                except: pass
                time.sleep(1)

            # Step 5: Backup & Enter
            if not self.config.get("backup_db"):
                self.config["backup_db"] = VisualPicker("Backup Database").selected_coords
                self.save_config()
            mouse.click(button='left', coords=tuple(self.config["backup_db"]))
            time.sleep(2)
            send_keys("{ENTER}")
            
            # Step 6: Đợi 2 phút (Đã rút ngắn)
            print("\n[Step 6] Chờ 2 phút để hệ thống hoàn tất sao lưu...")
            time.sleep(120)
            if self.app: self.app.kill()

            # Step 7: Đưa file backup về Drive
            self.sync_to_drive()
            
            print(f"\n[+] HOÀN TẤT TOÀN BỘ CÔNG VIỆC: {datetime.datetime.now()}")

        except Exception as e:
            print(f"!! Lỗi hệ thống: {e}")

if __name__ == "__main__":
    bot = autoBackupSMILE()
    bot.run()
