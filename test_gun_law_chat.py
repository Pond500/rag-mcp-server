#!/usr/bin/env python3
"""Test Hybrid Search with real gun law data"""
import requests
import json

def chat(query):
    r = requests.post(
        "http://localhost:8000/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "chat_with_kb",
                "arguments": {
                    "kb_name": "gun_law_hybrid",
                    "query": query,
                    "session_id": "test_gun_law"
                }
            }
        }
    )
    result = r.json()
    data = json.loads(result['result']['content'][0]['text'])
    
    print(f"\n{'='*80}")
    print(f"🔍 Query: {query}")
    print(f"{'='*80}")
    
    # Debug: print raw data if error
    if not data.get('success'):
        print(f"\n❌ Error: {data.get('message')}")
        return
    
    print(f"\n✅ Answer:\n{data['answer']}")
    print(f"\n📚 Sources ({len(data['sources'])} documents):")
    for i, src in enumerate(data['sources'][:3], 1):  # Show top 3
        print(f"\n  [{i}] Score: {src['rerank_score']:.4f}")
        print(f"      File: {src['metadata']['filename']}")
        print(f"      Preview: {src['content'][:100]}...")
    print(f"\n🔬 Search Method: {data['search_method']}")
    print(f"{'='*80}\n")

# Test queries
chat("ขั้นตอนการขอใบอนุญาตปืนมีอะไรบ้าง?")
chat("อายุขั้นต่ำในการขอใบอนุญาตปืนคือเท่าไหร่?")
chat("เอกสารที่ต้องใช้ในการขอใบอนุญาตปืนมีอะไรบ้าง?")
