import time
import json
import os
import datetime
import tkinter as tk
from pywinauto import Application, mouse
from pywinauto.keyboard import send_keys

# ==================== CONFIG ====================
SMILE_PATH = r"C:\Program Files (x86)\SMILE\SMILEFO.exe"
USER = "IT"
PASS = "123@123a"
CONFIG_FILE = "smile_config.json"
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
        self.canvas = tk.Canvas(self.root, cursor="cross", bg="blue") # Đổi sang màu xanh dương cho dễ nhìn
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
        return {"more_options": None, "backup_db": None, "ok_btn": None}

    def save_config(self):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=4)
        print(f"--> Đã lưu tọa độ vào {CONFIG_FILE}")

    def get_user_click_visual(self, label):
        print(f"--> Đang chờ bạn chỉ điểm vị trí: {label}")
        picker = VisualPicker(label)
        return picker.selected_coords

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

            # BƯỚC 3: More Options (Chỉ điểm/Click)
            if not self.config.get("more_options"):
                self.config["more_options"] = self.get_user_click_visual("More Options")
                self.save_config()
            
            print("Step 3: Click 'More Options'...")
            x, y = self.config["more_options"]
            mouse.click(button='left', coords=(x, y))
            time.sleep(3)

            # BƯỚC 4: Tự động Đăng nhập lần 2 (Chỉ nhập PASS)
            print("Step 4: Đang tự động xác thực mật khẩu lần 2...")
            # Đợi bảng Login 2 xuất hiện
            auth_wait_start = time.time()
            while time.time() - auth_wait_start < 10:
                top_win = self.app.top_window()
                if any(word in top_win.window_text() for word in ["Log", "Pass", "Mật khẩu"]):
                    print("   [+] Đã thấy bảng xác thực. Đang nhập mật khẩu...")
                    top_win.set_focus()
                    # Vì USER 'IT' đã có sẵn, nhấn TAB để chắc chắn nhảy vào ô Pass (hoặc nhập luôn)
                    send_keys("{TAB}" + PASS + "{ENTER}")
                    time.sleep(5)
                    break
                time.sleep(1)

            # BƯỚC 5: Backup Database (Chỉ điểm/Click)
            if not self.config.get("backup_db"):
                self.config["backup_db"] = self.get_user_click_visual("Backup Database")
                self.save_config()

            print("Step 5: Click 'Backup Database'...")
            x, y = self.config["backup_db"]
            mouse.click(button='left', coords=(x, y))
            
            # BƯỚC 6: Đợi nút OK
            print("Step 6: Đang chờ Database xử lý (60s)...")
            time.sleep(60) # Chờ backup chạy
            
            if not self.config.get("ok_btn"):
                self.config["ok_btn"] = self.get_user_click_visual("Nút OK Hoàn tất")
                self.save_config()
            
            print("--> Click OK để hoàn tất.")
            x, y = self.config["ok_btn"]
            mouse.click(button='left', coords=(x, y))
            
            print("\n[+] HOÀN TẤT QUY TRÌNH!")

        except Exception as e:
            print(f"!! Lỗi hệ thống: {e}")

if __name__ == "__main__":
    bot = autoBackupSMILE()
    bot.run()
