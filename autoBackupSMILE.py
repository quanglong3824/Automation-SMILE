import time
import json
import os
import sys
import shutil
import datetime
import tkinter as tk
import ctypes
import subprocess
import threading
from pywinauto import Application, mouse, timings
from pywinauto.keyboard import send_keys

# ==================== LOAD CONFIG ====================
# Ho tro ca chay tu Python source va PyInstaller EXE
if getattr(sys, 'frozen', False):
    SCRIPT_DIR = os.path.dirname(sys.executable)
else:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "config.json")

def load_config():
    """Đọc cấu hình từ file config.json"""
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[!] Không tìm thấy file cấu hình: {CONFIG_FILE}")
        print("[!] Vui lòng tạo file config.json theo mẫu. Chương trình sẽ thoát.")
        time.sleep(10)
        raise SystemExit(1)
    except json.JSONDecodeError as e:
        print(f"[!] Lỗi đọc file cấu hình: {e}")
        print("[!] Vui lòng kiểm tra cú pháp JSON. Chương trình sẽ thoát.")
        time.sleep(10)
        raise SystemExit(1)

# Tải cấu hình
CFG = load_config()

# Tối ưu hóa tốc độ phản hồi của pywinauto
timings.Timings.fast()

class autoBackupSMILE:
    def __init__(self):
        self.app = None
        self.overlay = None
        # Load config values vào instance
        self.SMILE_PATH = CFG["SMILE_PATH"]
        self.USER = CFG["USER"]
        self.PASS = CFG["PASS"]
        self.SOURCE_DIR = CFG["SOURCE_DIR"]
        self.MORE_OPTIONS_COORDS = tuple(CFG["MORE_OPTIONS_COORDS"])
        self.BACKUP_DB_COORDS = tuple(CFG["BACKUP_DB_COORDS"])
        self.OK_BTN_COORDS = tuple(CFG["OK_BTN_COORDS"])
        self.BACKUP_DURATION = CFG["BACKUP_DURATION"]
        self.SMILE_STARTUP_WAIT = CFG["SMILE_STARTUP_WAIT"]
        self.LOGIN_WAIT = CFG["LOGIN_WAIT"]
        self.BACKUP_OK_RETRIES = CFG["BACKUP_OK_RETRIES"]
        self.BACKUP_OK_RETRY_DELAY = CFG["BACKUP_OK_RETRY_DELAY"]
        self.CLICK_RETRIES = CFG["CLICK_RETRIES"]
        self.CLICK_RETRY_DELAY = CFG["CLICK_RETRY_DELAY"]
        self.WINDOW_GET_TIMEOUT = CFG["WINDOW_GET_TIMEOUT"]
        self.WINDOW_GET_RETRY_INTERVAL = CFG["WINDOW_GET_RETRY_INTERVAL"]
        self.SMILE_EXIT_KEY = CFG["SMILE_EXIT_KEY"]
        self.TERMINAL_CLOSE_DELAY = CFG["TERMINAL_CLOSE_DELAY"]

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

    # ===================== Desktop Active Check =====================
    def is_desktop_active(self):
        """Kiểm tra desktop có khả dụng không (phát hiện RDP ngắt hoặc màn hình khóa)"""
        try:
            # Kiểm tra explorer.exe đang chạy
            result = subprocess.run('tasklist /FI "IMAGENAME eq explorer.exe"',
                                  shell=True, capture_output=True, text=True)
            if "explorer.exe" not in result.stdout:
                self.log_message("   [!] Desktop không khả dụng (không thấy explorer.exe)")
                return False

            # Kiểm tra foreground window
            hwinst = ctypes.windll.user32.GetForegroundWindow()
            if hwinst == 0:
                self.log_message("   [!] Foreground window = 0, thử kích hoạt desktop...")
                self._wake_desktop()
                time.sleep(2)
                hwinst = ctypes.windll.user32.GetForegroundWindow()
                if hwinst == 0:
                    self.log_message("   [!] Desktop vẫn không khả dụng sau khi thử kích hoạt")
                    return False
            return True
        except Exception as e:
            self.log_message(f"   [!] Lỗi kiểm tra desktop: {e}")
            return True  # Tiếp tục nếu không chắc chắn

    def _wake_desktop(self):
        """Kích hoạt desktop (phòng RDP ngắt hoặc màn hình khóa)"""
        try:
            # Gửi phím SHIFT để "đánh thức" desktop
            ctypes.windll.user32.keybd_event(0x10, 0, 0, 0)  # SHIFT down
            time.sleep(0.1)
            ctypes.windll.user32.keybd_event(0x10, 0, 2, 0)  # SHIFT up
            time.sleep(0.5)
        except: pass

    # ===================== Ensure Foreground =====================
    def ensure_foreground(self, window):
        """Đảm bảo cửa sổ lên foreground bằng nhiều kỹ thuật (Fix SetForegroundWindow)"""
        # Phương pháp 1: set_focus bình thường
        try:
            window.set_focus()
            time.sleep(0.3)
            return True
        except: pass

        # Phương pháp 2: AttachThreadInput workaround
        try:
            hwnd = window.handle if hasattr(window, 'handle') else window
            current_thread = ctypes.windll.kernel32.GetCurrentThreadId()
            target_thread = ctypes.windll.user32.GetWindowThreadProcessId(hwnd, None)

            if current_thread != target_thread and target_thread != 0:
                ctypes.windll.user32.AttachThreadInput(current_thread, target_thread, True)
                # Gửi ALT để bypass foreground lock
                ctypes.windll.user32.keybd_event(0x12, 0, 0, 0)  # ALT down
                ctypes.windll.user32.keybd_event(0x12, 0, 2, 0)  # ALT up
                time.sleep(0.1)
                ctypes.windll.user32.SetForegroundWindow(hwnd)
                ctypes.windll.user32.AttachThreadInput(current_thread, target_thread, False)
                time.sleep(0.3)
                return True
        except: pass

        # Phương pháp 3: Minimize rồi Restore + SetForegroundWindow
        try:
            hwnd = window.handle if hasattr(window, 'handle') else window
            ctypes.windll.user32.ShowWindow(hwnd, 6)  # SW_MINIMIZE
            time.sleep(0.2)
            ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
            ctypes.windll.user32.SetForegroundWindow(hwnd)
            time.sleep(0.3)
            return True
        except: pass

        return False

    # ===================== Robust Click =====================
    def robust_click(self, window, coords, max_retries=None, retry_delay=None):
        """Click chuột với retry và nhiều phương pháp fallback"""
        if max_retries is None:
            max_retries = self.CLICK_RETRIES
        if retry_delay is None:
            retry_delay = self.CLICK_RETRY_DELAY

        for attempt in range(max_retries):
            # Phương pháp 1: click_input (ưu tiên - chính xác nhất)
            try:
                self.log_message(f"   [Action] Click {coords} (lần thử {attempt+1}/{max_retries})...")
                self.ensure_foreground(window)
                time.sleep(0.3)
                window.click_input(coords=coords)
                time.sleep(0.5)
                return True
            except Exception as e:
                self.log_message(f"   [!] Lỗi click_input {coords}: {e}")

            # Phương pháp 2: click() method (kém chính xác hơn nhưng bỏ qua trạng thái window)
            try:
                self.log_message(f"   [Action] Thử click() fallback...")
                window.click(coords=coords)
                time.sleep(0.5)
                return True
            except Exception as e2:
                self.log_message(f"   [!] Lỗi click() fallback: {e2}")

            # Phương pháp 3: ctypes mouse_event (độc lập với pywinauto)
            try:
                self.log_message(f"   [Action] Thử ctypes mouse_event...")
                rect = window.rectangle()
                abs_x = rect.left + coords[0]
                abs_y = rect.top + coords[1]
                ctypes.windll.user32.SetCursorPos(abs_x, abs_y)
                time.sleep(0.1)
                ctypes.windll.user32.mouse_event(0x0002, 0, 0, 0, 0)  # LEFTDOWN
                ctypes.windll.user32.mouse_event(0x0004, 0, 0, 0, 0)  # LEFTUP
                time.sleep(0.5)
                return True
            except Exception as e3:
                self.log_message(f"   [!] Lỗi ctypes mouse: {e3}")

            # Thử lại sau delay
            if attempt < max_retries - 1:
                self.log_message(f"   [...] Thử lại click sau {retry_delay} giây...")
                time.sleep(retry_delay)

        self.log_message(f"   [X] Không thể click {coords} sau {max_retries} lần thử")
        return False

    # ===================== OK Button After Backup =====================
    def click_ok_after_backup(self):
        """Xác nhận OK sau backup bằng nhiều phương pháp, ưu tiên phím ENTER"""
        max_retries = self.BACKUP_OK_RETRIES
        retry_delay = self.BACKUP_OK_RETRY_DELAY

        for attempt in range(max_retries):
            self.log_message(f"   [Action] Xác nhận OK sau backup (lần {attempt+1}/{max_retries})...")

            # Phương pháp 1: Gửi phím ENTER (OK là default button trong dialog)
            try:
                top = self.app.top_window()
                self.ensure_foreground(top)
                time.sleep(0.5)
                send_keys("{ENTER}")
                self.log_message(f"   [OK] Đã gửi ENTER lần {attempt+1}")
                time.sleep(2)

                # Kiểm tra xem dialog đã biến mất chưa
                try:
                    top_after = self.app.top_window()
                    if top_after.window_text() == top.window_text():
                        pass  # Dialog vẫn còn, thử thêm
                    else:
                        self.log_message(f"   [OK] Xác nhận OK thành công (ENTER)!")
                        return True
                except:
                    self.log_message(f"   [OK] Xác nhận OK thành công (ENTER)!")
                    return True
            except Exception as e:
                self.log_message(f"   [!] Lỗi send_keys ENTER: {e}")

            # Phương pháp 2: Click tọa độ OK bằng robust_click
            try:
                top = self.app.top_window()
                result = self.robust_click(top, self.OK_BTN_COORDS, max_retries=1)
                if result:
                    time.sleep(2)
                    self.log_message(f"   [OK] Đã click tọa độ OK lần {attempt+1}")
            except Exception as e:
                self.log_message(f"   [!] Lỗi click OK: {e}")

            # Phương pháp 3: ctypes mouse_event trực tiếp
            try:
                top = self.app.top_window()
                rect = top.rectangle()
                abs_x = rect.left + self.OK_BTN_COORDS[0]
                abs_y = rect.top + self.OK_BTN_COORDS[1]
                ctypes.windll.user32.SetCursorPos(abs_x, abs_y)
                time.sleep(0.1)
                ctypes.windll.user32.mouse_event(0x0002, 0, 0, 0, 0)  # LEFTDOWN
                ctypes.windll.user32.mouse_event(0x0004, 0, 0, 0, 0)  # LEFTUP
                time.sleep(2)
            except: pass

            time.sleep(retry_delay)

        self.log_message(f"   [X] Không thể xác nhận OK sau {max_retries} lần thử, tiếp tục quy trình...")
        return False

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
        """Tự động tìm kiếm thư mục Google Drive dựa trên config"""
        # 1. Kiểm tra các ổ đĩa trong danh sách config
        for drive_path in CFG["GOOGLE_DRIVE_PATHS"]:
            if os.path.exists(drive_path):
                full_path = os.path.join(drive_path, CFG["GOOGLE_DRIVE_SUBFOLDER"])
                self.log_message(f"   [OK] Tìm thấy Google Drive tại: {drive_path}")
                return full_path

        # 2. Kiểm tra đường dẫn USERPROFILE
        user_profile = os.environ.get("USERPROFILE")
        if user_profile:
            default_path = os.path.join(user_profile, CFG["GOOGLE_DRIVE_PROFILE_PATH"])
            if os.path.exists(os.path.dirname(default_path)):
                self.log_message(f"   [OK] Tìm thấy Google Drive tại USERPROFILE")
                return default_path

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
                    print(f"   --> Đang đẩy file: {os.path.basename(dst)}")
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
        log_path = os.path.join(SCRIPT_DIR, "backup_log.txt")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")

    # ===================== Get Window Safe =====================
    def get_main_window_safe(self, timeout=None, retry_interval=None):
        """Lấy cửa sổ chính SMILE với retry (Fix 'No windows for that process')"""
        if timeout is None:
            timeout = self.WINDOW_GET_TIMEOUT
        if retry_interval is None:
            retry_interval = self.WINDOW_GET_RETRY_INTERVAL

        for attempt in range(int(timeout / retry_interval)):
            try:
                main_window = self.app.top_window()
                if main_window.handle:
                    self.log_message(f"   [OK] Đã lấy cửa sổ SMILE (hwnd={main_window.handle})")
                    return main_window
            except Exception as e:
                self.log_message(f"   [!] Lỗi lấy cửa sổ (lần {attempt+1}): {e}")

            # Kiểm tra process SMILE còn chạy không
            try:
                result = subprocess.run('tasklist /FI "IMAGENAME eq SMILEFO.exe"',
                                      shell=True, capture_output=True, text=True)
                if "SMILEFO.exe" not in result.stdout:
                    self.log_message("   [!] Process SMILE không còn chạy!")
                    return None
            except: pass

            time.sleep(retry_interval)

        self.log_message("   [X] Không thể lấy cửa sổ SMILE sau thời gian chờ")
        return None

    def run(self):
        try:
            self.show_warning_overlay()
            self.log_message("\n[Step 0] Kiểm tra kết nối...")

            # Kiểm tra Source Dir
            if not os.path.exists(self.SOURCE_DIR):
                self.log_message(f"[!] LỖI: Không tìm thấy thư mục nguồn: {self.SOURCE_DIR}")
                return

            # Kiểm tra Google Drive
            drive_path = self.find_google_drive_path()
            if not drive_path:
                self.log_message("[!] LỖI: Không tìm thấy Google Drive.")
                return

            # Kiểm tra desktop khả dụng
            if not self.is_desktop_active():
                self.log_message("[!] CẢNH BÁO: Desktop không khả dụng, thử kích hoạt...")
                self._wake_desktop()
                time.sleep(3)
                if not self.is_desktop_active():
                    self.log_message("[!] LỖI: Desktop không khả dụng, không thể tiếp tục.")
                    return

            # STEP 1: Khởi động SMILE
            self.log_message(f"--- BẮT ĐẦU QUY TRÌNH SMILE ---")
            self.kill_smile()
            self.app = Application(backend="win32").start(self.SMILE_PATH)
            time.sleep(self.SMILE_STARTUP_WAIT)

            # Login 1 - với retry
            main_window = self.get_main_window_safe()
            if not main_window:
                self.log_message("[!] LỖI: Không thể lấy cửa sổ SMILE sau khi khởi động!")
                return

            self.ensure_foreground(main_window)

            dlg = self.app.window(title_re=".*Log.*In.*")
            if dlg.exists(timeout=5):
                self.ensure_foreground(dlg)
                send_keys("^a{BACKSPACE}" + self.USER + "{TAB}" + self.PASS + "{ENTER}")
                time.sleep(self.LOGIN_WAIT)
            send_keys("{ESC}")
            time.sleep(1)

            # Lấy cửa sổ chính sau khi Login
            main_window = self.get_main_window_safe(timeout=15, retry_interval=2)
            if not main_window:
                self.log_message("[!] LỖI: Không thể lấy cửa sổ SMILE sau khi login!")
                return

            self.ensure_foreground(main_window)

            # More Options
            self.robust_click(main_window, self.MORE_OPTIONS_COORDS)
            time.sleep(1)

            # Login 2 (nếu có)
            top = self.app.top_window()
            if any(w in top.window_text() for w in ["Log", "Pass", "Mật khẩu"]):
                self.ensure_foreground(top)
                send_keys(self.PASS + "{ENTER}")
                time.sleep(2)

            # Backup
            self.robust_click(main_window, self.BACKUP_DB_COORDS)
            time.sleep(1)
            send_keys("{ENTER}")

            # Chờ Backup
            wait_time = self.BACKUP_DURATION + 30
            self.log_message(f"[Step 6] TỰ ĐỘNG: Đang đợi backup ({wait_time} giây)...")
            for i in range(wait_time, 0, -1):
                if i % 30 == 0: self.log_message(f"   --> Còn {i} giây...")
                time.sleep(1)

            # Click OK sau backup
            self.log_message("   --> Xác nhận OK sau backup...")
            self.click_ok_after_backup()

            time.sleep(1)
            # Thoát SMILE
            for exit_attempt in range(3):
                try:
                    main_window = self.app.top_window()
                    self.ensure_foreground(main_window)
                    send_keys(self.SMILE_EXIT_KEY)
                    time.sleep(1)
                    break
                except Exception as e:
                    self.log_message(f"   [!] Lỗi thoát SMILE (lần {exit_attempt+1}): {e}")
                    time.sleep(2)

            # STEP 7: Đẩy lên Drive
            self.focus_terminal()
            self.log_message("[Step 7] Đang đồng bộ file backup mới nhất lên Google Drive...")
            files = [os.path.join(self.SOURCE_DIR, f) for f in os.listdir(self.SOURCE_DIR) if os.path.isfile(os.path.join(self.SOURCE_DIR, f))]
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
            time.sleep(5)
        finally:
            self.hide_warning_overlay()
            self.log_message(f"\n[!] Hệ thống sẽ tự động đóng toàn bộ Terminal trong {self.TERMINAL_CLOSE_DELAY} giây...")
            time.sleep(self.TERMINAL_CLOSE_DELAY)
            subprocess.run("taskkill /F /IM cmd.exe", shell=True)

if __name__ == "__main__":
    bot = autoBackupSMILE()
    bot.run()