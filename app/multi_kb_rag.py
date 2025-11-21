"""
Multi-Knowledge Base RAG Pipeline
Hybrid Approach: Simple but Powerful

Features:
- Dynamic collection creation (auto-create if not exists)
- Upload to new or existing collections
- Query single or multiple collections
- Collection management (list, info, delete)
"""

import qdrant_client
from qdrant_client.models import Distance, VectorParams, PointStruct
from typing import List, Dict, Any, Optional, Tuple
import uuid
from datetime import datetime
import json

# LangChain imports
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_qdrant import Qdrant
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory

# Local imports
import app.config as config
from app.ocr_service import get_text_from_pdf
import io


class MultiKnowledgeBaseRAG:
    """Multi-Knowledge Base RAG System with Hybrid Approach"""
    
    def __init__(self):
        """Initialize Multi-KB RAG system"""
        print("🚀 Initializing Multi-Knowledge Base RAG System...")
        
        # Qdrant client
        self.qdrant_client = qdrant_client.QdrantClient(
            host=config.QDRANT_HOST,
            port=config.QDRANT_PORT
        )
        
        # LLM
        self.llm = ChatOpenAI(
            model=config.LLM_MODEL_NAME,
            base_url=config.LLM_API_BASE,
            api_key=config.LLM_API_KEY,
            max_tokens=1500,
            temperature=0.5,
            request_timeout=120
        )
        
        # Embedding model
        self.embed_model = HuggingFaceEmbeddings(
            model_name=config.EMBED_MODEL_NAME,
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP
        )
        
        # Chat histories: {collection_name: {session_id: ConversationBufferMemory}}
        self.chat_histories: Dict[str, Dict[str, ConversationBufferMemory]] = {}
        
        print("✅ Multi-KB RAG System initialized")
    
    def _normalize_collection_name(self, name: str) -> str:
        """Normalize collection name (lowercase, replace spaces with underscore)"""
        return name.lower().replace(" ", "_").replace("-", "_")
    
    def _get_collection_name(self, kb_name: str) -> str:
        """Get full collection name with prefix"""
        normalized = self._normalize_collection_name(kb_name)
        return f"kb_{normalized}"
    
    def collection_exists(self, collection_name: str) -> bool:
        """Check if collection exists"""
        try:
            self.qdrant_client.get_collection(collection_name)
            return True
        except Exception:
            return False
    
    def create_collection(self, kb_name: str, description: str = "") -> Dict[str, Any]:
        """
        Create new knowledge base (collection)
        
        Args:
            kb_name: Knowledge base name (e.g., "medical", "legal")
            description: Optional description
            
        Returns:
            Dict with collection info
        """
        collection_name = self._get_collection_name(kb_name)
        
        if self.collection_exists(collection_name):
            return {
                "success": False,
                "message": f"Collection '{kb_name}' already exists",
                "collection_name": collection_name
            }
        
        try:
            # Create collection (bge-m3 dimension = 1024)
            self.qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
            )
            
            # Store metadata as payload in a special point
            metadata_point = PointStruct(
                id=str(uuid.uuid4()),
                vector=[0.0] * 1024,  # Dummy vector
                payload={
                    "_type": "collection_metadata",
                    "kb_name": kb_name,
                    "description": description,
                    "created_at": datetime.now().isoformat(),
                    "document_count": 0
                }
            )
            self.qdrant_client.upsert(
                collection_name=collection_name,
                points=[metadata_point]
            )
            
            print(f"✅ Created collection: {collection_name}")
            return {
                "success": True,
                "kb_name": kb_name,
                "collection_name": collection_name,
                "description": description,
                "created_at": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"❌ Failed to create collection: {e}")
            return {
                "success": False,
                "message": str(e)
            }
    
    def list_collections(self) -> List[Dict[str, Any]]:
        """List all knowledge base collections"""
        try:
            collections = self.qdrant_client.get_collections().collections
            kb_list = []
            
            for col in collections:
                if col.name.startswith("kb_"):
                    kb_name = col.name[3:]  # Remove "kb_" prefix
                    
                    # Get collection info
                    info = self.qdrant_client.get_collection(col.name)
                    
                    kb_list.append({
                        "kb_name": kb_name,
                        "collection_name": col.name,
                        "points_count": info.points_count,
                        "vectors_count": info.vectors_count
                    })
            
            return kb_list
        except Exception as e:
            print(f"❌ Failed to list collections: {e}")
            return []
    
    def get_collection_info(self, kb_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed info about a collection"""
        collection_name = self._get_collection_name(kb_name)
        
        if not self.collection_exists(collection_name):
            return None
        
        try:
            info = self.qdrant_client.get_collection(collection_name)
            
            # Try to get metadata
            metadata = None
            try:
                results = self.qdrant_client.scroll(
                    collection_name=collection_name,
                    scroll_filter={
                        "must": [
                            {"key": "_type", "match": {"value": "collection_metadata"}}
                        ]
                    },
                    limit=1
                )
                if results[0]:
                    metadata = results[0][0].payload
            except Exception:
                pass
            
            return {
                "kb_name": kb_name,
                "collection_name": collection_name,
                "points_count": info.points_count,
                "vectors_count": info.vectors_count,
                "metadata": metadata
            }
        except Exception as e:
            print(f"❌ Failed to get collection info: {e}")
            return None
    
    def delete_collection(self, kb_name: str) -> Dict[str, Any]:
        """Delete a knowledge base collection"""
        collection_name = self._get_collection_name(kb_name)
        
        if not self.collection_exists(collection_name):
            return {
                "success": False,
                "message": f"Collection '{kb_name}' not found"
            }
        
        try:
            self.qdrant_client.delete_collection(collection_name)
            
            # Clear chat histories for this collection
            if collection_name in self.chat_histories:
                del self.chat_histories[collection_name]
            
            print(f"✅ Deleted collection: {collection_name}")
            return {
                "success": True,
                "message": f"Collection '{kb_name}' deleted successfully"
            }
        except Exception as e:
            print(f"❌ Failed to delete collection: {e}")
            return {
                "success": False,
                "message": str(e)
            }
    
    def _extract_text_from_file(self, file_bytes: bytes, content_type: str) -> List[Dict[str, Any]]:
        """Extract text from file based on content type"""
        if content_type == "application/pdf":
            return get_text_from_pdf(file_bytes)
        
        elif content_type == "text/plain":
            try:
                text = file_bytes.decode('utf-8')
                return [{"page_number": 1, "text": text}]
            except Exception as e:
                print(f"❌ Failed to read TXT: {e}")
                return []
        
        elif content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            try:
                import docx
                doc = docx.Document(io.BytesIO(file_bytes))
                full_text = []
                for para in doc.paragraphs:
                    if para.text.strip():
                        full_text.append(para.text)
                text = '\n'.join(full_text)
                return [{"page_number": 1, "text": text}]
            except Exception as e:
                print(f"❌ Failed to read DOCX: {e}")
                return []
        
        else:
            print(f"❌ Unsupported file type: {content_type}")
            return []
    
    def upload_document(
        self,
        kb_name: str,
        file_bytes: bytes,
        filename: str,
        content_type: str,
        auto_create: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Upload document to knowledge base
        
        Args:
            kb_name: Knowledge base name
            file_bytes: File content
            filename: File name
            content_type: MIME type
            auto_create: Auto-create collection if not exists
            metadata: Additional metadata
            
        Returns:
            Dict with upload result
        """
        collection_name = self._get_collection_name(kb_name)
        
        # Auto-create collection if needed
        if not self.collection_exists(collection_name):
            if auto_create:
                print(f"📁 Collection '{kb_name}' not found, creating...")
                result = self.create_collection(kb_name, description=f"Auto-created for {filename}")
                if not result["success"]:
                    return result
            else:
                return {
                    "success": False,
                    "message": f"Knowledge base '{kb_name}' does not exist. Please create it first using create_collection, or set auto_create=true to create automatically.",
                    "suggestion": f"Try: create_collection(kb_name='{kb_name}') or upload_document_to_kb(..., auto_create=true)"
                }
        
        # Extract text
        print(f"📄 Extracting text from {filename}...")
        page_data_list = self._extract_text_from_file(file_bytes, content_type)
        
        if not page_data_list:
            return {
                "success": False,
                "message": "Failed to extract text from file"
            }
        
        # Create documents
        print(f"📝 Creating documents from {len(page_data_list)} pages...")
        documents: List[Document] = []
        
        for page_data in page_data_list:
            doc_metadata = {
                "kb_name": kb_name,
                "filename": filename,
                "page_number": page_data['page_number'],
                "uploaded_at": datetime.now().isoformat(),
                **(metadata or {})
            }
            
            doc = Document(
                page_content=page_data['text'],
                metadata=doc_metadata
            )
            documents.append(doc)
        
        # Split documents
        print(f"✂️ Splitting documents into chunks...")
        split_docs = self.text_splitter.split_documents(documents)
        print(f"   Created {len(split_docs)} chunks")
        
        # Store in Qdrant
        try:
            vector_store = Qdrant(
                client=self.qdrant_client,
                collection_name=collection_name,
                embeddings=self.embed_model
            )
            vector_store.add_documents(split_docs)
            
            print(f"✅ Successfully uploaded {filename} to {kb_name}")
            return {
                "success": True,
                "kb_name": kb_name,
                "filename": filename,
                "chunks": len(split_docs),
                "pages": len(page_data_list)
            }
        except Exception as e:
            print(f"❌ Failed to upload document: {e}")
            return {
                "success": False,
                "message": str(e)
            }
    
    def _get_or_create_memory(self, collection_name: str, session_id: str) -> ConversationBufferMemory:
        """Get or create conversation memory for a session"""
        if collection_name not in self.chat_histories:
            self.chat_histories[collection_name] = {}
        
        if session_id not in self.chat_histories[collection_name]:
            self.chat_histories[collection_name][session_id] = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True,
                output_key="answer"
            )
        
        return self.chat_histories[collection_name][session_id]
    
    def chat_with_collection(
        self,
        kb_name: str,
        query: str,
        session_id: str,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Chat with a single knowledge base
        
        Args:
            kb_name: Knowledge base name
            query: User query
            session_id: Session ID for conversation history
            top_k: Number of documents to retrieve
            
        Returns:
            Dict with answer and sources
        """
        collection_name = self._get_collection_name(kb_name)
        
        if not self.collection_exists(collection_name):
            return {
                "success": False,
                "message": f"Knowledge base '{kb_name}' does not exist. Please upload documents first.",
                "suggestion": f"Try: upload_document_to_kb(kb_name='{kb_name}', ...) to create KB and add documents, then use chat_with_kb.",
                "available_kbs": [info["kb_name"] for info in self.list_collections()["collections"]]
            }
        
        try:
            # Get vector store
            vector_store = Qdrant(
                client=self.qdrant_client,
                collection_name=collection_name,
                embeddings=self.embed_model
            )
            
            # Get or create memory
            memory = self._get_or_create_memory(collection_name, session_id)
            
            # Create conversational chain
            qa_chain = ConversationalRetrievalChain.from_llm(
                llm=self.llm,
                retriever=vector_store.as_retriever(search_kwargs={"k": top_k}),
                memory=memory,
                return_source_documents=True,
                verbose=False
            )
            
            # Query
            result = qa_chain({"question": query})
            
            # Format sources
            sources = []
            for doc in result.get("source_documents", []):
                sources.append({
                    "content": doc.page_content[:200] + "...",
                    "metadata": doc.metadata
                })
            
            return {
                "success": True,
                "kb_name": kb_name,
                "session_id": session_id,
                "answer": result["answer"],
                "sources": sources
            }
        except Exception as e:
            print(f"❌ Chat failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": str(e)
            }
    
    def clear_chat_history(self, kb_name: str, session_id: str) -> Dict[str, Any]:
        """Clear chat history for a session"""
        collection_name = self._get_collection_name(kb_name)
        
        if collection_name in self.chat_histories:
            if session_id in self.chat_histories[collection_name]:
                del self.chat_histories[collection_name][session_id]
                return {
                    "success": True,
                    "message": f"Chat history cleared for session {session_id}"
                }
        
        return {
            "success": False,
            "message": "Session not found"
        }


# Global instance
_multi_kb_rag = None

def get_multi_kb_rag() -> MultiKnowledgeBaseRAG:
    """Get global Multi-KB RAG instance (singleton)"""
    global _multi_kb_rag
    if _multi_kb_rag is None:
        _multi_kb_rag = MultiKnowledgeBaseRAG()
    return _multi_kb_rag
