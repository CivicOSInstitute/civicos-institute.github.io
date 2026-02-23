#!/bin/bash
# Token Dashboard Setup Script

set -e

echo "🦞 Token Dashboard Setup"
echo "========================"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose not found. Please install docker-compose first."
    exit 1
fi

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "📁 Dashboard directory: $SCRIPT_DIR"
echo ""

# Build and start
echo "🔨 Building Docker image..."
docker-compose build

echo ""
echo "🚀 Starting dashboard..."
docker-compose up -d

echo ""
echo "✅ Dashboard started!"
echo ""
echo "📊 Access the dashboard at:"
echo "   Local: http://localhost:8080"
echo ""

# Check if Tailscale is installed
if command -v tailscale &> /dev/null; then
    echo "🔒 Tailscale detected! To expose via Tailscale:"
    echo "   tailscale serve --bg --set-path=/ localhost:8080"
    echo ""
    echo "   Or use the Tailscale sidecar:"
    echo "   docker-compose -f docker-compose.yml -f docker-compose.tailscale.yml up -d"
    echo ""
fi

echo "📋 Useful commands:"
echo "   View logs:  docker-compose logs -f"
echo "   Stop:       docker-compose down"
echo "   Restart:    docker-compose restart"
echo ""
