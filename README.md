Ứng dụng ký và xác minh file với Chữ Ký Số (RSA + SHA-512)
1. Giới thiệu:
- Đây là một ứng dụng web đơn giản được xây dựng bằng Flask (Python) cho phép người dùng ký điện tử các file bằng chữ ký số RSA và thuật toán băm SHA-512, sau đó xác minh tính toàn vẹn và nguồn gốc của file. Ứng dụng này được thiết kế để hoạt động cùng với các dịch vụ chia sẻ file ngang hàng (P2P) bên ngoài (như Snapdrop, Sharedrop, Send-Anywhere, Wormhole) để đảm bảo file gốc được truyền tải một cách an toàn và riêng tư, trong khi chữ ký số và public key được trao đổi qua một kênh riêng biệt (ví dụ: email, tin nhắn).
3. Tính năng chính:
- Tạo chữ ký số: Người gửi có thể chọn một file, ứng dụng sẽ tạo chữ ký số (sử dụng RSA với SHA-512) cho file đó và hiển thị chữ ký (Base64) cùng với public key tương ứng (PEM).
- Xác minh chữ ký số: Người nhận có thể tải lên file gốc đã nhận, cung cấp chữ ký số và public key từ người gửi để xác minh xem file có bị thay đổi trong quá trình truyền tải hay không và xác nhận nguồn gốc của file.
- Giao diện người dùng trực quan: Sử dụng Tailwind CSS để tạo giao diện hiện đại, dễ sử dụng với bố cục hai cột rõ ràng cho hai chức năng chính.
- RSA 2048-bit: Sử dụng thuật toán mã hóa bất đối xứng RSA với độ dài khóa 2048-bit, cung cấp mức độ bảo mật mạnh mẽ.
- SHA-512 Hashing: Sử dụng SHA-512 để tạo hàm băm của file, đảm bảo tính toàn vẹn dữ liệu.
- Tích hợp P2P Web Sharing (khuyến nghị): Hướng dẫn người dùng sử dụng các dịch vụ chia sẻ file P2P bên ngoài để truyền file gốc, tăng cường quyền riêng tư và bảo mật cho nội dung file
4. Cách hoạt động:
a. Ký File để Gửi
- Người gửi chọn một file từ máy tính của mình.
- Ứng dụng sẽ tính toán hàm băm SHA-512 của file.
- Sử dụng private_key (được tạo sẵn khi ứng dụng khởi động), ứng dụng ký lên hàm băm này, tạo ra chữ ký số.
- Chữ ký số (Base64) và public_key (PEM) sẽ được hiển thị trên giao diện.
- Quan trọng: Người gửi tự chia sẻ file gốc qua một dịch vụ P2P và gửi chữ ký số cùng public key cho người nhận qua một kênh an toàn riêng biệt (ví dụ: email, tin nhắn).
b. Nhận và Xác minh File
- Người nhận tải file gốc từ dịch vụ P2P mà người gửi đã sử dụng.
- Người nhận dán chữ ký số (Base64) và public key (PEM) nhận được từ người gửi vào các ô tương ứng trên giao diện.
- Ứng dụng sẽ tính toán hàm băm SHA-512 của file đã nhận.
- Sử dụng public_key được cung cấp và chữ ký số, ứng dụng sẽ xác minh liệu chữ ký có khớp với hàm băm của file đã nhận hay không.
- Kết quả xác minh (thành công hoặc thất bại kèm lý do) sẽ được hiển thị.
5. Yêu cầu cài đặt:
- Python 3.x
- Flask
- Cryptography
6. Hướng dẫn cài đặt và chạy:
- Bước 1: clone repository
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
- Bước 2: Cài đặt các thư viện:
pip install Flask cryptography
- Bước 3: chạy ứng dụng:
python app.py
chú ý: Ứng dụng sẽ chạy trên http://0.0.0.0:5000 (hoặc http://127.0.0.1:5000 trên máy cục bộ).
7. Cấu trúc thư mục:
8. Giải thích mã nguồn:
9. Lưu ý bảo mật:
10. ẢNh chụp màn hình:
