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

# Cấu hình Google Drive (Download bằng gdown)
# Dán link share của bạn vào đây
GD_SHARE_LINK = "https://drive.google.com/uc?id=YOUR_FILE_ID" 
DOWNLOAD_DEST = r"C:\SMILE_Setup\config_new.json" # Nơi lưu tệp tải về

# Cấu hình Backup (Upload lên ổ mạng/Drive máy)
SOURCE_DIR = r"\\192.168.1.2\smile$"
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

    def download_from_drive(self):
        """Sử dụng gdown để tải tệp từ Google Drive"""
        print(f"\n[Step 0] Đang tải tệp từ Google Drive bằng gdown...")
        try:
            # Đảm bảo thư mục đích tồn tại
            os.makedirs(os.path.dirname(DOWNLOAD_DEST), exist_ok=True)
            
            # Tải tệp
            gdown.download(GD_SHARE_LINK, DOWNLOAD_DEST, quiet=False)
            print(f"   [+] Đã tải xong tệp vào: {DOWNLOAD_DEST}")
            return True
        except Exception as e:
            print(f"   [!] Lỗi khi dùng gdown: {e}")
            return False

    def sync_to_drive(self):
        """Tìm file mới nhất từ ổ mạng và copy sang Google Drive máy"""
        print(f"\n[Step 7] Đang quét file mới nhất tại {SOURCE_DIR}...")
        try:
            files = [os.path.join(SOURCE_DIR, f) for f in os.listdir(SOURCE_DIR) if os.path.isfile(os.path.join(SOURCE_DIR, f))]
            if not files: return
            latest_file = max(files, key=os.path.getmtime)
            file_name = os.path.basename(latest_file)
            
            os.makedirs(DRIVE_DIR, exist_ok=True)
            shutil.copy2(latest_file, os.path.join(DRIVE_DIR, file_name))
            print(f"   [OK] Đã đẩy file backup {file_name} lên Drive!")
        except Exception as e:
            print(f"   [!] Lỗi đồng bộ: {e}")

    def run(self):
        try:
            # BƯỚC 0: Tải tệp hỗ trợ từ Drive (Nếu cần)
            # self.download_from_drive() 

            print(f"--- BẮT ĐẦU: {datetime.datetime.now()} ---")
            
            # Step 1: Mở app & Login
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
            top_win = self.app.top_window()
            if any(word in top_win.window_text() for word in ["Log", "Pass", "Mật khẩu"]):
                top_win.set_focus()
                send_keys(PASS + "{ENTER}")
                time.sleep(5)

            # Step 5: Backup & Enter
            if not self.config.get("backup_db"):
                self.config["backup_db"] = VisualPicker("Backup Database").selected_coords
                self.save_config()
            mouse.click(button='left', coords=tuple(self.config["backup_db"]))
            time.sleep(2)
            send_keys("{ENTER}")
            
            # Step 6: Đợi 3 phút và đóng app
            print("\n[Step 6] Chờ 3 phút để hoàn tất sao lưu...")
            time.sleep(180)
            if self.app: self.app.kill()

            # Step 7: Đồng bộ lên Drive máy
            self.sync_to_drive()
            
            print(f"\n[+] HOÀN TẤT: {datetime.datetime.now()}")

        except Exception as e:
            print(f"!! Lỗi: {e}")

if __name__ == "__main__":
    bot = autoBackupSMILE()
    bot.run()
