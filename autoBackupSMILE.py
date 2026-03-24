import time
import json
import os
from pywinauto import Application, mouse
from pywinauto.keyboard import send_keys
import keyboard  # Cần cài đặt: pip install keyboard

# File lưu trữ kịch bản
ACTION_FILE = "smile_actions.json"

class autoBackupSMILE:
    def __init__(self):
        self.actions = []
        self.app = None

    def save_actions(self):
        with open(ACTION_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.actions, f, ensure_ascii=False, indent=4)
        print(f"\n[+] Đã lưu {len(self.actions)} hành động vào {ACTION_FILE}")

    def load_actions(self):
        if os.path.exists(ACTION_FILE):
            with open(ACTION_FILE, 'r', encoding='utf-8') as f:
                self.actions = json.load(f)
            return True
        return False

    def record_mode(self):
        """TẠO HÀNH ĐỘNG MỚI: Ghi lại tọa độ chuột và phím bấm"""
        print("\n=== CHẾ ĐỘ GHI HÀNH ĐỘNG (RECORD MODE) ===")
        print("- Di chuyển chuột đến vị trí cần Click và nhấn phím 'S' (Save Click)")
        print("- Để nhập văn bản/phím, nhấn phím 'K' (Key) sau đó nhập phím cần lưu")
        print("- Nhấn phím 'E' (Exit) để kết thúc và lưu kịch bản")
        
        self.actions = []
        
        while True:
            # Ghi tọa độ click chuột khi nhấn 'S'
            if keyboard.is_pressed('s'):
                pos = mouse.position()
                self.actions.append({"type": "click", "pos": [pos[0], pos[1]]})
                print(f"  [+] Đã ghi Click tại: {pos}")
                time.sleep(0.5) # Tránh ghi trùng

            # Ghi phím bấm khi nhấn 'k'
            elif keyboard.is_pressed('k'):
                key = input("  > Nhập phím hoặc chuỗi văn bản (VD: IT, {TAB}, {ENTER}): ")
                self.actions.append({"type": "key", "value": key})
                print(f"  [+] Đã ghi phím: {key}")
                time.sleep(0.5)

            # Kết thúc khi nhấn 'e'
            elif keyboard.is_pressed('e'):
                self.save_actions()
                break
            
            time.sleep(0.01)

    def play_mode(self):
        """THỰC THI HÀNH ĐỘNG: Tự động chạy lại kịch bản đã lưu"""
        if not self.load_actions():
            print("\n[!] Lỗi: Chưa có kịch bản nào được lưu. Hãy chọn mục 1 trước.")
            return

        print(f"\n=== ĐANG THỰC THI TỰ ĐỘNG ({len(self.actions)} bước) ===")
        try:
            for i, action in enumerate(self.actions):
                print(f"  Step {i+1}: ", end="")
                
                if action["type"] == "click":
                    x, y = action["pos"]
                    print(f"Click chuột tại ({x}, {y})")
                    mouse.click(button='left', coords=(x, y))
                
                elif action["type"] == "key":
                    val = action["value"]
                    print(f"Gửi phím/văn bản: {val}")
                    send_keys(val)
                
                time.sleep(2) # Khoảng nghỉ giữa các bước (có thể điều chỉnh)
            
            print("\n[+] HOÀN TẤT QUY TRÌNH TỰ ĐỘNG.")
        except Exception as e:
            print(f"\n[!] Lỗi khi đang chạy: {e}")

def main_menu():
    bot = autoBackupSMILE()
    while True:
        print("\n" + "="*30)
        print("   autoBackupSMILE MENU")
        print("="*30)
        print("1. Tạo hành động mới (Record)")
        print("2. Thực thi hành động đã lưu (Auto)")
        print("0. Thoát")
        print("-" * 30)
        
        choice = input("Chọn mục (0-2): ")
        
        if choice == '1':
            bot.record_mode()
        elif choice == '2':
            bot.play_mode()
        elif choice == '0':
            print("Tạm biệt!")
            break
        else:
            print("Lựa chọn không hợp lệ.")

if __name__ == "__main__":
    main_menu()
