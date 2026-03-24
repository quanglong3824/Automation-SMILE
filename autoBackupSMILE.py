import time
import json
import os
import shutil
import datetime
import tkinter as tk
from pywinauto import Application, mouse
from pywinauto.keyboard import send_keys

# ==================== CONFIG ====================
SMILE_PATH = r"C:\Program Files (x86)\SMILE\SMILEFO.exe"
USER = "IT"
PASS = "123@123a"
CONFIG_FILE = "smile_config.json"

# Cấu hình đường dẫn Backup
SOURCE_DIR = r"\\192.168.1.2\smile$"
# Thay đổi đường dẫn này thành thư mục Google Drive thực tế trên máy bạn
DRIVE_DIR = r"C:\Users\YourUser\Google Drive\SMILE_Backup" 
# ================================================

class VisualPicker:
    """Lớp tạo màn hình trong suốt để người dùng click chọn tọa độ"""
    def __init__(self, label):
        self.root = tk.Tk()
        self.root.title("Chỉ điểm tọa độ")
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
        print(f"--> Đã lưu tọa độ vào {CONFIG_FILE}")

    def get_user_click_visual(self, label):
        print(f"--> Đang chờ bạn chỉ điểm vị trí: {label}")
        picker = VisualPicker(label)
        return picker.selected_coords

    def sync_to_drive(self):
        """Tìm file mới nhất từ ổ mạng và copy sang Google Drive"""
        print(f"\n[Step 7] Đang quét file mới nhất tại {SOURCE_DIR}...")
        try:
            # Kiểm tra xem thư mục nguồn có tồn tại không
            if not os.path.exists(SOURCE_DIR):
                print(f"   [!] Lỗi: Không thể truy cập đường dẫn {SOURCE_DIR}")
                return

            # Lấy danh sách tất cả các file trong thư mục nguồn
            files = [os.path.join(SOURCE_DIR, f) for f in os.listdir(SOURCE_DIR) if os.path.isfile(os.path.join(SOURCE_DIR, f))]
            
            if not files:
                print("   [-] Không tìm thấy file nào trong thư mục nguồn.")
                return

            # Tìm file có thời gian sửa đổi (mtime) mới nhất
            latest_file = max(files, key=os.path.getmtime)
            file_name = os.path.basename(latest_file)
            
            print(f"   [+] Đã tìm thấy file mới nhất: {file_name}")
            print(f"   --> Thời gian tạo: {datetime.datetime.fromtimestamp(os.path.getmtime(latest_file))}")

            # Kiểm tra thư mục Drive
            if not os.path.exists(DRIVE_DIR):
                os.makedirs(DRIVE_DIR)
                print(f"   [+] Đã tạo thư mục Drive: {DRIVE_DIR}")

            # Thực hiện copy
            dest_path = os.path.join(DRIVE_DIR, file_name)
            print(f"   --> Đang sao chép lên Drive...")
            shutil.copy2(latest_file, dest_path)
            print(f"   [OK] Đã đẩy file lên Drive thành công!")

        except Exception as e:
            print(f"   [!] Lỗi khi đồng bộ Drive: {e}")

    def run(self):
        try:
            print(f"--- BẮT ĐẦU: {datetime.datetime.now()} ---")
            
            # BƯỚC 1: Khởi động & Đăng nhập 1
            print("Step 1: Khởi động SMILE...")
            self.app = Application(backend="win32").start(SMILE_PATH)
            time.sleep(10)
            
            dlg = self.app.window(title_re=".*Log.*In.*")
            if dlg.exists():
                print("--> Đăng nhập lần 1...")
                dlg.set_focus()
                send_keys("^a{BACKSPACE}" + USER + "{TAB}" + PASS + "{ENTER}")
                time.sleep(15)

            # BƯỚC 2: Xóa Popup
            print("Step 2: Dọn dẹp Popup thông báo...")
            send_keys("{ESC}")
            time.sleep(3)

            # BƯỚC 3: More Options
            if not self.config.get("more_options"):
                self.config["more_options"] = self.get_user_click_visual("More Options")
                self.save_config()
            
            x, y = self.config["more_options"]
            mouse.click(button='left', coords=(x, y))
            time.sleep(3)

            # BƯỚC 4: Tự động Đăng nhập lần 2
            print("Step 4: Đang xác thực lần 2...")
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

            # BƯỚC 5: Backup Database & Enter
            if not self.config.get("backup_db"):
                self.config["backup_db"] = self.get_user_click_visual("Backup Database")
                self.save_config()

            print("Step 5: Click 'Backup Database' và nhấn ENTER...")
            x, y = self.config["backup_db"]
            mouse.click(button='left', coords=(x, y))
            time.sleep(2)
            send_keys("{ENTER}")
            
            # BƯỚC 6: Đợi 3 phút và đóng app
            print("\n[Step 6] ĐANG CHẠY SAO LƯU... Vui lòng đợi 3 phút.")
            for i in range(180, 0, -1):
                if i % 30 == 0:
                    print(f"--> Còn lại {i} giây...")
                time.sleep(1)
            
            print("--> Đóng SMILE...")
            if self.app:
                self.app.kill()

            # BƯỚC 7: Đồng bộ file lên Drive (Mới)
            self.sync_to_drive()
            
            print(f"\n[+] HOÀN TẤT TOÀN BỘ QUY TRÌNH: {datetime.datetime.now()}")

        except Exception as e:
            print(f"!! Lỗi hệ thống: {e}")

if __name__ == "__main__":
    bot = autoBackupSMILE()
    bot.run()
