#!/bin/bash
# Quick setup script for E-ink Web UI

echo "🚀 Setting up E-ink Web UI..."

# Check if we're in the right directory
if [ ! -f "web_app.py" ]; then
    echo "❌ Error: Run this script from the project directory"
    exit 1
fi

# Install Python requirements
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Check if SDK is available
if [ -d "/opt/distiller-cm5-sdk" ]; then
    echo "✅ Distiller CM5 SDK found - hardware features will be available"
else
    echo "⚠️  SDK not found - hardware features will be disabled"
fi

# Make scripts executable
chmod +x run_web.py
chmod +x setup.sh

echo ""
echo "✅ Setup complete!"
echo ""
echo "🌐 To start the web UI:"
echo "   python run_web.py"
echo ""
echo "🌐 Then visit: http://localhost:5000"
echo "🌐 Or from network: http://$(hostname -I | awk '{print $1}'):5000"