# app/main.py (อัปเดต 4.0 - ย้ายไป LangChain)

from fastapi import FastAPI, UploadFile, File, HTTPException
from contextlib import asynccontextmanager

# --- (NEW) LangChain Imports ---
from langchain_core.runnables import Runnable
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
# --- (NEW) Reranker (ต้องสร้าง retriever ใน /chat) ---
from langchain.retrievers.document_compressors import CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain.retrievers import ContextualCompressionRetriever

# --- Python Typing Imports ---
from typing import Optional, List, Dict 

# --- Our App Module Imports ---
import app.rag_pipeline as rag_pipeline
import app.config as config
from app.schemas import (
    UploadResponse,
    QueryRequest,
    QueryResponse,
    SourceNode,
    ChatRequest
)
# (NEW) Import components จาก rag_pipeline ที่เราสร้าง
from app.rag_pipeline import llm, get_vector_store, THAI_QA_TEMPLATE_LC

# --- Global variable (อัปเดต Type Hint) ---
query_engine: Optional[Runnable] = None

# --- Global variable (อัปเดต Type Hint) ---
chat_histories: Dict[str, List[BaseMessage]] = {}


# --- Lifespan Manager (อัปเดต) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- 1. โค้ดที่รันตอน Startup ---
    print("Application is starting up...")
    
    # (ลบ setup_global_settings() - โมเดลถูกโหลดตอน import rag_pipeline แล้ว)
    
    # สร้างและเก็บ Query Engine (ตอนนี้เป็น Runnable) ไว้ใน Global variable
    global query_engine
    query_engine = rag_pipeline.get_query_engine()
    
    print("Application startup complete. Ready to serve requests.")
    yield
    
    # --- 2. โค้ดที่รันตอน Shutdown ---
    print("Application is shutting down...")
    query_engine = None
    chat_histories.clear()


# --- สร้างแอป FastAPI ---
app = FastAPI(
    title="RAG API Pipeline (LangChain Version)",
    description="API สำหรับ Indexing, Querying (Stateless), และ Chat (Stateful)",
    version="2.0.0",
    lifespan=lifespan
)


# --- Endpoint 1: Health Check (เหมือนเดิม) ---
@app.get("/health")
def health_check():
    """เช็กว่า API ทำงานอยู่หรือไม่"""
    return {"status": "ok"}


# --- Endpoint 2: Indexing (อัปเดต - รองรับ txt, docx) ---
@app.post("/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """
    Endpoint สำหรับอัปโหลดไฟล์ PDF, TXT, DOCX (Requirement 1)
    """
    # ตรวจสอบประเภทไฟล์
    allowed_types = ["application/pdf", "text/plain", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF, TXT, and DOCX allowed.")

    try:
        file_bytes = await file.read()
        print(f"Received file for indexing: {file.filename}")
        
        success, metadata = rag_pipeline.index_document(file_bytes, file.filename, file.content_type)

        if success:
            return UploadResponse(
                success=True,
                filename=file.filename,
                message="File processed and indexed successfully.",
                extracted_metadata=metadata
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to process or index the file.")

    except Exception as e:
        print(f"[Error] Upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


# --- Endpoint 3: Querying (Stateless) (อัปเดต) ---
def _get_confidence_level(score: float) -> str:
    """แปลง score เป็น confidence level"""
    if score >= 0.7:
        return "high"
    elif score >= 0.5:
        return "medium"
    elif score >= 0.3:
        return "low"
    else:
        return "very_low"

@app.post("/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest):
    """
    (อัปเดต) Endpoint สำหรับค้นหา (RAG) แบบ Stateless ด้วย LangChain
    """
    global query_engine
    if query_engine is None:
        raise HTTPException(status_code=503, detail="Query Engine is not available.")

    try:
        print(f"Received query: {request.question}")
        
        # (NEW) ใช้ .invoke() และส่ง input เป็น dict
        response = query_engine.invoke({"input": request.question}) 
        
        # (NEW) RAG chain จะคืนค่า dict ที่มี 'answer' และ 'context'
        answer = response.get("answer", "ไม่พบคำตอบ")
        source_nodes_data = response.get("context", [])
        
        source_nodes = []
        for idx, node in enumerate(source_nodes_data):
            # CrossEncoderReranker เก็บ score ไว้ที่ metadata.get('relevance_score') 
            # แต่ถ้าไม่มีให้ใช้ลำดับแทน (score สูงสุดคือ 1.0 ลดลงตามลำดับ)
            score = node.metadata.get("relevance_score", 1.0 - (idx * 0.1))
            
            source_nodes.append(SourceNode(
                text_content=node.page_content, 
                score=round(score, 4),  # ปัดเป็น 4 ตำแหน่ง
                confidence=_get_confidence_level(score),
                file_name=node.metadata.get("file_name", "Unknown"),
                page_number=node.metadata.get("page_number", 0)
            ))

        return QueryResponse(answer=answer, source_nodes=source_nodes)

    except Exception as e:
        print(f"[Error] Query failed: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred during query: {str(e)}")


# --- (NEW) Prompt สำหรับ Condense คำถามใน /chat ---
# (ดึงมาจาก prompts.py เดิม)
CONDENSE_QUESTION_PROMPT_TMPL = (
    "จากประวัติการสนทนาและคำถามล่าสุด, จงเรียบเรียงคำถามล่าสุด"
    "ให้เป็นคำถามที่สมบูรณ์และเข้าใจได้ในตัวเอง (Standalone Question)\n"
    "ประวัติการสนทนา: \n"
    "{chat_history}\n"
    "คำถามล่าสุด: {input}\n"
    "คำถามที่สมบูรณ์: "
)

# --- Endpoint 4: Chat (Stateful) (อัปเดตครั้งใหญ่) ---
@app.post("/chat", response_model=QueryResponse)
async def chat_endpoint(request: ChatRequest):
    """
    (อัปเดต) Endpoint สำหรับ Chat แบบ Stateful ด้วย LangChain
    """
    global query_engine, chat_histories, llm
    
    if query_engine is None or llm is None:
        raise HTTPException(status_code=503, detail="Query Engine or LLM is not available.")
    
    try:
        print(f"Received chat for session: {request.session_id}")
        
        # 1. ดึงประวัติแชทเก่า (ตอนนี้เป็น List[BaseMessage])
        session_history = chat_histories.get(request.session_id, [])
        
        # 2. (NEW) สร้าง Chain สำหรับแชท (ต้องทำใหม่ทุกครั้งที่เรียก)
        
        # 2.1 สร้าง Retriever (จำเป็นต้องสร้างใหม่)
        # (หมายเหตุ: นี่คือจุดที่ควร Refactor ในอนาคต)
        # (เราควรสร้างฟังก์ชัน get_retriever() ใน rag_pipeline.py)
        vector_store = get_vector_store()
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
        
        # 2.2 สร้าง History-Aware Retriever (Chain ย่อย 1)
        # (Chain นี้จะรับ history + input -> สร้าง standalone question -> ค้นหา)
        condense_prompt = ChatPromptTemplate.from_messages([
            ("system", CONDENSE_QUESTION_PROMPT_TMPL),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
        ])
        
        history_aware_retriever = create_history_aware_retriever(
            llm,
            compression_retriever,
            condense_prompt
        )

        # 2.3 สร้าง QA Chain (Chain ย่อย 2)
        # (Chain นี้จะรับ context + standalone question -> สร้าง answer)
        # (เราใช้ Prompt ที่ import มาจาก rag_pipeline)
        qa_document_chain = create_stuff_documents_chain(llm, THAI_QA_TEMPLATE_LC)
        
        # 2.4 ประกอบร่างเป็น RAG Chain (Chain หลัก)
        rag_chain = create_retrieval_chain(
            history_aware_retriever,
            qa_document_chain
        )
        
        # 3. (NEW) ยิงคำถาม
        response = rag_chain.invoke({
            "input": request.question,
            "chat_history": session_history
        })
        
        # 4. (NEW) บันทึกประวัติแชท (ต้องสร้าง Message objects)
        session_history.append(HumanMessage(content=request.question))
        session_history.append(AIMessage(content=response.get("answer", "")))
        chat_histories[request.session_id] = session_history
        
        # 5. คืนค่า (เหมือน /query)
        answer = response.get("answer", "ไม่พบคำตอบ")
        source_nodes_data = response.get("context", [])
        
        source_nodes = []
        for idx, node in enumerate(source_nodes_data):
            score = node.metadata.get("relevance_score", 1.0 - (idx * 0.1))
            
            source_nodes.append(SourceNode(
                text_content=node.page_content,
                score=score,
                file_name=node.metadata.get("file_name", "Unknown"),
                page_number=node.metadata.get("page_number", 0)
            ))
        
        return QueryResponse(answer=answer, source_nodes=source_nodes)
        
    except Exception as e:
        print(f"[Error] Chat failed: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred during chat: {str(e)}")