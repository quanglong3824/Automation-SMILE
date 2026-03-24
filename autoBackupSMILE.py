import time
import json
import os
import shutil
import datetime
import subprocess
import tkinter as tk
import gdown
from pywinauto import Application, mouse
from pywinauto.keyboard import send_keys

# ==================== CONFIG ====================
SMILE_PATH = r"C:\Program Files (x86)\SMILE\SMILEFO.exe"
USER = "IT"
PASS = "123@123a"
CONFIG_FILE = "smile_config.json"

# Cấu hình ổ mạng (Nếu cần User/Pass để vào ổ mạng, hãy điền ở đây)
REMOTE_PATH = r"\\192.168.1.2\smile$"
REMOTE_USER = "" # Ví dụ: "administrator" (để trống nếu không cần)
REMOTE_PASS = "" # Ví dụ: "password123" (để trống nếu không cần)

# Thư mục Google Drive trên máy (Thường là đường dẫn đồng bộ của Drive Desktop)
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

    def connect_network_drive(self):
        """Tự động kết nối tới ổ mạng nếu chưa có kết nối"""
        print(f"\n[Step 0.5] Đang kiểm tra kết nối tới ổ mạng {REMOTE_PATH}...")
        try:
            if os.path.exists(REMOTE_PATH):
                print("   [OK] Ổ mạng đã sẵn sàng.")
                return True
            
            print("   [-] Không thấy ổ mạng, đang thử lệnh 'net use' để kết nối...")
            cmd = f'net use "{REMOTE_PATH}"'
            if REMOTE_USER and REMOTE_PASS:
                cmd += f' /user:{REMOTE_USER} {REMOTE_PASS}'
            
            subprocess.run(cmd, shell=True, capture_output=True)
            time.sleep(2)
            
            if os.path.exists(REMOTE_PATH):
                print("   [OK] Đã kết nối thành công tới ổ mạng.")
                return True
            else:
                print(f"   [!] LỖI: Không thể kết nối tới {REMOTE_PATH}. Vui lòng Map Drive thủ công.")
                return False
        except Exception as e:
            print(f"   [!] Lỗi khi kết nối ổ mạng: {e}")
            return False

    def push_to_drive(self):
        """Kéo file từ ổ mạng và đẩy lên Drive"""
        print(f"\n[Step 7] Đang đồng bộ file backup lên Drive...")
        try:
            if not os.path.exists(REMOTE_PATH):
                print(f"   [!] Lỗi: Không tìm thấy ổ mạng {REMOTE_PATH}.")
                return

            files = [os.path.join(REMOTE_PATH, f) for f in os.listdir(REMOTE_PATH) if os.path.isfile(os.path.join(REMOTE_PATH, f))]
            if not files: return
            latest_file = max(files, key=os.path.getmtime)
            file_name = os.path.basename(latest_file)

            os.makedirs(DRIVE_DIR, exist_ok=True)
            shutil.copy2(latest_file, os.path.join(DRIVE_DIR, file_name))
            print(f"   [OK] Đã đẩy file {file_name} lên Drive!")
        except Exception as e:
            print(f"   [!] Lỗi đồng bộ: {e}")

    def run(self):
        try:
            # Step 0.5: Kết nối mạng trước
            self.connect_network_drive()

            print(f"\n--- BẮT ĐẦU: {datetime.datetime.now()} ---")
            
            # Step 1: Mở SMILE
            self.app = Application(backend="win32").start(SMILE_PATH)
            time.sleep(10)
            dlg = self.app.window(title_re=".*Log.*In.*")
            if dlg.exists():
                dlg.set_focus()
                send_keys("^a{BACKSPACE}" + USER + "{TAB}" + PASS + "{ENTER}")
                time.sleep(15)

            # Step 2: Popup
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

            # Step 5: Backup
            if not self.config.get("backup_db"):
                self.config["backup_db"] = VisualPicker("Backup Database").selected_coords
                self.save_config()
            mouse.click(button='left', coords=tuple(self.config["backup_db"]))
            time.sleep(2)
            send_keys("{ENTER}")
            
            # Step 6: Chờ 2 phút
            print("\n[Step 6] Chờ 2 phút để hoàn tất...")
            time.sleep(120)
            if self.app: self.app.kill()

            # Step 7: Sync Drive
            self.push_to_drive()
            
            print(f"\n[+] HOÀN TẤT: {datetime.datetime.now()}")

        except Exception as e:
            print(f"!! Lỗi: {e}")

if __name__ == "__main__":
    bot = autoBackupSMILE()
    bot.run()
