# HƯỚNG DẪN SỬ DỤNG HỆ THỐNG TỰ ĐỘNG SAO LƯU SMILE
(SMILE Automation Backup & Manager System)

Hệ thống này cung cấp giải pháp tự động hóa toàn bộ quy trình mở phần mềm SMILE FO, đăng nhập, nhấn lệnh sao lưu dữ liệu cơ sở dữ liệu (Database) và đồng bộ tệp sao lưu mới nhất lên Google Drive. Đồng thời, công cụ quản lý đi kèm giúp người dùng dễ dàng cấu hình đường dẫn và quản lý, dọn dẹp các tệp sao lưu cũ.

---

## 1. Cấu trúc Dự án
Dự án được tối giản gọn gàng với các tệp tin chính sau:
* **`manager.py`**: Trình quản lý giao diện dòng lệnh (Menu tương tác bằng Tiếng Việt có dấu).
* **`autoBackupSMILE.py`**: Kịch bản chính thực hiện tự động hóa quy trình sao lưu (không cần tương tác người dùng).
* **`config.json`**: Tệp cấu hình chứa các thông số tài khoản, đường dẫn và các tọa độ click chuột trên màn hình.
* **`backup_log.txt`**: Tệp nhật ký ghi lại lịch sử các lần chạy sao lưu tự động và thông tin lỗi chi tiết nếu có.

---

## 2. Hướng dẫn thiết lập tệp Cấu hình (`config.json`)
Trước khi vận hành, bạn cần cấu hình các thông số phù hợp với máy tính chạy công cụ trong tệp `config.json`.

```json
{
    "SMILE_PATH": "C:\\Program Files (x86)\\SMILE\\SMILEFO.exe", // Đường dẫn cài đặt phần mềm SMILE
    "USER": "IT",                                               // Tên đăng nhập vào SMILE
    "PASS": "123@123a",                                         // Mật khẩu đăng nhập vào SMILE
    "SOURCE_DIR": "\\\\192.168.1.2\\smile$",                    // Thư mục chứa tệp sao lưu gốc (.dat)
    "GOOGLE_DRIVE_PATHS": [
        "H:\\My Drive"                                          // Danh sách ổ đĩa Google Drive trên máy
    ],
    "GOOGLE_DRIVE_SUBFOLDER": "BACKUP SMILE",                   // Tên thư mục con dùng lưu dữ liệu trên Drive
    "GOOGLE_DRIVE_PROFILE_PATH": "Google Drive\\My Drive\\SMILE BACKUP",
    "MORE_OPTIONS_COORDS": [759, 408],                           // Tọa độ nút "More Options" (X, Y)
    "BACKUP_DB_COORDS": [800, 324],                             // Tọa độ nút "Backup DB" (X, Y)
    "OK_BTN_COORDS": [662, 447],                                // Tọa độ nút "OK" khi hoàn tất sao lưu (X, Y)
    "BACKUP_DURATION": 5,                                       // Thời gian chờ SMILE xử lý file sao lưu (giây)
    "SMILE_STARTUP_WAIT": 7,                                    // Thời gian chờ SMILE khởi động lên (giây)
    "LOGIN_WAIT": 10,                                           // Thời gian chờ tải sau khi đăng nhập (giây)
    "BACKUP_OK_RETRIES": 5,                                     // Số lần thử lại nhấn xác nhận OK khi sao lưu xong
    "BACKUP_OK_RETRY_DELAY": 3,                                 // Thời gian giữa các lần thử nhấn OK (giây)
    "CLICK_RETRIES": 3,                                         // Số lần thử lại tối đa cho thao tác click chuột
    "CLICK_RETRY_DELAY": 2,                                     // Thời gian chờ giữa các lần click lại (giây)
    "WINDOW_GET_TIMEOUT": 20,                                   // Thời gian tối đa chờ nhận diện cửa sổ SMILE (giây)
    "WINDOW_GET_RETRY_INTERVAL": 3,                             // Tần suất quét tìm lại cửa sổ SMILE (giây)
    "SMILE_EXIT_KEY": "0",                                      // Phím tắt để thoát khỏi phần mềm SMILE
    "TERMINAL_CLOSE_DELAY": 10                                  // Thời gian chờ trước khi tự động đóng terminal (giây)
}
```

---

## 3. Hướng dẫn sử dụng Trình Quản lý (`manager.py`)
Để khởi động trình quản lý, hãy mở Terminal (Command Prompt) tại thư mục dự án và chạy lệnh:
```bash
python manager.py
```
Giao diện hiển thị Menu Tiếng Việt có dấu trực quan với các chức năng chính:

```text
============================================================
  SMILE BACKUP MANAGER
============================================================

   1. Chạy tự động backup SMILE
   2. Cập nhật đường dẫn Google Drive
   3. Duyệt file tại ổ địa gốc (Remote)
   4. Duyệt file tại Google Drive
   5. Dọn dẹp file backup (chừa lại 3 ngày mới nhất)
   6. Duyệt & xóa theo khối tại Remote
   0. Thoát

   Chọn chức năng [0-6]:
```

### Chi tiết các chức năng:
* **Phím `1` (Chạy tự động backup SMILE)**: Khởi chạy trực tiếp tệp `autoBackupSMILE.py`. Hệ thống sẽ bắt đầu điều khiển tự động.
* **Phím `2` (Cập nhật đường dẫn Google Drive)**:
  * Tự động quét các phân vùng ổ đĩa và thư mục người dùng trên máy để định vị ứng dụng Google Drive.
  * Kiểm tra xem trên ổ đĩa đó đã tồn tại thư mục lưu sao lưu hay chưa (tự động nhận diện bất kỳ thư mục con nào có chứa chữ "backup", ví dụ: `BACKUP SMILE`, `SMILE BACKUP`).
  * Cho phép bạn nhập đường dẫn thư mục tùy ý hoặc tạo thư mục mới trực tiếp để lưu sao lưu.
* **Phím `3` (Duyệt file tại ổ đĩa gốc - Remote)**: Hiển thị bảng tổng hợp danh sách các tệp tin sao lưu hiện có tại thư mục nguồn `SOURCE_DIR` theo thứ tự thời gian, thống kê chi tiết dung lượng theo từng ngày.
* **Phím `4` (Duyệt file tại Google Drive)**: Duyệt tệp và thống kê dung lượng tệp tin đã tải lên thư mục lưu trữ của Google Drive.
* **Phím `5` (Dọn dẹp file backup)**: Tiến hành quét dọn đồng thời cả ở thư mục nguồn (Remote) và Google Drive, tự động xóa các file cũ và **chỉ giữ lại dữ liệu của 3 ngày gần nhất** để tiết kiệm dung lượng ổ cứng.
* **Phím `6` (Duyệt & xóa theo khối tại Remote)**: Hiển thị danh sách thống kê file theo ngày trên thư mục nguồn. Cho phép bạn nhập STT ngày muốn xóa (ví dụ: `4,5,6` hoặc dải ngày `4-8`). Chức năng này bắt buộc giữ lại tối thiểu 3 ngày mới nhất để bảo vệ an toàn dữ liệu.
* **Phím `0` (Thoát)**: Đóng chương trình quản lý.

---

## 4. Cơ chế hoạt động của Tiến trình tự động (`autoBackupSMILE.py`)
Khi khởi chạy (qua phím `1` ở Manager hoặc chạy bằng lịch trình Task Scheduler của Windows):
1. **Kiểm tra kết nối & Desktop**:
   * Kiểm tra thư mục nguồn và thư mục đích trên Google Drive có kết nối ổn định không.
   * Kiểm tra xem màn hình máy tính có đang bị khóa (Lock) hay ngắt kết nối không. Nếu có, công cụ sẽ tự động gửi tín hiệu đánh thức màn hình trước khi thao tác.
2. **Khởi chạy ứng dụng**: Đóng các phiên bản SMILE đang treo và mở phiên bản mới sạch sẽ thông qua đường dẫn `SMILE_PATH`.
3. **Hiển thị cảnh báo**: Một thanh thông báo màu đỏ hiển thị sát mép trên màn hình:
   `⚠️ HỆ THỐNG ĐANG TỰ ĐỘNG SAO LƯU SMILE - VUI LÒNG KHÔNG THAO TÁC ⚠️` để cảnh báo nhân viên không nhấn chuột làm gián đoạn robot.
4. **Đăng nhập & Thao tác sao lưu**:
   * Robot tự động điền tài khoản, mật khẩu để đăng nhập vào SMILE.
   * Nhấp chuột chính xác vào tọa độ cấu hình của mục "More Options", xác nhận mật khẩu lớp thứ hai, và nhấp chọn lệnh "Backup Database".
5. **Đồng bộ đám mây (Cloud Sync)**:
   * Chờ quá trình nén file backup hoàn thành.
   * Tự động gửi phím `ENTER` hoặc nhấp tọa độ để tắt hộp thoại thông báo hoàn thành của SMILE.
   * Tìm tệp tin sao lưu mới nhất vừa tạo tại máy chủ nguồn, đổi tên định dạng đính kèm hậu tố `_BOT` và tải lên thư mục Google Drive kèm hiển thị thanh tiến trình sao chép `%`.
6. **Thoát phần mềm**: Thoát ứng dụng SMILE một cách an toàn và tự động tắt cửa sổ dòng lệnh Terminal sau 10 giây (hoặc thời gian cấu hình).

---

## 5. Hướng dẫn Khắc phục & Theo dõi Sự cố
Mọi hoạt động chạy tự động đều chạy ẩn và tinh giản thông tin hiển thị trên màn hình để tránh làm phiền người dùng. Khi hệ thống gặp sự cố, hãy thực hiện các bước sau:
1. **Xem Nhật ký lỗi**:
   Mở tệp **`backup_log.txt`** nằm cùng thư mục dự án. Mọi thông tin lỗi chi tiết (Traceback) từ Python khi phát sinh lỗi ngoài ý muốn sẽ được ghi nhận tại đây dưới dạng:
   ```text
   [2026-06-11 10:20:00] [!] Đã xảy ra lỗi trong quá trình tự động sao lưu.
   Detailed Error: ...
   ```
2. **Lỗi không đăng nhập hoặc click sai**:
   Nếu SMILE thay đổi giao diện hoặc độ phân giải màn hình máy tính thay đổi dẫn đến click sai, bạn chỉ cần mở chương trình SMILE, tìm tọa độ mới của các nút và cập nhật lại tọa độ `MORE_OPTIONS_COORDS`, `BACKUP_DB_COORDS`, và `OK_BTN_COORDS` trong tệp `config.json`.
