import time
import datetime
from pywinauto import Application

# ==================== CONFIG ====================
SMILE_PATH = r"C:\Program Files (x86)\SMILE\SMILEFO.exe"
USER = "IT"
PASS = "123@123a"
# ================================================

def find_and_click_text(window, target_text):
    """Hàm quét toàn bộ UI để tìm và click vào text mong muốn"""
    print(f"--> Đang truy tìm chữ: '{target_text}'...")
    try:
        # Lấy tất cả các thành phần con của cửa sổ
        elements = window.descendants()
        for el in elements:
            # Kiểm tra nếu text của element chứa chữ mình cần (không phân biệt hoa thường)
            if target_text.lower() in el.window_text().lower():
                print(f"   [+] Đã tìm thấy '{target_text}'. Đang Click...")
                el.click_input()
                return True
        print(f"   [-] Không tìm thấy chữ '{target_text}' trên màn hình hiện tại.")
        return False
    except Exception as e:
        print(f"   [!] Lỗi khi quét text: {e}")
        return False

def find_edit_controls(window):
    """Quét và tìm tất cả các ô nhập liệu (Edit/TextBox) trên cửa sổ"""
    edits = []
    try:
        for el in window.descendants():
            class_name = el.friendly_class_name()
            # Tìm các control có class là Edit, TextBox, hoặc tương tự
            if class_name in ["Edit", "TextBox", "ComboBox"]:
                edits.append(el)
                print(f"   [SCAN] Tìm thấy ô nhập liệu: class='{class_name}', text='{el.window_text()}'")
    except Exception as e:
        print(f"   [!] Lỗi khi quét ô nhập liệu: {e}")
    return edits

def fill_login_form(window, username, password):
    """Quét form login, tìm các ô input và điền User/Pass"""
    print("--> Đang quét tìm các ô nhập liệu trên form Đăng nhập...")
    edits = find_edit_controls(window)
    
    if len(edits) >= 2:
        # Thường ô đầu tiên = User, ô thứ hai = Password
        print(f"   [+] Tìm thấy {len(edits)} ô nhập liệu. Đang điền thông tin...")
        
        # Xóa nội dung cũ và nhập mới cho ô User
        try:
            edits[0].set_focus()
            edits[0].set_edit_text(username)
            print(f"   [+] Đã nhập User: '{username}' vào ô 1")
        except:
            edits[0].click_input()
            edits[0].type_keys("^a" + username, with_spaces=True)
            print(f"   [+] Đã gõ phím User: '{username}' vào ô 1 (dự phòng)")
        
        # Xóa nội dung cũ và nhập mới cho ô Password
        try:
            edits[1].set_focus()
            edits[1].set_edit_text(password)
            print(f"   [+] Đã nhập Password vào ô 2")
        except:
            edits[1].click_input()
            edits[1].type_keys("^a" + password, with_spaces=True)
            print(f"   [+] Đã gõ phím Password vào ô 2 (dự phòng)")
        
        return True
    elif len(edits) == 1:
        # Chỉ có 1 ô (có thể chỉ cần nhập Password)
        print(f"   [+] Chỉ tìm thấy 1 ô. Nhập Password vào ô duy nhất...")
        try:
            edits[0].set_focus()
            edits[0].set_edit_text(password)
        except:
            edits[0].click_input()
            edits[0].type_keys("^a" + password, with_spaces=True)
        return True
    else:
        print("   [-] Không tìm thấy ô nhập liệu nào. Thử gõ phím dự phòng...")
        window.type_keys(username + "{TAB}" + password)
        return False

def run_backup():
    try:
        print(f"--- BẮT ĐẦU QUY TRÌNH BACKUP DATA: {datetime.datetime.now()} ---")
        
        # 1. Khởi động SMILE
        app = Application(backend="win32").start(SMILE_PATH)
        time.sleep(5)
        
        # 2. Đăng nhập (Màn hình Login)
        print("--> Đang tìm và chờ form Màn hình Đăng nhập (Log In)...")
        login_found = False
        start_login_wait = time.time()
        
        while time.time() - start_login_wait < 30: # Chờ tối đa 30s
            try:
                top_login = app.top_window()
                win_text = top_login.window_text()
                
                # Quét text của cửa sổ hiện tại xem có phải là form Login không
                if "Log" in win_text or "Password" in win_text or "User" in win_text or "Login" in win_text:
                    login_found = True
                    print(f"--> Đã tìm thấy form Đăng nhập (Window: '{win_text}')!")
                    top_login.set_focus()
                    time.sleep(1)
                    
                    # Quét tìm ô input User/Pass và điền trực tiếp
                    fill_login_form(top_login, USER, PASS)
                    time.sleep(1)
                    
                    # Quét text để tìm và click nút đăng nhập trên form
                    if not find_and_click_text(top_login, "OK") and not find_and_click_text(top_login, "Log In") and not find_and_click_text(top_login, "Login"):
                        print("!! Không quét được text nút Đăng nhập, gửi phím ENTER dự phòng.")
                        top_login.type_keys("{ENTER}")
                    
                    print("--> Đã Gửi lệnh Đăng nhập thành công. Đợi 15s...")
                    time.sleep(15)
                    break
            except Exception as ex:
                print(f"   [!] Lỗi khi quét form login: {ex}")
            time.sleep(2)
            
        if not login_found:
            print("!! Không tìm thấy form đăng nhập sau 30s. Thử gõ phím dự phòng...")
            try:
                app.top_window().type_keys(USER + "{TAB}" + PASS + "{ENTER}")
                time.sleep(15)
            except:
                pass

        # 3. Xử lý bảng Sinh nhật
        top_win = app.top_window()
        if "Happy" in top_win.window_text() or "Birth" in top_win.window_text():
            print("!!! Phát hiện bảng Sinh nhật. Đang tìm nút 'Close' để đóng...")
            if not find_and_click_text(top_win, "Close"):
                top_win.type_keys("{ESC}") 
            time.sleep(3)

        # 4. Gửi phím '0' để vào More Options
        # Lấy cửa sổ chính SMILE
        all_wins = app.windows(title_re=".*SMILE.*")
        main_win = max(all_wins, key=lambda w: w.rectangle().width() * w.rectangle().height())
        main_win.set_focus()
        
        print("--> Gửi phím '0' để chọn More Options...")
        main_win.type_keys("0")
        time.sleep(5)

        # 5. Xác thực mật khẩu lần 2 (nếu có hiện bảng Login tiếp theo)
        auth_dlg = app.top_window()
        auth_text = auth_dlg.window_text()
        if "Log" in auth_text or "Password" in auth_text or "User" in auth_text or "Login" in auth_text:
            print(f"--> Phát hiện form xác thực lần 2 (Window: '{auth_text}')...")
            auth_dlg.set_focus()
            time.sleep(1)
            
            # Quét tìm ô input và điền User/Pass
            fill_login_form(auth_dlg, USER, PASS)
            time.sleep(1)
            
            # Quét text nút OK/Login để click
            if not find_and_click_text(auth_dlg, "OK") and not find_and_click_text(auth_dlg, "Log In") and not find_and_click_text(auth_dlg, "Login"):
                print("!! Không quét được nút đăng nhập lần 2, gửi phím ENTER dự phòng.")
                auth_dlg.type_keys("{ENTER}")
            time.sleep(5)

        # 6. Gửi chữ 'A' để chạy Backup Database
        options_win = app.top_window()
        options_win.set_focus()
        print("--> Gửi chữ 'a' để tiến hành Backup Database...")
        options_win.type_keys("a")
            
        # 7. Treo máy đợi nút OK và tắt popup (1-2 phút)
        print("--> ĐANG CHẠY BACKUP... Đợi hiện tab popup và nút OK (1-2 phút)...")
        # Nghỉ 60 giây trước khi quét liên tục cho đỡ nặng CPU vì DB backup mất thời gian
        time.sleep(60)
        
        start_wait = time.time()
        while True:
            try:
                popup = app.top_window()
                # Quét xem có chữ OK trên màn hình popup không
                if find_and_click_text(popup, "OK"):
                    print("--> THÀNH CÔNG! Đã bấm nút OK hoàn tất trên popup.")
                    break
            except:
                pass
            
            # Timeout 10 phút để tránh bị treo vĩnh viễn
            if time.time() - start_wait > 600:
                print("!! Quá thời gian chờ (10 phút).")
                break
            time.sleep(5) # 5 giây quét 1 lần

        # 8. Thoát app (tắt)
        print("--> Hoàn tất chu trình. Đang đóng chuơng trình SMILE...")
        try:
            main_win.close()
        except:
            pass

    except Exception as e:
        print(f"!! Lỗi hệ thống: {e}")

if __name__ == "__main__":
    run_backup()
