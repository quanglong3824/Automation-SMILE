import time
import json
import os
import shutil
import datetime
import tkinter as tk
import gdown  # pip install gdown
from pywinauto import Application, mouse
from pywinauto.keyboard import send_keys

# ==================== CONFIG ====================
SMILE_PATH = r"C:\Program Files (x86)\SMILE\SMILEFO.exe"
USER = "IT"
PASS = "123@123a"
CONFIG_FILE = "smile_config.json"

# LINK THƯ MỤC GOOGLE DRIVE CỦA BẠN
GD_FOLDER_URL = "https://drive.google.com/drive/folders/15dTWt2vgwOtFDLXrz9GU8vJ-7m9k9gkC?usp=sharing"
DOWNLOAD_DEST_DIR = r"C:\SMILE_Setup"

# ĐƯỜNG DẪN Ổ MẠNG SMILE (Remote)
SOURCE_DIR = r"\\192.168.1.2\smile$"
# ĐƯỜNG DẪN THƯ MỤC DRIVE TRÊN MÁY BẠN (Để đẩy file lên)
DRIVE_DIR = r"C:\Users\YourUser\Google Drive\SMILE_Backup"
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
        else: self.config = {"more_options": None, "backup_db": None}

    def copy_with_progress(self, src, dst):
        """Sao chép file kèm hiển thị tiến trình %"""
        total_size = os.path.getsize(src)
        copied = 0
        with open(src, 'rb') as fsrc, open(dst, 'wb') as fdst:
            print(f"   --> Bắt đầu đẩy file: {os.path.basename(src)} ({total_size / (1024*1024):.2f} MB)")
            while True:
                chunk = fsrc.read(1024 * 1024) # 1MB mỗi lần
                if not chunk: break
                fdst.write(chunk)
                copied += len(chunk)
                percent = (copied / total_size) * 100
                print(f"\r   [Tiến trình]: {percent:.1f}% [{'#' * int(percent // 5)}{'-' * (20 - int(percent // 5))}]", end="")
        print(f"\n   [OK] Đã hoàn tất đẩy file lên Drive.")

    def run(self):
        try:
            # STEP 0: Tải dữ liệu từ Google Drive bằng gdown
            print("\n[Step 0] Đang đồng bộ dữ liệu từ Link Drive Share...")
            os.makedirs(DOWNLOAD_DEST_DIR, exist_ok=True)
            gdown.download_folder(url=GD_FOLDER_URL, output=DOWNLOAD_DEST_DIR, quiet=False)

            # STEP 0.5: Kiểm tra Remote
            print(f"\n[Step 0.5] Kiểm tra ổ mạng: {SOURCE_DIR}")
            if not os.path.exists(SOURCE_DIR):
                print(f"   [!] Cảnh báo: Không truy cập được ổ mạng {SOURCE_DIR}. Hãy mở ổ này trong File Explorer trước.")
            else: print("   [OK] Kết nối remote sẵn sàng.")

            # STEP 1-5: SMILE Automation
            print(f"\n--- BẮT ĐẦU CHẠY SMILE: {datetime.datetime.now()} ---")
            self.app = Application(backend="win32").start(SMILE_PATH)
            time.sleep(10)
            
            # Đăng nhập 1
            dlg = self.app.window(title_re=".*Log.*In.*")
            if dlg.exists():
                dlg.set_focus()
                send_keys("^a{BACKSPACE}" + USER + "{TAB}" + PASS + "{ENTER}")
                time.sleep(15)
            
            send_keys("{ESC}") # Xóa Popup
            time.sleep(3)

            # Chỉ điểm More Options
            if not self.config.get("more_options"):
                self.config["more_options"] = VisualPicker("More Options").selected_coords
                with open(CONFIG_FILE, 'w') as f: json.dump(self.config, f, indent=4)
            mouse.click(button='left', coords=tuple(self.config["more_options"]))
            time.sleep(3)

            # Login 2 (Chỉ nhập Pass)
            top = self.app.top_window()
            if any(w in top.window_text() for w in ["Log", "Pass", "Mật khẩu"]):
                top.set_focus()
                send_keys(PASS + "{ENTER}")
                time.sleep(5)

            # Chỉ điểm Backup Database
            if not self.config.get("backup_db"):
                self.config["backup_db"] = VisualPicker("Backup Database").selected_coords
                with open(CONFIG_FILE, 'w') as f: json.dump(self.config, f, indent=4)
            mouse.click(button='left', coords=tuple(self.config["backup_db"]))
            time.sleep(2)
            send_keys("{ENTER}")

            # STEP 6: Chờ 2 phút
            print("\n[Step 6] Chờ 2 phút sao lưu...")
            for i in range(120, 0, -1):
                if i % 20 == 0: print(f"   --> Còn {i} giây...")
                time.sleep(1)
            if self.app: self.app.kill()

            # STEP 7: Đẩy thẳng lên Drive với tiến trình
            print("\n[Step 7] Đẩy file backup mới nhất lên Drive...")
            files = [os.path.join(SOURCE_DIR, f) for f in os.listdir(SOURCE_DIR) if os.path.isfile(os.path.join(SOURCE_DIR, f))]
            if files:
                latest = max(files, key=os.path.getmtime)
                os.makedirs(DRIVE_DIR, exist_ok=True)
                self.copy_with_progress(latest, os.path.join(DRIVE_DIR, os.path.basename(latest)))
            else: print("   [!] Không tìm thấy file backup nào.")

            print(f"\n[+] TẤT CẢ ĐÃ XONG: {datetime.datetime.now()}")
            input("\nNhấn phím ENTER để đóng cửa sổ...")

        except Exception as e:
            print(f"!! Lỗi: {e}")
            input("\nĐã xảy ra lỗi. Nhấn ENTER để xem log và đóng...")

if __name__ == "__main__":
    bot = autoBackupSMILE()
    bot.run()
