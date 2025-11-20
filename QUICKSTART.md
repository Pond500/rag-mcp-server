# Quick Start Guide - MCP Server for Dify

## 🎯 เริ่มต้นใช้งานภายใน 5 นาที

### ขั้นตอนที่ 1: เตรียม Environment

```bash
# 1. เข้าสู่ folder โปรเจกต์
cd /Users/pond500/RAG/mcp_rag-main

# 2. Activate virtual environment
source venv_clean/bin/activate

# 3. ตรวจสอบว่า dependencies ครบหรือยัง
pip install -r requirements.txt
```

### ขั้นตอนที่ 2: เริ่ม Qdrant Database

```bash
# ใช้ Docker Compose (ถ้ามีไฟล์ docker-compose.yml)
docker-compose up -d

# หรือรัน Qdrant แบบ standalone
docker run -d -p 6333:6333 --name qdrant qdrant/qdrant
```

### ขั้นตอนที่ 3: เริ่ม MCP Server

```bash
# วิธีที่ 1: ใช้ start script (แนะนำ)
./start_mcp_server.sh

# วิธีที่ 2: รันด้วย Python
python mcp_server.py

# วิธีที่ 3: รันด้วย uvicorn
uvicorn mcp_server:app --host 0.0.0.0 --port 8000 --reload
```

Server จะรันที่: **http://localhost:8000**

### ขั้นตอนที่ 4: ทดสอบ Server

เปิด browser ไปที่: http://localhost:8000/health

ควรเห็น:
```json
{
  "status": "ok",
  "server": "rag-mcp-server",
  "version": "1.0.0",
  "timestamp": "2025-11-18T..."
}
```

### ขั้นตอนที่ 5: เชื่อมต่อกับ Dify

1. เปิด Dify workspace
2. ไปที่ **Tools → MCP**
3. คลิก **"Add MCP Server (HTTP)"**
4. กรอกข้อมูล:
   - **Server URL**: `http://localhost:8000`
   - **Name**: `RAG Document Assistant`
   - **Server Identifier**: `rag-mcp-server` ⚠️ ห้ามเปลี่ยน!
5. คลิก **Save**

Dify จะทำการ discover tools อัตโนมัติและคุณจะเห็น 4 tools:
- ✅ upload_document
- ✅ query_documents
- ✅ chat_with_documents
- ✅ clear_chat_history

### 🎉 เสร็จแล้ว!

ตอนนี้คุณสามารถใช้ RAG tools ใน Dify Agent หรือ Workflow ได้แล้ว

---

## 📖 อ่านเพิ่มเติม

- คู่มือฉบับเต็ม: [MCP_DIFY_SETUP.md](./MCP_DIFY_SETUP.md)
- Dify MCP Docs: https://docs.dify.ai/en/guides/tools/mcp

## 🆘 แก้ปัญหาเบื้องต้น

**Q: Server ไม่รัน?**  
A: ตรวจสอบว่า Qdrant ทำงานอยู่และ port 8000 ว่าง

**Q: Dify ไม่เห็น tools?**  
A: คลิก "Update Tools" ใน Dify หรือลอง restart MCP server

**Q: Query ไม่ได้คำตอบ?**  
A: ต้อง upload เอกสารก่อนโดยใช้ upload_document tool
