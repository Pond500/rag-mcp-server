# Dify MCP Integration Guide

คู่มือการทำ MCP Server ให้ทำงานกับ Dify Cloud/Self-hosted

## สิ่งที่ Dify ต้องการ

### 1. URL Endpoint Requirements

**CRITICAL:** Dify เลือก transport protocol จาก URL path segment สุดท้าย!

```
✅ ถูกต้อง: https://your-server.com/mcp
❌ ผิด:     https://your-server.com/
❌ ผิด:     https://your-server.com/api
❌ ผิด:     https://your-server.com/mcp/
```

**เหตุผล:** 
- URL ที่ลงท้ายด้วย `/mcp` (ไม่มี trailing slash) → Dify ใช้ **StreamableHTTPTransport**
- URL อื่นๆ → Dify fallback ไปใช้ **SSE client** ซึ่งจะทำให้เกิด error!

**อ้างอิง:** [Dify Issue #28111](https://github.com/langgenius/dify/issues/28111)

---

### 2. Protocol: StreamableHTTPTransport

Dify ใช้ **Streamable HTTP transport** ไม่ใช่ SSE (Server-Sent Events)!

#### ข้อแตกต่าง:

| Feature | SSE Transport | Streamable HTTP (Dify) |
|---------|---------------|-------------------------|
| Endpoint discovery | GET / → SSE stream with endpoint event | ไม่ต้อง! POST ตรงไปที่ /mcp |
| Initialize | POST /message หลังได้ endpoint | POST /mcp โดยตรง |
| Connection | Long-lived SSE connection | Request-response แบบปกติ |

#### Implementation:

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

app = FastAPI()

@app.post("/mcp")  # ต้องเป็น /mcp!
async def mcp_endpoint(request: Request):
    body = await request.json()
    method = body.get("method")
    message_id = body.get("id")
    
    if method == "initialize":
        return handle_initialize(message_id)
    elif method == "tools/list":
        return handle_tools_list(message_id)
    elif method == "tools/call":
        return handle_tools_call(message_id, body.get("params"))
    elif method.startswith("notifications/"):
        # CRITICAL: ดูข้อ 3!
        return handle_notification(method)
```

---

### 3. Notifications Handling (CRITICAL!)

#### ปัญหา:
Dify ส่ง `notifications/initialized` หลัง initialize และพยายาม **parse response เป็น JSONRPCMessage**!

#### JSON-RPC 2.0 Spec:
- Notifications ไม่มี `id` field
- Server **MUST NOT** respond to notifications

#### แต่ Dify มี bug:
- ถ้าไม่ return อะไร → error "EOF while parsing"
- ถ้า return `{}` → error "missing required fields"
- ถ้า return `{"jsonrpc": "2.0", "result": null}` → error "missing id"

#### วิธีแก้ที่ใช้ได้:

```python
elif method and method.startswith("notifications/"):
    # Return HTTP 202 Accepted with no body
    # 202 = "Acknowledged, no content to return"
    # Dify จะไม่พยายาม parse response!
    return Response(status_code=202, headers={"Content-Length": "0"})
```

**เหตุผล:**
- HTTP 202 Accepted = standard สำหรับ async acknowledgment
- ไม่มี response body → Dify ไม่พยายาม parse
- Tools จะขึ้นใน UI ได้สำเร็จ!

---

### 4. Initialize Response Format

```python
def handle_initialize(message_id):
    return JSONResponse(content={
        "jsonrpc": "2.0",
        "id": message_id,
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {
                    "listChanged": True  # บอก Dify ว่า tools list อาจเปลี่ยน
                }
            },
            "serverInfo": {
                "name": "your-server-name",
                "version": "1.0.0"
            },
            # OPTIONAL: ส่ง tools ตั้งแต่ตอน initialize (ช่วยลด requests)
            "tools": [
                {
                    "name": "tool_name",
                    "description": "Tool description",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "param1": {
                                "type": "string",
                                "description": "Parameter description"
                            }
                        },
                        "required": ["param1"]
                    }
                }
            ]
        }
    })
```

---

### 5. Tools List Response Format

```python
def handle_tools_list(message_id):
    return JSONResponse(content={
        "jsonrpc": "2.0",
        "id": message_id,
        "result": {
            "tools": [
                {
                    "name": "tool_name",
                    "description": "Tool description",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "param1": {"type": "string", "description": "..."}
                        },
                        "required": ["param1"]
                    }
                }
            ]
        }
    })
```

**สิ่งสำคัญ:**
- `inputSchema` ต้องเป็น valid JSON Schema
- Dify จะใช้ schema นี้สร้าง UI form ให้ user กรอก parameters
- `required` array บอกว่า parameters ไหนบังคับ

---

### 6. Tool Call Response Format

```python
def handle_tools_call(message_id, params):
    tool_name = params.get("name")
    arguments = params.get("arguments", {})
    
    try:
        # Execute your tool logic
        result = execute_tool(tool_name, arguments)
        
        return JSONResponse(content={
            "jsonrpc": "2.0",
            "id": message_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": str(result)
                    }
                ]
            }
        })
    except Exception as e:
        return JSONResponse(content={
            "jsonrpc": "2.0",
            "id": message_id,
            "error": {
                "code": -32603,
                "message": str(e)
            }
        })
```

---

### 7. Headers Requirements

```python
# ไม่จำเป็นต้องมี special headers!
# Dify จะส่ง:
# - Content-Type: application/json
# - Accept: application/json
# - User-Agent: python-httpx/0.27.2

# แต่ควรใส่ CORS ถ้าเป็น public API:
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Complete Example

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/mcp")
async def mcp_endpoint(request: Request):
    try:
        body = await request.json()
        method = body.get("method")
        message_id = body.get("id")
        params = body.get("params", {})
        
        if method == "initialize":
            return JSONResponse(content={
                "jsonrpc": "2.0",
                "id": message_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {"listChanged": True}},
                    "serverInfo": {"name": "my-server", "version": "1.0.0"}
                }
            })
        
        elif method == "tools/list":
            return JSONResponse(content={
                "jsonrpc": "2.0",
                "id": message_id,
                "result": {
                    "tools": [
                        {
                            "name": "echo",
                            "description": "Echo back the input",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "message": {
                                        "type": "string",
                                        "description": "Message to echo"
                                    }
                                },
                                "required": ["message"]
                            }
                        }
                    ]
                }
            })
        
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if tool_name == "echo":
                result = arguments.get("message", "")
                return JSONResponse(content={
                    "jsonrpc": "2.0",
                    "id": message_id,
                    "result": {
                        "content": [{"type": "text", "text": result}]
                    }
                })
        
        elif method and method.startswith("notifications/"):
            # HTTP 202 Accepted - no body!
            return Response(status_code=202, headers={"Content-Length": "0"})
        
        else:
            return JSONResponse(content={
                "jsonrpc": "2.0",
                "id": message_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            })
    
    except Exception as e:
        return JSONResponse(content={
            "jsonrpc": "2.0",
            "id": None,
            "error": {"code": -32603, "message": str(e)}
        })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## Testing with Dify

### 1. Local Development with ngrok

```bash
# Start your server
python server.py

# Start ngrok tunnel
ngrok http 8000

# Use ngrok URL in Dify
# URL: https://abc123.ngrok-free.app/mcp
```

### 2. Dify Configuration

```
Server URL: https://your-domain.com/mcp
Server Name: my-server
Server Identifier: myserver (lowercase, no spaces)
```

### 3. Expected Flow

```
Dify → POST /mcp {method: "initialize"}
  ← 200 OK {result: {serverInfo, capabilities}}

Dify → POST /mcp {method: "notifications/initialized"}
  ← 202 Accepted (no body)

Dify → POST /mcp {method: "tools/list"}
  ← 200 OK {result: {tools: [...]}}

→ Tools appear in Dify UI! ✅
```

---

## Common Errors & Solutions

### Error: "failed to get endpoint URL"
**สาเหตุ:** URL ไม่ลงท้ายด้วย `/mcp`  
**แก้:** เปลี่ยนเป็น `https://your-server.com/mcp`

### Error: "Error during cleanup: EOF while parsing"
**สาเหตุ:** Return empty string สำหรับ notification  
**แก้:** Return HTTP 202 with no body

### Error: "11 validation errors for JSONRPCMessage"
**สาเหตุ:** Return `{}` หรือ `{"result": null}` สำหรับ notification  
**แก้:** Return HTTP 202 Accepted

### Error: "StreamableHTTPTransport got exception"
**สาเหตุ:** Dify ใช้ SSE client แทน StreamableHTTPTransport  
**แก้:** ตรวจสอบ URL ต้องลงท้ายด้วย `/mcp`

### Tools ไม่ขึ้นใน Dify UI
**เช็คตามลำดับ:**
1. URL ลงท้ายด้วย `/mcp`? 
2. Initialize response มี `capabilities.tools.listChanged: true`?
3. Notification return HTTP 202?
4. Tools/list response มี valid JSON Schema?
5. ดู Dify logs มี error อะไร?

---

## Protocol Version

**ใช้:** `2024-11-05` (latest stable)

ถ้า Dify บ่นเรื่อง version ให้ดูที่:
- [Dify Issue #27677](https://github.com/langgenius/dify/issues/27677) - Protocol version compatibility

---

## References

1. [MCP Specification](https://spec.modelcontextprotocol.io/)
2. [Dify Issue #28111](https://github.com/langgenius/dify/issues/28111) - StreamableHTTPTransport bug
3. [Dify Issue #27740](https://github.com/langgenius/dify/issues/27740) - FastMCP with IP+port
4. [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification)

---

## Tips

1. **ใช้ logging:** Log ทุก request/response เพื่อ debug
2. **Test ด้วย curl:** ทดสอบ endpoint ก่อนเอาไปใช้กับ Dify
3. **ดู Dify logs:** Self-hosted Dify มี logs ที่ช่วย debug ได้
4. **Protocol version:** ติดตาม Dify updates - protocol อาจเปลี่ยน!
5. **Error handling:** Return proper JSON-RPC error responses

---

## Troubleshooting Commands

```bash
# Test initialize
curl -X POST https://your-server.com/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'

# Test notification
curl -v -X POST https://your-server.com/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized","params":{}}'
# Should return: HTTP 202 Accepted

# Test tools/list
curl -X POST https://your-server.com/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' | jq .
```

---

**สรุป:** Dify ต้องการ MCP server ที่:
1. ✅ URL ลงท้ายด้วย `/mcp`
2. ✅ ใช้ Streamable HTTP (POST directly, no SSE)
3. ✅ Return HTTP 202 สำหรับ notifications
4. ✅ Return valid JSON-RPC responses
5. ✅ มี proper error handling

เท่านี้ Tools จะขึ้นใน Dify UI! 🎉
