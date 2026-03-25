import time
import json
import os
import shutil
import datetime
import tkinter as tk
import ctypes
import subprocess
import threading
from pywinauto import Application, mouse, timings
from pywinauto.keyboard import send_keys

# Tối ưu hóa tốc độ phản hồi của pywinauto
timings.Timings.fast()

# ==================== CONFIG ====================
SMILE_PATH = r"C:\Program Files (x86)\SMILE\SMILEFO.exe"
USER = "IT"
PASS = "123@123a"

# TỌA ĐỘ VÀ THÔNG SỐ CỐ ĐỊNH (Tọa độ tương đối trong cửa sổ SMILE)
MORE_OPTIONS_COORDS = (759, 408)
BACKUP_DB_COORDS = (800, 324)
OK_BTN_COORDS = (662, 447)
BACKUP_DURATION = 5

# ĐƯỜNG DẪN Ổ MẠNG SMILE (Remote)
SOURCE_DIR = r"\\192.168.1.2\smile$"
# ================================================

class autoBackupSMILE:
    def __init__(self):
        self.app = None
        self.overlay = None

    def show_warning_overlay(self):
        """Hiển thị thanh thông báo màu đỏ trên cùng màn hình"""
        def create_overlay():
            self.overlay = tk.Tk()
            self.overlay.title("SMILE BACKUP WARNING")
            width = self.overlay.winfo_screenwidth()
            # Đặt ở sát mép trên, cao 35px
            self.overlay.geometry(f"{width}x35+0+0")
            self.overlay.overrideredirect(True)
            self.overlay.attributes("-topmost", True)
            self.overlay.configure(bg='red')
            
            label = tk.Label(self.overlay, 
                            text="⚠️ HỆ THỐNG ĐANG TỰ ĐỘNG BACKUP SMILE - VUI LÒNG KHÔNG THAO TÁC ⚠️", 
                            fg="white", bg="red", font=("Arial", 12, "bold"))
            label.pack(expand=True)
            self.overlay.mainloop()

        self.overlay_thread = threading.Thread(target=create_overlay, daemon=True)
        self.overlay_thread.start()
        print("   [!] Đang hiển thị cảnh báo trên màn hình.")

    def hide_warning_overlay(self):
        """Tắt thanh thông báo"""
        if self.overlay:
            try:
                self.overlay.after(0, self.overlay.destroy)
                print("   [OK] Đã tắt cảnh báo màn hình.")
            except: pass

    def robust_click(self, window, coords):
        """Click chuột nhanh hơn (Giảm thời gian chờ)"""
        try:
            self.log_message(f"   [Action] Click {coords}...")
            window.set_focus()
            # Giảm thời gian chờ xuống mức tối thiểu
            time.sleep(0.3)
            window.click_input(coords=coords)
            time.sleep(0.5)
        except Exception as e:
            self.log_message(f"   [!] Lỗi click {coords}: {e}")
            try:
                window.click(coords=coords)
            except: pass

    def focus_terminal(self):
        """Đưa cửa sổ Terminal lên vị trí cao nhất (Topmost)"""
        try:
            hWnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hWnd:
                ctypes.windll.user32.ShowWindow(hWnd, 9) # SW_RESTORE
                ctypes.windll.user32.SetForegroundWindow(hWnd)
                ctypes.windll.user32.SetWindowPos(hWnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002) 
                print("   --> Đã đưa Terminal lên trên cùng.")
        except Exception: pass

    def kill_smile(self):
        """Kiểm tra và đóng SMILE nếu đang chạy để đảm bảo khởi động sạch"""
        print("   --> Kiểm tra và đóng SMILE FO nếu đang chạy...")
        try:
            subprocess.run("taskkill /F /IM SMILEFO.exe /T", shell=True, capture_output=True)
            time.sleep(1)
        except Exception: pass

    def find_google_drive_path(self):
        """Tự động tìm kiếm ổ đĩa hoặc thư mục Google Drive trên Windows"""
        if os.path.exists(r"G:\My Drive"):
            return r"G:\My Drive\SMILE BACKUP"
        import string
        for letter in string.ascii_uppercase[7:]: # H to Z
            path = f"{letter}:\\My Drive"
            if os.path.exists(path):
                return f"{letter}:\\My Drive\\SMILE BACKUP"
        user_profile = os.environ.get("USERPROFILE")
        default_path = os.path.join(user_profile, "Google Drive", "My Drive", "SMILE BACKUP")
        if os.path.exists(os.path.dirname(default_path)): return default_path
        return None

    def copy_with_progress(self, src, dst):
        """Sao chép file kèm hiển thị tiến trình %"""
        MAX_RETRIES = 3
        RETRY_DELAY = 5
        for attempt in range(MAX_RETRIES):
            try:
                total_size = os.path.getsize(src)
                copied = 0
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                with open(src, 'rb') as fsrc, open(dst, 'wb') as fdst:
                    print(f"   --> Đang đẩy file: {os.path.basename(dst)}") # Hiển thị tên file đích (đã có _BOT)
                    while True:
                        chunk = fsrc.read(1024 * 1024)
                        if not chunk: break
                        fdst.write(chunk)
                        copied += len(chunk)
                        percent = (copied / total_size) * 100
                        print(f"\r   [Đang tải lên Drive]: {percent:.1f}%", end="")
                print(f"\n   [OK] Đã hoàn tất đẩy file lên Drive.")
                return True
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                    continue
                return False
        return False

    def log_message(self, message):
        """In ra màn hình và đồng thời ghi vào tệp backup_log.txt"""
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{now}] {message}"
        print(message)
        with open("backup_log.txt", "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")

    def run(self):
        try:
            self.show_warning_overlay()
            self.log_message("\n[Step 0] Kiểm tra kết nối...")
            drive_path = self.find_google_drive_path()
            if not drive_path or not os.path.exists(SOURCE_DIR):
                self.log_message("[!] LỖI: Không tìm thấy Drive hoặc Remote.")
                return

            # STEP 1: Khởi động SMILE
            self.log_message(f"--- BẮT ĐẦU QUY TRÌNH SMILE ---")
            self.kill_smile()
            self.app = Application(backend="win32").start(SMILE_PATH)
            time.sleep(7)
            
            # Login 1
            main_window = self.app.top_window()
            main_window.set_focus()
            
            dlg = self.app.window(title_re=".*Log.*In.*")
            if dlg.exists():
                dlg.set_focus()
                send_keys("^a{BACKSPACE}" + USER + "{TAB}" + PASS + "{ENTER}")
                time.sleep(10)
            send_keys("{ESC}")
            time.sleep(1)

            # Lấy cửa sổ chính sau khi Login
            main_window = self.app.top_window()
            main_window.set_focus()

            # More Options
            self.robust_click(main_window, MORE_OPTIONS_COORDS)
            time.sleep(1)

            # Login 2 (nếu có)
            top = self.app.top_window()
            if any(w in top.window_text() for w in ["Log", "Pass", "Mật khẩu"]):
                top.set_focus()
                send_keys(PASS + "{ENTER}")
                time.sleep(2)

            # Backup
            self.robust_click(main_window, BACKUP_DB_COORDS)
            time.sleep(1)
            send_keys("{ENTER}")

            # Chờ Backup
            wait_time = BACKUP_DURATION + 30
            self.log_message(f"[Step 6] TỰ ĐỘNG: Đang đợi backup ({wait_time} giây)...")
            for i in range(wait_time, 0, -1):
                if i % 30 == 0: self.log_message(f"   --> Còn {i} giây...")
                time.sleep(1)
            
            self.log_message("   --> Click OK sau backup")
            main_window = self.app.top_window()
            self.robust_click(main_window, OK_BTN_COORDS)
            time.sleep(1)
            send_keys("0") # Thoát
            time.sleep(1)

            # STEP 7: Đẩy lên Drive
            self.focus_terminal()
            self.log_message("[Step 7] Đang đồng bộ file backup mới nhất lên Google Drive...")
            files = [os.path.join(SOURCE_DIR, f) for f in os.listdir(SOURCE_DIR) if os.path.isfile(os.path.join(SOURCE_DIR, f))]
            if files:
                latest = max(files, key=os.path.getmtime)
                base, ext = os.path.splitext(os.path.basename(latest))
                new_filename = f"{base}_BOT{ext}"
                self.log_message(f"   --> Đang tải lên file: {new_filename}")
                self.copy_with_progress(latest, os.path.join(drive_path, new_filename))
            else:
                self.log_message("   [-] Không thấy file backup tại remote.")

            self.log_message(f"[+] HOÀN TẤT BACKUP SMILE.")
            
            # Đóng SMILE sau khi hoàn tất quy trình
            self.kill_smile()
            
        except Exception as e:
            self.log_message(f"!! Lỗi: {e}")
            time.sleep(5) # Đợi 5s để xem lỗi nếu có trước khi tự đóng
        finally:
            self.hide_warning_overlay()
            self.log_message("\n[!] Hệ thống sẽ tự động đóng toàn bộ Terminal trong 10 giây...")
            time.sleep(10)
            # Lệnh đóng toàn bộ cửa sổ Command Prompt (Terminal)
            subprocess.run("taskkill /F /IM cmd.exe", shell=True)

if __name__ == "__main__":
    bot = autoBackupSMILE()
    bot.run()
