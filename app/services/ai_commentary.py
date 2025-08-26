from typing import Literal
from groq import Groq
from app.config import settings

client = Groq(api_key=settings.GROQ_API_KEY)

PROMPT = """You are a trading analyst AI.
Summarize the provided indicator snapshot into a concise, risk-aware recommendation.
ALWAYS include: short context, key indicators, risk level, and numbered action plan.
Never promise profits. Keep it compliant and cautious.

Snapshot:
{snapshot}

Tone: {tone}
Output format (markdown, 5 bullets max + one-line verdict)."""

def generate_commentary(snapshot: dict, style: Literal["concise","detailed"]="concise") -> str:
    tone = "concise, factual" if style == "concise" else "detailed but crisp"
    content = PROMPT.format(snapshot=snapshot, tone=tone)

    # Chat Completions-style call (Groq python SDK)
    resp = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[
            {"role":"system","content":"You are a cautious, precise trading assistant."},
            {"role":"user","content": content}
        ],
        temperature=0.2,
        max_tokens=400
    )
    return resp.choices[0].message.content.strip()
