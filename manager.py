import time
import json
import os
import sys
import datetime
import shutil
import ctypes
import string
import subprocess

# ==================== LOAD CONFIG ====================
# Ho tro ca chay tu Python source va PyInstaller EXE
if getattr(sys, 'frozen', False):
    # Chay tu PyInstaller EXE - lay thu muc cha cua EXE
    SCRIPT_DIR = os.path.dirname(sys.executable)
else:
    # Chay tu Python source - lay thu muc cua script
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "config.json")

def load_config():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[!] Không tìm thấy tệp cấu hình: {CONFIG_FILE}")
        input("Nhấn Enter để thoát...")
        raise SystemExit(1)
    except json.JSONDecodeError as e:
        print(f"[!] Lỗi đọc tệp cấu hình: {e}")
        input("Nhấn Enter để thoát...")
        raise SystemExit(1)

def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4, ensure_ascii=False)
    print("[OK] Đã lưu cấu hình vào config.json")

# ==================== UTILITY ====================
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def print_files_table(files_info):
    """In bảng file với STT, tên tệp, ngày, kích thước"""
    if not files_info:
        print("   (Không có tệp nào)")
        return
    print(f"   {'STT':<5} {'Ngày sao lưu':<25} {'Tên tệp':<40} {'Kích thước':<15}")
    print(f"   {'-'*5} {'-'*25} {'-'*40} {'-'*15}")
    for i, info in enumerate(files_info, 1):
        print(f"   {i:<5} {info['date_str']:<25} {info['name']:<40} {info['size_str']:<15}")

def format_size(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

def get_file_info(filepath):
    """Lay thong tin file: ten, ngay, kich thuoc"""
    try:
        stat = os.stat(filepath)
        mtime = datetime.datetime.fromtimestamp(stat.st_mtime)
        return {
            'path': filepath,
            'name': os.path.basename(filepath),
            'date': mtime,
            'date_str': mtime.strftime("%Y-%m-%d %H:%M:%S"),
            'size': stat.st_size,
            'size_str': format_size(stat.st_size),
            'day_key': mtime.strftime("%Y-%m-%d")
        }
    except Exception as e:
        return None

def get_files_in_dir(dir_path, pattern=None):
    """Lấy danh sách tệp trong thư mục, sắp xếp theo ngày mới nhất"""
    if not os.path.exists(dir_path):
        return []
    files = []
    try:
        for f in os.listdir(dir_path):
            fp = os.path.join(dir_path, f)
            if os.path.isfile(fp):
                info = get_file_info(fp)
                if info:
                    files.append(info)
    except Exception as e:
        print(f"[!] Lỗi đọc thư mục {dir_path}: {e}")
    files.sort(key=lambda x: x['date'], reverse=True)
    return files

def get_unique_days(files_info):
    """Lay danh sach ngay doc nhat tu danh sach file"""
    days = {}
    for f in files_info:
        day = f['day_key']
        if day not in days:
            days[day] = []
        days[day].append(f)
    # Sap xep ngay moi nhat truoc
    sorted_days = sorted(days.items(), key=lambda x: x[0], reverse=True)
    return sorted_days

def browse_folder(start_path):
    """Duyệt thư mục và cho người dùng chọn thư mục mục tiêu.
    Trả về đường dẫn đầy đủ của thư mục được chọn, hoặc None để hủy."""
    current_path = start_path
    
    while True:
        clear_screen()
        print_header("DUYỆT THƯ MỤC")
        print(f"\n   Đang tải: {current_path}\n")

        # Liệt kê các thư mục con
        subfolders = []
        try:
            for item in sorted(os.listdir(current_path)):
                item_path = os.path.join(current_path, item)
                if os.path.isdir(item_path):
                    try:
                        # Đếm số file con trong thư mục
                        num_items = len([f for f in os.listdir(item_path) if os.path.isfile(os.path.join(item_path, f))])
                        subfolders.append({
                            'name': item,
                            'path': item_path,
                            'num_files': num_items
                        })
                    except:
                        subfolders.append({
                            'name': item,
                            'path': item_path,
                            'num_files': '?'
                        })
        except Exception as e:
            print(f"   [!] Lỗi đọc thư mục: {e}")
            input("   Nhấn Enter để quay lại...")
            return None

        # Hiển thị danh sách
        print(f"   {'STT':<5} {'Tên thư mục':<45} {'Số tệp':<10}")
        print(f"   {'-'*5} {'-'*45} {'-'*10}")
        
        # Tùy chọn đi lên thư mục cha
        parent = os.path.dirname(current_path)
        can_go_up = parent and parent != current_path and len(parent) >= len(start_path.split("\\")[0] + "\\")
        if can_go_up:
            print(f"   {'0':<5} {'.. (Thư mục cha)':<45}")
        
        for i, sf in enumerate(subfolders, 1):
            files_str = str(sf['num_files']) if sf['num_files'] != 0 else "-"
            print(f"   {i:<5} {sf['name']:<45} {files_str:<10}")

        if not subfolders:
            print("   (Không có thư mục con nào)")

        print()
        print("   Tùy chọn:")
        print(f"   - Nhập STT (1-{len(subfolders)}) để vào thư mục con")
        if can_go_up:
            print("   - Nhập '0' để quay về thư mục cha")
        print("   - Nhập 'S' để chọn thư mục hiện tại làm nơi lưu sao lưu")
        print("   - Nhập 'C' để tạo thư mục mới")
        print("   - Nhập 'X' để hủy")

        choice = input("\n   Lựa chọn: ").strip()

        if choice.lower() == 'x':
            return None

        if choice.lower() == 's':
            # Chọn thư mục hiện tại
            return current_path

        if choice.lower() == 'c':
            # Tạo thư mục mới
            new_name = input("   Nhập tên thư mục mới: ").strip()
            if not new_name:
                print("   [!] Tên không được để trống.")
                continue
            # Loại bỏ ký tự không hợp lệ
            new_name = new_name.replace('/', '_').replace('\\', '_').replace(':', '_').replace('"', '_')
            new_path = os.path.join(current_path, new_name)
            if os.path.exists(new_path):
                print(f"   [!] Thư mục '{new_name}' đã tồn tại.")
                # Hỏi có muốn vào thư mục đó không
                if confirm(f"   Vào thư mục '{new_name}'? (Y/N): "):
                    current_path = new_path
                continue
            try:
                os.makedirs(new_path, exist_ok=True)
                print(f"   [OK] Đã tạo thư mục: {new_path}")
                current_path = new_path
            except Exception as e:
                print(f"   [!] Lỗi tạo thư mục: {e}")
            continue

        if choice == '0' and can_go_up:
            current_path = parent
            continue

        try:
            idx = int(choice)
            if idx < 1 or idx > len(subfolders):
                print(f"   [!] STT không hợp lệ. Chọn từ 1 đến {len(subfolders)}")
                input("   Nhấn Enter để tiếp tục...")
                continue
            current_path = subfolders[idx - 1]['path']
        except ValueError:
            print("   [!] Nhập không hợp lệ.")
            input("   Nhấn Enter để tiếp tục...")

def input_int(prompt, min_val=None, max_val=None):
    """Nhập số nguyên có kiểm tra"""
    while True:
        try:
            val = input(prompt).strip()
            if val == '':
                return None
            val = int(val)
            if min_val is not None and val < min_val:
                print(f"   [!] Giá trị phải >= {min_val}")
                continue
            if max_val is not None and val > max_val:
                print(f"   [!] Giá trị phải <= {max_val}")
                continue
            return val
        except ValueError:
            print("   [!] Vui lòng nhập số nguyên.")

def confirm(prompt):
    """Xác nhận Có/Không (Yes/No)"""
    while True:
        val = input(prompt).strip().lower()
        if val in ['y', 'yes', 'co', 'c']:
            return True
        if val in ['n', 'no', 'khong', 'k']:
            return False
        print("   [!] Vui lòng nhập Y/N hoặc C/K.")

def run_auto_backup():
    """Chạy tự động sao lưu SMILE"""
    clear_screen()
    print_header("CHẠY TỰ ĐỘNG SAO LƯU SMILE")

    auto_script = os.path.join(SCRIPT_DIR, "autoBackupSMILE.py")
    if not os.path.exists(auto_script):
        print(f"\n   [!] Không tìm thấy tệp: {auto_script}")
        input("   Nhấn Enter để quay lại...")
        return

    print(f"\n   Kịch bản: {auto_script}")
    print(f"   Đang khởi động tiến trình tự động sao lưu SMILE...")
    print(f"   (Nhấn Ctrl+C để dừng lại nếu cần)")
    print()

    # Kiểm tra xem đang chạy từ EXE (PyInstaller) hay Python source
    is_frozen = getattr(sys, 'frozen', False)

    try:
        if is_frozen:
            # Chạy từ EXE - import autoBackupSMILE như module
            if SCRIPT_DIR not in sys.path:
                sys.path.insert(0, SCRIPT_DIR)
            import importlib
            auto_module = importlib.import_module("autoBackupSMILE")
            bot = auto_module.autoBackupSMILE()
            bot.run()
            print(f"\n   [OK] Tự động sao lưu đã hoàn tất thành công!")
        else:
            # Chạy từ Python source - dùng subprocess
            result = subprocess.run(
                [sys.executable, auto_script],
                cwd=SCRIPT_DIR,
                timeout=None
            )
            if result.returncode == 0:
                print(f"\n   [OK] Tự động sao lưu đã hoàn tất thành công!")
            else:
                print(f"\n   [!] Tiến trình sao lưu kết thúc với mã thoát: {result.returncode}")
    except KeyboardInterrupt:
        print("\n   [!] Đã dừng lại bởi người dùng.")
    except SystemExit:
        print("\n   [!] Kịch bản đã thoát.")
    except Exception as e:
        print(f"\n   [!] Đã xảy ra lỗi khi chạy tự động sao lưu: {e}")

    input("\n   Nhấn Enter để quay lại menu...")



# ==================== FEATURE 1: CAP NHAT GOOGLE DRIVE ====================
def update_google_drive():
    """Quét tất cả ổ đĩa, liệt kê và cho người dùng chọn hoặc tạo thư mục mới"""
    clear_screen()
    print_header("CẬP NHẬT ĐƯỜNG DẪN GOOGLE DRIVE")

    while True:
        # Đọc cấu hình hiện tại trước tiên
        cfg = load_config()
        current_paths = cfg.get("GOOGLE_DRIVE_PATHS", [])
        current_subfolder = cfg.get("GOOGLE_DRIVE_SUBFOLDER", "SMILE BACKUP")

        print("\n   Đang quét các ổ đĩa...")
        print()

        found_drives = []
        other_drives = []

        # Quét các ổ đĩa từ A-Z
        for letter in string.ascii_uppercase:
            drive_root = f"{letter}:\\"
            if not os.path.exists(drive_root):
                continue

            # Lấy tên ổ đĩa
            try:
                volume_name = subprocess.run(f'vol {letter}:', shell=True, capture_output=True, text=True).stdout.strip()
            except:
                volume_name = ""

            my_drive = os.path.join(drive_root, "My Drive")
            if os.path.exists(my_drive):
                # Là Google Drive
                # Tìm xem có thư mục nào chứa chữ "backup" (không phân biệt hoa thường) không
                is_existing = False
                found_backup_folder = current_subfolder
                try:
                    for f in os.listdir(my_drive):
                        if os.path.isdir(os.path.join(my_drive, f)) and "backup" in f.lower():
                            is_existing = True
                            found_backup_folder = f
                            break
                except:
                    pass

                smile_backup = os.path.join(my_drive, found_backup_folder)
                if not is_existing:
                    is_existing = os.path.exists(smile_backup)

                found_drives.append({
                    'letter': letter,
                    'drive_root': drive_root,
                    'my_drive': my_drive,
                    'smile_backup': smile_backup,
                    'is_existing': is_existing,
                    'is_google_drive': True,
                    'label': f"Google Drive ({letter}:)"
                })
            else:
                # Ổ đĩa thường - có thể dùng làm nơi lưu sao lưu
                other_drives.append({
                    'letter': letter,
                    'drive_root': drive_root,
                    'is_google_drive': False,
                    'label': f"Ổ đĩa {letter}:"
                })

        # Kiểm tra USERPROFILE
        user_profile = os.environ.get("USERPROFILE")
        if user_profile:
            profile_drive = os.path.join(user_profile, "Google Drive", "My Drive")
            if os.path.exists(profile_drive):
                # Tìm xem có thư mục nào chứa chữ "backup" (không phân biệt hoa thường) không
                is_existing = False
                found_backup_folder = current_subfolder
                try:
                    for f in os.listdir(profile_drive):
                        if os.path.isdir(os.path.join(profile_drive, f)) and "backup" in f.lower():
                            is_existing = True
                            found_backup_folder = f
                            break
                except:
                    pass

                smile_backup = os.path.join(profile_drive, found_backup_folder)
                if not is_existing:
                    is_existing = os.path.exists(smile_backup)

                found_drives.append({
                    'letter': 'U',
                    'drive_root': os.path.join(user_profile, "Google Drive"),
                    'my_drive': profile_drive,
                    'smile_backup': smile_backup,
                    'is_existing': is_existing,
                    'is_google_drive': True,
                    'label': "Google Drive (User Profile)"
                })

        print(f"   --- Đường dẫn hiện tại trong cấu hình ---")
        for i, p in enumerate(current_paths, 1):
            print(f"   {i}. {p}")
        print(f"   Thư mục con: {current_subfolder}")
        print()

        # Hiển thị danh sách Google Drive phát hiện được
        if found_drives:
            print(f"   === Google Drive phát hiện được ===")
            print(f"   {'STT':<5} {'Nhãn':<25} {'Đường dẫn':<50} {'THƯ MỤC BACKUP?':<15}")
            print(f"   {'-'*5} {'-'*25} {'-'*50} {'-'*15}")
            for i, d in enumerate(found_drives, 1):
                existing_str = "CÓ" if d['is_existing'] else "CHƯA CÓ"
                print(f"   {i:<5} {d['label']:<25} {d['my_drive']:<50} {existing_str:<15}")
            print()

        # Hiển thị danh sách ổ đĩa khác
        if other_drives:
            print(f"   === Ổ đĩa khác (có thể dùng lưu sao lưu) ===")
            print(f"   {'STT':<5} {'Nhãn':<25} {'Đường dẫn':<50}")
            print(f"   {'-'*5} {'-'*25} {'-'*50}")
            for i, d in enumerate(other_drives, len(found_drives) + 1):
                print(f"   {i:<5} {d['label']:<25} {d['drive_root']:<50}")
            print()

        print("   Tùy chọn:")
        print(f"   - Nhập STT (1-{len(found_drives) + len(other_drives)}) để chọn ổ đĩa")
        print(f"   - Nhập 'N' để nhập đường dẫn thủ công") 
        print(f"   - Nhập '0' để quay lại menu")
        print()

        choice = input("   Lựa chọn: ").strip()

        if choice == '0':
            return

        if choice.lower() == 'n':
            # Nhập đường dẫn thủ công
            print("\n   Nhập đường dẫn đầy đủ đến thư mục muốn lưu sao lưu")
            print("   Ví dụ: D:\\Backup\\SMILE_BACKUP hoặc \\\\SERVER\\share\\backup")
            print("   (Thư mục SMILE BACKUP sẽ được tạo tự động nếu chưa có)")
            custom_path = input("\n   Đường dẫn: ").strip().strip('"').strip("'")

            if not custom_path:
                print("   [!] Đường dẫn không được để trống.")
                continue

            # Kiểm tra đường dẫn có tồn tại thư mục cha không
            parent_dir = custom_path
            if not os.path.exists(parent_dir):
                # Thử tạo thư mục cha
                try:
                    os.makedirs(parent_dir, exist_ok=True)
                    print(f"   [OK] Đã tạo thư mục: {parent_dir}")
                except Exception as e:
                    print(f"   [!] Không thể tạo thư mục: {e}")
                    input("   Nhấn Enter để thử lại...")
                    continue

            # Kiểm tra/tạo thư mục SMILE BACKUP
            smile_dir = os.path.join(parent_dir, current_subfolder) if current_subfolder in parent_dir else os.path.join(parent_dir, "SMILE BACKUP") if "SMILE BACKUP" not in custom_path else custom_path
            if not os.path.exists(smile_dir) and "SMILE BACKUP" not in custom_path:
                if confirm(f"   Tạo thư mục '{smile_dir}'? (Y/N): "):
                    try:
                        os.makedirs(smile_dir, exist_ok=True)
                        print(f"   [OK] Đã tạo thư mục: {smile_dir}")
                    except Exception as e:
                        print(f"   [!] Lỗi tạo thư mục: {e}")
                        input("   Nhấn Enter để thử lại...")
                        continue

            # Cập nhật cấu hình
            if "SMILE BACKUP" in custom_path or current_subfolder in custom_path:
                base_path = custom_path
                final_path = custom_path
            else:
                base_path = custom_path
                final_path = os.path.join(custom_path, current_subfolder)

            cfg["GOOGLE_DRIVE_PATHS"] = [base_path]
            save_config(cfg)
            print(f"\n   [OK] Đã cập nhật đường dẫn: {base_path}")
            print(f"   [OK] Thư mục sao lưu: {final_path}")
            input("   Nhấn Enter để quay lại...")
            return

        # Chọn STT
        try:
            idx = int(choice)
            total_drives = found_drives + other_drives
            if idx < 1 or idx > len(total_drives):
                print(f"   [!] STT không hợp lệ. Chọn từ 1 đến {len(total_drives)}")
                input("   Nhấn Enter để thử lại...")
                continue

            selected = total_drives[idx - 1]

            if selected['is_google_drive']:
                # Là Google Drive - mở duyệt thư mục bên trong
                start_browse = selected['my_drive']
                print(f"\n   Mở duyệt thư mục trong {selected['label']}...")
                print(f"   Hãy chọn hoặc tạo thư mục để lưu sao lưu.")
                input("   Nhấn Enter để bắt đầu duyệt...")

                chosen = browse_folder(start_browse)
                if chosen is None:
                    print("   [!] Đã hủy chọn thư mục.")
                    input("   Nhấn Enter để thử lại...")
                    continue

                # Tính toán base_path và subfolder từ đường dẫn đã chọn
                my_drive = selected['my_drive']
                if chosen == my_drive:
                    # Chọn chính My Drive - dùng subfolder mặc định
                    cfg["GOOGLE_DRIVE_PATHS"] = [my_drive]
                    final_path = os.path.join(my_drive, current_subfolder)
                else:
                    # Chọn thư mục con
                    try:
                        subfolder_rel = os.path.relpath(chosen, my_drive)
                        if subfolder_rel == '.':
                            subfolder_rel = current_subfolder
                        cfg["GOOGLE_DRIVE_PATHS"] = [my_drive]
                        cfg["GOOGLE_DRIVE_SUBFOLDER"] = subfolder_rel
                        final_path = chosen
                    except:
                        cfg["GOOGLE_DRIVE_PATHS"] = [chosen]
                        final_path = chosen

                # Kiểm tra/tạo thư mục nếu cần
                if not os.path.exists(final_path):
                    if confirm(f"   Tạo thư mục '{final_path}'? (Y/N): "):
                        try:
                            os.makedirs(final_path, exist_ok=True)
                            print(f"   [OK] Đã tạo thư mục: {final_path}")
                        except Exception as e:
                            print(f"   [!] Lỗi tạo thư mục: {e}")
                            input("   Nhấn Enter để thử lại...")
                            continue

                save_config(cfg)
                print(f"\n   [OK] Đã cập nhật đường dẫn Google Drive!")
                print(f"   [OK] Thư mục sao lưu: {final_path}")
                input("   Nhấn Enter để quay lại...")
                return
            else:
                # Là ổ đĩa thường - mở duyệt thư mục
                start_browse = selected['drive_root']
                print(f"\n   Mở duyệt thư mục trong {selected['label']}...")
                print(f"   Hãy chọn hoặc tạo thư mục để lưu sao lưu.")
                input("   Nhấn Enter để bắt đầu duyệt...")

                chosen = browse_folder(start_browse)
                if chosen is None:
                    print("   [!] Đã hủy chọn thư mục.")
                    input("   Nhấn Enter để thử lại...")
                    continue

                # Tính toán base và subfolder
                drive_root = selected['drive_root']
                if chosen == drive_root:
                    cfg["GOOGLE_DRIVE_PATHS"] = [drive_root]
                    cfg["GOOGLE_DRIVE_SUBFOLDER"] = current_subfolder
                    final_path = os.path.join(drive_root, current_subfolder)
                else:
                    try:
                        subfolder_rel = os.path.relpath(chosen, drive_root)
                        if subfolder_rel == '.':
                            subfolder_rel = current_subfolder
                        cfg["GOOGLE_DRIVE_PATHS"] = [drive_root]
                        cfg["GOOGLE_DRIVE_SUBFOLDER"] = subfolder_rel
                        final_path = chosen
                    except:
                        cfg["GOOGLE_DRIVE_PATHS"] = [chosen]
                        final_path = chosen

                # Kiểm tra/tạo thư mục
                if not os.path.exists(final_path):
                    if confirm(f"   Tạo thư mục '{final_path}'? (Y/N): "):
                        try:
                            os.makedirs(final_path, exist_ok=True)
                            print(f"   [OK] Đã tạo thư mục: {final_path}")
                        except Exception as e:
                            print(f"   [!] Lỗi tạo thư mục: {e}")
                            input("   Nhấn Enter để thử lại...")
                            continue
                    else:
                        print("   [!] Đã hủy.")
                        continue

                save_config(cfg)
                print(f"\n   [OK] Đã cập nhật đường dẫn: {drive_root}")
                print(f"   [OK] Thư mục sao lưu: {final_path}")
                input("   Nhấn Enter để quay lại...")
                return

        except ValueError:
            print("   [!] Nhập không hợp lệ.")
            input("   Nhấn Enter để thử lại...")
            continue

# ==================== FEATURE 2: DUYỆT FILE Ở GỐC (REMOTE) ====================
def browse_remote_files():
    """Duyệt file backup tại thư mục nguồn (Remote)"""
    clear_screen()
    print_header("DUYỆT FILE TẠI Ổ ĐĨA GỐC (REMOTE)")

    cfg = load_config()
    source_dir = cfg["SOURCE_DIR"]

    print(f"\n   Thư mục nguồn: {source_dir}")
    print("   Đang lấy danh sách file...\n")

    if not os.path.exists(source_dir):
        print(f"   [!] Không thể truy cập: {source_dir}")
        print("   [!] Kiểm tra lại kết nối mạng hoặc ổ đĩa.")
        input("\n   Nhấn Enter để quay lại...")
        return

    files = get_files_in_dir(source_dir)

    if not files:
        print("   [!] Không có file nào trong thư mục.")
        input("\n   Nhấn Enter để quay lại...")
        return

    # Thống kê theo ngày
    days = get_unique_days(files)
    print(f"   Tổng cộng: {len(files)} file, {len(days)} ngày backup\n")
    print_files_table(files)

    print(f"\n   --- THỐNG KÊ THEO NGÀY ---")
    for day_key, day_files in days:
        total_size = sum(f['size'] for f in day_files)
        print(f"   {day_key}: {len(day_files)} file, {format_size(total_size)}")

    input("\n   Nhấn Enter để quay lại...")

# ==================== FEATURE 3: DUYỆT FILE GOOGLE DRIVE ====================
def browse_drive_files():
    """Duyệt file backup tại Google Drive"""
    clear_screen()
    print_header("DUYỆT FILE TẠI GOOGLE DRIVE")

    cfg = load_config()
    drive_paths = cfg["GOOGLE_DRIVE_PATHS"]
    subfolder = cfg["GOOGLE_DRIVE_SUBFOLDER"]
    profile_path = cfg["GOOGLE_DRIVE_PROFILE_PATH"]

    # Tìm đường dẫn Drive
    target_dir = None
    user_profile = os.environ.get("USERPROFILE")

    for dp in drive_paths:
        full = os.path.join(dp, subfolder)
        if os.path.exists(dp):
            target_dir = full
            break

    if not target_dir and user_profile:
        alt = os.path.join(user_profile, profile_path)
        if os.path.exists(os.path.dirname(alt)):
            target_dir = alt

    if not target_dir:
        print("   [!] Không tìm thấy Google Drive!")
        input("\n   Nhấn Enter để quay lại...")
        return

    print(f"   Thư mục Drive: {target_dir}")
    print("   Đang lấy danh sách file...\n")

    if not os.path.exists(target_dir):
        print(f"   [!] Thư mục chưa tồn tại: {target_dir}")
        input("\n   Nhấn Enter để quay lại...")
        return

    files = get_files_in_dir(target_dir)

    if not files:
        print("   [!] Không có file backup nào trên Drive.")
        input("\n   Nhấn Enter để quay lại...")
        return

    # Thống kê theo ngày
    days = get_unique_days(files)
    print(f"   Tổng cộng: {len(files)} file, {len(days)} ngày backup\n")
    print_files_table(files)

    print(f"\n   --- THỐNG KÊ THEO NGÀY ---")
    for day_key, day_files in days:
        total_size = sum(f['size'] for f in day_files)
        print(f"   {day_key}: {len(day_files)} file, {format_size(total_size)}")

    input("\n   Nhấn Enter để quay lại...")

# ==================== FEATURE 4: DON DEP CA 2 O ====================
def cleanup_all_drives():
    """Dọn dẹp file backup ở cả Remote và Drive, chỉ chừa lại 3 ngày"""
    clear_screen()
    print_header("DỌN DẸP FILE BACKUP (CHỪA LẠI 3 NGÀY MỚI NHẤT)")

    KEEP_DAYS = 3
    cfg = load_config()

    print(f"\n   [!] SẼ XÓA TẤT CẢ FILE BACKUP CỦA HƠN {KEEP_DAYS} NGÀY")
    print(f"   [!] Chỉ chừa lại {KEEP_DAYS} ngày backup mới nhất")
    print()

    # --- Dọn dẹp Remote ---
    source_dir = cfg["SOURCE_DIR"]
    source_deleted = 0
    source_freed = 0

    if os.path.exists(source_dir):
        print(f"   --- Dọn dẹp Remote: {source_dir} ---")
        files = get_files_in_dir(source_dir)
        if files:
            days = get_unique_days(files)
            keep_days_list = [d[0] for d in days[:KEEP_DAYS]]

            for day_key, day_files in days:
                if day_key in keep_days_list:
                    print(f"   [GIỮ] {day_key}: {len(day_files)} file")
                else:
                    print(f"   [XÓA] {day_key}: {len(day_files)} file")
                    for f in day_files:
                        try:
                            sz = f['size']
                            os.remove(f['path'])
                            source_deleted += 1
                            source_freed += sz
                        except Exception as e:
                            print(f"      [!] Lỗi xóa {f['name']}: {e}")
        else:
            print("   [!] Không có file nào tại Remote.")
    else:
        print(f"   [!] Không thể truy cập Remote: {source_dir}")

    print()

    # --- Dọn dẹp Google Drive ---
    drive_paths = cfg["GOOGLE_DRIVE_PATHS"]
    subfolder = cfg["GOOGLE_DRIVE_SUBFOLDER"]
    profile_path = cfg["GOOGLE_DRIVE_PROFILE_PATH"]
    drive_dir = None
    drive_deleted = 0
    drive_freed = 0

    for dp in drive_paths:
        full = os.path.join(dp, subfolder)
        if os.path.exists(dp):
            drive_dir = full
            break

    if not drive_dir:
        user_profile = os.environ.get("USERPROFILE")
        if user_profile:
            alt = os.path.join(user_profile, profile_path)
            if os.path.exists(os.path.dirname(alt)):
                drive_dir = alt

    if drive_dir and os.path.exists(drive_dir):
        print(f"   --- Dọn dẹp Google Drive: {drive_dir} ---")
        drive_files = get_files_in_dir(drive_dir)
        if drive_files:
            days = get_unique_days(drive_files)
            keep_days_list = [d[0] for d in days[:KEEP_DAYS]]

            for day_key, day_files in days:
                if day_key in keep_days_list:
                    print(f"   [GIỮ] {day_key}: {len(day_files)} file")
                else:
                    print(f"   [XÓA] {day_key}: {len(day_files)} file")
                    for f in day_files:
                        try:
                            sz = f['size']
                            os.remove(f['path'])
                            drive_deleted += 1
                            drive_freed += sz
                        except Exception as e:
                            print(f"      [!] Lỗi xóa {f['name']}: {e}")
        else:
            print("   [!] Không có file nào trên Drive.")
    else:
        print("   [!] Không thể truy cập Google Drive.")

    # Tổng kết
    print(f"\n{'='*60}")
    print(f"   KẾT QUẢ DỌN DẸP:")
    print(f"   Remote:       Xóa {source_deleted} file, giải phóng {format_size(source_freed)}")
    print(f"   Google Drive:  Xóa {drive_deleted} file, giải phóng {format_size(drive_freed)}")
    print(f"{'='*60}")
    input("\n   Nhấn Enter để quay lại...")

# ==================== FEATURE 5: DUYET & XOA THEO KHOI TAI REMOTE ====================
def browse_and_delete_remote():
    """Truy cập Remote, tổng hợp theo ngày, cho phép chọn xóa theo khối (bắt buộc chừa lại tối thiểu 3 ngày)"""
    clear_screen()
    print_header("DUYỆT & XÓA THEO KHỐI TẠI REMOTE")

    MIN_KEEP_DAYS = 3
    cfg = load_config()
    source_dir = cfg["SOURCE_DIR"]

    print(f"   Thư mục nguồn: {source_dir}")
    print("   Đang lấy danh sách file...\n")

    if not os.path.exists(source_dir):
        print(f"   [!] Không thể truy cập: {source_dir}")
        input("\n   Nhấn Enter để quay lại...")
        return

    files = get_files_in_dir(source_dir)
    if not files:
        print("   [!] Không có file nào trong thư mục.")
        input("\n   Nhấn Enter để quay lại...")
        return

    days = get_unique_days(files)
    total_days = len(days)

    print(f"   Tổng cộng {len(files)} file, {total_days} ngày backup\n")
    print(f"   {'STT':<5} {'Ngày':<15} {'Số file':<10} {'Kích thước':<15} {'Trạng thái':<15}")
    print(f"   {'-'*5} {'-'*15} {'-'*10} {'-'*15} {'-'*15}")

    for i, (day_key, day_files) in enumerate(days, 1):
        total_size = sum(f['size'] for f in day_files)
        status = "ĐƯỢC GIỮ" if i <= MIN_KEEP_DAYS else "Có thể xóa"
        print(f"   {i:<5} {day_key:<15} {len(day_files):<10} {format_size(total_size):<15} {status:<15}")

    print(f"\n   [!] Bắt buộc chừa lại tối thiểu {MIN_KEEP_DAYS} ngày mới nhất (đánh số 1-{min(MIN_KEEP_DAYS, total_days)})")
    print()

    # Cho chọn ngày để xóa
    max_deletable = total_days - MIN_KEEP_DAYS
    if max_deletable <= 0:
        print(f"   [!] Chỉ có {total_days} ngày backup, không đủ ngày để xóa (cần tối thiểu {MIN_KEEP_DAYS}).")
        input("\n   Nhấn Enter để quay lại...")
        return

    print(f"   Các ngày có thể xóa: {MIN_KEEP_DAYS + 1} đến {total_days}")

    while True:
        print(f"\n   Nhập số thứ tự ngày muốn xóa (ví dụ: 4,5,6 hoặc 4-8)")
        print(f"   Nhập 'list' để xem lại, '0' để quay lại menu")
        choice = input("   Lựa chọn: ").strip()

        if choice == '0':
            return
        if choice.lower() == 'list':
            # Hiển thị lại danh sách
            clear_screen()
            print_header("DUYỆT & XÓA THEO KHỐI TẠI REMOTE")
            print(f"   {'STT':<5} {'Ngày':<15} {'Số file':<10} {'Kích thước':<15}")
            for i, (day_key, day_files) in enumerate(days, 1):
                total_size = sum(f['size'] for f in day_files)
                protected = " (ĐƯỢC GIỮ)" if i <= MIN_KEEP_DAYS else ""
                print(f"   {i:<5} {day_key:<15} {len(day_files):<10} {format_size(total_size):<15}{protected}")
            continue

        # Parse lựa chọn (ví dụ: "4,5,6" hoặc "4-8")
        try:
            selected_indices = set()
            parts = choice.split(',')
            for part in parts:
                part = part.strip()
                if '-' in part:
                    start, end = part.split('-', 1)
                    start, end = int(start.strip()), int(end.strip())
                    for idx in range(start, end + 1):
                        selected_indices.add(idx)
                else:
                    selected_indices.add(int(part))

            # Kiểm tra xem có chọn ngày được bảo vệ không
            protected = [idx for idx in selected_indices if idx <= MIN_KEEP_DAYS]
            if protected:
                print(f"   [!] KHÔNG THỂ XÓA các ngày {protected} (bắt buộc chừa lại {MIN_KEEP_DAYS} ngày!)")
                continue

            # Kiểm tra xem số thứ tự hợp lệ không
            invalid = [idx for idx in selected_indices if idx < 1 or idx > total_days]
            if invalid:
                print(f"   [!] Số thứ tự không hợp lệ: {invalid}")
                continue

            if not selected_indices:
                continue

            # Hiển thị xác nhận
            total_files_to_delete = 0
            total_size_to_delete = 0
            print(f"\n   Sẽ xóa {len(selected_indices)} ngày backup sau:")
            for idx in sorted(selected_indices):
                day_key, day_files = days[idx - 1]
                day_size = sum(f['size'] for f in day_files)
                print(f"     - {day_key}: {len(day_files)} file, {format_size(day_size)}")
                total_files_to_delete += len(day_files)
                total_size_to_delete += day_size

            print(f"\n   Tổng cộng: Xóa {total_files_to_delete} file, giải phóng {format_size(total_size_to_delete)}")

            if confirm("   Xác nhận xóa? (Y/N): "):
                # Thực hiện xóa
                actual_deleted = 0
                for idx in sorted(selected_indices, reverse=True):
                    day_key, day_files = days[idx - 1]
                    for f in day_files:
                        try:
                            os.remove(f['path'])
                            actual_deleted += 1
                        except Exception as e:
                            print(f"      [!] Lỗi xóa {f['name']}: {e}")
                print(f"\n   [OK] Đã xóa {actual_deleted} file thành công!")
                input("   Nhấn Enter để quay lại...")
                return
            else:
                print("   [!] Đã hủy xóa.")
                continue

        except (ValueError, IndexError):
            print("   [!] Nhập không hợp lệ. Ví dụ: 4,5,6 hoặc 4-8")
            continue

# ==================== MAIN MENU ====================
def main():
    while True:
        clear_screen()
        print_header("SMILE BACKUP MANAGER")
        print()

        print("   1. Chạy tự động backup SMILE")
        print("   2. Cập nhật đường dẫn Google Drive")
        print("   3. Duyệt file tại ổ đĩa gốc (Remote)")
        print("   4. Duyệt file tại Google Drive")
        print("   5. Dọn dẹp file backup (chừa lại 3 ngày mới nhất)")
        print("   6. Duyệt & xóa theo khối tại Remote")
        print("   0. Thoát")
        print()

        choice = input("   Chọn chức năng [0-6]: ").strip()

        if choice == '1':
            run_auto_backup()
        elif choice == '2':
            update_google_drive()
        elif choice == '3':
            browse_remote_files()
        elif choice == '4':
            browse_drive_files()
        elif choice == '5':
            cleanup_all_drives()
        elif choice == '6':
            browse_and_delete_remote()
        elif choice == '0':
            print("\n   Tạm biệt!")
            time.sleep(1)
            break
        else:
            print("   [!] Lựa chọn không hợp lệ.")
            time.sleep(1)

if __name__ == "__main__":
    main()
