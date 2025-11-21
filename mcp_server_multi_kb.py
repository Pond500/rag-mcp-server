#!/usr/bin/env python3
"""
Multi-KB MCP Server - Hybrid Approach
Simple but Powerful Multi-Knowledge Base RAG System

Features:
- Dynamic collection creation (auto-create if not exists)
- Upload to new or existing collections  
- Query single collections with conversation history
- Collection management (list, info, delete)
- Agent-friendly tool design
"""

import os
import logging
import base64
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import json
from typing import Dict, Any, Optional
import traceback

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Import Multi-KB RAG
from app.multi_kb_rag import get_multi_kb_rag

# Global variables
multi_kb_rag = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    global multi_kb_rag
    print("🚀 Starting Multi-KB MCP Server...")
    
    # Initialize Multi-KB RAG
    multi_kb_rag = get_multi_kb_rag()
    
    print("✅ Multi-KB MCP Server ready")
    yield
    
    # Cleanup
    print("🛑 Shutting down Multi-KB MCP Server...")

# Create FastAPI app
app = FastAPI(
    title="Multi-KB RAG MCP Server",
    description="Multi-Knowledge Base RAG with MCP Protocol",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# MCP Tools Definitions
# ============================================================================

MULTI_KB_TOOLS = [
    {
        "name": "create_collection",
        "description": "สร้าง knowledge base (collection) ใหม่สำหรับเก็บเอกสารแยกประเภท. ใช้เมื่อต้องการเตรียม KB ก่อนอัพโหลดเอกสาร แต่ส่วนใหญ่ไม่จำเป็น เพราะ upload_document_to_kb สามารถสร้าง KB ให้อัตโนมัติได้ (auto_create=true)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "kb_name": {
                    "type": "string",
                    "description": "ชื่อ knowledge base (เช่น 'medical', 'legal', 'project_2024')"
                },
                "description": {
                    "type": "string",
                    "description": "คำอธิบาย knowledge base (optional)"
                }
            },
            "required": ["kb_name"]
        }
    },
    {
        "name": "list_collections",
        "description": "แสดงรายการ knowledge bases ทั้งหมดที่มีในระบบพร้อมจำนวนเอกสารและข้อมูลพื้นฐาน. ใช้เพื่อดูว่ามี KB อะไรบ้าง หรือเช็คว่า KB ที่ต้องการมีอยู่แล้วหรือยัง",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_collection_info",
        "description": "ดูข้อมูลรายละเอียดของ knowledge base เฉพาะตัว รวมถึงจำนวนเอกสาร metadata และสถานะ. ใช้เมื่อต้องการตรวจสอบว่า KB มีเอกสารกี่ชิ้น หรือดูรายละเอียดก่อนใช้งาน",
        "inputSchema": {
            "type": "object",
            "properties": {
                "kb_name": {
                    "type": "string",
                    "description": "ชื่อ knowledge base ที่ต้องการดูข้อมูล"
                }
            },
            "required": ["kb_name"]
        }
    },
    {
        "name": "upload_document_to_kb",
        "description": "อัพโหลดเอกสารไปยัง knowledge base ที่ระบุ (auto-create collection ถ้ายังไม่มี). ใช้ tool นี้เมื่อต้องการเพิ่มเอกสารใหม่ หรือสร้าง KB ใหม่พร้อมอัพโหลดเอกสารครั้งแรก. หลังจากอัพโหลดสำเร็จแล้วสามารถใช้ chat_with_kb เพื่อถามคำถามได้ทันที",
        "inputSchema": {
            "type": "object",
            "properties": {
                "kb_name": {
                    "type": "string",
                    "description": "ชื่อ knowledge base ที่ต้องการอัพโหลดไป"
                },
                "file_content": {
                    "type": "string",
                    "description": "เนื้อหาไฟล์ที่ encode เป็น base64"
                },
                "filename": {
                    "type": "string",
                    "description": "ชื่อไฟล์ (เช่น 'document.pdf')"
                },
                "content_type": {
                    "type": "string",
                    "description": "ประเภทไฟล์: 'application/pdf', 'text/plain', หรือ 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'",
                    "enum": ["application/pdf", "text/plain", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
                },
                "auto_create": {
                    "type": "boolean",
                    "description": "สร้าง collection อัตโนมัติถ้ายังไม่มี (default: true)",
                    "default": True
                }
            },
            "required": ["kb_name", "file_content", "filename", "content_type"]
        }
    },
    {
        "name": "chat_with_kb",
        "description": "คุยกับ knowledge base ที่เลือก (มี conversation history). ใช้ tool นี้เมื่อต้องการถามคำถามเกี่ยวกับเอกสารใน KB. ต้องมีเอกสารอัพโหลดไว้แล้ว (ใช้ upload_document_to_kb ก่อน). ใช้ session_id เดียวกันเพื่อให้ AI จำบทสนทนาก่อนหน้า",
        "inputSchema": {
            "type": "object",
            "properties": {
                "kb_name": {
                    "type": "string",
                    "description": "ชื่อ knowledge base ที่ต้องการคุยด้วย"
                },
                "query": {
                    "type": "string",
                    "description": "คำถามหรือข้อความที่ต้องการส่ง"
                },
                "session_id": {
                    "type": "string",
                    "description": "Session ID สำหรับเก็บประวัติการสนทนา (เช่น 'user123_session1')"
                },
                "top_k": {
                    "type": "integer",
                    "description": "จำนวนเอกสารที่ต้องการดึงมา (default: 5)",
                    "default": 5
                }
            },
            "required": ["kb_name", "query", "session_id"]
        }
    },
    {
        "name": "clear_chat_history",
        "description": "ลบประวัติการสนทนาของ session ใน knowledge base",
        "inputSchema": {
            "type": "object",
            "properties": {
                "kb_name": {
                    "type": "string",
                    "description": "ชื่อ knowledge base"
                },
                "session_id": {
                    "type": "string",
                    "description": "Session ID ที่ต้องการลบประวัติ"
                }
            },
            "required": ["kb_name", "session_id"]
        }
    },
    {
        "name": "delete_collection",
        "description": "ลบ knowledge base ทั้งหมด (ระวัง: จะลบเอกสารทั้งหมดใน collection)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "kb_name": {
                    "type": "string",
                    "description": "ชื่อ knowledge base ที่ต้องการลบ"
                }
            },
            "required": ["kb_name"]
        }
    }
]

# ============================================================================
# MCP Protocol Handlers
# ============================================================================

async def handle_mcp_message(request: Request):
    """Main MCP message handler"""
    try:
        body = await request.json()
        method = body.get("method")
        message_id = body.get("id")
        params = body.get("params", {})
        
        print(f"📥 Received: {method}")
        
        # Route to appropriate handler
        if method == "initialize":
            return handle_initialize(message_id)
        elif method == "tools/list":
            return handle_tools_list(message_id)
        elif method == "tools/call":
            return await handle_tools_call(message_id, params)
        elif method and method.startswith("notifications/"):
            # Notifications: HTTP 202 Accepted with no body
            print(f"✅ Notification acknowledged: {method}")
            return Response(status_code=202, headers={"Content-Length": "0"})
        else:
            return create_error_response(message_id, -32601, f"Method not found: {method}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        traceback.print_exc()
        return create_error_response(None, -32603, str(e))

def handle_initialize(message_id: Any) -> JSONResponse:
    """Handle initialize request"""
    response = {
        "jsonrpc": "2.0",
        "id": message_id,
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {"listChanged": True}
            },
            "serverInfo": {
                "name": "multi-kb-rag-server",
                "version": "2.0.0"
            },
            "instructions": """Multi-Knowledge Base RAG Server v2.0 - Agent Instructions:

📚 WORKFLOW PATTERNS:
1. First time with new KB:
   → upload_document_to_kb (auto_create=true) → chat_with_kb
   
2. Add documents to existing KB:
   → upload_document_to_kb (kb_name=existing) → chat_with_kb
   
3. Query existing KB:
   → chat_with_kb (use same session_id for conversation continuity)
   
4. Explore KBs:
   → list_collections → get_collection_info → chat_with_kb

🔑 KEY FEATURES:
- Auto-create: upload_document_to_kb creates KB if not exists (no need to call create_collection first)
- Session management: Use consistent session_id per user/conversation for context memory
- Multi-KB: Each KB is isolated - no cross-contamination of data
- File types: PDF, TXT, DOCX supported

⚠️ ERROR HANDLING:
- If KB doesn't exist: Use upload_document_to_kb with auto_create=true
- If no documents yet: Upload at least one document before chat_with_kb
- If session not found: It will be created automatically on first chat_with_kb call

💡 TIPS:
- Use descriptive kb_names: 'client_abc', 'project_2024', 'medical_research'
- Use descriptive session_ids: 'user123_medical', 'user456_legal'
- Check list_collections first if unsure which KBs exist""",
            "tools": MULTI_KB_TOOLS
        }
    }
    print(f"📤 Sending initialize response with {len(MULTI_KB_TOOLS)} tools")
    return JSONResponse(response)

def handle_tools_list(message_id: Any) -> JSONResponse:
    """Handle tools/list request"""
    return JSONResponse({
        "jsonrpc": "2.0",
        "id": message_id,
        "result": {"tools": MULTI_KB_TOOLS}
    })

async def handle_tools_call(message_id: Any, params: Dict[str, Any]) -> JSONResponse:
    """Handle tools/call request"""
    tool_name = params.get("name")
    arguments = params.get("arguments", {})
    
    try:
        result = None
        
        if tool_name == "create_collection":
            result = multi_kb_rag.create_collection(
                kb_name=arguments["kb_name"],
                description=arguments.get("description", "")
            )
        
        elif tool_name == "list_collections":
            result = multi_kb_rag.list_collections()
        
        elif tool_name == "get_collection_info":
            result = multi_kb_rag.get_collection_info(
                kb_name=arguments["kb_name"]
            )
        
        elif tool_name == "upload_document_to_kb":
            # Decode base64 file content
            file_bytes = base64.b64decode(arguments["file_content"])
            
            result = multi_kb_rag.upload_document(
                kb_name=arguments["kb_name"],
                file_bytes=file_bytes,
                filename=arguments["filename"],
                content_type=arguments["content_type"],
                auto_create=arguments.get("auto_create", True)
            )
        
        elif tool_name == "chat_with_kb":
            result = multi_kb_rag.chat_with_collection(
                kb_name=arguments["kb_name"],
                query=arguments["query"],
                session_id=arguments["session_id"],
                top_k=arguments.get("top_k", 5)
            )
        
        elif tool_name == "clear_chat_history":
            result = multi_kb_rag.clear_chat_history(
                kb_name=arguments["kb_name"],
                session_id=arguments["session_id"]
            )
        
        elif tool_name == "delete_collection":
            result = multi_kb_rag.delete_collection(
                kb_name=arguments["kb_name"]
            )
        
        else:
            return create_error_response(message_id, -32601, f"Unknown tool: {tool_name}")
        
        # Format result
        result_text = json.dumps(result, ensure_ascii=False, indent=2)
        
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": message_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": result_text
                    }
                ]
            }
        })
    
    except Exception as e:
        print(f"❌ Tool execution failed: {e}")
        traceback.print_exc()
        return create_error_response(message_id, -32603, f"Tool execution failed: {str(e)}")

def create_error_response(message_id: Any, code: int, message: str) -> JSONResponse:
    """Create JSON-RPC error response"""
    return JSONResponse({
        "jsonrpc": "2.0",
        "id": message_id,
        "error": {
            "code": code,
            "message": message
        }
    })

# ============================================================================
# MCP Endpoints
# ============================================================================

@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """Main MCP endpoint - MUST be /mcp for Dify StreamableHTTPTransport"""
    return await handle_mcp_message(request)

@app.post("/")
async def root_post(request: Request):
    """Fallback MCP endpoint"""
    return await handle_mcp_message(request)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "2.0.0", "server": "multi-kb-rag-server"}

# ============================================================================
# Run Server
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
