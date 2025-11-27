import requests
import base64
import json
import os
import mimetypes
import time

# ---------------- Configuration ----------------
SERVER_URL = "http://localhost:8000/mcp"
FOLDER_PATH = "/Users/pond500/Downloads/1. งานอาวุธปืน"  # ⚠️ ระบุเป็นโฟล์เดอร์แทน
KB_NAME = "gun_law_hybrid"  # ใช้ชื่อใหม่สำหรับ Hybrid Search version
ALLOWED_EXTENSIONS = {'.pdf', '.txt', '.docx'} # นามสกุลที่รองรับ
# -------------------------------------------

def upload_single_file(file_path):
    filename = os.path.basename(file_path)
    
    # 1. อ่านและแปลงไฟล์
    try:
        with open(file_path, "rb") as f:
            file_content = f.read()
            encoded_content = base64.b64encode(file_content).decode('utf-8')
    except Exception as e:
        print(f"❌ Error reading {filename}: {e}")
        return False

    # 2. หา MIME Type
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        # Map manual types if auto-detect fails
        ext = os.path.splitext(filename)[1].lower()
        if ext == '.pdf': mime_type = 'application/pdf'
        elif ext == '.txt': mime_type = 'text/plain'
        elif ext == '.docx': mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        else: mime_type = 'application/octet-stream'

    # 3. เตรียม Payload
    payload = {
        "jsonrpc": "2.0",
        "id": int(time.time()), # ใช้ timestamp เป็น ID ไม่ให้ซ้ำ
        "method": "tools/call",
        "params": {
            "name": "upload_document_to_kb",
            "arguments": {
                "kb_name": KB_NAME,
                "file_content": encoded_content,
                "filename": filename,
                "content_type": mime_type,
                "auto_create": True
            }
        }
    }

    # 4. ยิง Request
    try:
        print(f"⏳ Uploading: {filename}...")
        response = requests.post(SERVER_URL, json=payload, headers={"Content-Type": "application/json"})
        
        if response.status_code == 200:
            result = response.json()
            if "error" in result:
                print(f"   ❌ Server Error: {result['error']['message']}")
                return False
            else:
                content_block = result["result"]["content"][0]
                tool_output = json.loads(content_block["text"])
                if tool_output.get("success"):
                    print(f"   ✅ Success! (Metadata: {tool_output.get('metadata', {}).get('doc_type', 'N/A')})")
                    return True
                else:
                    print(f"   ❌ Failed: {tool_output.get('message')}")
                    return False
        else:
            print(f"   ❌ HTTP Error: {response.status_code}")
            return False

    except Exception as e:
        print(f"   ❌ Connection Error: {e}")
        return False

def process_folder():
    if not os.path.exists(FOLDER_PATH):
        print(f"❌ Folder not found: {FOLDER_PATH}")
        return

    print(f"🚀 Starting Bulk Upload from: {FOLDER_PATH}")
    print(f"📂 Target Knowledge Base: {KB_NAME}")
    print("-" * 50)

    files = [f for f in os.listdir(FOLDER_PATH) if os.path.isfile(os.path.join(FOLDER_PATH, f))]
    success_count = 0
    skip_count = 0

    for f in files:
        ext = os.path.splitext(f)[1].lower()
        if ext in ALLOWED_EXTENSIONS:
            full_path = os.path.join(FOLDER_PATH, f)
            if upload_single_file(full_path):
                success_count += 1
        else:
            skip_count += 1
            # print(f"⏩ Skipping unsupported file: {f}")

    print("-" * 50)
    print(f"📊 Summary: Uploaded {success_count} files, Skipped {skip_count} files.")
    print(f"🎉 Ready to chat in Dify with KB: '{KB_NAME}'")

if __name__ == "__main__":
    process_folder()