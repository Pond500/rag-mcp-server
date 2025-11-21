#!/usr/bin/env python3
"""Replace print statements with logger in multi_kb_rag.py"""

import re

file_path = "/Users/pond500/RAG/mcp_rag-main/app/multi_kb_rag.py"

# Read file
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Define specific replacements
replacements = [
    # ✅ Success messages -> logger.info
    (r'print\(f"✅ Created collection: \{collection_name\}"\)', r'logger.info(f"✅ Created collection: {collection_name}")'),
    (r'print\(f"✅ Deleted collection: \{collection_name\}"\)', r'logger.info(f"✅ Deleted collection: {collection_name}")'),
    (r'print\(f"✅ Collection created: \{collection_name\}"\)', r'logger.info(f"✅ Collection created: {collection_name}")'),
    (r'print\(f"✅ AI Metadata extracted: \{extracted_data\}"\)', r'logger.debug(f"AI Metadata extracted: {extracted_data}")'),
    (r'print\(f"✅ Successfully uploaded', r'logger.info(f"✅ Successfully uploaded'),
    
    # ❌ Errors -> logger.error
    (r'print\(f"❌ Failed to create collection: \{e\}"\)', r'logger.error(f"Failed to create collection: {e}", exc_info=True)'),
    (r'print\(f"❌ Failed to list collections: \{e\}"\)', r'logger.error(f"Failed to list collections: {e}", exc_info=True)'),
    (r'print\(f"❌ Failed to get collection info: \{e\}"\)', r'logger.error(f"Failed to get collection info: {e}", exc_info=True)'),
    (r'print\(f"❌ Failed to delete collection: \{e\}"\)', r'logger.error(f"Failed to delete collection: {e}", exc_info=True)'),
    (r'print\(f"❌ Failed to read TXT: \{e\}"\)', r'logger.error(f"Failed to read TXT: {e}", exc_info=True)'),
    (r'print\(f"❌ Failed to read DOCX: \{e\}"\)', r'logger.error(f"Failed to read DOCX: {e}", exc_info=True)'),
    (r'print\(f"❌ Unsupported file type: \{content_type\}"\)', r'logger.warning(f"Unsupported file type: {content_type}")'),
    (r'print\(f"❌ Failed to upload document: \{e\}"\)', r'logger.error(f"Failed to upload document: {e}", exc_info=True)'),
    (r'print\(f"❌ Chat failed: \{e\}"\)', r'logger.error(f"Chat failed: {e}", exc_info=True)'),
    (r'print\(f"❌ Routing failed: \{e\}"\)', r'logger.error(f"Routing failed: {e}", exc_info=True)'),
    
    # ⚠️ Warnings -> logger.warning
    (r'print\(f"⚠️ Metadata extraction failed: \{e\}"\)', r'logger.warning(f"Metadata extraction failed: {e}")'),
    (r'print\("⚠️ No text found in first page, skipping AI metadata extraction"\)', r'logger.warning("No text found in first page, skipping AI metadata extraction")'),
    (r'print\("⚠️ Router index does not exist"\)', r'logger.warning("Router index does not exist")'),
    (r'print\("⚠️ Router index is empty', r'logger.warning("Router index is empty'),
    (r'print\("⚠️ No results from router index"\)', r'logger.warning("No results from router index")'),
    (r'print\(f"⚠️ Score', r'logger.warning(f"Score'),
    
    # 🤖 AI operations -> logger.info
    (r'print\("🤖 AI Extracting metadata from document..."\)', r'logger.info("🤖 AI Extracting metadata from document...")'),
    
    # 📄 📝 Main steps -> logger.info
    (r'print\(f"📄 Extracting text from \{filename\}..."\)', r'logger.info(f"📄 Extracting text from {filename}...")'),
    (r'print\(f"📝 Generated description: \{smart_description\}"\)', r'logger.info(f"📝 Generated description: {smart_description}")'),
    (r'print\(f"📝 Creating documents from \{len\(page_data_list\)\} pages..."\)', r'logger.info(f"📝 Creating documents from {len(page_data_list)} pages...")'),
    
    # ✂️ Processing steps -> logger.info
    (r'print\(f"✂️ Splitting documents into chunks..."\)', r'logger.info(f"✂️ Splitting documents into chunks...")'),
    
    # Detailed info with "   " -> logger.debug
    (r'print\(f"   Description: \{smart_description\}"\)', r'logger.debug(f"Description: {smart_description}")'),
    (r'print\(f"   Created \{len\(split_docs\)\} chunks"\)', r'logger.debug(f"Created {len(split_docs)} chunks")'),
    (r'print\(f"   KB Name: \{kb_name\}"\)', r'logger.debug(f"KB Name: {kb_name}")'),
    (r'print\(f"   Collection: \{collection_name\}"\)', r'logger.debug(f"Collection: {collection_name}")'),
    (r'print\(f"   Description: \{description\}"\)', r'logger.debug(f"Description: {description}")'),
    (r'print\(f"   AI Metadata: \{ai_metadata\}"\)', r'logger.debug(f"AI Metadata: {ai_metadata}")'),
    
    # 🎯 🌐 Routing -> logger.info
    (r'print\(f"🎯 Router found:', r'logger.info(f"🎯 Router found:'),
    (r'print\(f"🌐 Auto-routing query:', r'logger.info(f"🌐 Auto-routing query:'),
    (r'print\(f"✅ Routed to:', r'logger.info(f"✅ Routed to:'),
    (r'print\(f"✅ Auto-route successful:', r'logger.info(f"✅ Auto-route successful:'),
    
    # Traceback prints
    (r'traceback\.print_exc\(\)', r'pass  # traceback handled by logger'),
    (r'import traceback\nprint_exc', r'# traceback handled by logger'),
]

# Apply replacements
for pattern, replacement in replacements:
    content = re.sub(pattern, replacement, content)

# Write back
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"✅ Replaced print statements with logger in {file_path}")
