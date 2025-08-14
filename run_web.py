#!/usr/bin/env python3
"""
Launch script for the E-ink Web UI
Handles environment setup and starts the Flask server
"""

import sys
import os
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Add SDK path if available
sdk_path = '/opt/distiller-cm5-sdk'
if os.path.exists(sdk_path):
    sys.path.insert(0, sdk_path)
    print("✓ SDK path added")
else:
    print("⚠ SDK not found - hardware features will be disabled")

# Check for required dependencies
try:
    import flask
    print("✓ Flask available")
except ImportError:
    print("❌ Flask not found. Install with: pip install flask")
    sys.exit(1)

try:
    from eink_composer import EinkComposer
    print("✓ E-ink composer available")
except ImportError:
    print("❌ E-ink composer not found. Make sure you're in the correct directory.")
    sys.exit(1)

# Create required directories
os.makedirs(current_dir / 'templates', exist_ok=True)
os.makedirs(current_dir / 'static', exist_ok=True)

print("\n" + "="*50)
print("🖥️  E-ink Web UI Starting...")
print("="*50)
print(f"📁 Working directory: {current_dir}")
print(f"🌐 Access URL: http://localhost:5000")
print(f"🌐 Network access: http://0.0.0.0:5000")
print("="*50 + "\n")

# Import and run the web app
try:
    from web_app import app
    app.run(host='0.0.0.0', port=5000, debug=False)
except KeyboardInterrupt:
    print("\n👋 E-ink Web UI stopped")
except Exception as e:
    print(f"❌ Error starting web UI: {e}")
    sys.exit(1)