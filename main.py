import sys
import os

# Add crwlr directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'crwlr'))

# Import the FastAPI app from crwlr/app/api.py
from app.api import app

# This allows uvicorn to find the app at main:app
__all__ = ['app']
