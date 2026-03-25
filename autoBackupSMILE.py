import time
import json
import os
import shutil
import datetime
import tkinter as tk
import ctypes
import subprocess
import threading
from pywinauto import Application, mouse
from pywinauto.keyboard import send_keys

# ==================== CONFIG ====================
SMILE_PATH = r"C:\Program Files (x86)\SMILE\SMILEFO.exe"
USER = "IT"
PASS = "123@123a"

# TỌA ĐỘ VÀ THÔNG SỐ CỐ ĐỊNH
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
            # Thiết kế thanh thông báo
            width = self.overlay.winfo_screenwidth()
            self.overlay.geometry(f"{width}x40+0+0")
            self.overlay.overrideredirect(True) # Xóa thanh tiêu đề
            self.overlay.attributes("-topmost", True) # Luôn trên cùng
            self.overlay.configure(bg='red')
            
            label = tk.Label(self.overlay, 
                            text="⚠️ HỆ THỐNG ĐANG TỰ ĐỘNG BACKUP SMILE - VUI LÒNG KHÔNG CHẠM VÀO CHUỘT/BÀN PHÍM ⚠️", 
                            fg="white", bg="red", font=("Arial", 14, "bold"))
            label.pack(expand=True)
            self.overlay.mainloop()

        self.overlay_thread = threading.Thread(target=create_overlay, daemon=True)
        self.overlay_thread.start()
        print("   [!] Đang hiển thị cảnh báo trên màn hình.")

    def hide_warning_overlay(self):
        """Tắt thanh thông báo"""
        if self.overlay:
            self.overlay.after(0, self.overlay.destroy)
            print("   [OK] Đã tắt cảnh báo màn hình.")

    def focus_terminal(self):
        """Đưa cửa sổ Terminal lên vị trí cao nhất (Topmost)"""
        try:
            hWnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hWnd:
                # SW_RESTORE = 9, HWND_TOPMOST = -1
                ctypes.windll.user32.ShowWindow(hWnd, 9)
                ctypes.windll.user32.SetForegroundWindow(hWnd)
                ctypes.windll.user32.SetWindowPos(hWnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002) 
                print("   --> Đã đưa Terminal lên trên cùng để theo dõi.")
        except Exception as e:
            print(f"   [!] Không thể đưa terminal lên đầu: {e}")

    def kill_smile(self):
        """Kiểm tra và đóng SMILE nếu đang chạy để đảm bảo khởi động sạch"""
        print("   --> Kiểm tra và đóng SMILE FO nếu đang chạy...")
        try:
            subprocess.run("taskkill /F /IM SMILEFO.exe /T", shell=True, capture_output=True)
            time.sleep(2)
        except Exception:
            pass

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
        if os.path.exists(os.path.dirname(default_path)):
            return default_path
            
        return None

    def copy_with_progress(self, src, dst):
        """Sao chép file kèm hiển thị tiến trình % và xử lý lỗi Permission"""
        MAX_RETRIES = 3
        RETRY_DELAY = 5
        
        for attempt in range(MAX_RETRIES):
            try:
                total_size = os.path.getsize(src)
                copied = 0
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                
                if os.path.exists(dst):
                    try:
                        with open(dst, 'ab') as f: pass
                    except PermissionError:
                        print(f"   [!] File đích đang bị khóa bởi ứng dụng khác (Drive sync?). Thử lại sau {RETRY_DELAY}s... ({attempt+1}/{MAX_RETRIES})")
                        time.sleep(RETRY_DELAY)
                        continue

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
                return True
            except PermissionError as e:
                if attempt < MAX_RETRIES - 1:
                    print(f"\n   [!] Lỗi Permission (Error 13). Thử lại sau {RETRY_DELAY}s... ({attempt+1}/{MAX_RETRIES})")
                    time.sleep(RETRY_DELAY)
                else:
                    print(f"\n   [x] Không thể ghi file. Lỗi: {e}")
                    try:
                        shutil.copy2(src, dst)
                        return True
                    except: return False
            except Exception as e:
                return False
        return False

    def run(self):
        try:
            # HIỂN THỊ CẢNH BÁO TRÊN MÀN HÌNH
            self.show_warning_overlay()

            # STEP 0: KIỂM TRA ĐƯỜNG DẪN
            print("\n[Step 0] Kiểm tra kết nối folder Remote và Google Drive...")
            drive_path = self.find_google_drive_path()
            
            if not drive_path or not os.path.exists(SOURCE_DIR):
                print("\n[!] LỖI: Không tìm thấy Drive hoặc Remote.")
                return

            print(f"   [OK] Đã kết nối Drive: {drive_path}")
            print(f"   [OK] Đã kết nối Remote: {SOURCE_DIR}")

            # STEP 1-5: SMILE FO
            print(f"\n--- BẮT ĐẦU QUY TRÌNH SMILE: {datetime.datetime.now()} ---")
            self.kill_smile()
            
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
            mouse.click(button='left', coords=MORE_OPTIONS_COORDS)
            time.sleep(3)

            # Login 2
            top = self.app.top_window()
            if any(w in top.window_text() for w in ["Log", "Pass", "Mật khẩu"]):
                top.set_focus()
                send_keys(PASS + "{ENTER}")
                time.sleep(5)

            # Backup
            mouse.click(button='left', coords=BACKUP_DB_COORDS)
            time.sleep(2)
            send_keys("{ENTER}")

            # Chờ Backup
            wait_time = BACKUP_DURATION + 30
            print(f"\n[Step 6] TỰ ĐỘNG: Đang đợi backup ({wait_time} giây)...")
            for i in range(wait_time, 0, -1):
                if i % 30 == 0: print(f"   --> Còn {i} giây...")
                time.sleep(1)
            
            mouse.click(button='left', coords=OK_BTN_COORDS)
            time.sleep(2)
            send_keys("0") # Thoát
            time.sleep(3)

            # STEP 7: Đẩy lên Drive
            self.focus_terminal()
            print("\n[Step 7] Đang đồng bộ file backup mới nhất lên Google Drive...")
            files = [os.path.join(SOURCE_DIR, f) for f in os.listdir(SOURCE_DIR) if os.path.isfile(os.path.join(SOURCE_DIR, f))]
            if files:
                latest = max(files, key=os.path.getmtime)
                base, ext = os.path.splitext(os.path.basename(latest))
                new_filename = f"{base}_BOT{ext}"
                self.copy_with_progress(latest, os.path.join(drive_path, new_filename))
            else:
                print("   [-] Không thấy file backup tại remote.")

            print(f"\n[+] HOÀN TẤT: {datetime.datetime.now()}")
            
        except Exception as e:
            print(f"!! Lỗi: {e}")
        finally:
            self.hide_warning_overlay()
            input("\nNhấn ENTER để đóng cửa sổ...")

if __name__ == "__main__":
    bot = autoBackupSMILE()
    bot.run()


if __name__ == "__main__":
    bot = autoBackupSMILE()
    bot.run()


if __name__ == "__main__":
    bot = autoBackupSMILE()
    bot.run()
