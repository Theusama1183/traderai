import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    DATA_SOURCE: str = os.getenv("DATA_SOURCE", "BINANCE").upper()
    DEFAULT_SYMBOL: str = os.getenv("DEFAULT_SYMBOL", "BTCUSDT")
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "*")

    # Groq model tuned for trading commentary/reasoning
    GROQ_MODEL: str = "llama-3.1-70b-versatile"

settings = Settings()
