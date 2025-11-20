# สรุปโปรเจค MCP RAG Server สำหรับ Dify

## 📋 ภาพรวมโปรเจค

โปรเจคนี้พยายามแปลง RAG API service เดิมให้เป็น **Model Context Protocol (MCP) Server** เพื่อเชื่อมต่อกับ **Dify Cloud** ผ่าน ngrok tunnel

### เป้าหมายหลัก
- ✅ สร้าง MCP server ที่รองรับ HTTP+SSE transport
- ✅ Deploy ผ่าน ngrok เพื่อให้ Dify Cloud เข้าถึงได้
- ❌ ทำให้ tools แสดงใน Dify UI (ยังไม่สำเร็จ)

---

## 🛠️ สิ่งที่สร้างเสร็จแล้ว

### 1. MCP Server Implementation (`mcp_server.py`)
**FastAPI-based MCP Server** พร้อมฟีเจอร์:

#### RAG Tools (4 tools):
1. **`upload_document`**
   - อัพโหลดและ index เอกสาร (PDF, TXT, DOCX)
   - รับ base64 encoded file content
   - เก็บใน Qdrant vector database

2. **`query_documents`**
   - ค้นหาและตอบคำถามจากเอกสาร
   - Stateless (ไม่มี conversation history)
   - ใช้ RAG pipeline ของ LangChain

3. **`chat_with_documents`**
   - แชทกับเอกสารแบบมี conversation history
   - ใช้ session_id ในการจัดการ history
   - Stateful conversation

4. **`clear_chat_history`**
   - ล้างประวัติการสนทนาของ session ที่กำหนด

#### Technical Stack:
- **Framework**: FastAPI + Uvicorn
- **MCP Protocol Version**: 2024-11-05
- **Transport**: HTTP + Server-Sent Events (SSE)
- **Vector DB**: Qdrant (localhost:6333)
- **Embeddings**: HuggingFace bge-m3
- **LLM**: OpenAI-compatible endpoints

### 2. Deployment Setup
- **Port**: 8000 (localhost)
- **ngrok URL**: `https://c98ee8d682c2.ngrok-free.app`
- **Python Environment**: venv_clean (Python 3.10)
- **Startup Script**: `start_with_ngrok.sh` (automated setup)

### 3. Files Created/Modified

```
mcp_rag-main/
├── mcp_server.py           # MCP server implementation (553 lines)
├── start_with_ngrok.sh     # Automated startup script
├── requirements.txt        # Python dependencies
├── app/                    # Original RAG application
│   ├── main.py
│   ├── rag_pipeline.py
│   ├── config.py
│   └── ...
├── qdrant_storage/        # Vector database storage
└── mcp_server.log         # Server logs
```

---

## 🔄 Evolution ของ Implementation

### Phase 1: HTTP+SSE with Endpoint Events (ตาม MCP Spec เก่า)
**พยายาม**: ส่ง endpoint URL ผ่าน SSE events

```python
# ส่ง endpoint ใน 3 รูปแบบ
yield f"event: endpoint\ndata: {base_url}/\n\n"                    # Plain
yield f'event: endpoint\ndata: "{base_url}/"\n\n'                  # JSON string  
yield f"event: endpoint\ndata: {json.dumps({'url': url})}\n\n"    # JSON object
```

**ผลลัพธ์**: ❌ Dify ยังไม่เห็น tools

### Phase 2: Streamable HTTP (ตาม MCP Spec ใหม่)
**พยายาม**: ปิด SSE และให้ Dify POST โดยตรง

```python
# ปิด SSE connection ทันที
async def empty_sse():
    return
    yield
```

**ผลลัพธ์**: ❌ Dify ยังส่ง `Accept: text/event-stream` มา

### Phase 3: SSE with JSON-RPC Messages
**พยายาม**: ส่ง endpoint เป็น JSON-RPC notification

```python
notification = {
    "jsonrpc": "2.0",
    "method": "notifications/initialized",
    "params": {...}
}
yield f"data: {json.dumps(notification)}\n\n"
```

**ผลลัพธ์**: ❌ Dify ยังไม่เห็น tools

### Phase 4: Tools in Initialize Response (Current)
**พยายาม**: ส่ง tools list ไปพร้อมกับ initialize response

```python
"result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
        "tools": {"listChanged": True}
    },
    "serverInfo": {...},
    "tools": [...]  # 4 tools ทั้งหมด
}
```

**ผลลัพธ์**: ⚠️ Server ส่งสำเร็จ แต่ Dify ไม่แสดง tools

---

## 📊 Log Analysis

### Successful Handshake Pattern:
```
📍 GET / from 3.214.24.53
📍 Accept: text/event-stream
📍 Sending endpoint as SSE event
INFO: 200 OK
📍 Sent endpoint event (plain): https://c98ee8d682c2.ngrok-free.app/
📥 Received: initialize
📤 Sending initialize response with 4 tools
INFO: 200 OK
```

### Key Observations:
1. ✅ Dify เชื่อมต่อมาได้ (IP: 3.214.24.53)
2. ✅ Dify ส่ง `Accept: text/event-stream` → ต้องการ SSE
3. ✅ Initialize handshake สำเร็จ (200 OK)
4. ✅ Server ส่ง tools list ไปแล้ว (4 tools)
5. ❌ Dify **ไม่ส่ง** `tools/list` request มา
6. ❌ Tools **ไม่แสดง** ใน Dify UI

---

## 🐛 Debugging Efforts

### Issues Encountered:
1. **Python Bytecode Caching**
   - Code changes ไม่มีผล → old code ยังทำงานอยู่
   - **Solution**: ใช้ `python -B` flag, ลบ `__pycache__/` และ `*.pyc`

2. **Process Management**
   - Multiple server instances running
   - **Solution**: `pkill -9 -f mcp_server` ก่อน restart

3. **SSE Format Confusion**
   - ไม่แน่ใจว่า Dify ต้องการ format ไหน
   - **Solution**: ลองหลายรูปแบบ (plain, JSON string, JSON object, JSON-RPC)

4. **Transport Protocol Mismatch**
   - Documentation บอก HTTP แต่ Dify ส่ง SSE headers
   - **Solution**: Implement hybrid approach

---

## 🔍 Research Findings

### MCP Protocol:
- **Official Transports**:
  - `stdio` - สำหรับ local use (Claude Desktop)
  - `HTTP+SSE` - สำหรับ remote use (spec เก่า)
  - `Streamable HTTP` - transport ใหม่ (spec ใหม่)

### Dify Implementation:
- ✅ Dify รองรับ MCP (documented)
- ❌ Dify **ไม่มีตัวอย่าง** HTTP MCP server ที่ work
- ⚠️ Dify docs แสดงแค่ stdio transport (Mintlify MCP)
- ❓ Dify อาจ implement MCP **ไม่ครบตาม spec**

### MCP Servers Research:
- 📊 ดู GitHub `modelcontextprotocol/servers` (800+ servers)
- 🔍 ส่วนใหญ่เป็น **stdio transport**
- 🔍 HTTP servers ที่มี → ไม่มีข้อมูลว่าใช้กับ Dify ได้
- 📝 ไม่เจอ working example ของ HTTP MCP + Dify เลย

---

## 💡 Root Cause Analysis

### ทำไม Tools ไม่แสดงใน Dify?

**สมมติฐาน 1**: Format ของ tools list ไม่ถูกต้อง
- Dify อาจต้องการ structure ที่แตกต่างออกไป
- อาจต้อง nested ใน capabilities แทน result

**สมมติฐาน 2**: Dify ไม่ support HTTP MCP อย่างสมบูรณ์
- Documentation ไม่ชัดเจน
- Implementation อาจไม่ตรงตาม MCP spec
- อาจรองรับแค่ stdio transport

**สมมติฐาน 3**: Missing Step ที่ไม่ได้ documented
- อาจมีขั้นตอนเพิ่มเติมหลัง initialize
- อาจต้อง trigger tools/list แบบอื่น

**สมมติฐาน 4**: Client-side validation
- Dify อาจ validate tools format ที่ client-side
- การ validate fail → ไม่แสดง tools
- ไม่มี error feedback กลับมา

---

## ⚙️ Technical Details

### MCP Server Configuration:

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "tools": {
        "listChanged": true
      }
    },
    "serverInfo": {
      "name": "rag-mcp-server",
      "version": "1.0.0"
    },
    "instructions": "RAG MCP Server for document upload, query, and chat operations",
    "tools": [
      {
        "name": "upload_document",
        "description": "Upload and index a document...",
        "inputSchema": {
          "type": "object",
          "properties": {
            "file_content": {"type": "string"},
            "file_name": {"type": "string"},
            "content_type": {"type": "string"}
          },
          "required": ["file_content", "file_name", "content_type"]
        }
      },
      // ... 3 more tools
    ]
  }
}
```

### Endpoints Implemented:
- `GET /` - SSE endpoint discovery + keep-alive
- `POST /` - JSON-RPC message handling
  - `initialize` - Server capabilities
  - `tools/list` - List available tools (not called by Dify)
  - `tools/call` - Execute tool

### Headers Sent:
```
MCP-Protocol-Version: 2024-11-05
Cache-Control: no-cache
Connection: keep-alive
X-Accel-Buffering: no
Content-Type: text/event-stream
```

---

## 🎯 Next Steps / Alternatives

### Option 1: Continue MCP Debugging ⚠️
**Pros**: ตรงตามเป้าหมายเดิม
**Cons**: ไม่มี working example, documentation ไม่ชัดเจน
**Effort**: สูง, ความสำเร็จไม่แน่นอน

**Actions**:
- ติดต่อทีม Dify โดยตรง (GitHub issues / Discord)
- หา Dify MCP client source code มาดู
- ลองแก้ initialize response format อีก

### Option 2: Convert to REST API ✅
**Pros**: แน่นอนว่าใช้งานได้, Dify รองรับดี
**Cons**: ไม่ได้ใช้ MCP protocol
**Effort**: ต่ำ, implement เสร็จภายใน 1-2 ชั่วโมง

**Actions**:
- สร้าง REST API endpoints สำหรับ 4 tools
- ใช้ FastAPI เดิม (แค่เปลี่ยน routing)
- Configure ใน Dify เป็น Custom API Tools

### Option 3: Hybrid Approach 🔄
**Pros**: ได้ทั้ง MCP และ API
**Cons**: Maintain 2 interfaces
**Effort**: กลาง

**Actions**:
- Keep MCP implementation ไว้
- เพิ่ม REST API endpoints
- Deploy แยก port หรือ path

---

## 📦 Resources

### Files:
- **Server Code**: `mcp_server.py` (553 lines)
- **Startup Script**: `start_with_ngrok.sh`
- **Logs**: `mcp_server.log`
- **This Summary**: `PROJECT_SUMMARY.md`

### URLs:
- **ngrok**: https://c98ee8d682c2.ngrok-free.app
- **Local**: http://localhost:8000
- **Qdrant**: http://localhost:6333

### Documentation Referenced:
- [MCP Specification](https://modelcontextprotocol.io/)
- [Dify MCP Guide](https://docs.dify.ai/guides/tools/mcp)
- [MCP Servers List](https://github.com/modelcontextprotocol/servers)

---

## 🎓 Lessons Learned

1. **Protocol Implementation != Documentation**
   - Vendor อาจ implement ไม่ตรง spec
   - Working example > Documentation

2. **Transport Layer Matters**
   - stdio vs HTTP มีความแตกต่างมาก
   - SSE implementation มีหลายแบบ

3. **Debugging Distributed Systems**
   - Logging เป็นสิ่งสำคัญ
   - Cache management critical สำหรับ Python

4. **Research First**
   - ควรหา working example ก่อน implement
   - Community resources มีค่ามาก

---

## 👥 Credits

- **Developer**: [Your Name]
- **Date**: November 19, 2025
- **Framework**: FastAPI, LangChain, Qdrant
- **Protocol**: Model Context Protocol (MCP)
- **Target**: Dify Cloud Platform

---

## 📝 Status Summary

| Component | Status | Notes |
|-----------|--------|-------|
| MCP Server | ✅ Complete | Fully functional, all tools work |
| RAG Pipeline | ✅ Complete | LangChain + Qdrant working |
| HTTP Transport | ✅ Complete | SSE + JSON-RPC working |
| ngrok Tunnel | ✅ Complete | Public URL accessible |
| Dify Connection | ⚠️ Partial | Handshake works, tools not visible |
| Tools Display | ❌ Failed | Root cause unknown |

**Overall Status**: 🟡 **Blocked** - Waiting for Dify compatibility resolution

---

## 🔖 Conclusion

โปรเจคนี้สร้าง **working MCP server** ที่สมบูรณ์แล้ว แต่ติดปัญหาที่ **Dify ไม่แสดง tools** ทั้งที่:
- ✅ Initialize handshake สำเร็จ
- ✅ Server ส่ง tools list ไปแล้ว
- ✅ ไม่มี error ใน logs

**แนะนำ**: ควรพิจารณา **Option 2 (REST API)** เพื่อให้โปรเจคใช้งานได้จริง หรือติดต่อทีม Dify เพื่อขอคำแนะนำเกี่ยว HTTP MCP implementation ที่ถูกต้อง

---

*Generated: November 19, 2025*
*Last Updated: November 19, 2025*
