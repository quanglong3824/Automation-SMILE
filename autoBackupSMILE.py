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
# ĐƯỜNG DẪN THƯ MỤC DRIVE TRÊN MÁY BẠN
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
        else: self.config = {"more_options": None, "backup_db": None, "ok_btn": None, "backup_duration": 60}

    def copy_with_progress(self, src, dst):
        """Sao chép file kèm hiển thị tiến trình %"""
        total_size = os.path.getsize(src)
        copied = 0
        with open(src, 'rb') as fsrc, open(dst, 'wb') as fdst:
            print(f"   --> Đang đẩy file: {os.path.basename(src)} ({total_size / (1024*1024):.2f} MB)")
            while True:
                chunk = fsrc.read(1024 * 1024)
                if not chunk: break
                fdst.write(chunk)
                copied += len(chunk)
                percent = (copied / total_size) * 100
                print(f"\r   [Tiến trình]: {percent:.1f}% [{'#' * int(percent // 5)}{'-' * (20 - int(percent // 5))}]", end="")
        print(f"\n   [OK] Đã hoàn tất đẩy file lên Drive.")

    def run(self):
        try:
            # STEP 0: Đồng bộ Drive
            print("\n[Step 0] Đang đồng bộ dữ liệu từ Link Drive Share...")
            os.makedirs(DOWNLOAD_DEST_DIR, exist_ok=True)
            gdown.download_folder(url=GD_FOLDER_URL, output=DOWNLOAD_DEST_DIR, quiet=True)

            # STEP 1-2: Mở app & Login 1
            print(f"\n--- BẮT ĐẦU QUY TRÌNH SMILE: {datetime.datetime.now()} ---")
            self.app = Application(backend="win32").start(SMILE_PATH)
            time.sleep(10)
            dlg = self.app.window(title_re=".*Log.*In.*")
            if dlg.exists():
                dlg.set_focus()
                send_keys("^a{BACKSPACE}" + USER + "{TAB}" + PASS + "{ENTER}")
                time.sleep(15)
            send_keys("{ESC}")
            time.sleep(3)

            # Bước 3: More Options
            if not self.config.get("more_options"):
                print("[!] Đang cài đặt tọa độ More Options...")
                self.config["more_options"] = VisualPicker("More Options").selected_coords
                with open(CONFIG_FILE, 'w') as f: json.dump(self.config, f, indent=4)
            mouse.click(button='left', coords=tuple(self.config["more_options"]))
            time.sleep(3)

            # Step 4: Login 2
            top = self.app.top_window()
            if any(w in top.window_text() for w in ["Log", "Pass", "Mật khẩu"]):
                top.set_focus()
                send_keys(PASS + "{ENTER}")
                time.sleep(5)

            # Bước 5: Backup Database
            if not self.config.get("backup_db"):
                print("[!] Đang cài đặt tọa độ Backup Database...")
                self.config["backup_db"] = VisualPicker("Backup Database").selected_coords
                with open(CONFIG_FILE, 'w') as f: json.dump(self.config, f, indent=4)
            
            # Bắt đầu tính giờ Backup
            start_backup_time = time.time()
            mouse.click(button='left', coords=tuple(self.config["backup_db"]))
            time.sleep(2)
            send_keys("{ENTER}")

            # STEP 6: Xử lý nút OK và Thời gian chờ
            if not self.config.get("ok_btn"):
                print("\n[CHẾ ĐỘ CÀI ĐẶT] Đang đo thời gian backup và lấy tọa độ nút OK...")
                self.config["ok_btn"] = VisualPicker("Nút OK Khi Xong").selected_coords
                # Tính toán thời gian thực tế đã chờ
                duration = int(time.time() - start_backup_time)
                self.config["backup_duration"] = duration
                with open(CONFIG_FILE, 'w') as f: json.dump(self.config, f, indent=4)
                print(f"   [+] Đã học xong thời gian backup: {duration} giây.")
            else:
                # CHẾ ĐỘ TỰ ĐỘNG: Đợi thời gian đã học + 30 giây an toàn
                wait_time = self.config.get("backup_duration", 60) + 30
                print(f"\n[Step 6] TỰ ĐỘNG: Đang đợi backup hoàn tất (Cần chờ {wait_time} giây)...")
                for i in range(wait_time, 0, -1):
                    if i % 30 == 0: print(f"   --> Còn {i} giây...")
                    time.sleep(1)
            
            # Click nút OK hoàn tất trên SMILE
            mouse.click(button='left', coords=tuple(self.config["ok_btn"]))
            time.sleep(2)

            # Thoát SMILE lịch sự
            print("--> Đang thoát SMILE (Phím 0)...")
            try:
                main_win = self.app.top_window()
                main_win.set_focus()
                send_keys("0")
                time.sleep(3)
            except: pass

            # STEP 7: Đẩy lên Drive
            print("\n[Step 7] Đang đồng bộ file backup mới nhất lên Drive...")
            if os.path.exists(SOURCE_DIR):
                files = [os.path.join(SOURCE_DIR, f) for f in os.listdir(SOURCE_DIR) if os.path.isfile(os.path.join(SOURCE_DIR, f))]
                if files:
                    latest = max(files, key=os.path.getmtime)
                    os.makedirs(DRIVE_DIR, exist_ok=True)
                    self.copy_with_progress(latest, os.path.join(DRIVE_DIR, os.path.basename(latest)))
                else: print("   [!] Không thấy file backup.")
            else: print(f"   [!] Không thể truy cập {SOURCE_DIR}")

            print(f"\n[+] HOÀN TẤT QUY TRÌNH: {datetime.datetime.now()}")
            input("\nNhấn phím ENTER để đóng...")

        except Exception as e:
            print(f"!! Lỗi: {e}")
            input("\nNhấn ENTER để thoát...")

if __name__ == "__main__":
    bot = autoBackupSMILE()
    bot.run()
