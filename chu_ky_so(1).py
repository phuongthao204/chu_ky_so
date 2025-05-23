from flask import Flask, request, render_template_string
import os, hashlib, base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.exceptions import InvalidSignature

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
RECEIVED_FOLDER = "received"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RECEIVED_FOLDER, exist_ok=True)

# Khởi tạo RSA key pair (Chỉ tạo một lần khi ứng dụng khởi động)
private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
public_key = private_key.public_key()
public_pem = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
).decode()

# HTML Giao diện chính (có cải tiến để tích hợp Peer-to-Peer Web Sharing và 2 cột)
HTML = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Truyền - Nhận File có Chữ Ký Số (RSA + SHA-512)</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .message-box {
            padding: 0.75rem 1rem;
            border-radius: 0.5rem;
            font-size: 0.9rem;
            margin-top: 1rem;
        }
        .message-success {
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .message-error {
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .message-info {
            background-color: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }
        .file-input-label {
            display: block;
            padding: 0.5rem 1rem;
            background-color: #f0f4f8;
            border: 1px solid #cbd5e1;
            border-radius: 0.375rem;
            cursor: pointer;
            text-align: center;
            transition: background-color 0.2s ease;
        }
        .file-input-label:hover {
            background-color: #e2e8f0;
        }
    </style>
</head>
<body class="bg-gray-100 min-h-screen flex items-center justify-center p-4">
    <div class="max-w-6xl mx-auto p-8 bg-white rounded-xl shadow-lg space-y-8 w-full">
        <h1 class="text-3xl font-extrabold text-blue-700 text-center flex items-center justify-center gap-3">
            <span class="text-4xl">📩</span> Truyền - Nhận File có Chữ Ký Số
        </h1>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div class="border border-green-200 rounded-lg p-6 bg-green-50">
                <h2 class="text-xl font-bold text-green-800 mb-4 flex items-center gap-2">
                    <span class="text-2xl">🔐</span> Ký file để gửi
                </h2>
                <p class="text-sm text-gray-700 mb-4">
                    Chọn tệp bạn muốn ký. Sau khi ký, bạn sẽ nhận được chữ ký số và public key.
                    Bạn cần <strong class="text-green-700">tự chia sẻ tệp gốc này</strong> qua một dịch vụ chia sẻ trực tiếp như
                    <a href="https://snapdrop.net/" target="_blank" class="text-blue-600 hover:underline">Snapdrop.net</a>,
                    <a href="https://sharedrop.io/" target="_blank" class="text-blue-600 hover:underline">Sharedrop.io</a>,
                    <a href="https://send-anywhere.com/" target="_blank" class="text-blue-600 hover:underline">Send-Anywhere.com</a>, hoặc
                    <a href="https://wormhole.app/" target="_blank" class="text-blue-600 hover:underline">Wormhole.app</a>.
                    Gửi <strong class="text-green-700">chữ ký số</strong>, và <strong class="text-green-700">public key của bạn</strong> cho người nhận qua một kênh riêng (email, tin nhắn, v.v.).
                </p>
                <form method="POST" enctype="multipart/form-data" action="/sign_and_get_details" class="space-y-4">
                    <div>
                        <label for="file_to_sign" class="file-input-label">
                            Chọn tệp để ký
                            <span id="file_to_sign_name" class="ml-2 text-gray-500"></span>
                        </label>
                        <input type="file" name="file" id="file_to_sign" class="hidden" required onchange="document.getElementById('file_to_sign_name').innerText = this.files[0].name || ''">
                    </div>
                    <button type="submit" class="w-full bg-green-600 text-white px-5 py-2.5 rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 transition-colors duration-200">
                        Ký file và nhận thông tin
                    </button>
                </form>
                {% if signed_data %}
                <div class="mt-6 p-4 bg-gray-100 rounded-lg border border-gray-200 space-y-4">
                    <p class="text-lg font-semibold text-gray-800">Thông tin sau khi ký:</p>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Chữ ký số (Base64):</label>
                        <textarea readonly class="w-full border border-gray-300 p-2 rounded-md bg-white text-gray-800 text-xs font-mono resize-y" rows="4" onclick="this.select()">{{ signed_data.signature }}</textarea>
                        <button onclick="navigator.clipboard.writeText(this.previousElementSibling.value)" class="mt-2 bg-blue-500 text-white px-3 py-1.5 rounded-md hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors duration-200 text-sm">
                            Sao chép Chữ ký
                        </button>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Public Key (PEM):</label>
                        <textarea readonly class="w-full border border-gray-300 p-2 rounded-md bg-white text-gray-800 text-xs font-mono resize-y" rows="8" onclick="this.select()">{{ signed_data.public_key }}</textarea>
                        <button onclick="navigator.clipboard.writeText(this.previousElementSibling.value)" class="mt-2 bg-blue-500 text-white px-3 py-1.5 rounded-md hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors duration-200 text-sm">
                            Sao chép Public Key
                        </button>
                    </div>
                    <p class="text-sm text-red-700 font-semibold mt-4">
                        ⚠️ Quan trọng: Hãy tự chia sẻ tệp gốc đã ký qua một dịch vụ chia sẻ trực tiếp và gửi Chữ ký số và Public Key trên cho người nhận.
                    </p>
                </div>
                {% endif %}
                {% if sent_message %}
                <p class="message-box {% if 'Lỗi' in sent_message %}message-error{% else %}message-success{% endif %}">
                    {{ sent_message }}
                </p>
                {% endif %}
            </div>

            <div class="border border-purple-200 rounded-lg p-6 bg-purple-50">
                <h2 class="text-xl font-bold text-purple-800 mb-4 flex items-center gap-2">
                    <span class="text-2xl">📥</span> Nhận và xác minh file
                </h2>
                <p class="text-sm text-gray-700 mb-4">
                    Người nhận cần tải tệp gốc từ dịch vụ chia sẻ trực tiếp mà người gửi đã sử dụng.
                    Sau đó, dán chữ ký số và public key được cung cấp bởi người gửi vào đây.
                </p>
                <form method="POST" enctype="multipart/form-data" action="/receive" class="space-y-4">
                    <div>
                        <label for="file_receive" class="file-input-label">
                            Chọn tệp đã nhận (từ dịch vụ chia sẻ)
                            <span id="file_receive_name" class="ml-2 text-gray-500"></span>
                        </label>
                        <input type="file" name="file" id="file_receive" class="hidden" required onchange="document.getElementById('file_receive_name').innerText = this.files[0].name || ''">
                    </div>
                    <textarea name="signature" placeholder="Dán chữ ký (base64) từ người gửi" class="w-full border border-gray-300 p-3 rounded-md focus:ring-purple-500 focus:border-purple-500" rows="4" required></textarea>
                    <textarea name="pubkey" placeholder="Dán public key (PEM) của người gửi" class="w-full border border-gray-300 p-3 rounded-md focus:ring-purple-500 focus:border-purple-500" rows="6" required></textarea>
                    <button type="submit" class="w-full bg-purple-600 text-white px-5 py-2.5 rounded-md hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 transition-colors duration-200">
                        Xác minh file
                    </button>
                </form>
                {% if verify_message %}
                <p class="message-box {% if 'thất bại' in verify_message %}message-error{% else %}message-success{% endif %}">
                    {{ verify_message }}
                </p>
                {% endif %}
            </div>
        </div>
    </div>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def home():
    return render_template_string(HTML)

@app.route("/sign_and_get_details", methods=["POST"])
def sign_and_get_details():
    file = request.files.get("file")

    if not file:
        return render_template_string(HTML, sent_message="❌ Lỗi: Vui lòng chọn tệp để ký.")

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    try:
        file.save(filepath)
    except Exception as e:
        return render_template_string(HTML, sent_message=f"❌ Lỗi khi lưu tệp: {e}")

    with open(filepath, "rb") as f:
        data = f.read()

    # Tạo chữ ký
    digest = hashlib.sha512(data).digest()
    try:
        signature = private_key.sign(
            digest,
            padding.PKCS1v15(),
            hashes.SHA512()
        )
        signature_b64 = base64.b64encode(signature).decode()
        
        # Trả về chữ ký và public key để người dùng sao chép
        signed_data = {
            "signature": signature_b64,
            "public_key": public_pem
        }
        return render_template_string(HTML, signed_data=signed_data)

    except Exception as e:
        return render_template_string(HTML, sent_message=f"❌ Lỗi khi tạo chữ ký: {e}")

@app.route("/receive", methods=["POST"])
def receive():
    file = request.files.get("file")
    signature_b64 = request.form.get("signature")
    pubkey_pem = request.form.get("pubkey")

    if not file or not signature_b64 or not pubkey_pem:
        return render_template_string(HTML, verify_message="❌ Lỗi: Vui lòng cung cấp đầy đủ tệp, chữ ký và public key.")

    filepath = os.path.join(RECEIVED_FOLDER, file.filename)
    try:
        file.save(filepath)
    except Exception as e:
        return render_template_string(HTML, verify_message=f"❌ Lỗi khi lưu tệp đã nhận: {e}")

    with open(filepath, "rb") as f:
        data = f.read()
    digest = hashlib.sha512(data).digest()
    
    try:
        signature = base64.b64decode(signature_b64)
    except Exception as e:
        return render_template_string(HTML, verify_message=f"❌ Xác minh thất bại: Chữ ký không hợp lệ (không phải Base64): {e}")

    try:
        public_key = serialization.load_pem_public_key(pubkey_pem.encode())
        # Cố gắng xác minh chữ ký
        public_key.verify(signature, digest, padding.PKCS1v15(), hashes.SHA512())
        verify_msg = f"✅ Xác minh thành công! File '{file.filename}' hợp lệ và đã được lưu tại thư mục '{RECEIVED_FOLDER}'."
    except InvalidSignature:
        verify_msg = "❌ Xác minh thất bại: Chữ ký không khớp với dữ liệu hoặc public key. File có thể đã bị thay đổi hoặc chữ ký/public key không đúng."
    except ValueError as e:
        verify_msg = f"❌ Xác minh thất bại: Public key không hợp lệ (không phải định dạng PEM hoặc lỗi khác): {e}"
    except Exception as e:
        verify_msg = f"❌ Xác minh thất bại: Xảy ra lỗi không xác định trong quá trình xác minh: {e}"

    return render_template_string(HTML, verify_message=verify_msg)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)