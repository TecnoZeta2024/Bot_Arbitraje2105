"""
Production Server Launcher - Bot_Arbitraje2105
Handles module imports and environment setup correctly
"""

import os
import sys
from pathlib import Path

# Add parent directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Now import the clean production server
from src.production_server import start_production_server

if __name__ == "__main__":
    # Change to the src directory
    os.chdir(Path(__file__).parent)
    
    # Start the server
    start_production_server()
