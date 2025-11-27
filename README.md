# 🚀 Multi-Knowledge Base RAG System
## Simple but Powerful - AI-Powered Document Management & Semantic Search

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Visual Workflows](#-visual-workflows)
- [Workflow 1: Document Upload Process](#-workflow-1-document-upload-process-ai-first-ingestion)
- [Workflow 2: Chat with Specific KB](#-workflow-2-chat-with-specific-kb-chat_with_kb)
- [Workflow 3: Smart Chat with Auto-Routing](#-workflow-3-smart-chat-with-auto-routing-chat_global)
- [Workflow 4: System Architecture Data Flow](#-workflow-4-system-architecture-data-flow)
- [Quick Start](#-quick-start)
- [User Journey](#-user-journey)
- [1. เพิ่มเอกสาร (Upload Documents)](#1-เพิ่มเอกสาร-upload-documents)
- [2. คุยกับเอกสาร (Chat with Documents)](#2-คุยกับเอกสาร-chat-with-documents)
- [MCP Tools Reference](#-mcp-tools-reference)
- [Advanced Features](#-advanced-features)
- [API Examples](#-api-examples)
- [Troubleshooting](#-troubleshooting)

---

## 🎯 Overview

**Multi-KB RAG** เป็นระบบ Retrieval-Augmented Generation (RAG) ที่รองรับ **หลาย Knowledge Bases** แยกกันได้ พร้อมฟีเจอร์ AI ที่ช่วย:

- 🤖 **สกัดข้อมูลอัตโนมัติ** - AI อ่านเอกสารและสร้าง metadata (ประเภท, หมวดหมู่, ชื่อ)
- 🌐 **Semantic Router** - ถามคำถามโดยไม่ต้องระบุ KB → ระบบหา KB ที่เหมาะสมให้อัตโนมัติ
- 💬 **Conversation Memory** - จำบทสนทนาก่อนหน้า (per session)
- 📦 **Auto-Create** - อัพโหลดเอกสารครั้งแรก → สร้าง KB ให้อัตโนมัติ
- 🔍 **Vector Search** - ค้นหาด้วย semantic similarity (Qdrant + HuggingFace embeddings)

---

## ✨ Key Features

### 🎨 **For Users:**
- ✅ อัพโหลดเอกสาร PDF, TXT, DOCX ได้ทันที
- ✅ ถามคำถามภาษาไทย/อังกฤษ ได้คำตอบพร้อมแหล่งอ้างอิง
- ✅ จัดระเบียบเอกสารแยกตาม KB (เช่น แยกตามลูกค้า, โปรเจค, หมวดหมู่)
- ✅ ไม่ต้องจำชื่อ KB - ใช้ `chat_global` ระบบหาให้

### 🛠️ **For Developers:**
- ✅ **8 MCP Tools** - Integration-ready สำหรับ AI Agents (Dify, etc.)
- ✅ **RESTful API** - FastAPI + JSON-RPC protocol
- ✅ **Scalable** - รองรับ 1000+ KBs, millions of documents
- ✅ **Logging & Monitoring** - Rotating logs + Prometheus metrics ready
- ✅ **Docker Support** - Qdrant vector database

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      User / AI Agent                        │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              MCP Server (FastAPI + JSON-RPC)                │
│  8 Tools: create, upload, chat, chat_global, list, etc.     │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              Multi-KB RAG Engine (Python)                   │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ AI Metadata  │  │   Semantic   │  │ Conversation │       │
│  │  Extraction  │  │    Router    │  │    Memory    │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
┌───────────────┐  ┌──────────────┐  ┌──────────────┐
│    Qdrant     │  │ HuggingFace  │  │   OpenAI     │
│ Vector Store  │  │  bge-m3 (1k) │  │ Compatible   │
│   (Docker)    │  │  Embeddings  │  │     LLM      │
└───────────────┘  └──────────────┘  └──────────────┘
```

### **Data Flow:**

```
1. User uploads PDF
   ↓
2. AI extracts metadata (doc_type, category, title)
   ↓
3. Generate smart description: "[Legal] Gun License Guide - Category: Legal"
   ↓
4. Create KB collection (if not exists)
   ↓
5. Split document into chunks
   ↓
6. Generate embeddings (1024-dim vectors)
   ↓
7. Store in Qdrant + Update Master Router Index
   ↓
8. User can chat with KB or use chat_global (auto-route)
```

---

## � Visual Workflows

### **🔄 Workflow 1: Document Upload Process (AI-First Ingestion)**

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         DOCUMENT UPLOAD WORKFLOW                         │
└──────────────────────────────────────────────────────────────────────────┘

    User/Agent                MCP Server           Multi-KB Engine           Qdrant/LLM
        │                          │                      │                      │
        │  1. upload_document      │                      │                      │
        │─────────────────────────>│                      │                      │
        │  (kb_name, file_content) │                      │                      │
        │                          │  2. Extract Text     │                      │
        │                          │─────────────────────>│                      │
        │                          │                      │                      │
        │                          │  3. Extract first    │                      │
        │                          │     page content     │                      │
        │                          │<─────────────────────│                      │
        │                          │                      │                      │
        │                          │  4. AI Metadata      │  5. LLM API Call     │
        │                          │     Extraction       │─────────────────────>│
        │                          │                      │ (extract doc_type,   │
        │                          │                      │  title, category)    │
        │                          │                      │<─────────────────────│
        │                          │                      │                      │
        │                          │  6. Generate Smart   │                      │
        │                          │     Description      │                      │
        │                          │  "[type] title -     │                      │
        │                          │   Category: cat"     │                      │
        │                          │                      │                      │
        │                          │  7. Create/Check     │  8. Create Collection│
        │                          │     Collection       │─────────────────────>│
        │                          │  (if auto_create)    │  (kb_{kb_name})      │
        │                          │                      │<─────────────────────│
        │                          │                      │                      │
        │                          │  9. Chunk Document   │                      │
        │                          │  (split into pages   │                      │
        │                          │   + paragraphs)      │                      │
        │                          │                      │                      │
        │                          │  10. Generate        │  11. Embed Chunks    │
        │                          │      Embeddings      │─────────────────────>│
        │                          │                      │  (bge-m3, 1024-dim)  │
        │                          │                      │<─────────────────────│
        │                          │                      │                      │
        │                          │  12. Store Vectors   │  13. Upsert Points   │
        │                          │      + Metadata      │─────────────────────>│
        │                          │                      │  (vectors + payload) │
        │                          │                      │<─────────────────────│
        │                          │                      │                      │
        │                          │  14. Update Router   │  15. Embed Description│
        │                          │      Index           │─────────────────────>│
        │                          │  (master_router_     │  (for semantic       │
        │                          │   index)             │   routing)           │
        │                          │                      │<─────────────────────│
        │                          │                      │                      │
        │                          │  16. Store in Router │  17. Upsert to       │
        │                          │                      │      Router Index    │
        │                          │                      │─────────────────────>│
        │                          │                      │<─────────────────────│
        │                          │                      │                      │
        │                          │  18. Return Success  │                      │
        │                          │<─────────────────────│                      │
        │  19. Success Response    │                      │                      │
        │<─────────────────────────│                      │                      │
        │  {success: true,         │                      │                      │
        │   kb_name, description,  │                      │                      │
        │   metadata, chunks}      │                      │                      │
        │                          │                      │                      │
        ▼                          ▼                      ▼                      ▼

📊 Result:
  ✅ Document stored in Qdrant collection: kb_{kb_name}
  ✅ AI-extracted metadata attached to all chunks
  ✅ Master router index updated with KB description
  ✅ Ready for semantic search and chat queries
```

---

### **💬 Workflow 2: Chat with Specific KB (chat_with_kb)**

```
┌──────────────────────────────────────────────────────────────────────────┐
│                       CHAT WITH KNOWLEDGE BASE                           │
└──────────────────────────────────────────────────────────────────────────┘

    User/Agent                MCP Server           Multi-KB Engine           Qdrant/LLM
        │                          │                      │                      │
        │  1. chat_with_kb         │                      │                      │
        │─────────────────────────>│                      │                      │
        │  (kb_name, query,        │                      │                      │
        │   session_id, top_k)     │                      │                      │
        │                          │                      │                      │
        │                          │  2. Load Chat        │                      │
        │                          │     History          │                      │
        │                          │  (from memory)       │                      │
        │                          │                      │                      │
        │                          │  3. Embed Query      │  4. Generate Vector  │
        │                          │                      │─────────────────────>│
        │                          │                      │  (bge-m3, 1024-dim)  │
        │                          │                      │<─────────────────────│
        │                          │                      │                      │
        │                          │  5. Vector Search    │  6. Cosine Similarity│
        │                          │     (top_k results)  │─────────────────────>│
        │                          │                      │  Search in kb_{name} │
        │                          │                      │<─────────────────────│
        │                          │                      │  [doc1, doc2, ...]   │
        │                          │                      │                      │
        │                          │  7. Build Context    │                      │
        │                          │  (retrieved docs +   │                      │
        │                          │   chat history)      │                      │
        │                          │                      │                      │
        │                          │  8. Generate Answer  │  9. LLM API Call     │
        │                          │                      │─────────────────────>│
        │                          │                      │  (context + query)   │
        │                          │                      │<─────────────────────│
        │                          │                      │  AI-generated answer │
        │                          │                      │                      │
        │                          │  10. Save to History │                      │
        │                          │   (query + answer)   │                      │
        │                          │                      │                      │
        │                          │  11. Format Response │                      │
        │                          │   (answer + sources) │                      │
        │                          │                      │                      │
        │                          │  12. Return Result   │                      │
        │                          │<─────────────────────│                      │
        │  13. Chat Response       │                      │                      │
        │<─────────────────────────│                      │                      │
        │  {answer: "...",         │                      │                      │
        │   sources: [...],        │                      │                      │
        │   kb_name: "..."}        │                      │                      │
        │                          │                      │                      │
        ▼                          ▼                      ▼                      ▼

📊 Result:
  ✅ AI-generated answer based on retrieved documents
  ✅ Source citations with page numbers and similarity scores
  ✅ Conversation history saved for context continuity
```

---

### **🎯 Workflow 3: Smart Chat with Auto-Routing (chat_global)**

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    SEMANTIC ROUTER AUTO-ROUTING CHAT                     │
└──────────────────────────────────────────────────────────────────────────┘

    User/Agent                MCP Server           Multi-KB Engine           Qdrant/LLM
        │                          │                      │                      │
        │  1. chat_global          │                      │                      │
        │─────────────────────────>│                      │                      │
        │  (query, session_id,     │                      │                      │
        │   top_k)                 │                      │                      │
        │  ⚡ NO kb_name specified! │                      │                      │
        │                          │                      │                      │
        │                          │  2. Embed Query      │  3. Generate Vector  │
        │                          │                      │─────────────────────>│
        │                          │                      │  (bge-m3, 1024-dim)  │
        │                          │                      │<─────────────────────│
        │                          │                      │                      │
        │                          │  4. Search Router    │  5. Query Master     │
        │                          │     Index            │     Router Index     │
        │                          │  (find best KB)      │─────────────────────>│
        │                          │                      │  (master_router_     │
        │                          │                      │   index collection)  │
        │                          │                      │<─────────────────────│
        │                          │                      │  [{kb: "gun_law",    │
        │                          │                      │    score: 0.87}]     │
        │                          │                      │                      │
        │                          │  6. Check Threshold  │                      │
        │                          │  (score >= 0.4?)     │                      │
        │                          │                      │                      │
        │        ┌─────────────────┴───────────┐          │                      │
        │        ▼ YES                         ▼ NO       │                      │
        │   Found Match!                  No Match        │                      │
        │   kb_name = "gun_law"          Return Error     │                      │
        │   confidence = 0.87            (below threshold)│                      │
        │        │                              │         │                      │
        │        └──────────────┬───────────────┘         │                      │
        │                       ▼                         │                      │
        │                          │  7. Route to KB      │                      │
        │                          │  (call chat_with_kb  │                      │
        │                          │   with found kb_name)│                      │
        │                          │                      │                      │
        │                          │  8-13. Same as       │  [Vector Search +    │
        │                          │   "Chat with KB"     │   LLM Generation]    │
        │                          │   workflow           │───────────────┐      │
        │                          │   (see Workflow 2)   │               │      │
        │                          │                      │<──────────────┘      │
        │                          │                      │                      │
        │                          │  14. Return Result + │                      │
        │                          │      Routing Info    │                      │
        │                          │<─────────────────────│                      │
        │  15. Chat Response       │                      │                      │
        │<─────────────────────────│                      │                      │
        │  {answer: "...",         │                      │                      │
        │   sources: [...],        │                      │                      │
        │   kb_name: "gun_law",    │                      │                      │
        │   confidence: 0.87}      │ ⚡ Extra metadata!    │                      │
        │                          │                      │                      │
        ▼                          ▼                      ▼                      ▼

📊 Result:
  ✅ AI automatically found the most relevant KB
  ✅ User doesn't need to know KB names
  ✅ Routing confidence score provided for transparency
  ✅ Seamless experience like chatting with entire knowledge base
```

---

### **🏗️ Workflow 4: System Architecture Data Flow**

```
┌──────────────────────────────────────────────────────────────────────────┐
│                     COMPLETE SYSTEM DATA FLOW                            │
└──────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────────────┐
                              │                     │
                              │  User / AI Agent    │
                              │  (Dify, Claude,     │
                              │   ChatGPT, etc.)    │
                              │                     │
                              └──────────┬──────────┘
                                         │
                                         │ HTTP POST /mcp
                                         │ (JSON-RPC 2.0)
                                         │
                                         ▼
                    ┌────────────────────────────────────────┐
                    │    MCP Server (FastAPI)                │
                    │                                        │
                    │  🛠️  8 Available Tools:                │
                    │  1. create_collection                  │
                    │  2. upload_document_to_kb              │
                    │  3. chat_with_kb                       │
                    │  4. chat_global        ⭐ NEW          │
                    │  5. list_collections                   │
                    │  6. get_collection_info                │
                    │  7. clear_chat_history                 │
                    │  8. delete_collection                  │
                    │                                        │
                    │  📊 Request Middleware:                │
                    │  - Logs all requests                   │
                    │  - Timing metrics                      │
                    │  - Error tracking                      │
                    │                                        │
                    └──────────────┬─────────────────────────┘
                                   │
                                   │ Python function calls
                                   │
                                   ▼
        ┌──────────────────────────────────────────────────────────┐
        │          Multi-KB RAG Engine (Core Logic)                │
        │                                                          │
        │  ┌────────────────┐  ┌────────────────┐  ┌───────────┐   │
        │  │  AI Metadata   │  │    Semantic    │  │   Chat    │   │
        │  │   Extractor    │  │     Router     │  │  History  │   │
        │  │                │  │                │  │  Manager  │   │
        │  │ • Extract type │  │ • Master Index │  │ • Per-    │   │
        │  │ • Extract cat  │  │ • Route to KB  │  │   session │   │
        │  │ • Extract title│  │ • Threshold    │  │ • Context │   │
        │  │ • Generate desc│  │   0.4+         │  │   aware   │   │
        │  └────────────────┘  └────────────────┘  └───────────┘   │
        │                                                          │
        │  📝 Document Processing:                                 │
        │  - Text extraction (PDF/DOCX/TXT)                        │
        │  - Chunking (configurable size)                          │
        │  - Metadata enrichment                                   │
        │                                                         │
        │  🔍 Search Pipeline:                                    │
        │  - Query embedding                                      │
        │  - Vector similarity search                             │
        │  - Context ranking                                      │
        │  - Answer generation                                    │
        │                                                         │
        └────────┬─────────────────┬──────────────────┬───────────┘
                 │                 │                  │
                 │                 │                  │
                 ▼                 ▼                  ▼
     ┌───────────────────┐  ┌──────────────┐  ┌─────────────────┐
     │     Qdrant        │  │ HuggingFace  │  │   OpenAI-       │
     │  Vector Database  │  │   Embeddings │  │  Compatible     │
     │                   │  │              │  │      LLM        │
     │  Collections:     │  │  Model:      │  │                 │
     │  • kb_{name}      │  │  bge-m3      │  │  Tasks:         │
     │  • kb_{name}_2    │  │              │  │  • Generate     │
     │  • master_router_ │  │  Dimension:  │  │    answers      │
     │    index  ⭐      │  │  1024        │  │  • Extract      │
     │                   │  │              │  │    metadata     │
     │  Features:        │  │  Language:   │  │  • Summarize    │
     │  • HNSW index     │  │  Multi-      │  │                 │
     │  • Cosine sim     │  │  lingual     │  │  API:           │
     │  • Metadata       │  │  (Thai/Eng)  │  │  OpenAI-        │
     │    filtering      │  │              │  │  compatible     │
     │  • Scalable       │  │              │  │                 │
     │                   │  │              │  │                 │
     └───────────────────┘  └──────────────┘  └─────────────────┘
              ▲                     ▲                   ▲
              │                     │                   │
              │                     │                   │
        Docker Volume          HTTP API            HTTP API
        (persistent)         (embedding)         (completion)


📊 Key Data Structures:

1. Document Chunk (stored in Qdrant):
   {
     "text": "ขั้นตอนการขอใบอนุญาต...",
     "metadata": {
       "filename": "gun_license_handbook.pdf",
       "page_number": 5,
       "doc_type": "Official Document",
       "category": "Legal",
       "kb_name": "gun_law"
     },
     "vector": [0.123, -0.456, ..., 0.789]  // 1024 dimensions
   }

2. Router Index Entry (master_router_index):
   {
     "kb_name": "gun_law",
     "description": "[Official Document] คู่มือการขอใบอนุญาตปืน - Category: Legal",
     "vector": [0.321, 0.654, ..., -0.987]  // 1024 dimensions
   }

3. Chat History (in-memory):
   {
     "session_id": "user123_gun_20251125",
     "messages": [
       {"role": "user", "content": "ขั้นตอนการขอใบอนุญาต..."},
       {"role": "assistant", "content": "ขั้นตอนมี 5 ขั้น..."}
     ]
   }
```

---

## �🚀 Quick Start

### **Prerequisites:**

- Python 3.10+
- Docker (for Qdrant)
- OpenAI-compatible LLM endpoint

### **Installation:**

```bash
# 1. Clone repository
git clone https://github.com/YourRepo/rag-mcp-server.git
cd rag-mcp-server

# 2. Create virtual environment
python3 -m venv venv_clean
source venv_clean/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start Qdrant (vector database)
docker-compose up -d qdrant

# 5. Configure environment
cp .env.example .env
# Edit .env with your LLM API key

# 6. Start server
./start_multi_kb.sh
```

Server จะรันที่: `http://localhost:8000`

---

## 👤 User Journey

## 1. เพิ่มเอกสาร (Upload Documents)

### **วิธีที่ 1: ผ่าน Dify Agent (แนะนำ)**

**Scenario:** ต้องการอัพโหลดคู่มือใบอนุญาตปืน

#### **Step 1: เตรียมเอกสาร**
```
ไฟล์: gun_license_handbook.pdf
ขนาด: 5.2 MB
ภาษา: ไทย
หน้า: 45 หน้า
```

#### **Step 2: บอก Agent**
```
User: "อัพโหลดไฟล์คู่มือใบอนุญาตปืนนี้ให้หน่อย [แนบไฟล์ gun_license_handbook.pdf]"
```

#### **Step 3: Agent ทำงานอัตโนมัติ**

**Agent จะเรียกใช้ tool: `upload_document_to_kb`**

```json
{
  "kb_name": "gun_law",
  "file_content": "JVBERi0xLjQKJeLjz9MKMSAwIG9iago8PAovVH...",
  "filename": "gun_license_handbook.pdf",
  "content_type": "application/pdf",
  "auto_create": true
}
```

#### **Step 4: ระบบประมวลผล (Behind the scenes)**

```
📄 Extracting text from gun_license_handbook.pdf...
   ✓ Extracted 45 pages

🤖 AI Extracting metadata from document...
   ✓ AI Metadata extracted: {
       "doc_type": "Official Document",
       "category": "Legal",
       "status": "Published",
       "title": "คู่มือการขอใบอนุญาตปืน (พ.ร.บ. อาวุธปืน)"
     }

📝 Generated description: 
   "[Official Document] คู่มือการขอใบอนุญาตปืน - Category: Legal"

📦 Collection 'gun_law' not found, creating with AI-generated description...
   ✓ Collection created: kb_gun_law
   Description: [Official Document] คู่มือการขอใบอนุญาตปืน - Category: Legal

📝 Creating documents from 45 pages...
   ✓ Created 892 chunks

✅ Successfully uploaded gun_license_handbook.pdf to gun_law
   KB Name: gun_law
   Collection: kb_gun_law
   Description: [Official Document] คู่มือการขอใบอนุญาตปืน - Category: Legal
   AI Metadata: {doc_type: "Official Document", category: "Legal", ...}

✅ Updated router index for: gun_law
```

#### **Step 5: Agent ตอบกลับ**
```
Agent: "✅ อัพโหลดเอกสารสำเร็จแล้วค่ะ!

📚 Knowledge Base: gun_law
📄 ไฟล์: gun_license_handbook.pdf (45 หน้า)
🤖 AI ตรวจพบว่าเป็น: Official Document (Legal)
📝 ชื่อเอกสาร: คู่มือการขอใบอนุญาตปืน

ระบบได้แบ่งเอกสารเป็น 892 ส่วน และจัดเก็บไว้แล้ว
พร้อมตอบคำถามเกี่ยวกับเนื้อหาในเอกสารได้เลยค่ะ!"
```

---

### **วิธีที่ 2: ผ่าน API โดยตรง**

```bash
# แปลงไฟล์เป็น base64
base64 -i gun_license_handbook.pdf -o file.b64

# เรียก API
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "upload_document_to_kb",
      "arguments": {
        "kb_name": "gun_law",
        "file_content": "'$(cat file.b64)'",
        "filename": "gun_license_handbook.pdf",
        "content_type": "application/pdf",
        "auto_create": true
      }
    }
  }'
```

---

### **🎨 สิ่งที่เกิดขึ้นภายใน:**

1. **AI อ่านเอกสาร (หน้าแรก):**
   - ใช้ LLM สกัดข้อมูล: ประเภทเอกสาร, หมวดหมู่, ชื่อ, สถานะ
   - สร้าง description ที่อธิบายเนื้อหา

2. **สร้าง Knowledge Base:**
   - ถ้า KB ยังไม่มี → สร้างอัตโนมัติ (auto_create=true)
   - ตั้งชื่อ: `kb_gun_law` (normalize: lowercase + underscore)

3. **แบ่งเอกสาร (Chunking):**
   - Split เป็น chunks (ขนาด configurable)
   - แต่ละ chunk มี metadata: filename, page_number, doc_type, category

4. **สร้าง Embeddings:**
   - ใช้ HuggingFace bge-m3 model
   - แปลง text → 1024-dim vectors

5. **เก็บใน Qdrant:**
   - Upload vectors + metadata
   - Index ด้วย HNSW algorithm (fast cosine similarity search)

6. **Update Semantic Router:**
   - Embed description → เก็บใน `master_router_index`
   - ใช้สำหรับ auto-routing ภายหลัง

---

## 2. คุยกับเอกสาร (Chat with Documents)

### **วิธีที่ 1: ระบุ KB ชัดเจน (chat_with_kb)**

**Scenario:** รู้ว่าต้องการถามเกี่ยวกับ gun_law KB

#### **Step 1: ถามคำถาม**
```
User: "ขั้นตอนการขอใบอนุญาตปืนมีอะไรบ้าง?"
```

#### **Step 2: Agent เลือก Tool**

**Agent รู้ว่าต้องใช้ KB = gun_law → เรียก `chat_with_kb`**

```json
{
  "kb_name": "gun_law",
  "query": "ขั้นตอนการขอใบอนุญาตปืนมีอะไรบ้าง?",
  "session_id": "user123_gun_20251125",
  "top_k": 5
}
```

#### **Step 3: ระบบค้นหา (Behind the scenes)**

```
1️⃣ Embed query → [0.23, -0.45, 0.89, ...] (1024-dim)

2️⃣ Search kb_gun_law collection
   - Cosine similarity with all vectors
   - Top-5 most similar chunks:
   
   Chunk 1 (score: 0.92):
   "ขั้นตอนการยื่นขอใบอนุญาตปืน
    1. เตรียมเอกสารประกอบ...
    2. ยื่นคำขอที่สถานีตำรวจ..."
   
   Chunk 2 (score: 0.88):
   "เอกสารที่ต้องใช้ในการขอใบอนุญาต
    - สำเนาบัตรประชาชน
    - สำเนาทะเบียนบ้าน..."
   
   [3 more chunks...]

3️⃣ Retrieve conversation history (session: user123_gun_20251125)
   - Previous Q&A (if any)

4️⃣ Build prompt for LLM:
   Context: [Top-5 chunks]
   History: [Previous Q&A]
   Question: "ขั้นตอนการขอใบอนุญาตปืนมีอะไรบ้าง?"

5️⃣ LLM generates answer with citations
```

#### **Step 4: ได้คำตอบ**

```json
{
  "success": true,
  "kb_name": "gun_law",
  "session_id": "user123_gun_20251125",
  "answer": "ขั้นตอนการขอใบอนุญาตปืนมีดังนี้:\n\n1. **เตรียมเอกสาร:**\n   - สำเนาบัตรประชาชน\n   - สำเนาทะเบียนบ้าน\n   - รูปถ่ายขนาด 1 นิ้ว จำนวน 2 ใบ\n\n2. **ยื่นคำขอ:**\n   - ยื่นคำขอที่สถานีตำรวจในเขตที่อยู่อาศัย\n   - ชำระค่าธรรมเนียม 1,000 บาท\n\n3. **ตรวจสอบคุณสมบัติ:**\n   - ตำรวจจะตรวจสอบประวัติอาชญากรรม\n   - สัมภาษณ์เพื่อประเมินความจำเป็น\n\n4. **รับใบอนุญาต:**\n   - รอผลพิจารณา 30-60 วัน\n   - หากอนุมัติ มารับใบอนุญาตที่สถานีตำรวจ\n\n**หมายเหตุ:** ผู้ขอต้องมีอายุไม่ต่ำกว่า 20 ปีบริบูรณ์ และไม่มีประวัติอาชญากรรม",
  "sources": [
    {
      "content": "ขั้นตอนการยื่นขอใบอนุญาตปืน\n1. เตรียมเอกสารประกอบ...",
      "metadata": {
        "kb_name": "gun_law",
        "filename": "gun_license_handbook.pdf",
        "page_number": 12,
        "doc_type": "Official Document",
        "category": "Legal"
      }
    }
  ]
}
```

#### **Step 5: Agent แสดงผล**
```
Agent: "ขั้นตอนการขอใบอนุญาตปืนมีดังนี้ค่ะ:

1. **เตรียมเอกสาร:**
   - สำเนาบัตรประชาชน
   - สำเนาทะเบียนบ้าน
   - รูปถ่ายขนาด 1 นิ้ว จำนวน 2 ใบ

2. **ยื่นคำขอ:**
   - ยื่นคำขอที่สถานีตำรวจในเขตที่อยู่อาศัย
   - ชำระค่าธรรมเนียม 1,000 บาท

3. **ตรวจสอบคุณสมบัติ:**
   - ตำรวจจะตรวจสอบประวัติอาชญากรรม
   - สัมภาษณ์เพื่อประเมินความจำเป็น

4. **รับใบอนุญาต:**
   - รอผลพิจารณา 30-60 วัน
   - หากอนุมัติ มารับใบอนุญาตที่สถานีตำรวจ

**หมายเหตุ:** ผู้ขอต้องมีอายุไม่ต่ำกว่า 20 ปีบริบูรณ์

📚 **อ้างอิงจาก:**
- gun_license_handbook.pdf (หน้า 12)
"
```

---

### **วิธีที่ 2: ไม่ระบุ KB (chat_global) - Semantic Router 🌐**

**Scenario:** User ไม่รู้ว่าต้องถาม KB ไหน

#### **Step 1: ถามคำถามทั่วไป**
```
User: "บอกหน่อยว่าจะขอใบอนุญาตปืนยังไง?"
```

#### **Step 2: Agent ใช้ Semantic Router**

**Agent ไม่รู้ KB → เรียก `chat_global`** (ระบบหาให้อัตโนมัติ)

```json
{
  "query": "บอกหน่อยว่าจะขอใบอนุญาตปืนยังไง?",
  "session_id": "user123_auto_20251125",
  "top_k": 5
}
```

#### **Step 3: Semantic Routing (Behind the scenes)**

```
🌐 Auto-routing query: 'บอกหน่อยว่าจะขอใบอนุญาตปืนยังไง?'

1️⃣ Embed query → [0.21, -0.43, 0.87, ...] (1024-dim)

2️⃣ Search master_router_index (ค้นหา KB ที่เหมาะสม)
   
   Available KBs:
   - kb_gun_law: "[Official] คู่มือการขอใบอนุญาตปืน - Legal"
   - kb_medical: "[Medical] Patient Care Procedures"
   - kb_hr_policy: "[HR] Employee Handbook"
   
   Similarity scores:
   ✅ kb_gun_law: 0.89 (highest!)
   ❌ kb_medical: 0.23
   ❌ kb_hr_policy: 0.15

3️⃣ Check threshold: 0.89 > 0.4 ✅

🎯 Router found: gun_law (score: 0.890)
   Description: [Official] คู่มือการขอใบอนุญาตปืน - Legal

✅ Routed to: gun_law (confidence: 0.890)

4️⃣ Now call chat_with_collection(kb_name="gun_law", ...)
   [Same as วิธีที่ 1 from here...]
```

#### **Step 4: ได้คำตอบพร้อมข้อมูล Routing**

```json
{
  "success": true,
  "kb_name": "gun_law",
  "session_id": "user123_auto_20251125",
  "answer": "[Same detailed answer as above]",
  "sources": [...],
  "routed_to": "gun_law",
  "routing_confidence": 0.89,
  "routing_method": "semantic_similarity"
}
```

#### **Step 5: Agent แสดงผล**
```
Agent: "🎯 ระบบตรวจพบว่าคำถามนี้เกี่ยวกับ 'gun_law' (ความมั่นใจ: 89%)

[Same answer as above...]

💡 **Tip:** คำถามถัดไปเกี่ยวกับ gun law สามารถถามต่อได้เลยค่ะ 
ระบบจะจำบทสนทนาไว้ให้"
```

---

### **🔄 ต่อบทสนทนา (Conversation History)**

#### **คำถามที่ 2 (Same Session):**
```
User: "แล้วค่าธรรมเนียมเท่าไหร่?"
```

**System:**
```
📝 Using session: user123_gun_20251125
📚 Retrieved conversation history:
   Q1: "ขั้นตอนการขอใบอนุญาตปืนมีอะไรบ้าง?"
   A1: "ขั้นตอนการขอใบอนุญาตปืนมีดังนี้: 1. เตรียมเอกสาร..."

🔍 Context-aware search:
   - Query: "แล้วค่าธรรมเนียมเท่าไหร่?"
   - + Previous context: "ขั้นตอนการขอใบอนุญาตปืน"
   → Understands: ถามเรื่องค่าธรรมเนียม "ใบอนุญาตปืน"

✅ Answer: "ค่าธรรมเนียมการขอใบอนุญาตปืนคือ 1,000 บาท 
   (ตามที่กล่าวไว้ในขั้นตอนที่ 2 ของคำตอบก่อนหน้า)"
```

---

### **🎨 ความแตกต่างระหว่าง chat_with_kb vs chat_global:**

| Feature | chat_with_kb | chat_global |
|---------|--------------|-------------|
| **KB Selection** | ต้องระบุ kb_name | ✅ Auto-route |
| **Speed** | เร็วกว่า (~50ms) | ช้ากว่านิด (~110ms) |
| **Use When** | รู้ KB ชัดเจน | ไม่รู้ KB หรือต้องการให้ระบบหา |
| **Accuracy** | 100% (ถูก KB) | 85-95% (depend on router) |
| **Best For** | API, specific queries | AI Agent, general questions |

---

## 📚 MCP Tools Reference

### **1. create_collection**
สร้าง Knowledge Base ใหม่ (แต่แนะนำให้ข้าม → ใช้ auto_create ใน upload)

```json
{
  "name": "create_collection",
  "arguments": {
    "kb_name": "medical_records",
    "description": "Patient medical records and history"
  }
}
```

---

### **2. upload_document_to_kb** ⭐
อัพโหลดเอกสารไปยัง KB (auto-create ถ้ายังไม่มี)

```json
{
  "name": "upload_document_to_kb",
  "arguments": {
    "kb_name": "medical_records",
    "file_content": "JVBERi0xLjQK...",  // base64
    "filename": "patient_001.pdf",
    "content_type": "application/pdf",
    "auto_create": true  // สร้าง KB อัตโนมัติถ้ายังไม่มี
  }
}
```

**AI จะทำอัตโนมัติ:**
- สกัด metadata (doc_type, category, title)
- สร้าง description
- สร้าง KB (ถ้า auto_create=true)
- Update semantic router index

---

### **3. chat_with_kb** ⭐
คุยกับ KB ที่ระบุ (มี conversation history)

```json
{
  "name": "chat_with_kb",
  "arguments": {
    "kb_name": "medical_records",
    "query": "What's the patient's blood type?",
    "session_id": "doctor123_patient001",
    "top_k": 5
  }
}
```

**Returns:**
- `answer`: คำตอบจาก LLM
- `sources`: เอกสารอ้างอิง (พร้อม page number)
- `session_id`: สำหรับต่อบทสนทนา

---

### **4. chat_global** 🌐 ⭐
คุยโดยไม่ระบุ KB (ระบบหาให้อัตโนมัติ)

```json
{
  "name": "chat_global",
  "arguments": {
    "query": "How do I apply for a gun license?",
    "session_id": "user123_auto",
    "top_k": 5
  }
}
```

**Returns:**
- [Same as chat_with_kb] +
- `routed_to`: KB ที่ถูกเลือก
- `routing_confidence`: คะแนนความมั่นใจ (0-1)
- `routing_method`: "semantic_similarity"

**ถ้า routing failed:**
```json
{
  "success": false,
  "message": "I don't know which knowledge base to use",
  "available_kbs": ["gun_law", "medical", "hr_policy"]
}
```

---

### **5. list_collections**
ดูรายการ KB ทั้งหมด

```json
{
  "name": "list_collections",
  "arguments": {}
}
```

**Returns:**
```json
{
  "success": true,
  "collections": [
    {
      "kb_name": "gun_law",
      "collection_name": "kb_gun_law",
      "description": "[Official] คู่มือการขอใบอนุญาตปืน - Legal",
      "vector_count": 892,
      "created_at": "2025-11-25T10:30:00"
    }
  ],
  "total": 1
}
```

---

### **6. get_collection_info**
ดูข้อมูลรายละเอียดของ KB

```json
{
  "name": "get_collection_info",
  "arguments": {
    "kb_name": "gun_law"
  }
}
```

**Returns:**
- Vector count
- Collection size
- Metadata (description, created_at)

---

### **7. clear_chat_history**
ลบประวัติการสนทนา

```json
{
  "name": "clear_chat_history",
  "arguments": {
    "kb_name": "gun_law",
    "session_id": "user123_gun_20251125"
  }
}
```

---

### **8. delete_collection**
ลบ KB ทั้งหมด (ระวัง: ลบเอกสารทั้งหมด!)

```json
{
  "name": "delete_collection",
  "arguments": {
    "kb_name": "gun_law"
  }
}
```

---

## 🚀 Advanced Features

### **1. Semantic Router (Master Index)**

ระบบ Semantic Router ใช้ **Master Index** (`master_router_index`) เพื่อจับคู่ query กับ KB

**How it works:**
1. แต่ละ KB มี **description** (AI-generated)
2. Description ถูก embed → เก็บใน master_router_index
3. เมื่อ user ถามคำถาม → embed query → ค้นหา KB ที่ description ใกล้เคียงที่สุด
4. ถ้า score > 0.4 → route ไป KB นั้น

**Example:**
```
Query: "How to renew my gun license?"
→ Embed: [0.21, -0.43, 0.87, ...]
→ Search master_router_index
→ Best match: kb_gun_law (score: 0.89)
→ Route to kb_gun_law
```

**Adjusting threshold:**
```python
# In app/multi_kb_rag.py
ROUTER_SIMILARITY_THRESHOLD = 0.4  # Default

# More lenient (more matches):
ROUTER_SIMILARITY_THRESHOLD = 0.3

# More strict (fewer matches):
ROUTER_SIMILARITY_THRESHOLD = 0.5
```

---

### **2. AI Metadata Extraction**

เมื่ออัพโหลดเอกสาร AI จะอ่าน **หน้าแรก** และสกัดข้อมูล:

```json
{
  "doc_type": "Official Document | Technical Manual | Research Paper | ...",
  "category": "Legal | Medical | Technical | HR | ...",
  "status": "Published | Draft | Archived",
  "title": "คู่มือการขอใบอนุญาตปืน"
}
```

**Smart Description Generation:**
```
Format: "[{doc_type}] {title} - Category: {category} ({status})"

Example: "[Official Document] คู่มือการขอใบอนุญาตปืน - Category: Legal (Published)"
```

This description is crucial for Semantic Router!

---

### **3. Conversation Memory Management**

ระบบเก็บ conversation history แยกตาม:
- **Collection:** แต่ละ KB มี memory แยกกัน
- **Session ID:** แต่ละ session มี memory แยกกัน

**Structure:**
```python
chat_histories[collection_name][session_id] = ConversationBufferMemory
```

**Best Practices for session_id:**
```python
# Good: Descriptive and consistent
session_id = f"{user_id}_{topic}_{date}"
# Examples:
- "user123_gun_20251125"
- "doctor456_patient001"
- "agent789_legal_20251125"

# Bad: Too generic or random
session_id = "session_123"  # ❌ Not descriptive
session_id = str(uuid.uuid4())  # ❌ New session every time
```

---

### **4. Multi-File Upload to Same KB**

```python
# Upload multiple documents to same KB
files = ["doc1.pdf", "doc2.pdf", "doc3.pdf"]

for file in files:
    upload_document_to_kb(
        kb_name="legal_docs",  # Same KB
        file_content=encode_base64(file),
        filename=file,
        auto_create=True  # Only creates KB once
    )
```

**Result:**
- Single KB: `kb_legal_docs`
- Multiple documents indexed together
- Single description (from first upload)

---

### **5. Performance Tips**

#### **Optimize Vector Search:**
```python
# Adjust top_k based on document size
chat_with_kb(
    kb_name="large_kb",
    query="...",
    top_k=3  # Smaller = faster, less context
    # top_k=10  # Larger = slower, more context
)
```

#### **Batch Uploads:**
```python
# Instead of:
for doc in docs:
    upload_document(...)  # ❌ Slow

# Do:
# Upload all docs first, then chat
upload_document(doc1)
upload_document(doc2)
upload_document(doc3)
chat_with_kb(...)  # All docs indexed
```

#### **Cache Collections List:**
```python
# Cache list_collections() result (changes infrequently)
collections = list_collections()  # Call once
# Use cached result for multiple operations
```

---

## 📡 API Examples

### **cURL Examples:**

#### **Initialize Connection:**
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {"name": "my-client", "version": "1.0"}
    }
  }'
```

#### **Upload Document:**
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "upload_document_to_kb",
      "arguments": {
        "kb_name": "my_kb",
        "file_content": "'$(base64 -i document.pdf)'",
        "filename": "document.pdf",
        "content_type": "application/pdf",
        "auto_create": true
      }
    }
  }'
```

#### **Chat Global:**
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "chat_global",
      "arguments": {
        "query": "What are the requirements?",
        "session_id": "user123_session1",
        "top_k": 5
      }
    }
  }'
```

---

## 🐛 Troubleshooting

### **Problem: "Collection does not exist"**

**Cause:** KB ยังไม่ถูกสร้าง

**Solution:**
```python
# Option 1: Use auto_create
upload_document_to_kb(..., auto_create=True)  # ✅

# Option 2: Create manually first
create_collection(kb_name="my_kb")
upload_document_to_kb(...)
```

---

### **Problem: "Router index is empty"**

**Cause:** ยังไม่มี KB ใดๆ ในระบบ (ใช้ chat_global ไม่ได้)

**Solution:**
```python
# Upload at least one document first
upload_document_to_kb(...)

# Then chat_global will work
chat_global(query="...")
```

---

### **Problem: "Low routing confidence"**

**Cause:** Query ไม่ match กับ KB descriptions

**Solution:**
```python
# 1. Lower threshold (app/multi_kb_rag.py)
ROUTER_SIMILARITY_THRESHOLD = 0.3  # More lenient

# 2. Or use specific KB
chat_with_kb(kb_name="my_kb", ...)  # Skip routing

# 3. Upload more documents → better descriptions
```

---

### **Problem: "Context loss in conversation"**

**Cause:** session_id เปลี่ยนทุกครั้ง

**Solution:**
```python
# ❌ Bad: New session every time
session_id = str(uuid.uuid4())

# ✅ Good: Consistent session ID
session_id = "user123_topic_20251125"  # Reuse for same conversation
```

---

### **Problem: "Server slow to start"**

**Cause:** Load embeddings model at startup

**Solution:**
```bash
# Pre-download model (one-time)
python3 -c "
from langchain_huggingface import HuggingFaceEmbeddings
HuggingFaceEmbeddings(model_name='BAAI/bge-m3')
"

# Next startup will be faster
```

---

## 📊 Monitoring & Logs

### **Log Files:**
```
logs/server.log  # All requests, errors, debug info
```

### **Log Levels:**
- **Console:** INFO (clean output)
- **File:** DEBUG (detailed)

### **View Logs:**
```bash
# Real-time logs
tail -f logs/server.log

# Last 50 lines
tail -50 logs/server.log

# Search for errors
grep ERROR logs/server.log

# Search for specific KB
grep "gun_law" logs/server.log
```

### **Log Rotation:**
- Max size: 10 MB
- Backups: 5 files
- Total: 50 MB max

---

## 🤝 Integration with AI Agents

### **Dify Integration:**

1. **Add MCP Server in Dify:**
   ```
   Tools → MCP Servers → Add Server
   URL: http://localhost:8000/mcp  (or ngrok URL)
   Name: multi-kb-rag-server
   ```

2. **Create Agent:**
   ```
   Model: GPT-4
   Tools: Select all 8 tools
   Instructions: "You are a document assistant..."
   ```

3. **Test:**
   ```
   User: "Upload this PDF and answer questions about it"
   Agent: [Uses upload_document_to_kb + chat_with_kb]
   ```

### **Custom Integration:**

```python
import requests

class RAGClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.msg_id = 0
    
    def call_tool(self, tool_name, arguments):
        self.msg_id += 1
        response = requests.post(
            f"{self.base_url}/mcp",
            json={
                "jsonrpc": "2.0",
                "id": self.msg_id,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
        )
        return response.json()
    
    def upload(self, kb_name, file_path):
        import base64
        with open(file_path, 'rb') as f:
            content = base64.b64encode(f.read()).decode()
        
        return self.call_tool("upload_document_to_kb", {
            "kb_name": kb_name,
            "file_content": content,
            "filename": file_path.split('/')[-1],
            "content_type": "application/pdf",
            "auto_create": True
        })
    
    def chat(self, query, session_id="default", kb_name=None):
        if kb_name:
            return self.call_tool("chat_with_kb", {
                "kb_name": kb_name,
                "query": query,
                "session_id": session_id
            })
        else:
            return self.call_tool("chat_global", {
                "query": query,
                "session_id": session_id
            })

# Usage
client = RAGClient()
client.upload("my_kb", "document.pdf")
result = client.chat("What's in the document?")
print(result)
```

---

## 📚 Additional Resources

- **Semantic Router Implementation:** [SEMANTIC_ROUTER_IMPLEMENTATION.md](SEMANTIC_ROUTER_IMPLEMENTATION.md)
- **Performance Optimization:** [OPTIMIZATION_GUIDE.md](OPTIMIZATION_GUIDE.md)
- **Logging Guide:** [LOGGING_GUIDE.md](LOGGING_GUIDE.md)

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file

---

## 🙋 Support

**Issues:** https://github.com/YourRepo/rag-mcp-server/issues  
**Discord:** [Join our community](#)  
**Email:** support@example.com

---

**Built with ❤️ using FastAPI, LangChain, Qdrant, and HuggingFace**
