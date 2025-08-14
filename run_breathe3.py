import os
import sys
import subprocess

# Ensure pip is up-to-date
subprocess.call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])

# Install requirements from requirements.txt
req_file = os.path.join(os.path.dirname(__file__), "requirements.txt")
subprocess.call([sys.executable, "-m", "pip", "install", "-r", req_file])

# Launch breathe3.py
script_path = os.path.join(os.path.dirname(__file__), "breathe3.py")
subprocess.call([sys.executable, script_path])
