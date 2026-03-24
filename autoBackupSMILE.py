import time
import json
import os
import shutil
import datetime
import tkinter as tk
import gdown
from pywinauto import Application, mouse
from pywinauto.keyboard import send_keys

# ==================== CONFIG ====================
SMILE_PATH = r"C:\Program Files (x86)\SMILE\SMILEFO.exe"
USER = "IT"
PASS = "123@123a"
CONFIG_FILE = "smile_config.json"

# LINK THƯ MỤC GOOGLE DRIVE ĐỂ TẢI DỮ LIỆU ĐẦU VÀO
GD_FOLDER_URL = "https://drive.google.com/drive/folders/15dTWt2vgwOtFDLXrz9GU8vJ-7m9k9gkC?usp=sharing"
DOWNLOAD_DEST_DIR = r"C:\SMILE_Setup"

# ĐƯỜNG DẪN Ổ MẠNG SMILE (Remote)
SOURCE_DIR = r"\\192.168.1.2\smile$"
# ================================================

class VisualPicker:
    """Màn hình xanh để chỉ điểm tọa độ"""
    def __init__(self, label):
        self.root = tk.Tk()
        self.root.attributes("-alpha", 0.3, "-fullscreen", True, "-topmost", True)
        self.root.config(cursor="cross")
        self.canvas = tk.Canvas(self.root, cursor="cross", bg="blue")
        self.canvas.pack(fill="both", expand=True)
        txt = f"HÃY CLICK VÀO NÚT: [{label.upper()}]"
        self.text_id = self.canvas.create_text(
            self.root.winfo_screenwidth() // 2, self.root.winfo_screenheight() // 2,
            text=txt, font=("Arial", 30, "bold"), fill="white"
        )
        self.selected_coords = None
        self.canvas.bind("<Button-1>", self.on_click)
        self.blink()
        self.root.mainloop()

    def blink(self):
        c = self.canvas.itemcget(self.text_id, "fill")
        self.canvas.itemconfig(self.text_id, fill="yellow" if c == "white" else "white")
        self.root.after(500, self.blink)

    def on_click(self, event):
        self.selected_coords = [event.x_root, event.y_root]
        self.root.destroy()

class autoBackupSMILE:
    def __init__(self):
        self.app = None
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f: self.config = json.load(f)
        else: self.config = {"more_options": None, "backup_db": None, "ok_btn": None, "backup_duration": 60}

    def find_google_drive_path(self):
        """Tự động tìm kiếm ổ đĩa hoặc thư mục Google Drive trên Windows"""
        # 1. Kiểm tra ổ đĩa G: (Mặc định của Google Drive Desktop)
        if os.path.exists(r"G:\My Drive"):
            return r"G:\My Drive\SMILE BACKUP"
        
        # 2. Kiểm tra các ổ đĩa khác từ H-Z
        import string
        for letter in string.ascii_uppercase[7:]: # H to Z
            path = f"{letter}:\\My Drive"
            if os.path.exists(path):
                return f"{letter}:\\My Drive\\SMILE BACKUP"
        
        # 3. Kiểm tra trong thư mục User mặc định
        user_profile = os.environ.get("USERPROFILE")
        default_path = os.path.join(user_profile, "Google Drive", "My Drive", "SMILE BACKUP")
        if os.path.exists(os.path.dirname(default_path)):
            return default_path
            
        return None

    def copy_with_progress(self, src, dst):
        """Sao chép file kèm hiển thị tiến trình %"""
        total_size = os.path.getsize(src)
        copied = 0
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(src, 'rb') as fsrc, open(dst, 'wb') as fdst:
            print(f"   --> Đang đẩy file: {os.path.basename(src)} ({total_size / (1024*1024):.2f} MB)")
            while True:
                chunk = fsrc.read(1024 * 1024)
                if not chunk: break
                fdst.write(chunk)
                copied += len(chunk)
                percent = (copied / total_size) * 100
                print(f"\r   [Đang tải lên Drive]: {percent:.1f}% [{'#' * int(percent // 5)}{'-' * (20 - int(percent // 5))}]", end="")
        print(f"\n   [OK] Đã hoàn tất đẩy file lên Drive.")

    def run(self):
        try:
            # STEP 0: Đồng bộ Drive đầu vào
            print("\n[Step 0] Đang tải dữ liệu từ Google Drive (gdown)...")
            os.makedirs(DOWNLOAD_DEST_DIR, exist_ok=True)
            try:
                gdown.download_folder(url=GD_FOLDER_URL, output=DOWNLOAD_DEST_DIR, quiet=True)
            except: print("   [!] Không tải được dữ liệu từ Drive, bỏ qua...")

            # STEP 1-5: SMILE FO
            print(f"\n--- BẮT ĐẦU QUY TRÌNH SMILE: {datetime.datetime.now()} ---")
            self.app = Application(backend="win32").start(SMILE_PATH)
            time.sleep(10)
            
            # Login 1
            dlg = self.app.window(title_re=".*Log.*In.*")
            if dlg.exists():
                dlg.set_focus()
                send_keys("^a{BACKSPACE}" + USER + "{TAB}" + PASS + "{ENTER}")
                time.sleep(15)
            send_keys("{ESC}")
            time.sleep(3)

            # More Options
            if not self.config.get("more_options"):
                self.config["more_options"] = VisualPicker("More Options").selected_coords
                with open(CONFIG_FILE, 'w') as f: json.dump(self.config, f, indent=4)
            mouse.click(button='left', coords=tuple(self.config["more_options"]))
            time.sleep(3)

            # Login 2
            top = self.app.top_window()
            if any(w in top.window_text() for w in ["Log", "Pass", "Mật khẩu"]):
                top.set_focus()
                send_keys(PASS + "{ENTER}")
                time.sleep(5)

            # Backup
            if not self.config.get("backup_db"):
                self.config["backup_db"] = VisualPicker("Backup Database").selected_coords
                with open(CONFIG_FILE, 'w') as f: json.dump(self.config, f, indent=4)
            
            start_backup = time.time()
            mouse.click(button='left', coords=tuple(self.config["backup_db"]))
            time.sleep(2)
            send_keys("{ENTER}")

            # Chờ Backup
            if not self.config.get("ok_btn"):
                self.config["ok_btn"] = VisualPicker("Nút OK Khi Xong").selected_coords
                duration = int(time.time() - start_backup)
                self.config["backup_duration"] = duration
                with open(CONFIG_FILE, 'w') as f: json.dump(self.config, f, indent=4)
            else:
                wait_time = self.config.get("backup_duration", 60) + 30
                print(f"\n[Step 6] TỰ ĐỘNG: Đang đợi backup ({wait_time} giây)...")
                for i in range(wait_time, 0, -1):
                    if i % 30 == 0: print(f"   --> Còn {i} giây...")
                    time.sleep(1)
            
            mouse.click(button='left', coords=tuple(self.config["ok_btn"]))
            time.sleep(2)
            send_keys("0") # Thoát
            time.sleep(3)

            # STEP 7: Đẩy lên Drive
            print("\n[Step 7] Đang đồng bộ file backup lên Google Drive...")
            drive_path = self.find_google_drive_path()
            
            if not drive_path:
                print("\n[!] LỖI: Không tìm thấy ứng dụng Google Drive trên máy.")
                print("--> Vui lòng cài đặt 'Google Drive cho máy tính' để kích hoạt tính năng này.")
            else:
                if os.path.exists(SOURCE_DIR):
                    files = [os.path.join(SOURCE_DIR, f) for f in os.listdir(SOURCE_DIR) if os.path.isfile(os.path.join(SOURCE_DIR, f))]
                    if files:
                        latest = max(files, key=os.path.getmtime)
                        self.copy_with_progress(latest, os.path.join(drive_path, os.path.basename(latest)))
                    else: print("   [-] Không thấy file backup tại remote.")
                else: print(f"   [-] Không truy cập được {SOURCE_DIR}")

            print(f"\n[+] HOÀN TẤT: {datetime.datetime.now()}")
            input("\nNhấn ENTER để đóng cửa sổ...")

        except Exception as e:
            print(f"!! Lỗi: {e}")
            input("\nNhấn ENTER để thoát...")

if __name__ == "__main__":
    bot = autoBackupSMILE()
    bot.run()
