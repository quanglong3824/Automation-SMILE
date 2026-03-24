import time
import json
import os
from pywinauto import Application, mouse
from pywinauto.keyboard import send_keys
import keyboard

# ==================== CONFIG ====================
SMILE_PATH = r"C:\Program Files (x86)\SMILE\SMILEFO.exe"
ACTION_FILE = "smile_actions.json"
# ================================================

class autoBackupSMILE:
    def __init__(self):
        self.actions = []

    def save_actions(self):
        with open(ACTION_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.actions, f, ensure_ascii=False, indent=4)
        print(f"\n[+] Đã lưu kịch bản vào {ACTION_FILE}")

    def load_actions(self):
        if os.path.exists(ACTION_FILE):
            with open(ACTION_FILE, 'r', encoding='utf-8') as f:
                self.actions = json.load(f)
            return True
        return False

    def record_mode(self):
        """Màn hình SMILE nên được mở sẵn ở bước Đăng nhập trước khi bắt đầu"""
        print("\n=== CHẾ ĐỘ GHI HÀNH ĐỘNG (RECORD MODE) ===")
        print("Hướng dẫn:")
        print("1. Di chuyển chuột đến vị trí cần bấm -> Nhấn 'S' để lưu Click.")
        print("2. Cần nhập văn bản (User/Pass) -> Nhấn 'K', sau đó nhập nội dung vào Console.")
        print("3. Cần chờ (sau khi bấm Login/Backup) -> Nhấn 'D', nhập số giây cần đợi (VD: 15).")
        print("4. Nhấn 'E' để Kết thúc và Lưu.")
        print("-" * 30)
        
        self.actions = []
        while True:
            if keyboard.is_pressed('s'):
                pos = mouse.position()
                self.actions.append({"type": "click", "pos": [pos[0], pos[1]]})
                print(f"  [+] Đã ghi Click tại: {pos}")
                time.sleep(0.5)

            elif keyboard.is_pressed('k'):
                key = input("  > Nhập nội dung (VD: IT, {TAB}, 123@123a, {ENTER}): ")
                self.actions.append({"type": "key", "value": key})
                print(f"  [+] Đã ghi phím: {key}")
                time.sleep(0.5)

            elif keyboard.is_pressed('d'):
                sec = input("  > Nhập số giây cần chờ tại bước này (VD: 10): ")
                self.actions.append({"type": "wait", "value": int(sec)})
                print(f"  [+] Đã ghi lệnh chờ: {sec} giây")
                time.sleep(0.5)

            elif keyboard.is_pressed('e'):
                self.save_actions()
                break
            time.sleep(0.01)

    def play_mode(self):
        if not self.load_actions():
            print("\n[!] Lỗi: Chưa có kịch bản. Hãy chọn mục 1.")
            return

        print("\n--> Đang khởi động SMILE...")
        try:
            # Tự động mở App trước khi chạy kịch bản
            Application(backend="win32").start(SMILE_PATH)
            print("--> Chờ 10 giây cho App khởi động...")
            time.sleep(10)

            print(f"=== ĐANG CHẠY TỰ ĐỘNG ({len(self.actions)} bước) ===")
            for i, action in enumerate(self.actions):
                if action["type"] == "click":
                    x, y = action["pos"]
                    print(f"  [{i+1}] Click tại ({x}, {y})")
                    mouse.click(button='left', coords=(x, y))
                    time.sleep(1)
                
                elif action["type"] == "key":
                    print(f"  [{i+1}] Gửi phím: {action['value']}")
                    send_keys(action["value"])
                    time.sleep(1)

                elif action["type"] == "wait":
                    print(f"  [{i+1}] Chờ trong {action['value']} giây...")
                    time.sleep(action["value"])
            
            print("\n[+] HOÀN TẤT.")
        except Exception as e:
            print(f"\n[!] Lỗi: {e}")

def main_menu():
    bot = autoBackupSMILE()
    while True:
        print("\n" + "="*30)
        print("   autoBackupSMILE v2 (Recorder)")
        print("="*30)
        print("1. Ghi hành động mới (Record)")
        print("   (Mở sẵn SMILE ở màn hình Login trước khi chọn)")
        print("2. Chạy tự động (Auto Play)")
        print("0. Thoát")
        print("-" * 30)
        
        choice = input("Chọn (0-2): ")
        if choice == '1':
            bot.record_mode()
        elif choice == '2':
            bot.play_mode()
        elif choice == '0':
            break

if __name__ == "__main__":
    main_menu()
