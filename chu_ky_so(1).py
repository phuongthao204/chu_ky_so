import os
import base64
import hashlib
from flask import Flask, request, jsonify, render_template_string, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename # Import secure_filename for security

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Dictionary to temporarily store original filenames for download after verification
# In a real app, you might use a database or a more robust session management
# Key: safe_filename (from uploads folder), Value: original_filename
VERIFIED_FILES_INFO = {}

def fake_sign_file_with_rsa_sha512(file_content: bytes) -> str:
    """
    Giả lập ký số file với RSA + SHA-512.
    """
    sha512_hash = hashlib.sha512(file_content).digest()
    fake_signature = base64.b64encode(sha512_hash).decode('utf-8')
    return fake_signature

def fake_verify_signature(file_content: bytes, signature_b64: str) -> bool:
    """
    Giả lập xác minh chữ ký.
    """
    try:
        decoded_signature_bytes = base64.b64decode(signature_b64)
        sha512_hash_of_original_file = hashlib.sha512(file_content).digest()
        return sha512_hash_of_original_file == decoded_signature_bytes
    except Exception as e:
        print(f"Lỗi khi giả lập xác minh chữ ký: {e}")
        return False

# Định nghĩa route cho trang chủ
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/upload-and-sign', methods=['POST'])
def upload_and_sign():
    if 'file' not in request.files:
        return jsonify({"error": "Không có phần file trong yêu cầu."}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Không có file nào được chọn."}), 400

    if file:
        original_filename = file.filename
        # Sử dụng secure_filename để đảm bảo tên file an toàn
        safe_filename = secure_filename(original_filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
        file_content = file.read() # Đọc nội dung file trước khi lưu
        file.seek(0) # Đặt lại con trỏ file về đầu sau khi đọc
        file.save(file_path)

        signature = fake_sign_file_with_rsa_sha512(file_content)

        # Lưu thông tin file đã upload vào dictionary tạm thời
        # Lưu ý: Trong thực tế, bạn cần một cơ chế lưu trữ bền vững hơn
        VERIFIED_FILES_INFO[safe_filename] = original_filename

        return jsonify({"signature": signature, "filename": safe_filename, "original_filename": original_filename}), 200
    return jsonify({"error": "Đã xảy ra lỗi không xác định khi tải file lên."}), 500

@app.route('/verify-signature', methods=['POST'])
def verify_signature():
    if 'file' not in request.files:
        return jsonify({"error": "Không có file gốc trong yêu cầu."}), 400
    if 'signature' not in request.form:
        return jsonify({"error": "Không có chữ ký trong yêu cầu."}), 400

    original_file = request.files['file']
    signature_b64 = request.form['signature']

    if original_file.filename == '':
        return jsonify({"error": "File gốc chưa được chọn."}), 400

    if original_file:
        file_content = original_file.read()
        is_valid = fake_verify_signature(file_content, signature_b64)

        # Lưu file gốc tạm thời để có thể tải xuống sau khi xác minh (nếu muốn)
        # Lưu ý: Đây chỉ là ví dụ đơn giản. Trong thực tế, bạn sẽ quản lý file đã upload khác.
        original_filename = original_file.filename
        safe_filename = secure_filename(original_filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
        original_file.seek(0) # Reset con trỏ để có thể lưu
        original_file.save(file_path)
        VERIFIED_FILES_INFO[safe_filename] = original_filename

        return jsonify({"is_valid": is_valid, "filename": safe_filename, "original_filename": original_filename}), 200
    return jsonify({"error": "Đã xảy ra lỗi không xác định khi xác minh chữ ký."}), 500

# New route for downloading verified original files
# We need to store mapping of safe filename to original filename for this
@app.route('/download-verified-file/<filename>', methods=['GET'])
def download_verified_file(filename):
    # Ensure filename is safe to prevent directory traversal
    safe_filename = secure_filename(filename) # Sử dụng secure_filename cho filename từ URL
    
    # Ở đây, chúng ta dùng safe_filename để tìm trong UPLOAD_FOLDER
    # Và dùng filename ban đầu (đã được encodeURIComponent từ client) làm download_name
    
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
    
    if os.path.exists(file_path):
        # Lấy lại tên file gốc từ VERIFIED_FILES_INFO nếu có, nếu không thì dùng safe_filename
        # Đây là một điểm cần cải thiện trong ứng dụng thực tế để đảm bảo tên file chính xác
        download_name = VERIFIED_FILES_INFO.get(safe_filename, safe_filename) 
        return send_from_directory(app.config['UPLOAD_FOLDER'], safe_filename, as_attachment=True, download_name=download_name)
    else:
        return jsonify({"error": "File không tồn tại trên server để tải xuống."}), 404

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hệ Thống Gửi & Nhận File với Chữ Ký Số (RSA + SHA-512)</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f0f2f5;
            display: flex;
            justify-content: center;
            align-items: flex-start;
            min-height: 100vh;
            margin: 20px;
            color: #333;
        }

        .container {
            background-color: #fff;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            width: 100%;
            max-width: 1000px; /* Tăng max-width để có không gian cho 2 cột */
        }

        h1 {
            color: #0056b3;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2em;
        }

        h2 {
            color: #0056b3;
            font-size: 1.5em;
            margin-bottom: 15px;
            border-bottom: 2px solid #e0e0e0;
            padding-bottom: 5px;
            display: flex;
            align-items: center;
        }

        h2::before {
            content: '➤';
            margin-right: 10px;
            color: #007bff;
        }

        .section {
            background-color: #f9f9f9;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 25px;
        }

        .main-sections-wrapper {
            display: flex;
            gap: 25px;
            /* Loại bỏ flex-wrap để buộc chúng nằm ngang, trừ khi có media query cụ thể */
            /* flex-wrap: wrap; */ 
        }

        .send-section, .receive-section {
            flex: 1; /* Chia đều không gian */
            min-width: 45%; /* Đảm bảo đủ không gian, có thể điều chỉnh */
            box-sizing: border-box; /* Quan trọng để padding không làm tràn width */
        }

        input[type="file"] {
            display: none;
        }

        .custom-file-upload {
            display: inline-block;
            padding: 10px 15px;
            border: 1px solid #ccc;
            border-radius: 5px;
            cursor: pointer;
            background-color: #e9e9e9;
            margin-right: 10px;
            transition: background-color 0.3s ease;
        }

        .custom-file-upload:hover {
            background-color: #dcdcdc;
        }

        #fileNameDisplay, #verifyOriginalFileNameDisplay, #verifySignatureFileNameDisplay {
            font-style: italic;
            color: #666;
            word-break: break-all; /* Để xử lý tên file dài */
        }

        button {
            background-color: #28a745;
            color: white;
            padding: 12px 25px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1.1em;
            width: 100%;
            box-sizing: border-box;
            transition: background-color 0.3s ease;
            margin-top: 15px;
        }

        button:hover {
            background-color: #218838;
        }

        #verifyButton {
            background-color: #007bff;
        }
        #verifyButton:hover {
            background-color: #0056b3;
        }


        .result-box {
            background-color: #e6f7ff;
            border: 1px solid #91d5ff;
            border-radius: 5px;
            padding: 15px;
            margin-top: 15px;
        }

        textarea {
            width: calc(100% - 20px);
            padding: 10px;
            margin-top: 10px;
            border: 1px solid #ccc;
            border-radius: 4px;
            font-family: monospace;
            resize: vertical;
            min-height: 80px;
            max-height: 200px;
            box-sizing: border-box; /* Quan trọng để padding không làm tràn width */
        }

        .message {
            margin-top: 15px;
            padding: 10px;
            border-radius: 4px;
            font-weight: bold;
        }

        .message.success {
            background-color: #d4edda;
            color: #155724;
            border-color: #c3e6cb;
        }

        .message.error {
            background-color: #f8d7da;
            color: #721c24;
            border-color: #f5c6cb;
        }

        .message.valid {
            background-color: #d4edda;
            color: #155724;
        }
        .message.invalid {
            background-color: #f8d7da;
            color: #721c24;
        }
        .message.pending {
            background-color: #fff3cd;
            color: #664d03;
        }

        .footer-links {
            margin-top: 20px; /* Adjusted margin to be closer to content */
            text-align: center;
        }

        .footer-links a {
            color: #007bff;
            text-decoration: none;
            margin: 0 10px; /* Adjusted margin for closer links */
            font-weight: bold;
            display: none; /* Mặc định ẩn, chỉ hiện khi cần */
            white-space: nowrap; /* Prevent breaking on smaller screens */
        }

        .footer-links a:hover {
            text-decoration: underline;
        }

        /* Responsive adjustments */
        @media (max-width: 900px) { /* Thay đổi breakpoint để phù hợp với việc giữ 2 cột */
            .main-sections-wrapper {
                flex-direction: column; /* Chuyển thành cột khi màn hình nhỏ hơn 900px */
            }
            .send-section, .receive-section {
                width: 100%; /* Chiếm toàn bộ chiều rộng */
                min-width: unset; /* Bỏ min-width khi ở chế độ cột */
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Hệ Thống Gửi & Nhận File với Chữ Ký Số</h1>

        <div class="main-sections-wrapper">
            <div class="section send-section">
                <h2>Gửi và Ký File</h2>
                <div>
                    <p>Chọn file cần gửi:</p>
                    <label for="fileInput" class="custom-file-upload">
                        Chọn File
                    </label>
                    <input type="file" id="fileInput">
                    <span id="fileNameDisplay">Chưa có file nào được chọn</span>
                </div>

                <button id="uploadButton">Gửi và ký số</button>

                <div class="result-box">
                    <p><strong>Chữ ký (base64):</strong></p>
                    <textarea id="signatureOutput" rows="5" readonly></textarea>
                </div>
                <p id="messageOutput" class="message"></p>
                <div class="footer-links">
                    <a href="#" id="downloadOriginalFileAfterSign">Tải file gốc đã ký</a>
                    <a href="#" id="downloadSignature">Tải file chữ ký (.sig)</a>
                </div>
            </div>

            <div class="section receive-section">
                <h2>Nhận và Xác minh File</h2>
                <div class="file-upload-verify">
                    <p>Chọn file gốc để xác minh:</p>
                    <label for="verifyOriginalFileInput" class="custom-file-upload">
                        Chọn File
                    </label>
                    <input type="file" id="verifyOriginalFileInput">
                    <span id="verifyOriginalFileNameDisplay">Chưa có file nào được chọn</span>
                </div>
                <div class="file-upload-verify">
                    <p>Chọn file chữ ký (.sig):</p>
                    <label for="verifySignatureFileInput" class="custom-file-upload">
                        Chọn File .sig
                    </label>
                    <input type="file" id="verifySignatureFileInput" accept=".sig">
                    <span id="verifySignatureFileNameDisplay">Chưa có file nào được chọn</span>
                </div>
                <div class="result-box">
                    <p><strong>Chữ ký đọc được (base64):</strong></p>
                    <textarea id="parsedSignatureOutput" rows="3" readonly placeholder="Chữ ký sẽ hiển thị ở đây sau khi bạn chọn file .sig"></textarea>
                </div>
                <button id="verifyButton">Xác minh chữ ký</button>
                <p id="verifyMessage" class="message"></p>
                <div class="footer-links">
                    <a href="#" id="downloadVerifiedFile">Tải file gốc đã xác minh</a>
                </div>
            </div>
        </div>
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', () => {
            // Elements for Upload and Sign
            const fileInput = document.getElementById('fileInput');
            const fileNameDisplay = document.getElementById('fileNameDisplay');
            const uploadButton = document.getElementById('uploadButton');
            const signatureOutput = document.getElementById('signatureOutput');
            const messageOutput = document.getElementById('messageOutput');
            const downloadSignature = document.getElementById('downloadSignature');
            const downloadOriginalFileAfterSign = document.getElementById('downloadOriginalFileAfterSign'); // New link

            // Elements for Receive and Verify
            const verifyOriginalFileInput = document.getElementById('verifyOriginalFileInput');
            const verifyOriginalFileNameDisplay = document.getElementById('verifyOriginalFileNameDisplay');
            const verifySignatureFileInput = document.getElementById('verifySignatureFileInput');
            const verifySignatureFileNameDisplay = document.getElementById('verifySignatureFileNameDisplay');
            const parsedSignatureOutput = document.getElementById('parsedSignatureOutput'); // Ô hiển thị chữ ký đọc được
            const verifyButton = document.getElementById('verifyButton');
            const verifyMessage = document.getElementById('verifyMessage');
            const downloadVerifiedFile = document.getElementById('downloadVerifiedFile'); // Link tải file gốc đã xác minh

            let selectedFileForUpload = null;
            let currentSignatureText = null;
            let originalFileNameForSigning = null; // Tên file gốc khi ký số
            let safeFilenameAfterSign = null; // Tên file an toàn trả về từ server sau khi ký

            let selectedVerifyOriginalFile = null; // File gốc được chọn cho xác minh
            let selectedVerifySignatureFile = null; // File .sig được chọn cho xác minh
            let safeFilenameAfterVerify = null; // Tên file an toàn trả về từ server sau khi xác minh

            // --- Upload and Sign Logic ---
            fileInput.addEventListener('change', (event) => {
                if (event.target.files.length > 0) {
                    selectedFileForUpload = event.target.files[0];
                    fileNameDisplay.textContent = selectedFileForUpload.name;
                    originalFileNameForSigning = selectedFileForUpload.name; // Cập nhật tên file gốc
                    downloadSignature.style.display = 'none';
                    downloadOriginalFileAfterSign.style.display = 'none'; // Hide the new link
                    signatureOutput.value = '';
                    messageOutput.textContent = '';
                    messageOutput.classList.remove('success', 'error');

                    // Reset phần xác minh khi chọn file mới để gửi
                    verifyOriginalFileInput.value = '';
                    verifyOriginalFileNameDisplay.textContent = 'Chưa có file nào được chọn';
                    verifySignatureFileInput.value = '';
                    verifySignatureFileNameDisplay.textContent = 'Chưa có file nào được chọn';
                    parsedSignatureOutput.value = ''; // Xóa chữ ký đã đọc
                    verifyMessage.textContent = '';
                    verifyMessage.classList.remove('valid', 'invalid', 'pending', 'error');
                    downloadVerifiedFile.style.display = 'none'; // Ẩn link tải file đã giải mã

                } else {
                    selectedFileForUpload = null;
                    fileNameDisplay.textContent = 'Chưa có file nào được chọn';
                    originalFileNameForSigning = null;
                    safeFilenameAfterSign = null;
                }
            });

            uploadButton.addEventListener('click', async () => {
                if (!selectedFileForUpload) {
                    messageOutput.textContent = 'Vui lòng chọn một file để gửi.';
                    messageOutput.classList.add('error');
                    messageOutput.classList.remove('success');
                    return;
                }

                messageOutput.textContent = 'Đang tải lên và ký số...';
                messageOutput.classList.remove('success', 'error');
                signatureOutput.value = '';
                currentSignatureText = null;
                downloadSignature.style.display = 'none';
                downloadOriginalFileAfterSign.style.display = 'none'; // Hide the new link
                verifyMessage.textContent = '';
                verifyMessage.classList.remove('valid', 'invalid', 'pending', 'error');
                downloadVerifiedFile.style.display = 'none'; // Ẩn link tải file đã giải mã

                const formData = new FormData();
                formData.append('file', selectedFileForUpload);

                try {
                    const response = await fetch('/upload-and-sign', {
                        method: 'POST',
                        body: formData
                    });

                    const data = await response.json();

                    if (response.ok) {
                        signatureOutput.value = data.signature;
                        currentSignatureText = data.signature;
                        safeFilenameAfterSign = data.filename; // Store the safe filename from server

                        messageOutput.textContent = 'Thành công! Chữ ký đã được tạo.';
                        messageOutput.classList.add('success');
                        messageOutput.classList.remove('error');

                        // Display download link for the original file after signing
                        downloadOriginalFileAfterSign.href = `/download-verified-file/${encodeURIComponent(safeFilenameAfterSign)}`;
                        downloadOriginalFileAfterSign.download = data.original_filename; // Use original name for download
                        downloadOriginalFileAfterSign.style.display = 'inline-block';

                        // Display download link for the signature file
                        try {
                           const b64Signature = btoa(currentSignatureText);
                           downloadSignature.href = `data:text/plain;base64,${b64Signature}`;
                        } catch (e) {
                           console.error("Error btoa'ing signature for download:", e);
                           downloadSignature.href = `data:text/plain;charset=utf-8,${encodeURIComponent(currentSignatureText)}`;
                        }

                        downloadSignature.download = `${originalFileNameForSigning}.sig`;
                        downloadSignature.style.display = 'inline-block';

                    } else {
                        messageOutput.textContent = `Lỗi: ${data.error || 'Không xác định'}`;
                        messageOutput.classList.add('error');
                        messageOutput.classList.remove('success');
                        signatureOutput.value = '';
                        downloadOriginalFileAfterSign.style.display = 'none';
                    }
                } catch (error) {
                    console.error('Lỗi khi gửi file:', error);
                    messageOutput.textContent = 'Đã xảy ra lỗi mạng hoặc máy chủ không phản hồi.';
                    messageOutput.classList.add('error');
                    messageOutput.classList.remove('success');
                    signatureOutput.value = '';
                    downloadOriginalFileAfterSign.style.display = 'none';
                }
            });

            // --- Receive and Verify Logic ---
            verifyOriginalFileInput.addEventListener('change', (event) => {
                if (event.target.files.length > 0) {
                    selectedVerifyOriginalFile = event.target.files[0];
                    verifyOriginalFileNameDisplay.textContent = selectedVerifyOriginalFile.name;
                } else {
                    selectedVerifyOriginalFile = null;
                    verifyOriginalFileNameDisplay.textContent = 'Chưa có file nào được chọn';
                }
                verifyMessage.textContent = '';
                verifyMessage.classList.remove('valid', 'invalid', 'pending', 'error');
                downloadVerifiedFile.style.display = 'none';
            });

            verifySignatureFileInput.addEventListener('change', (event) => {
                if (event.target.files.length > 0) {
                    selectedVerifySignatureFile = event.target.files[0];
                    verifySignatureFileNameDisplay.textContent = selectedVerifySignatureFile.name;
                    // Đọc nội dung file .sig và hiển thị vào textarea
                    const reader = new FileReader();
                    reader.onload = (e) => {
                        parsedSignatureOutput.value = e.target.result;
                    };
                    reader.onerror = (e) => {
                        console.error("Lỗi đọc file chữ ký:", e);
                        parsedSignatureOutput.value = 'Không thể đọc file chữ ký.';
                    };
                    reader.readAsText(selectedVerifySignatureFile); // Đọc dưới dạng văn bản (Base64)

                } else {
                    selectedVerifySignatureFile = null;
                    verifySignatureFileNameDisplay.textContent = 'Chưa có file nào được chọn';
                    parsedSignatureOutput.value = '';
                }
                verifyMessage.textContent = '';
                verifyMessage.classList.remove('valid', 'invalid', 'pending', 'error');
                downloadVerifiedFile.style.display = 'none';
            });

            verifyButton.addEventListener('click', async () => {
                if (!selectedVerifyOriginalFile) {
                    verifyMessage.textContent = 'Vui lòng chọn file gốc để xác minh.';
                    verifyMessage.classList.add('error');
                    verifyMessage.classList.remove('valid', 'invalid', 'pending');
                    return;
                }
                if (!selectedVerifySignatureFile) {
                    verifyMessage.textContent = 'Vui lòng chọn file chữ ký (.sig) để xác minh.';
                    verifyMessage.classList.add('error');
                    verifyMessage.classList.remove('valid', 'invalid', 'pending');
                    return;
                }

                verifyMessage.textContent = 'Đang xác minh chữ ký...';
                verifyMessage.classList.add('pending');
                verifyMessage.classList.remove('valid', 'invalid', 'error');
                downloadVerifiedFile.style.display = 'none'; // Ẩn link cho mỗi lần xác minh mới

                // Đọc nội dung của file chữ ký (.sig)
                const reader = new FileReader();
                reader.onload = async (e) => {
                    const signatureContent = e.target.result; // Chữ ký Base64 dạng string

                    const formData = new FormData();
                    formData.append('file', selectedVerifyOriginalFile); // File gốc
                    formData.append('signature', signatureContent); // Nội dung chữ ký từ file .sig

                    try {
                        const response = await fetch('/verify-signature', {
                            method: 'POST',
                            body: formData
                        });

                        const data = await response.json();

                        if (response.ok) {
                            if (data.is_valid) {
                                verifyMessage.textContent = 'Chữ ký hợp lệ! File không bị thay đổi.';
                                verifyMessage.classList.add('valid');
                                verifyMessage.classList.remove('invalid', 'pending', 'error');

                                // Hiển thị link tải file gốc đã xác minh
                                safeFilenameAfterVerify = data.filename;
                                const originalFileNameForDownload = data.original_filename; // Use original name from server
                                downloadVerifiedFile.href = `/download-verified-file/${encodeURIComponent(safeFilenameAfterVerify)}`;
                                downloadVerifiedFile.style.display = 'inline-block';
                                downloadVerifiedFile.download = originalFileNameForDownload; // Tên file khi tải về
                            } else {
                                verifyMessage.textContent = 'Chữ ký không hợp lệ! File có thể đã bị thay đổi hoặc chữ ký không đúng.';
                                verifyMessage.classList.add('invalid');
                                verifyMessage.classList.remove('valid', 'pending', 'error');
                                downloadVerifiedFile.style.display = 'none'; // Ẩn link nếu xác minh không thành công
                            }
                        } else {
                            verifyMessage.textContent = `Lỗi xác minh: ${data.error || 'Không xác định'}`;
                            verifyMessage.classList.add('error');
                            verifyMessage.classList.remove('valid', 'invalid', 'pending');
                            downloadVerifiedFile.style.display = 'none';
                        }
                    } catch (error) {
                        console.error('Lỗi khi xác minh:', error);
                        verifyMessage.textContent = 'Đã xảy ra lỗi mạng hoặc máy chủ không phản hồi khi xác minh.';
                        verifyMessage.classList.add('error');
                        verifyMessage.classList.remove('valid', 'invalid', 'pending');
                        downloadVerifiedFile.style.display = 'none';
                    }
                };
                reader.onerror = (e) => {
                    console.error("Lỗi đọc file chữ ký:", e);
                    verifyMessage.textContent = 'Lỗi khi đọc file chữ ký.';
                    verifyMessage.classList.add('error');
                    downloadVerifiedFile.style.display = 'none';
                };
                reader.readAsText(selectedVerifySignatureFile);
            });
        });
    </script>
</body>
</html>
"""


if __name__ == '__main__':
    app.run(debug=True, port=5000)