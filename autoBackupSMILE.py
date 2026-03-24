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
DOWNLOAD_DEST_DIR = r"C:\SMILE_Setup" # Thư mục lưu các file tải về từ Drive

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

    def download_folder_from_drive(self):
        """Sử dụng gdown để tải toàn bộ thư mục từ Google Drive"""
        print(f"\n[Step 0] Đang đồng bộ thư mục từ Google Drive...")
        try:
            # Đảm bảo thư mục đích tồn tại
            os.makedirs(DOWNLOAD_DEST_DIR, exist_ok=True)
            
            # Tải toàn bộ folder
            gdown.download_folder(url=GD_FOLDER_URL, output=DOWNLOAD_DEST_DIR, quiet=False, use_cookies=False)
            print(f"   [+] Đã tải/cập nhật toàn bộ thư mục vào: {DOWNLOAD_DEST_DIR}")
            return True
        except Exception as e:
            print(f"   [!] Lỗi khi tải thư mục từ Drive: {e}")
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
            # BƯỚC 0: Tải/Cập nhật dữ liệu từ Drive trước khi làm việc
            self.download_folder_from_drive() 

            print(f"--- BẮT ĐẦU QUY TRÌNH SMILE: {datetime.datetime.now()} ---")
            
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

            # Step 4: Login 2 (Chỉ nhập Pass)
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
            
            # Step 6: Đợi 3 phút và đóng app
            print("\n[Step 6] Chờ 3 phút để hoàn tất sao lưu...")
            time.sleep(180)
            if self.app: self.app.kill()

            # Step 7: Đồng bộ lên Drive máy
            self.sync_to_drive()
            
            print(f"\n[+] HOÀN TẤT TOÀN BỘ CÔNG VIỆC: {datetime.datetime.now()}")

        except Exception as e:
            print(f"!! Lỗi hệ thống: {e}")

if __name__ == "__main__":
    bot = autoBackupSMILE()
    bot.run()
