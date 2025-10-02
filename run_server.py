#!/usr/bin/env python3
"""
Startup script for the Amadeus Hotels MCP server.
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from main import main

if __name__ == "__main__":
    main()
