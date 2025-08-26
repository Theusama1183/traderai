from fastapi import Depends, HTTPException
from app.config import settings

def require_groq_api_key():
    if not settings.GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not configured")
    return True
