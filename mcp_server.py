#!/usr/bin/env python3
"""
MCP Server for RAG Pipeline (Streamable HTTP Transport)
Compatible with Dify MCP Integration

This server exposes RAG capabilities as MCP tools via Streamable HTTP transport.
Streamable HTTP is the new MCP transport that Dify requires (POST initialize directly, no SSE endpoint discovery).
"""

import os
import logging
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import json
import asyncio
from typing import Dict, Any, Optional, List
import traceback
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)

# Import our RAG pipeline components
import app.rag_pipeline as rag_pipeline
import app.config as config
from app.schemas import SourceNode

# Global variables
query_engine = None
chat_histories: Dict[str, List] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    global query_engine
    print("🚀 Starting MCP Server for RAG...")
    
    # Initialize query engine
    query_engine = rag_pipeline.get_query_engine()
    
    print("✅ MCP Server ready")
    yield
    
    # Cleanup
    print("🛑 Shutting down MCP Server...")
    query_engine = None
    chat_histories.clear()

# Create FastAPI app
app = FastAPI(
    title="RAG MCP Server",
    description="Model Context Protocol Server for RAG Operations",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware for Dify integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# MCP Protocol Implementation (HTTP+SSE)
# ============================================================================

# SSE message creator removed - using Streamable HTTP (pure JSON-RPC over POST)

# SSE generator removed - Streamable HTTP uses direct POST initialize
# No SSE endpoint discovery needed with Streamable HTTP transport

# SSE endpoint removed - Streamable HTTP doesn't need it
# Dify expects pure HTTP POST for initialize, not SSE discovery

async def handle_mcp_message(request: Request):
    """
    Main MCP message handler
    Handles all MCP JSON-RPC requests
    """
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
            # Notifications per JSON-RPC 2.0 don't have "id" and server MUST NOT respond
            # Dify has a bug where it tries to parse notification responses as JSONRPCMessage
            # Solution: Return HTTP 202 Accepted with no body (standard for async acknowledgment)
            print(f"✅ Notification acknowledged: {method}")
            return Response(status_code=202, headers={"Content-Length": "0"})
        else:
            return create_error_response(message_id, -32601, f"Method not found: {method}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        traceback.print_exc()
        return create_error_response(None, -32603, str(e))


# --------------------------------------------------------------------------------
# CRITICAL: Dify requires URL to end with /mcp for StreamableHTTPTransport!
# See: https://github.com/langgenius/dify/issues/28111
# "Dify selects the transport based solely on the last segment of your MCP server URL:
#  it must end exactly with /mcp"
# --------------------------------------------------------------------------------

@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """Main MCP endpoint - MUST be /mcp for Dify to use StreamableHTTPTransport."""
    return await handle_mcp_message(request)


# Fallback endpoints for compatibility
@app.post("/")
async def root_post(request: Request):
    """Fallback MCP endpoint."""
    return await handle_mcp_message(request)


@app.post("/message")
async def message_endpoint(request: Request):
    """Alternative MCP endpoint."""
    return await handle_mcp_message(request)


@app.get("/")
async def root_get(request: Request):
    """Handle SSE requests - send endpoint URL as SSE event"""
    accept = request.headers.get("accept", "")
    
    if "text/event-stream" in accept:
        logger.info(f"📍 GET / from {request.client.host}")
        logger.info(f"📍 Accept: {accept}")
        logger.info("📍 Sending endpoint as SSE event")
        
        async def send_endpoint():
            try:
                base_url = str(request.base_url).rstrip('/')
                
                # Try multiple formats - one of them should work
                # Format 1: Plain URL as event data
                yield f"event: endpoint\ndata: {base_url}/\n\n"
                logger.info(f"📍 Sent endpoint event (plain): {base_url}/")
                
                await asyncio.sleep(0.5)
                
                # Format 2: JSON string
                yield f'event: endpoint\ndata: "{base_url}/"\n\n'
                logger.info(f"📍 Sent endpoint event (JSON string)")
                
                await asyncio.sleep(0.5)
                
                # Format 3: JSON object
                endpoint_data = json.dumps({"url": f"{base_url}/"})
                yield f"event: endpoint\ndata: {endpoint_data}\n\n"
                logger.info(f"📍 Sent endpoint event (JSON object)")
                
                # Keep alive
                while True:
                    await asyncio.sleep(15)
                    yield ": keepalive\n\n"
                    
            except Exception as e:
                logger.error(f"❌ SSE error: {e}")
        
        return StreamingResponse(
            send_endpoint(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "MCP-Protocol-Version": "2024-11-05"
            }
        )

# ============================================================================
# MCP Protocol Handlers
# ============================================================================

def handle_initialize(message_id: Any) -> JSONResponse:
    """Handle initialize request - includes tools list directly"""
    response = {
        "jsonrpc": "2.0",
        "id": message_id,
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {
                    "listChanged": True
                }
            },
            "serverInfo": {
                "name": "rag-mcp-server",
                "version": "1.0.0"
            },
            "instructions": "RAG MCP Server for document upload, query, and chat operations",
            # Include tools list directly in initialize response for Dify compatibility
            "tools": [
                {
                    "name": "upload_document",
                    "description": "Upload and index a document (PDF, TXT, or DOCX) for RAG. Returns extracted metadata and confirmation.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "file_content": {
                                "type": "string",
                                "description": "Base64 encoded file content"
                            },
                            "file_name": {
                                "type": "string",
                                "description": "Name of the file (e.g., 'document.pdf')"
                            },
                            "content_type": {
                                "type": "string",
                                "description": "MIME type: 'application/pdf', 'text/plain', or 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'",
                                "enum": ["application/pdf", "text/plain", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
                            }
                        },
                        "required": ["file_content", "file_name", "content_type"]
                    }
                },
                {
                    "name": "query_documents",
                    "description": "Query the RAG system with a question. Returns an answer with source documents. Stateless - no conversation history.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "question": {
                                "type": "string",
                                "description": "The question to ask"
                            }
                        },
                        "required": ["question"]
                    }
                },
                {
                    "name": "chat_with_documents",
                    "description": "Chat with documents using conversation history. Maintains context across messages in a session. Use for multi-turn conversations.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "question": {
                                "type": "string",
                                "description": "The question or message to send"
                            },
                            "session_id": {
                                "type": "string",
                                "description": "Unique session ID to maintain conversation history (e.g., 'user123_session1')"
                            }
                        },
                        "required": ["question", "session_id"]
                    }
                },
                {
                    "name": "clear_chat_history",
                    "description": "Clear conversation history for a specific session",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "session_id": {
                                "type": "string",
                                "description": "Session ID to clear"
                            }
                        },
                        "required": ["session_id"]
                    }
                }
            ]
        }
    }
    print(f"📤 Sending initialize response with {len(response['result']['tools'])} tools")
    return JSONResponse(response)

def handle_tools_list(message_id: Any) -> JSONResponse:
    """Handle tools/list request - Define available tools"""
    return JSONResponse({
        "jsonrpc": "2.0",
        "id": message_id,
        "result": {
            "tools": [
                {
                    "name": "upload_document",
                    "description": "Upload and index a document (PDF, TXT, or DOCX) for RAG. Returns extracted metadata and confirmation.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "file_content": {
                                "type": "string",
                                "description": "Base64 encoded file content"
                            },
                            "file_name": {
                                "type": "string",
                                "description": "Name of the file (e.g., 'document.pdf')"
                            },
                            "content_type": {
                                "type": "string",
                                "description": "MIME type: 'application/pdf', 'text/plain', or 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'",
                                "enum": ["application/pdf", "text/plain", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
                            }
                        },
                        "required": ["file_content", "file_name", "content_type"]
                    }
                },
                {
                    "name": "query_documents",
                    "description": "Query the RAG system with a question. Returns an answer with source documents. Stateless - no conversation history.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "question": {
                                "type": "string",
                                "description": "The question to ask"
                            }
                        },
                        "required": ["question"]
                    }
                },
                {
                    "name": "chat_with_documents",
                    "description": "Chat with documents using conversation history. Maintains context across messages in a session. Use for multi-turn conversations.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "question": {
                                "type": "string",
                                "description": "The question or message to send"
                            },
                            "session_id": {
                                "type": "string",
                                "description": "Unique session ID to maintain conversation history (e.g., 'user123_session1')"
                            }
                        },
                        "required": ["question", "session_id"]
                    }
                },
                {
                    "name": "clear_chat_history",
                    "description": "Clear conversation history for a specific session",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "session_id": {
                                "type": "string",
                                "description": "Session ID to clear"
                            }
                        },
                        "required": ["session_id"]
                    }
                }
            ]
        }
    })

async def handle_tools_call(message_id: Any, params: Dict[str, Any]) -> JSONResponse:
    """Handle tools/call request - Execute tool"""
    try:
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        print(f"🔧 Calling tool: {tool_name}")
        
        # Route to appropriate tool handler
        if tool_name == "upload_document":
            result = await tool_upload_document(arguments)
        elif tool_name == "query_documents":
            result = await tool_query_documents(arguments)
        elif tool_name == "chat_with_documents":
            result = await tool_chat_with_documents(arguments)
        elif tool_name == "clear_chat_history":
            result = await tool_clear_chat_history(arguments)
        else:
            return create_error_response(message_id, -32602, f"Unknown tool: {tool_name}")
        
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": message_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, ensure_ascii=False, indent=2)
                    }
                ]
            }
        })
        
    except Exception as e:
        print(f"❌ Tool execution error: {e}")
        traceback.print_exc()
        return create_error_response(message_id, -32603, f"Tool execution failed: {str(e)}")

# ============================================================================
# Tool Implementations
# ============================================================================

async def tool_upload_document(args: Dict[str, Any]) -> Dict[str, Any]:
    """Tool: Upload and index a document"""
    import base64
    
    file_content_b64 = args.get("file_content")
    file_name = args.get("file_name")
    content_type = args.get("content_type")
    
    # Decode base64 file content
    file_bytes = base64.b64decode(file_content_b64)
    
    # Index the document
    success, metadata = rag_pipeline.index_document(file_bytes, file_name, content_type)
    
    if success:
        return {
            "success": True,
            "filename": file_name,
            "message": "Document indexed successfully",
            "metadata": metadata
        }
    else:
        return {
            "success": False,
            "filename": file_name,
            "message": "Failed to index document",
            "metadata": None
        }

async def tool_query_documents(args: Dict[str, Any]) -> Dict[str, Any]:
    """Tool: Query documents (stateless)"""
    global query_engine
    
    if query_engine is None:
        return {
            "error": "Query engine not initialized",
            "answer": None,
            "sources": []
        }
    
    question = args.get("question")
    
    # Execute query
    response = query_engine.invoke({"input": question})
    
    answer = response.get("answer", "ไม่พบคำตอบ")
    source_nodes_data = response.get("context", [])
    
    # Format sources
    sources = []
    for idx, node in enumerate(source_nodes_data):
        score = node.metadata.get("relevance_score", 1.0 - (idx * 0.1))
        sources.append({
            "text": node.page_content[:200] + "..." if len(node.page_content) > 200 else node.page_content,
            "score": round(score, 4),
            "file_name": node.metadata.get("file_name", "Unknown"),
            "page_number": node.metadata.get("page_number", 0)
        })
    
    return {
        "answer": answer,
        "sources": sources,
        "source_count": len(sources)
    }

async def tool_chat_with_documents(args: Dict[str, Any]) -> Dict[str, Any]:
    """Tool: Chat with documents (stateful)"""
    global query_engine, chat_histories
    
    from langchain_core.messages import HumanMessage, AIMessage
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain.chains import create_history_aware_retriever, create_retrieval_chain
    from langchain.chains.combine_documents import create_stuff_documents_chain
    from langchain.retrievers.document_compressors import CrossEncoderReranker
    from langchain_community.cross_encoders import HuggingFaceCrossEncoder
    from langchain.retrievers import ContextualCompressionRetriever
    
    if query_engine is None:
        return {
            "error": "Query engine not initialized",
            "answer": None,
            "sources": []
        }
    
    question = args.get("question")
    session_id = args.get("session_id")
    
    # Get or create chat history
    session_history = chat_histories.get(session_id, [])
    
    # Create retriever
    vector_store = rag_pipeline.get_vector_store()
    retriever = vector_store.as_retriever(
        search_type="similarity", 
        search_kwargs={"k": 10}
    )
    model = HuggingFaceCrossEncoder(model_name="BAAI/bge-reranker-v2-m3")
    compressor = CrossEncoderReranker(model=model, top_n=3)
    compression_retriever = ContextualCompressionRetriever(
        base_compressor=compressor,
        base_retriever=retriever
    )
    
    # Create history-aware retriever
    CONDENSE_QUESTION_PROMPT_TMPL = (
        "จากประวัติการสนทนาและคำถามล่าสุด, จงเรียบเรียงคำถามล่าสุด"
        "ให้เป็นคำถามที่สมบูรณ์และเข้าใจได้ในตัวเอง (Standalone Question)\n"
        "ประวัติการสนทนา: \n"
        "{chat_history}\n"
        "คำถามล่าสุด: {input}\n"
        "คำถามที่สมบูรณ์: "
    )
    
    condense_prompt = ChatPromptTemplate.from_messages([
        ("system", CONDENSE_QUESTION_PROMPT_TMPL),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
    ])
    
    history_aware_retriever = create_history_aware_retriever(
        rag_pipeline.llm,
        compression_retriever,
        condense_prompt
    )
    
    # Create QA chain
    qa_document_chain = create_stuff_documents_chain(rag_pipeline.llm, rag_pipeline.THAI_QA_TEMPLATE_LC)
    
    # Create RAG chain
    rag_chain = create_retrieval_chain(
        history_aware_retriever,
        qa_document_chain
    )
    
    # Execute query with history
    response = rag_chain.invoke({
        "input": question,
        "chat_history": session_history
    })
    
    # Update chat history
    session_history.append(HumanMessage(content=question))
    session_history.append(AIMessage(content=response.get("answer", "")))
    chat_histories[session_id] = session_history
    
    # Format response
    answer = response.get("answer", "ไม่พบคำตอบ")
    source_nodes_data = response.get("context", [])
    
    sources = []
    for idx, node in enumerate(source_nodes_data):
        score = node.metadata.get("relevance_score", 1.0 - (idx * 0.1))
        sources.append({
            "text": node.page_content[:200] + "..." if len(node.page_content) > 200 else node.page_content,
            "score": round(score, 4),
            "file_name": node.metadata.get("file_name", "Unknown"),
            "page_number": node.metadata.get("page_number", 0)
        })
    
    return {
        "answer": answer,
        "sources": sources,
        "source_count": len(sources),
        "session_id": session_id,
        "conversation_length": len(session_history)
    }

async def tool_clear_chat_history(args: Dict[str, Any]) -> Dict[str, Any]:
    """Tool: Clear chat history for a session"""
    global chat_histories
    
    session_id = args.get("session_id")
    
    if session_id in chat_histories:
        del chat_histories[session_id]
        return {
            "success": True,
            "message": f"Chat history cleared for session: {session_id}"
        }
    else:
        return {
            "success": False,
            "message": f"No chat history found for session: {session_id}"
        }

# ============================================================================
# Utility Functions
# ============================================================================

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
# Health Check (for debugging)
# ============================================================================

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "server": "rag-mcp-server",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    
    # Support PORT environment variable for cloud deployment
    port = int(os.getenv("PORT", 8000))
    
    # Run directly with app instance (not string) to avoid reload cache issues
    uvicorn.run(
        app,  # Direct app instance instead of "mcp_server:app"
        host="0.0.0.0",
        port=port,
        reload=False  # Disable reload to avoid cache issues
    )
