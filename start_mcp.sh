#!/bin/bash
# Start MCP Server with ngrok tunnel
# Usage: ./start_mcp.sh

set -e

cd "$(dirname "$0")"

echo "🧹 Cleaning up old processes..."
pkill -9 -f "uvicorn mcp_server:app" 2>/dev/null || true
pkill -9 ngrok 2>/dev/null || true

echo "⏳ Waiting for cleanup..."
sleep 2

echo "🚀 Starting MCP Server on port 8000..."
source venv_clean/bin/activate
nohup python -B -m uvicorn mcp_server:app --host 0.0.0.0 --port 8000 > mcp_server.log 2>&1 &
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
echo "✅ MCP Server is running!"
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
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 To view logs:"
echo "   tail -f mcp_server.log"
echo ""
echo "🛑 To stop:"
echo "   pkill -9 -f 'uvicorn mcp_server:app'; pkill -9 ngrok"
echo ""



####สรุป

#cd /Users/pond500/RAG/mcp_rag-main
#chmod +x start_mcp.sh
#./start_mcp.sh