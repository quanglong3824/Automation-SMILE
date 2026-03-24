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
        """Sao chép file kèm hiển thị tiến trình % và xử lý lỗi Permission"""
        MAX_RETRIES = 3
        RETRY_DELAY = 5
        
        for attempt in range(MAX_RETRIES):
            try:
                total_size = os.path.getsize(src)
                copied = 0
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                
                # Kiểm tra nếu file đích đã tồn tại và đang bị khóa (thường do Drive đang sync)
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
                    print(f"\n   [!] Lỗi Permission (Error 13). Có thể file đang bị lock. Thử lại sau {RETRY_DELAY}s... ({attempt+1}/{MAX_RETRIES})")
                    time.sleep(RETRY_DELAY)
                else:
                    print(f"\n   [x] Không thể ghi file sau {MAX_RETRIES} lần thử. Lỗi: {e}")
                    # Thử phương thức copy thay thế của shutil như phương án cuối cùng
                    try:
                        print("   --> Thử dùng phương thức shutil.copy2...")
                        shutil.copy2(src, dst)
                        print("   [OK] Đã hoàn tất bằng shutil.copy2.")
                        return True
                    except Exception as e2:
                        print(f"   [x] Thất bại hoàn toàn: {e2}")
                        return False
            except Exception as e:
                print(f"\n   [x] Lỗi không xác định khi copy: {e}")
                return False
        return False

    def run(self):
        try:
            # STEP 0: KIỂM TRA ĐƯỜNG DẪN DRIVE VÀ REMOTE
            print("\n[Step 0] Kiểm tra kết nối folder Remote và Google Drive...")
            drive_path = self.find_google_drive_path()
            
            if not drive_path:
                print("\n[!] LỖI: Không tìm thấy ứng dụng Google Drive hoặc thư mục 'SMILE BACKUP' trên máy.")
                print("--> Vui lòng đảm bảo Google Drive Desktop đang chạy và đã ánh xạ ổ đĩa (thường là ổ G:).")
                input("\nNhấn ENTER để thoát...")
                return

            if not os.path.exists(SOURCE_DIR):
                print(f"\n[!] LỖI: Không thể truy cập ổ mạng Remote: {SOURCE_DIR}")
                print("--> Hãy kiểm tra lại kết nối mạng hoặc quyền truy cập vào thư mục chia sẻ.")
                input("\nNhấn ENTER để thoát...")
                return

            print(f"   [OK] Đã kết nối Drive: {drive_path}")
            print(f"   [OK] Đã kết nối Remote: {SOURCE_DIR}")

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
            print("   --> Click More Options")
            mouse.click(button='left', coords=MORE_OPTIONS_COORDS)
            time.sleep(3)

            # Login 2
            top = self.app.top_window()
            if any(w in top.window_text() for w in ["Log", "Pass", "Mật khẩu"]):
                top.set_focus()
                send_keys(PASS + "{ENTER}")
                time.sleep(5)

            # Backup
            print("   --> Click Backup Database")
            mouse.click(button='left', coords=BACKUP_DB_COORDS)
            time.sleep(2)
            send_keys("{ENTER}")

            # Chờ Backup
            wait_time = BACKUP_DURATION + 30
            print(f"\n[Step 6] TỰ ĐỘNG: Đang đợi backup ({wait_time} giây)...")
            for i in range(wait_time, 0, -1):
                if i % 30 == 0: print(f"   --> Còn {i} giây...")
                time.sleep(1)
            
            print("   --> Click OK sau backup")
            mouse.click(button='left', coords=OK_BTN_COORDS)
            time.sleep(2)
            send_keys("0") # Thoát
            time.sleep(3)

            # STEP 7: Đẩy lên Drive
            print("\n[Step 7] Đang đồng bộ file backup mới nhất lên Google Drive...")
            files = [os.path.join(SOURCE_DIR, f) for f in os.listdir(SOURCE_DIR) if os.path.isfile(os.path.join(SOURCE_DIR, f))]
            if files:
                latest = max(files, key=os.path.getmtime)
                self.copy_with_progress(latest, os.path.join(drive_path, os.path.basename(latest)))
            else:
                print("   [-] Không thấy file backup tại remote.")

            print(f"\n[+] HOÀN TẤT: {datetime.datetime.now()}")
            input("\nNhấn ENTER để đóng cửa sổ...")

        except Exception as e:
            print(f"!! Lỗi: {e}")
            input("\nNhấn ENTER để thoát...")

if __name__ == "__main__":
    bot = autoBackupSMILE()
    bot.run()
