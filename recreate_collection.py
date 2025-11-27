#!/usr/bin/env python3
import requests
import json

BASE_URL = "http://localhost:8000/mcp"

def mcp_call(tool_name, args):
    r = requests.post(BASE_URL, json={
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": args}
    })
    return r.json()

# 1. Delete old collection
print("=== Deleting old collection ===")
result = mcp_call("delete_collection", {"kb_name": "gun_law_hybrid"})
print(json.dumps(result, indent=2, ensure_ascii=False))

# 2. Create new with Hybrid Search
print("\n=== Creating new Hybrid Search collection ===")
result = mcp_call("create_collection", {
    "kb_name": "gun_law_hybrid",
    "description": "Gun law knowledge base with Hybrid Search (Dense + Sparse BM25 + Reranking)"
})
print(json.dumps(result, indent=2, ensure_ascii=False))

print("\n✅ Ready to upload documents with manual_upload.py")
