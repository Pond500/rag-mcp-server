# การใช้งาน RAG MCP Server กับ Dify

## 📋 ภาพรวม

MCP Server นี้ถูกสร้างเพื่อใช้งานร่วมกับ Dify โดยใช้ **HTTP+SSE Transport** ตามที่ Dify กำหนด

ระบบนี้แปลง API endpoints เดิม (`/upload`, `/query`, `/chat`) เป็น **MCP Tools** ที่ Dify สามารถเรียกใช้ได้

## 🚀 การติดตั้งและรัน

### 1. ติดตั้ง Dependencies

```bash
# สร้าง virtual environment (ถ้ายังไม่มี)
python -m venv venv_clean

# Activate virtual environment
source venv_clean/bin/activate  # macOS/Linux
# หรือ
venv_clean\Scripts\activate     # Windows

# ติดตั้ง packages
pip install -r requirements.txt
```

### 2. ตั้งค่า Environment Variables

สร้างไฟล์ `.env` หรือแก้ไขไฟล์ที่มีอยู่:

```env
# LLM Configuration
LLM_API_BASE=https://tokenmind.abdul.in.th/v1
LLM_API_KEY=sk-WIqY-Eg2u9q24jnZ9jbFHw
LLM_MODEL_NAME=ptm-gpt-oss-120b
```

### 3. เริ่ม Qdrant Database

```bash
# ใช้ Docker Compose (ถ้ามีไฟล์ docker-compose.yml)
docker-compose up -d

# หรือรัน Qdrant แบบ standalone
docker run -p 6333:6333 qdrant/qdrant
```

### 4. รัน MCP Server

```bash
# รันด้วย Python
python mcp_server.py

# หรือรันด้วย uvicorn โดยตรง
uvicorn mcp_server:app --host 0.0.0.0 --port 8000 --reload
```

Server จะรันที่: `http://localhost:8000`

## 🔧 การเชื่อมต่อกับ Dify

### 1. เข้าสู่ Dify Workspace
- ไปที่ **Tools → MCP** ใน Dify workspace ของคุณ

### 2. เพิ่ม MCP Server
- คลิก **"Add MCP Server (HTTP)"**
- กรอกข้อมูลดังนี้:

```
Server URL: http://localhost:8000
Name: RAG Document Assistant
Server Identifier: rag-mcp-server
```

**⚠️ สำคัญ:** `Server Identifier` ต้องเป็น **"rag-mcp-server"** เหมือนกับที่กำหนดใน code (lowercase, ตัวเลข, underscore, hyphen เท่านั้น, ไม่เกิน 24 ตัวอักษร)

**หมายเหตุ:** หากคุณ deploy MCP Server บน production, ให้เปลี่ยน URL เป็น public URL ของคุณ (เช่น `https://your-domain.com`)

### 3. Authorization และ Tool Discovery
- Dify จะทำการเชื่อมต่อและค้นหา tools อัตโนมัติ
- คุณจะเห็น 4 tools ปรากฏขึ้น:
  1. **upload_document** - อัปโหลดและ index เอกสาร
  2. **query_documents** - ค้นหาแบบไม่มีประวัติการสนทนา (stateless)
  3. **chat_with_documents** - แชทแบบมีประวัติการสนทนา (stateful)
  4. **clear_chat_history** - ลบประวัติการสนทนา

## 📚 MCP Tools ที่มีให้ใช้งาน

### 1. upload_document
อัปโหลดและ index เอกสาร (PDF, TXT, DOCX) เข้าสู่ระบบ RAG

**Input Parameters:**
- `file_content` (string, required): Base64 encoded file content
- `file_name` (string, required): ชื่อไฟล์ (เช่น "document.pdf")
- `content_type` (string, required): MIME type
  - `application/pdf` สำหรับ PDF
  - `text/plain` สำหรับ TXT
  - `application/vnd.openxmlformats-officedocument.wordprocessingml.document` สำหรับ DOCX

**Output:**
```json
{
  "success": true,
  "filename": "document.pdf",
  "message": "Document indexed successfully",
  "metadata": {
    "doc_type": "รายงาน",
    "category": "การเงิน",
    "title": "รายงานประจำปี 2024"
  }
}
```

### 2. query_documents
ค้นหาเอกสารแบบ stateless (ไม่มีประวัติการสนทนา)

**Input Parameters:**
- `question` (string, required): คำถามที่ต้องการถาม

**Output:**
```json
{
  "answer": "คำตอบจาก RAG system",
  "sources": [
    {
      "text": "ข้อความจากเอกสาร...",
      "score": 0.8523,
      "file_name": "document.pdf",
      "page_number": 5
    }
  ],
  "source_count": 3
}
```

### 3. chat_with_documents
แชทกับเอกสารแบบ stateful (มีประวัติการสนทนา)

**Input Parameters:**
- `question` (string, required): คำถามหรือข้อความที่ต้องการส่ง
- `session_id` (string, required): Session ID เพื่อเก็บประวัติการสนทนา (เช่น "user123_session1")

**Output:**
```json
{
  "answer": "คำตอบจาก RAG system (พร้อม context จากการสนทนาก่อนหน้า)",
  "sources": [...],
  "source_count": 3,
  "session_id": "user123_session1",
  "conversation_length": 6
}
```

### 4. clear_chat_history
ลบประวัติการสนทนาสำหรับ session ที่ระบุ

**Input Parameters:**
- `session_id` (string, required): Session ID ที่ต้องการลบ

**Output:**
```json
{
  "success": true,
  "message": "Chat history cleared for session: user123_session1"
}
```

## 💡 ตัวอย่างการใช้งานใน Dify

### Scenario 1: อัปโหลดและค้นหาเอกสาร

**Step 1:** สร้าง Agent Application ใน Dify

**Step 2:** เพิ่ม tools จาก RAG MCP Server:
- เพิ่ม `upload_document` tool
- เพิ่ม `query_documents` tool

**Step 3:** สร้าง prompt สำหรับ agent:
```
คุณเป็นผู้ช่วยจัดการเอกสาร คุณสามารถอัปโหลดเอกสารและตอบคำถามจากเอกสารได้

เมื่อผู้ใช้ต้องการอัปโหลดเอกสาร ให้ใช้ upload_document tool
เมื่อผู้ใช้ถามคำถาม ให้ใช้ query_documents tool เพื่อค้นหาคำตอบ
```

### Scenario 2: แชทแบบมีบริบท

**Step 1:** สร้าง Agent Application ใน Dify

**Step 2:** เพิ่ม `chat_with_documents` tool

**Step 3:** ตั้งค่า parameter:
- `question`: ให้ AI กำหนด (Auto)
- `session_id`: ตั้งเป็น Fixed Value = `{{user_id}}_chat` (ใช้ variable จาก Dify)

**Step 4:** แชทกับระบบ - ระบบจะจำบริบทการสนทนาได้!

## 🔍 การทดสอบ MCP Server

### ทดสอบด้วย curl

```bash
# 1. ทดสอบ initialize
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {}
  }'

# 2. ทดสอบ list tools
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list",
    "params": {}
  }'

# 3. ทดสอบ query
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "query_documents",
      "arguments": {
        "question": "บริษัทมีรายได้เท่าไหร่ในปี 2024?"
      }
    }
  }'
```

### ทดสอบ SSE endpoint

```bash
curl -N http://localhost:8000/sse
```

## 🛠️ Configuration

### เปลี่ยน Port

แก้ไขในไฟล์ `mcp_server.py`:

```python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "mcp_server:app",
        host="0.0.0.0",
        port=8000,  # <-- เปลี่ยนที่นี่
        reload=True
    )
```

### เปลี่ยน Server Info

แก้ไขใน function `handle_initialize()`:

```python
"serverInfo": {
    "name": "rag-mcp-server",  # <-- ตรงกับ Server Identifier ใน Dify
    "version": "1.0.0"
}
```

## 🐛 Troubleshooting

### ปัญหา: Dify ไม่พบ tools

**วิธีแก้:**
1. ตรวจสอบว่า MCP Server รันอยู่และเข้าถึงได้จาก Dify
2. ลองคลิก "Update Tools" ใน Dify
3. ตรวจสอบ logs ของ MCP Server

### ปัญหา: Query engine not initialized

**วิธีแก้:**
1. ตรวจสอบว่า Qdrant ทำงานอยู่
2. รีสตาร์ท MCP Server
3. ตรวจสอบ environment variables

### ปัญหา: CORS errors

**วิธีแก้:**
- CORS middleware ถูกตั้งค่าให้ allow_origins=["*"] แล้ว
- ถ้ายังมีปัญหา ให้ระบุ origin ของ Dify โดยตรง:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-dify-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 📊 สถาปัตยกรรม

```
┌─────────────────┐
│   Dify Agent    │
│   Application   │
└────────┬────────┘
         │ MCP Protocol (HTTP+SSE)
         │
┌────────▼────────┐
│   MCP Server    │
│  (mcp_server.py)│
└────────┬────────┘
         │
    ┌────┴─────┬────────────┐
    │          │            │
┌───▼──┐  ┌───▼───┐  ┌────▼────┐
│ LLM  │  │Qdrant │  │ Embedder│
│(PTM) │  │Vector │  │(bge-m3) │
└──────┘  │  DB   │  └─────────┘
          └───────┘
```

## 📝 Notes

1. **Server Identifier ต้องไม่เปลี่ยน** หลังจากที่มี application ใช้งานแล้ว ไม่เช่นนั้น application จะเสีย
2. **Session ID สำหรับ chat** ควรเป็น unique ต่อผู้ใช้แต่ละคน (เช่น `user_id` + `_chat`)
3. **Base64 encoding** สำหรับ upload_document ทำได้ใน Dify workflow หรือให้ agent ทำเอง
4. **Production deployment** ควร:
   - ใช้ HTTPS
   - ตั้ง CORS อย่างถูกต้อง
   - ใช้ authentication/authorization
   - Monitor logs และ errors

## 🎯 Best Practices

1. **ใช้ Fixed Values สำหรับ parameters ที่ไม่เปลี่ยน** เช่น `session_id` หรือ search parameters
2. **Document ให้ทีมรู้ว่า application ใช้ MCP server ไหน** และ server ID คืออะไร
3. **Test ใน development environment ก่อน** แล้วค่อย deploy production
4. **Backup chat histories** หากจำเป็น (ปัจจุบันเก็บใน memory)
5. **Monitor performance** และ optimize chunk size/overlap ตามความเหมาะสม

## 🔗 เพิ่มเติม

- [Dify MCP Documentation](https://docs.dify.ai/en/guides/tools/mcp)
- [Model Context Protocol Spec](https://modelcontextprotocol.io)
- [LangChain Documentation](https://python.langchain.com)

---

**สร้างโดย:** RAG MCP Server v1.0.0  
**วันที่:** 2025-11-18  
**ใช้สำหรับ:** Dify Integration
