#!/bin/bash
# Start Multi-KB MCP Server with ngrok
# Usage: ./start_multi_kb.sh

set -e

cd "$(dirname "$0")"

echo "🧹 Cleaning up old processes..."
# Kill ALL uvicorn processes (including old mcp_server.py)
pkill -9 -f "uvicorn" 2>/dev/null || true
# Kill ngrok
pkill -9 ngrok 2>/dev/null || true

# Also kill by port 8000 (backup method)
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

echo "⏳ Waiting for cleanup..."
sleep 2

echo "🚀 Starting Multi-KB MCP Server on port 8000..."
source venv_clean/bin/activate
nohup python -B -m uvicorn mcp_server_multi_kb:app --host 0.0.0.0 --port 8000 > mcp_server_multi_kb.log 2>&1 &
SERVER_PID=$!
echo "   Server PID: $SERVER_PID"

echo "⏳ Waiting for server to start..."
sleep 5

echo "🌐 Starting ngrok tunnel..."
nohup ngrok http 8000 > /dev/null 2>&1 &
NGROK_PID=$!
echo "   ngrok PID: $NGROK_PID"

echo "⏳ Waiting for ngrok..."
sleep 5

echo ""
echo "✅ Multi-KB MCP Server is running!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Get ngrok public URL
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['tunnels'][0]['public_url']) if data.get('tunnels') else print('Error')")

if [ "$NGROK_URL" = "Error" ]; then
    echo "❌ Failed to get ngrok URL"
    echo "   Run: curl -s http://localhost:4040/api/tunnels | python3 -m json.tool"
else
    echo "📍 Dify MCP URL: ${NGROK_URL}/mcp"
    echo ""
    echo "   Use this URL in Dify Cloud MCP Tool settings"
    echo "   Server Name: multi-kb-rag-server"
    echo "   Server Version: 2.0.0"
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Features:"
echo "   ✅ 7 MCP Tools (create, upload, chat, list, info, clear, delete)"
echo "   ✅ Dynamic collection creation (auto-create)"
echo "   ✅ Multi-knowledge base support"
echo "   ✅ Conversation history per collection/session"
echo ""
echo "📊 To view logs:"
echo "   tail -f mcp_server_multi_kb.log"
echo ""
echo "🛑 To stop:"
echo "   pkill -9 -f 'uvicorn mcp_server_multi_kb:app'; pkill -9 ngrok"
echo ""
