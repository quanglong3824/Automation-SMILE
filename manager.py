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
        print(f"[!] Khong tim thay file cau hinh: {CONFIG_FILE}")
        input("Nhan Enter de thoat...")
        raise SystemExit(1)
    except json.JSONDecodeError as e:
        print(f"[!] Loi doc file cau hinh: {e}")
        input("Nhan Enter de thoat...")
        raise SystemExit(1)

def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4, ensure_ascii=False)
    print("[OK] Da luu cau hinh vao config.json")

# ==================== UTILITY ====================
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def print_files_table(files_info):
    """In bang file voi STT, ten, ngay, kich thuoc"""
    if not files_info:
        print("   (Khong co file nao)")
        return
    print(f"   {'STT':<5} {'Ngay backup':<25} {'Ten file':<40} {'Kich thuoc':<15}")
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
    """Lay danh sach file trong thu muc, sap xep theo ngay moi nhat"""
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
        print(f"[!] Loi doc thu muc {dir_path}: {e}")
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
    """Duyet thu muc va cho nguoi dung chon thu muc muc tieu.
    Tra ve duong dan day du cua thu muc duoc chon, hoac None de huy."""
    current_path = start_path
    
    while True:
        clear_screen()
        print_header("DUYET THU MUC")
        print(f"\n   Dang tai: {current_path}\n")

        # Liet ke cac thu muc con
        subfolders = []
        try:
            for item in sorted(os.listdir(current_path)):
                item_path = os.path.join(current_path, item)
                if os.path.isdir(item_path):
                    try:
                        # Dem so file con trong thu muc
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
            print(f"   [!] Loi doc thu muc: {e}")
            input("   Nhan Enter de quay lai...")
            return None

        # Hien thi danh sach
        print(f"   {'STT':<5} {'Ten thu muc':<45} {'So file':<10}")
        print(f"   {'-'*5} {'-'*45} {'-'*10}")
        
        # Tuy chon di len thu muc cha
        parent = os.path.dirname(current_path)
        can_go_up = parent and parent != current_path and len(parent) >= len(start_path.split("\\")[0] + "\\")
        if can_go_up:
            print(f"   {'0':<5} {'.. (Thu muc cha)':<45}")
        
        for i, sf in enumerate(subfolders, 1):
            files_str = str(sf['num_files']) if sf['num_files'] != 0 else "-"
            print(f"   {i:<5} {sf['name']:<45} {files_str:<10}")

        if not subfolders:
            print("   (Khong co thu muc con nao)")

        print()
        print("   Tuy chon:")
        print(f"   - Nhap STT (1-{len(subfolders)}) de vao thu muc con")
        if can_go_up:
            print("   - Nhap '0' de quay ve thu muc cha")
        print("   - Nhap 'S' de chon thu muc hien tai lam noi luu backup")
        print("   - Nhap 'C' de nhap ten thu muc moi (tao thu muc moi)")
        print("   - Nhap 'X' de huy")

        choice = input("\n   Lua chon: ").strip()

        if choice.lower() == 'x':
            return None

        if choice.lower() == 's':
            # Chon thu muc hien tai
            return current_path

        if choice.lower() == 'c':
            # Tao thu muc moi
            new_name = input("   Nhap ten thu muc moi: ").strip()
            if not new_name:
                print("   [!] Ten khong duoc de trong.")
                continue
            # Loai bo ky tu khong hop le
            new_name = new_name.replace('/', '_').replace('\\', '_').replace(':', '_').replace('"', '_')
            new_path = os.path.join(current_path, new_name)
            if os.path.exists(new_path):
                print(f"   [!] Thu muc '{new_name}' da ton tai.")
                # Hoi co muon vao thu muc do khong
                if confirm(f"   Vao thu muc '{new_name}'? (Y/N): "):
                    current_path = new_path
                continue
            try:
                os.makedirs(new_path, exist_ok=True)
                print(f"   [OK] Da tao thu muc: {new_path}")
                current_path = new_path
            except Exception as e:
                print(f"   [!] Loi tao thu muc: {e}")
            continue

        if choice == '0' and can_go_up:
            current_path = parent
            continue

        try:
            idx = int(choice)
            if idx < 1 or idx > len(subfolders):
                print(f"   [!] STT khong hop le. Chon tu 1 den {len(subfolders)}")
                input("   Nhan Enter de tiep tuc...")
                continue
            current_path = subfolders[idx - 1]['path']
        except ValueError:
            print("   [!] Nhap khong hop le.")
            input("   Nhan Enter de tiep tuc...")

def input_int(prompt, min_val=None, max_val=None):
    """Nhap so nguyen voi kiem tra"""
    while True:
        try:
            val = input(prompt).strip()
            if val == '':
                return None
            val = int(val)
            if min_val is not None and val < min_val:
                print(f"   [!] Gia tri phai >= {min_val}")
                continue
            if max_val is not None and val > max_val:
                print(f"   [!] Gia tri phai <= {max_val}")
                continue
            return val
        except ValueError:
            print("   [!] Vui long nhap so nguyen.")

def confirm(prompt):
    """Xac nhan yes/no"""
    while True:
        val = input(prompt).strip().lower()
        if val in ['y', 'yes', 'co']:
            return True
        if val in ['n', 'no', 'khong']:
            return False
        print("   [!] Vui long nhap Y/N.")

# ==================== ENVIRONMENT CHECK & AUTO INSTALL ====================
def check_environment():
    """Kiem tra moi truong va bao cao"""
    # Import setup_env tu cung thu muc
    setup_env_path = os.path.join(SCRIPT_DIR, "setup_env.py")
    if not os.path.exists(setup_env_path):
        print(f"\n   [!] Khong tim thay file setup_env.py tai: {setup_env_path}")
        input("   Nhan Enter de quay lai...")
        return

    # Them SCRIPT_DIR vao sys.path tam thoi
    if SCRIPT_DIR not in sys.path:
        sys.path.insert(0, SCRIPT_DIR)

    try:
        import setup_env
        # Goi ham kiem tra moi truong
        results = setup_env.full_environment_check()
        all_ok = setup_env.print_environment_report(results)

        if not all_ok:
            missing = setup_env.get_missing_critical_packages()
            print(f"   Cac thu vien con thieu: {', '.join(p['package'] for p in missing)}")
            answer = input("\n   Ban co muon tu dong cai dat? (Y/N): ").strip().lower()
            if answer in ['y', 'yes', 'co']:
                success, failed = setup_env.auto_install_missing(
                    progress_callback=lambda msg: print(f"   {msg}")
                )
                print(f"\n   Da cai dat: {success} thu vien")
                if failed:
                    print(f"   That bai: {', '.join(p['package'] for p in failed)}")
                    print("   Vui long cai dat thu cong bang lenh:")
                    for p in failed:
                        print(f"     pip install {p['package']}")
                else:
                    print("   [OK] Tat ca da san sang!")
                input("\n   Nhan Enter de quay lai...")
        else:
            input("\n   Nhan Enter de quay lai...")
    except Exception as e:
        print(f"\n   [!] Loi kiem tra moi truong: {e}")
        import traceback
        traceback.print_exc()
        input("\n   Nhan Enter de quay lai...")

def run_auto_backup():
    """Chay auto backup SMILE"""
    clear_screen()
    print_header("CHAY TU DONG BACKUP SMILE")

    # Kiem tra moi truong truoc khi chay
    setup_env_path = os.path.join(SCRIPT_DIR, "setup_env.py")
    if os.path.exists(setup_env_path):
        if SCRIPT_DIR not in sys.path:
            sys.path.insert(0, SCRIPT_DIR)
        try:
            import setup_env
            missing = setup_env.get_missing_critical_packages()
            if missing:
                print(f"\n   [!] THIEU THU VIEN! Cac thu vien sau chua duoc cai dat:")
                for p in missing:
                    print(f"       - {p['package']} ({p['description']})")
                print(f"\n   Vui long chon menu '7' de kiem tra va cai dat moi truong truoc.")
                input("\n   Nhan Enter de quay lai...")
                return
        except Exception:
            pass  # Neu khong import duoc, tiep tuc chay binh thuong

    auto_script = os.path.join(SCRIPT_DIR, "autoBackupSMILE.py")
    if not os.path.exists(auto_script):
        print(f"\n   [!] Khong tim thay file: {auto_script}")
        input("   Nhan Enter de quay lai...")
        return

    print(f"\n   Script: {auto_script}")
    print(f"   Dang khoi dong tu dong backup SMILE...")
    print(f"   (Nhan Ctrl+C de dung lai neu can)")
    print()

    # Kiem tra xem dang chay tu EXE (PyInstaller) hay Python source
    is_frozen = getattr(sys, 'frozen', False)

    try:
        if is_frozen:
            # Chay tu EXE - import autoBackupSMILE nhu module
            if SCRIPT_DIR not in sys.path:
                sys.path.insert(0, SCRIPT_DIR)
            import importlib
            auto_module = importlib.import_module("autoBackupSMILE")
            bot = auto_module.autoBackupSMILE()
            bot.run()
            print(f"\n   [OK] Auto backup da hoan thanh thanh cong!")
        else:
            # Chay tu Python source - dung subprocess de bao ly do rieng
            result = subprocess.run(
                [sys.executable, auto_script],
                cwd=SCRIPT_DIR,
                timeout=None
            )
            if result.returncode == 0:
                print(f"\n   [OK] Auto backup da hoan thanh thanh cong!")
            else:
                print(f"\n   [!] Auto backup da thoat voi ma: {result.returncode}")
    except KeyboardInterrupt:
        print("\n   [!] Da dung lai boi nguoi dung.")
    except SystemExit:
        print("\n   [!] Script da thoat.")
    except Exception as e:
        print(f"\n   [!] Loi khi chay auto backup: {e}")
        import traceback
        traceback.print_exc()

    input("\n   Nhan Enter de quay lai menu...")

def full_environment_check_and_fix():
    """Kiem tra moi truong day du va tu dong cai dat neu can"""
    clear_screen()
    print_header("KIEM TRA & CAI DAT MOI TRUONG")
    print()
    print("   Dang kiem tra moi truong...")
    print()

    setup_env_path = os.path.join(SCRIPT_DIR, "setup_env.py")
    if not os.path.exists(setup_env_path):
        print(f"   [!] Khong tim thay file setup_env.py tai: {setup_env_path}")
        input("   Nhan Enter de quay lai...")
        return

    if SCRIPT_DIR not in sys.path:
        sys.path.insert(0, SCRIPT_DIR)

    try:
        import setup_env
        results = setup_env.full_environment_check()
        all_ok = setup_env.print_environment_report(results)

        if not all_ok:
            missing = setup_env.get_missing_critical_packages()
            print(f"   Cac thu vien con thieu:")
            for p in missing:
                print(f"     - {p['package']}: {p['description']} (cho {p['required_by']})")

            print(f"\n   Ban co muon tu dong cai dat tat ca thu vien con thieu? (Y/N)")
            answer = input("   Lua chon: ").strip().lower()

            if answer in ['y', 'yes', 'co']:
                print()
                success, failed = setup_env.auto_install_missing(
                    progress_callback=lambda msg: print(f"   {msg}")
                )

                print(f"\n   {'='*50}")
                print(f"   Ket qua cai dat:")
                print(f"   - Thanh cong: {success} thu vien")
                if failed:
                    print(f"   - That bai: {len(failed)} thu vien")
                    for p in failed:
                        print(f"     X {p['package']}: {p['description']}")
                    print(f"\n   Cai dat thu cong bang lenh:")
                    for p in failed:
                        print(f"     pip install {p['package']}")
                else:
                    print(f"   [OK] Tat ca thu vien da duoc cai dat thanh cong!")
                print(f"   {'='*50}")

                # Kiem tra lai sau khi cai dat
                print(f"\n   Dang kiem tra lai moi truong...")
                results2 = setup_env.full_environment_check()
                all_ok2 = setup_env.print_environment_report(results2)

                if all_ok2:
                    print("\n   [OK] MOI TRUONG DA SAN SANG! Ban co the chay auto backup.")
                else:
                    print("\n   [!] Van con loi. Vui long kiem tra thu cong.")
            else:
                print("\n   [!] Da huy cai dat. Mot so chuc nang co the khong hoat dong.")
        else:
            print("\n   [OK] MOI TRUONG SAN SANG! Tat ca thu vien da du day du.")
            print("   Ban co the chay auto backup binh thuong.")

        input("\n   Nhan Enter de quay lai menu...")
    except Exception as e:
        print(f"\n   [!] Loi kiem tra moi truong: {e}")
        import traceback
        traceback.print_exc()
        input("\n   Nhan Enter de quay lai...")

# ==================== FEATURE 1: CAP NHAT GOOGLE DRIVE ====================
def update_google_drive():
    """Quet tat ca o dia, liet ke va cho nguoi dung chon hoac tao thu muc moi"""
    clear_screen()
    print_header("CAP NHAT DUONG DAN GOOGLE DRIVE")

    while True:
        print("\n   Dang quet cac o dia...")
        print()

        found_drives = []
        other_drives = []

        # Quet cac o dia tu A-Z
        for letter in string.ascii_uppercase:
            drive_root = f"{letter}:\\"
            if not os.path.exists(drive_root):
                continue

            # Lay ten o dia
            try:
                volume_name = subprocess.run(f'vol {letter}:', shell=True, capture_output=True, text=True).stdout.strip()
            except:
                volume_name = ""

            my_drive = os.path.join(drive_root, "My Drive")
            if os.path.exists(my_drive):
                # La Google Drive
                smile_backup = os.path.join(my_drive, "SMILE BACKUP")
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
                # O dia thuong - co the dung lam noi luu backup
                other_drives.append({
                    'letter': letter,
                    'drive_root': drive_root,
                    'is_google_drive': False,
                    'label': f"O dia {letter}:"
                })

        # Kiem tra USERPROFILE
        user_profile = os.environ.get("USERPROFILE")
        if user_profile:
            profile_drive = os.path.join(user_profile, "Google Drive", "My Drive")
            if os.path.exists(profile_drive):
                smile_backup = os.path.join(profile_drive, "SMILE BACKUP")
                found_drives.append({
                    'letter': 'U',
                    'drive_root': os.path.join(user_profile, "Google Drive"),
                    'my_drive': profile_drive,
                    'smile_backup': smile_backup,
                    'is_existing': os.path.exists(smile_backup),
                    'is_google_drive': True,
                    'label': "Google Drive (User Profile)"
                })

        # Doc config hien tai
        cfg = load_config()
        current_paths = cfg.get("GOOGLE_DRIVE_PATHS", [])
        current_subfolder = cfg.get("GOOGLE_DRIVE_SUBFOLDER", "SMILE BACKUP")

        print(f"   --- Duong dan hien tai trong config ---")
        for i, p in enumerate(current_paths, 1):
            print(f"   {i}. {p}")
        print(f"   Thu muc con: {current_subfolder}")
        print()

        # Hien thi danh sach Google Drive phat hien duoc
        if found_drives:
            print(f"   === Google Drive phat hien duoc ===")
            print(f"   {'STT':<5} {'Nhan':<25} {'Duong dan':<50} {'SMILE BACKUP?':<15}")
            print(f"   {'-'*5} {'-'*25} {'-'*50} {'-'*15}")
            for i, d in enumerate(found_drives, 1):
                existing_str = "CO" if d['is_existing'] else "CHUA CO"
                print(f"   {i:<5} {d['label']:<25} {d['my_drive']:<50} {existing_str:<15}")
            print()

        # Hien thi danh sach o dia khac
        if other_drives:
            print(f"   === O dia khac (co the dung luu backup) ===")
            print(f"   {'STT':<5} {'Nhan':<25} {'Duong dan':<50}")
            print(f"   {'-'*5} {'-'*25} {'-'*50}")
            for i, d in enumerate(other_drives, len(found_drives) + 1):
                print(f"   {i:<5} {d['label']:<25} {d['drive_root']:<50}")
            print()

        print("   Tuy chon:")
        print(f"   - Nhap STT (1-{len(found_drives) + len(other_drives)}) de chon o dia")
        print(f"   - Nhap 'N' de nhap duong dan thu cong") 
        print(f"   - Nhap '0' de quay lai menu")
        print()

        choice = input("   Lua chon: ").strip()

        if choice == '0':
            return

        if choice.lower() == 'n':
            # Nhap duong dan thu cong
            print("\n   Nhap duong dan day du den thu muc muon luu backup")
            print("   Vi du: D:\\Backup\\SMILE_BACKUP hoac \\\\SERVER\\share\\backup")
            print("   (Thu muc SMILE BACKUP se duoc tao tu dong neu chua co)")
            custom_path = input("\n   Duong dan: ").strip().strip('"').strip("'")

            if not custom_path:
                print("   [!] Duong dan khong duoc de trong.")
                continue

            # Kiem tra duong dan co ton tai thu muc cha khong
            parent_dir = custom_path
            if not os.path.exists(parent_dir):
                # Thu tao thu muc cha
                try:
                    os.makedirs(parent_dir, exist_ok=True)
                    print(f"   [OK] Da tao thu muc: {parent_dir}")
                except Exception as e:
                    print(f"   [!] Khong the tao thu muc: {e}")
                    input("   Nhan Enter de thu lai...")
                    continue

            # Kiem tra/tao thu muc SMILE BACKUP
            smile_dir = os.path.join(parent_dir, current_subfolder) if current_subfolder in parent_dir else os.path.join(parent_dir, "SMILE BACKUP") if "SMILE BACKUP" not in custom_path else custom_path
            if not os.path.exists(smile_dir) and "SMILE BACKUP" not in custom_path:
                if confirm(f"   Tao thu muc '{smile_dir}'? (Y/N): "):
                    try:
                        os.makedirs(smile_dir, exist_ok=True)
                        print(f"   [OK] Da tao thu muc: {smile_dir}")
                    except Exception as e:
                        print(f"   [!] Loi tao thu muc: {e}")
                        input("   Nhan Enter de thu lai...")
                        continue

            # Cap nhat config
            # Su dung custom_path lam base, them SMILE BACKUP vao
            if "SMILE BACKUP" in custom_path or current_subfolder in custom_path:
                base_path = custom_path
                final_path = custom_path
            else:
                base_path = custom_path
                final_path = os.path.join(custom_path, current_subfolder)

            cfg["GOOGLE_DRIVE_PATHS"] = [base_path]
            save_config(cfg)
            print(f"\n   [OK] Da cap nhat duong dan: {base_path}")
            print(f"   [OK] Thu muc backup: {final_path}")
            input("   Nhan Enter de quay lai...")
            return

        # Chon STT
        try:
            idx = int(choice)
            total_drives = found_drives + other_drives
            if idx < 1 or idx > len(total_drives):
                print(f"   [!] STT khong hop le. Chon tu 1 den {len(total_drives)}")
                input("   Nhan Enter de thu lai...")
                continue

            selected = total_drives[idx - 1]

            if selected['is_google_drive']:
                # La Google Drive - mo duyet thu muc ben trong
                start_browse = selected['my_drive']
                print(f"\n   Mo duyet thu muc trong {selected['label']}...")
                print(f"   Hay chon hoac tao thu muc de luu backup.")
                input("   Nhan Enter de bat dau duyet...")

                chosen = browse_folder(start_browse)
                if chosen is None:
                    print("   [!] Da huy chon thu muc.")
                    input("   Nhan Enter de thu lai...")
                    continue

                # Tinh toan base_path va subfolder tu duong dan da chon
                my_drive = selected['my_drive']
                if chosen == my_drive:
                    # Chon chinh My Drive - dung subfolder mac dinh
                    cfg["GOOGLE_DRIVE_PATHS"] = [my_drive]
                    final_path = os.path.join(my_drive, current_subfolder)
                else:
                    # Chon thu muc con - tính relative path
                    rel = os.path.relpath(chosen, os.path.dirname(my_drive))
                    # Tach base va subfolder
                    # Vi du: chosen = G:\My Drive\SMILE BACKUP → base = G:\My Drive, subfolder = SMILE BACKUP
                    # Vi du: chosen = G:\My Drive\Work\Backups → base = G:\My Drive, subfolder = Work\Backups
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

                # Kiem tra/tao thu muc SMILE BACKUP neu can
                if not os.path.exists(final_path):
                    if confirm(f"   Tao thu muc '{final_path}'? (Y/N): "):
                        try:
                            os.makedirs(final_path, exist_ok=True)
                            print(f"   [OK] Da tao thu muc: {final_path}")
                        except Exception as e:
                            print(f"   [!] Loi tao thu muc: {e}")
                            input("   Nhan Enter de thu lai...")
                            continue

                save_config(cfg)
                print(f"\n   [OK] Da cap nhat duong dan Google Drive!")
                print(f"   [OK] Thu muc backup: {final_path}")
                input("   Nhan Enter de quay lai...")
                return
            else:
                # La o dia thuong - mo duyet thu muc
                start_browse = selected['drive_root']
                print(f"\n   Mo duyet thu muc trong {selected['label']}...")
                print(f"   Hay chon hoac tao thu muc de luu backup.")
                input("   Nhan Enter de bat dau duyet...")

                chosen = browse_folder(start_browse)
                if chosen is None:
                    print("   [!] Da huy chon thu muc.")
                    input("   Nhan Enter de thu lai...")
                    continue

                # Tinh toan base va subfolder
                drive_root = selected['drive_root']
                if chosen == drive_root:
                    # Chon chinh o dia - dung ten mac dinh
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

                # Kiem tra/tao thu muc
                if not os.path.exists(final_path):
                    if confirm(f"   Tao thu muc '{final_path}'? (Y/N): "):
                        try:
                            os.makedirs(final_path, exist_ok=True)
                            print(f"   [OK] Da tao thu muc: {final_path}")
                        except Exception as e:
                            print(f"   [!] Loi tao thu muc: {e}")
                            input("   Nhan Enter de thu lai...")
                            continue
                    else:
                        print("   [!] Da huy.")
                        continue

                save_config(cfg)
                print(f"\n   [OK] Da cap nhat duong dan: {drive_root}")
                print(f"   [OK] Thu muc backup: {final_path}")
                input("   Nhan Enter de quay lai...")
                return

        except ValueError:
            print("   [!] Nhap khong hop le.")
            input("   Nhan Enter de thu lai...")
            continue

# ==================== FEATURE 2: DUYET FILE O GOC (REMOTE) ====================
def browse_remote_files():
    """Duyet file backup tai thu muc nguon (Remote)"""
    clear_screen()
    print_header("DUYET FILE TAI O DIA GOC (REMOTE)")

    cfg = load_config()
    source_dir = cfg["SOURCE_DIR"]

    print(f"\n   Thu muc nguon: {source_dir}")
    print("   Dang lay danh sach file...\n")

    if not os.path.exists(source_dir):
        print(f"   [!] Khong the truy cap: {source_dir}")
        print("   [!] Kiem tra lai ket noi mang hoac o dia.")
        input("\n   Nhan Enter de quay lai...")
        return

    files = get_files_in_dir(source_dir)

    if not files:
        print("   [!] Khong co file nao trong thu muc.")
        input("\n   Nhan Enter de quay lai...")
        return

    # Thong ke theo ngay
    days = get_unique_days(files)
    print(f"   Tong cong: {len(files)} file, {len(days)} ngay backup\n")
    print_files_table(files)

    print(f"\n   --- THONG KE THEO NGAY ---")
    for day_key, day_files in days:
        total_size = sum(f['size'] for f in day_files)
        print(f"   {day_key}: {len(day_files)} file, {format_size(total_size)}")

    input("\n   Nhan Enter de quay lai...")

# ==================== FEATURE 3: DUYET FILE GOOGLE DRIVE ====================
def browse_drive_files():
    """Duyet file backup tai Google Drive"""
    clear_screen()
    print_header("DUYET FILE TAI GOOGLE DRIVE")

    cfg = load_config()
    drive_paths = cfg["GOOGLE_DRIVE_PATHS"]
    subfolder = cfg["GOOGLE_DRIVE_SUBFOLDER"]
    profile_path = cfg["GOOGLE_DRIVE_PROFILE_PATH"]

    # Tim duong dan Drive
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
        print("   [!] Khong tim thay Google Drive!")
        input("\n   Nhan Enter de quay lai...")
        return

    print(f"   Thu muc Drive: {target_dir}")
    print("   Dang lay danh sach file...\n")

    if not os.path.exists(target_dir):
        print(f"   [!] Thu muc chua ton tai: {target_dir}")
        input("\n   Nhan Enter de quay lai...")
        return

    files = get_files_in_dir(target_dir)

    if not files:
        print("   [!] Khong co file backup nao tren Drive.")
        input("\n   Nhan Enter de quay lai...")
        return

    # Thong ke theo ngay
    days = get_unique_days(files)
    print(f"   Tong cong: {len(files)} file, {len(days)} ngay backup\n")
    print_files_table(files)

    print(f"\n   --- THONG KE THEO NGAY ---")
    for day_key, day_files in days:
        total_size = sum(f['size'] for f in day_files)
        print(f"   {day_key}: {len(day_files)} file, {format_size(total_size)}")

    input("\n   Nhan Enter de quay lai...")

# ==================== FEATURE 4: DON DEP CA 2 O ====================
def cleanup_all_drives():
    """Don dep file backup o ca Remote va Drive, chi chua lai 3 ngay"""
    clear_screen()
    print_header("DON DEP FILE BACKUP (CHUA LAI 3 NGAY MOI NHAT)")

    KEEP_DAYS = 3
    cfg = load_config()

    print(f"\n   [!] SE XOA TAT CA FILE BACKUP CUA HON {KEEP_DAYS} NGAY")
    print(f"   [!] Chi chua lai {KEEP_DAYS} ngay backup moi nhat")
    print()

    # --- Don dep Remote ---
    source_dir = cfg["SOURCE_DIR"]
    source_deleted = 0
    source_freed = 0

    if os.path.exists(source_dir):
        print(f"   --- Don dep Remote: {source_dir} ---")
        files = get_files_in_dir(source_dir)
        if files:
            days = get_unique_days(files)
            keep_days_list = [d[0] for d in days[:KEEP_DAYS]]

            for day_key, day_files in days:
                if day_key in keep_days_list:
                    print(f"   [GIU] {day_key}: {len(day_files)} file")
                else:
                    print(f"   [XOA] {day_key}: {len(day_files)} file")
                    for f in day_files:
                        try:
                            sz = f['size']
                            os.remove(f['path'])
                            source_deleted += 1
                            source_freed += sz
                        except Exception as e:
                            print(f"      [!] Loi xoa {f['name']}: {e}")
        else:
            print("   [!] Khong co file nao tai Remote.")
    else:
        print(f"   [!] Khong the truy cap Remote: {source_dir}")

    print()

    # --- Don dep Google Drive ---
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
        print(f"   --- Don dep Google Drive: {drive_dir} ---")
        drive_files = get_files_in_dir(drive_dir)
        if drive_files:
            days = get_unique_days(drive_files)
            keep_days_list = [d[0] for d in days[:KEEP_DAYS]]

            for day_key, day_files in days:
                if day_key in keep_days_list:
                    print(f"   [GIU] {day_key}: {len(day_files)} file")
                else:
                    print(f"   [XOA] {day_key}: {len(day_files)} file")
                    for f in day_files:
                        try:
                            sz = f['size']
                            os.remove(f['path'])
                            drive_deleted += 1
                            drive_freed += sz
                        except Exception as e:
                            print(f"      [!] Loi xoa {f['name']}: {e}")
        else:
            print("   [!] Khong co file nao tren Drive.")
    else:
        print("   [!] Khong the truy cap Google Drive.")

    # Tong ket
    print(f"\n{'='*60}")
    print(f"   KET QUA DON DEP:")
    print(f"   Remote:       Xoa {source_deleted} file, giai phong {format_size(source_freed)}")
    print(f"   Google Drive:  Xoa {drive_deleted} file, giai phong {format_size(drive_freed)}")
    print(f"{'='*60}")
    input("\n   Nhan Enter de quay lai...")

# ==================== FEATURE 5: DUYET & XOA THEO KHOI TAI REMOTE ====================
def browse_and_delete_remote():
    """Truy cap Remote, tong hop theo ngay, cho phep chon xoa theo khoi (bat buoc chua lai toi thieu 3 ngay)"""
    clear_screen()
    print_header("DUYET & XOA THEO KHOI TAI REMOTE")

    MIN_KEEP_DAYS = 3
    cfg = load_config()
    source_dir = cfg["SOURCE_DIR"]

    print(f"   Thu muc nguon: {source_dir}")
    print("   Dang lay danh sach file...\n")

    if not os.path.exists(source_dir):
        print(f"   [!] Khong the truy cap: {source_dir}")
        input("\n   Nhan Enter de quay lai...")
        return

    files = get_files_in_dir(source_dir)
    if not files:
        print("   [!] Khong co file nao trong thu muc.")
        input("\n   Nhan Enter de quay lai...")
        return

    days = get_unique_days(files)
    total_days = len(days)

    print(f"   Tong cong {len(files)} file, {total_days} ngay backup\n")
    print(f"   {'STT':<5} {'Ngay':<15} {'So file':<10} {'Kich thuoc':<15} {'Trang thai':<15}")
    print(f"   {'-'*5} {'-'*15} {'-'*10} {'-'*15} {'-'*15}")

    for i, (day_key, day_files) in enumerate(days, 1):
        total_size = sum(f['size'] for f in day_files)
        status = "DUOC GIU" if i <= MIN_KEEP_DAYS else "Co the xoa"
        print(f"   {i:<5} {day_key:<15} {len(day_files):<10} {format_size(total_size):<15} {status:<15}")

    print(f"\n   [!] Bat buoc chua lai toi thieu {MIN_KEEP_DAYS} ngay moi nhat (danh so 1-{min(MIN_KEEP_DAYS, total_days)})")
    print()

    # Cho chon ngay de xoa
    max_deletable = total_days - MIN_KEEP_DAYS
    if max_deletable <= 0:
        print(f"   [!] Chi co {total_days} ngay backup, khong du ngay de xoa (can toi thieu {MIN_KEEP_DAYS}).")
        input("\n   Nhan Enter de quay lai...")
        return

    print(f"   Cac ngay co the xoa: {MIN_KEEP_DAYS + 1} den {total_days}")

    while True:
        print(f"\n   Nhap so thu tu ngay muon xoa (vi du: 4,5,6 hoac 4-8)")
        print(f"   Nhap 'list' de xem lai, '0' de quay lai menu")
        choice = input("   Lua chon: ").strip()

        if choice == '0':
            return
        if choice.lower() == 'list':
            # Hien thi lai danh sach
            clear_screen()
            print_header("DUYET & XOA THEO KHOI TAI REMOTE")
            print(f"   {'STT':<5} {'Ngay':<15} {'So file':<10} {'Kich thuoc':<15}")
            for i, (day_key, day_files) in enumerate(days, 1):
                total_size = sum(f['size'] for f in day_files)
                protected = " (DUOC GIU)" if i <= MIN_KEEP_DAYS else ""
                print(f"   {i:<5} {day_key:<15} {len(day_files):<10} {format_size(total_size):<15}{protected}")
            continue

        # Parse lua chon (vi du: "4,5,6" hoac "4-8")
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

            # Kiem tra xem co chon ngay duoc bao ve khong
            protected = [idx for idx in selected_indices if idx <= MIN_KEEP_DAYS]
            if protected:
                print(f"   [!] KHONG THE XOA cac ngay {protected} (bat buoc chua lai {MIN_KEEP_DAYS} ngay!)")
                continue

            # Kiem tra xem so thu tu hop le khong
            invalid = [idx for idx in selected_indices if idx < 1 or idx > total_days]
            if invalid:
                print(f"   [!] So thu tu khong hop le: {invalid}")
                continue

            if not selected_indices:
                continue

            # Hien thi xac nhan
            total_files_to_delete = 0
            total_size_to_delete = 0
            print(f"\n   Se xoa {len(selected_indices)} ngay backup sau:")
            for idx in sorted(selected_indices):
                day_key, day_files = days[idx - 1]
                day_size = sum(f['size'] for f in day_files)
                print(f"     - {day_key}: {len(day_files)} file, {format_size(day_size)}")
                total_files_to_delete += len(day_files)
                total_size_to_delete += day_size

            print(f"\n   Tong cong: Xoa {total_files_to_delete} file, giai phong {format_size(total_size_to_delete)}")

            if confirm("   Xac nhan xoa? (Y/N): "):
                # Thuc hien xoa
                actual_deleted = 0
                for idx in sorted(selected_indices, reverse=True):
                    day_key, day_files = days[idx - 1]
                    for f in day_files:
                        try:
                            os.remove(f['path'])
                            actual_deleted += 1
                        except Exception as e:
                            print(f"      [!] Loi xoa {f['name']}: {e}")
                print(f"\n   [OK] Da xoa {actual_deleted} file thanh cong!")
                input("   Nhan Enter de quay lai...")
                return
            else:
                print("   [!] Da huy xoa.")
                continue

        except (ValueError, IndexError):
            print("   [!] Nhap khong hop le. Vi du: 4,5,6 hoac 4-8")
            continue

# ==================== MAIN MENU ====================
def main():
    # Kiem tra moi truong luc khoi dong
    env_ok = False
    setup_env_path = os.path.join(SCRIPT_DIR, "setup_env.py")
    if os.path.exists(setup_env_path):
        if SCRIPT_DIR not in sys.path:
            sys.path.insert(0, SCRIPT_DIR)
        try:
            import setup_env
            missing = setup_env.get_missing_critical_packages()
            if not missing:
                env_ok = True
        except Exception:
            pass

    while True:
        clear_screen()
        print_header("SMILE BACKUP MANAGER")
        print()

        # Hien thi trang thai moi truong
        if env_ok:
            print("   [OK] Moi truong: San sang")
        else:
            print("   [!] Moi truong: Can kiem tra/cai dat thu vien")

        print()
        print("   1. Chay tu dong backup SMILE")
        print("   2. Cap nhat duong dan Google Drive")
        print("   3. Duyet file tai o dia goc (Remote)")
        print("   4. Duyet file tai Google Drive")
        print("   5. Don dep file backup (chua lai 3 ngay moi nhat)")
        print("   6. Duyet & xoa theo khoi tai Remote")
        print("   7. Kiem tra & cai dat moi truong")
        print("   0. Thoat")
        print()

        choice = input("   Chon chuc nang [0-7]: ").strip()

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
        elif choice == '7':
            full_environment_check_and_fix()
            # Update env status after check/install
            if os.path.exists(setup_env_path):
                try:
                    import setup_env
                    missing = setup_env.get_missing_critical_packages()
                    env_ok = len(missing) == 0
                except Exception:
                    env_ok = False
        elif choice == '0':
            print("\n   Tam biet!")
            time.sleep(1)
            break
        else:
            print("   [!] Lua chon khong hop le.")
            time.sleep(1)

if __name__ == "__main__":
    main()
