# # from typing import TypedDict
# # from langgraph.graph import StateGraph, END
# # from langchain_openai import ChatOpenAI

# # class ChatState(TypedDict):
# #     user_message: str
# #     intent: str
# #     response: str

# # llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# # def router_agent(state: ChatState):
# #     prompt = f"""
# #     Classify the user query into one intent:
# #     sales
# #     marketing
# #     technical_support
# #     order_logistics

# #     User message: {state['user_message']}

# #     Return only the intent.
# #     """
# #     state["intent"] = llm.invoke(prompt).content.strip()
# #     return state

# # def sales_agent(state: ChatState):
# #     state["response"] = f"Sales agent handled: {state['user_message']}"
# #     return state

# # def marketing_agent(state: ChatState):
# #     state["response"] = f"Marketing agent handled: {state['user_message']}"
# #     return state

# # def tech_agent(state: ChatState):
# #     state["response"] = f"Technical support handled: {state['user_message']}"
# #     return state

# # def order_agent(state: ChatState):
# #     state["response"] = f"Order & logistics handled: {state['user_message']}"
# #     return state

# # def route(state: ChatState):
# #     if state["intent"] == "sales":
# #         return "sales"
# #     if state["intent"] == "marketing":
# #         return "marketing"
# #     if state["intent"] == "technical_support":
# #         return "tech"
# #     if state["intent"] == "order_logistics":
# #         return "order"
# #     return END

# # graph = StateGraph(ChatState)

# # graph.add_node("router", router_agent)
# # graph.add_node("sales", sales_agent)
# # graph.add_node("marketing", marketing_agent)
# # graph.add_node("tech", tech_agent)
# # graph.add_node("order", order_agent)

# # graph.add_conditional_edges(
# #     "router",
# #     route,
# #     {
# #         "sales": "sales",
# #         "marketing": "marketing",
# #         "tech": "tech",
# #         "order": "order",
# #         END: END
# #     }
# # )

# # graph.set_entry_point("router")

# # graph.add_edge("sales", END)
# # graph.add_edge("marketing", END)
# # graph.add_edge("tech", END)
# # graph.add_edge("order", END)

# # app = graph.compile()

# # if __name__ == "__main__":
# #     while True:
# #         msg = input("You: ")
# #         if msg.lower() in ["exit", "quit"]:
# #             break
# #         result = app.invoke({"user_message": msg})
# #         print("AI:", result["response"])

# # from http.client import HTTPException
# import os
# import re
# from typing import TypedDict, Literal, Optional

# from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
# import httpx
# from pydantic import BaseModel
# from langgraph.graph import StateGraph, END
# from langchain_openai import ChatOpenAI
# from fastapi.middleware.cors import CORSMiddleware


# # -----------------------------
# # LangGraph multi-agent (text)
# # -----------------------------
# class ChatState(TypedDict):
#     user_message: str
#     intent: str
#     response: str


# Intent = Literal["sales", "marketing", "technical_support", "order_logistics"]


# class IntentOut(BaseModel):
#     intent: Intent


# llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
# router_llm = llm.with_structured_output(IntentOut)

# # Minimal mock data (expand as per your PDF requirement)
# MOCK_PRODUCTS = [
#     {"sku": "LAP-001", "name": "ElectroMart Laptop 14", "price": 549, "stock": 12},
#     {"sku": "LAP-002", "name": "ElectroMart Laptop 16 Pro", "price": 1099, "stock": 4},
#     {"sku": "PHN-101", "name": "ElectroMart Phone X", "price": 699, "stock": 18},
# ]

# MOCK_PROMOS = [
#     {"title": "New Year Sale", "details": "Up to 15% off laptops this week."},
#     {"title": "Free Shipping", "details": "Free shipping on orders above $50."},
# ]

# MOCK_ORDERS = {
#     "1001": {"status": "Shipped", "eta": "2026-01-03", "carrier": "UPS"},
#     "1002": {"status": "Processing", "eta": "2026-01-05", "carrier": "DHL"},
# }


# def router_agent(state: ChatState):
#     # Structured output ensures we ALWAYS get one of the allowed labels.
#     prompt = (
#         "Classify the user query into exactly one intent:\n"
#         "- sales\n"
#         "- marketing\n"
#         "- technical_support\n"
#         "- order_logistics\n\n"
#         f"User message: {state['user_message']}\n"
#     )
#     out: IntentOut = router_llm.invoke(prompt)
#     state["intent"] = out.intent
#     return state


# def sales_agent(state: ChatState):
#     prompt = (
#         "You are the Sales Agent for an electronics store.\n"
#         "Use the product list below. If user asks price/availability, answer directly.\n"
#         "If user is vague, ask 1 short clarifying question.\n\n"
#         f"Products: {MOCK_PRODUCTS}\n\n"
#         f"User: {state['user_message']}\n"
#         "Answer:"
#     )
#     state["response"] = llm.invoke(prompt).content.strip()
#     return state


# def marketing_agent(state: ChatState):
#     prompt = (
#         "You are the Marketing/Promotions Agent.\n"
#         "Promote relevant deals and be concise. Don't invent promotions.\n\n"
#         f"Promotions: {MOCK_PROMOS}\n\n"
#         f"User: {state['user_message']}\n"
#         "Answer:"
#     )
#     state["response"] = llm.invoke(prompt).content.strip()
#     return state


# def tech_agent(state: ChatState):
#     prompt = (
#         "You are the Technical Support Agent.\n"
#         "Give step-by-step troubleshooting. Ask for device/model if missing.\n"
#         "Keep it short and practical.\n\n"
#         f"User: {state['user_message']}\n"
#         "Answer:"
#     )
#     state["response"] = llm.invoke(prompt).content.strip()
#     return state


# def _extract_order_id(text: str) -> Optional[str]:
#     # accepts "order 1001", "#1001", "1001"
#     m = re.search(r"(?:order\s*#?\s*)?(\d{4,})", text.lower())
#     return m.group(1) if m else None


# def order_agent(state: ChatState):
#     order_id = _extract_order_id(state["user_message"])
#     if not order_id:
#         state["response"] = "Sure—what is your order number?"
#         return state

#     order = MOCK_ORDERS.get(order_id)
#     if not order:
#         state["response"] = f"I can’t find order {order_id} in the demo data. Please confirm the order number."
#         return state

#     state["response"] = (
#         f"Order {order_id} is {order['status']}. "
#         f"ETA: {order['eta']}. Carrier: {order['carrier']}."
#     )
#     return state


# def route(state: ChatState):
#     intent = (state.get("intent") or "").strip().lower()
#     if intent == "sales":
#         return "sales"
#     if intent == "marketing":
#         return "marketing"
#     if intent == "technical_support":
#         return "tech"
#     if intent == "order_logistics":
#         return "order"
#     return END


# graph = StateGraph(ChatState)
# graph.add_node("router", router_agent)
# graph.add_node("sales", sales_agent)
# graph.add_node("marketing", marketing_agent)
# graph.add_node("tech", tech_agent)
# graph.add_node("order", order_agent)

# graph.add_conditional_edges(
#     "router",
#     route,
#     {"sales": "sales", "marketing": "marketing", "tech": "tech", "order": "order", END: END},
# )

# graph.set_entry_point("router")
# graph.add_edge("sales", END)
# graph.add_edge("marketing", END)
# graph.add_edge("tech", END)
# graph.add_edge("order", END)

# app_graph = graph.compile()


# # -----------------------------
# # FastAPI
# # -----------------------------
# app = FastAPI()

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# class ChatRequest(BaseModel):
#     message: str


# class ChatResponse(BaseModel):
#     intent: str
#     response: str


# @app.post("/chat", response_model=ChatResponse)
# def chat(req: ChatRequest):
#     result = app_graph.invoke({"user_message": req.message})
#     return {"intent": result.get("intent", ""), "response": result["response"]}


# # -----------------------------
# # Realtime session (unchanged)
# # -----------------------------
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
# OPENAI_REALTIME_MODEL = os.getenv("OPENAI_REALTIME_MODEL", "gpt-realtime-mini")


# class RealtimeSessionRequest(BaseModel):
#     character_id: str | None = None
#     character_name: str | None = None
#     character_description: str | None = None
#     gender_type: str | None = None
#     character_accent: str | None = None
#     instructions: str | None = None


# @app.post("/realtime/session")
# async def create_realtime_session(req: RealtimeSessionRequest):
#     if not OPENAI_API_KEY:
#         raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not set on the backend")

#     voice_type = "sage" if (req.gender_type or "").lower() == "female" else "ash"

#     instructions = req.instructions or (
#         "You are ElectroMart AI.\n"
#         "You can transcribe and speak.\n"
#         "Note: routing/agent logic is handled by backend /chat.\n"
#     )

#     url = "https://api.openai.com/v1/realtime/sessions"
#     headers = {
#         "Authorization": f"Bearer {OPENAI_API_KEY}",
#         "Content-Type": "application/json",
#         "OpenAI-Beta": "realtime=v1",
#     }
#     payload = {
#         "model": OPENAI_REALTIME_MODEL,
#         "voice": voice_type,
#         "modalities": ["text", "audio"],
#         "input_audio_format": "pcm16",
#         "output_audio_format": "pcm16",
#         "input_audio_transcription": {"model": "whisper-1"},
#         "instructions": instructions,
#     }

#     async with httpx.AsyncClient(timeout=30) as client:
#         r = await client.post(url, headers=headers, json=payload)

#     if r.status_code >= 400:
#         raise HTTPException(status_code=r.status_code, detail=r.text)

#     return r.json()

import os
import re
import json
import random
from typing import TypedDict, Literal, Optional, Dict, Any, List

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI


# =============================
# Config
# =============================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_REALTIME_MODEL = os.getenv("OPENAI_REALTIME_MODEL", "gpt-realtime")
OPENAI_TTS_MODEL = os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")  # per docs: gpt-4o-mini-tts supported
OPENAI_TTS_VOICE = os.getenv("OPENAI_TTS_VOICE", "alloy")

if not OPENAI_API_KEY:
    # don't hard crash on import; raise on endpoints that need it
    pass


# =============================
# Mock Data (Assessment-friendly)
# =============================
def _make_products() -> List[Dict[str, Any]]:
    # 24 products
    categories = [
        ("Laptop", "LAP"),
        ("Phone", "PHN"),
        ("Tablet", "TAB"),
        ("Headphones", "HDP"),
        ("Monitor", "MON"),
        ("Keyboard", "KEY"),
        ("Mouse", "MSE"),
        ("Speaker", "SPK"),
    ]
    products = []
    sku_idx = 1
    rng = random.Random(42)
    for cat, prefix in categories:
        for size in range(1, 4):  # 3 each category = 24
            sku = f"{prefix}-{sku_idx:03d}"
            sku_idx += 1
            products.append(
                {
                    "sku": sku,
                    "name": f"ElectroMart {cat} {size}",
                    "category": cat.lower(),
                    "price": int(rng.uniform(29, 1499)),
                    "stock": int(rng.uniform(0, 25)),
                }
            )
    return products


MOCK_PRODUCTS = _make_products()

MOCK_PROMOS = [
    {"title": "New Year Sale", "details": "Up to 15% off laptops this week."},
    {"title": "Free Shipping", "details": "Free shipping on orders above $50."},
    {"title": "Bundle Bonus", "details": "Buy a laptop + mouse, get 10% off the mouse."},
    {"title": "Student Discount", "details": "Students get 5% off tablets (ID required)."},
    {"title": "Accessories Week", "details": "Save up to 20% on keyboards and headphones."},
]

MOCK_FAQ = [
    {"q": "What is your return policy?", "a": "Returns accepted within 14 days for unopened items; opened items may incur a restocking fee."},
    {"q": "Do you provide warranty?", "a": "Yes. Most electronics come with a 12-month manufacturer warranty."},
    {"q": "How long does shipping take?", "a": "Standard shipping is 2–5 business days depending on location."},
    {"q": "Do you ship internationally?", "a": "Not in this demo. We support domestic shipping only."},
    {"q": "How do I contact support?", "a": "Use the chat, or provide an order number for logistics queries."},
]

# Order DB with write support (in-memory demo)
ORDERS_DB: Dict[str, Dict[str, Any]] = {
    "1001": {"status": "Shipped", "eta": "2026-01-03", "carrier": "UPS", "return_requested": False, "notes": []},
    "1002": {"status": "Processing", "eta": "2026-01-05", "carrier": "DHL", "return_requested": False, "notes": []},
    "1003": {"status": "Delivered", "eta": "2025-12-29", "carrier": "FedEx", "return_requested": False, "notes": []},
}


# =============================
# LangGraph Multi-Agent
# =============================
class ChatState(TypedDict):
    user_message: str
    intent: str
    response: str


Intent = Literal["sales", "marketing", "technical_support", "order_logistics"]


class IntentOut(BaseModel):
    intent: Intent


llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
router_llm = llm.with_structured_output(IntentOut)


def router_agent(state: ChatState):
    prompt = (
        "Classify the user query into exactly one intent:\n"
        "- sales\n"
        "- marketing\n"
        "- technical_support\n"
        "- order_logistics\n\n"
        f"User message: {state['user_message']}\n"
        "Return ONLY the intent.\n"
    )
    out: IntentOut = router_llm.invoke(prompt)
    state["intent"] = out.intent
    return state


def sales_agent(state: ChatState):
    prompt = (
        "You are the Sales Agent for an electronics store.\n"
        "You have access to the product catalog below.\n"
        "- If user asks price/availability, answer directly using the catalog.\n"
        "- If user is vague, ask 1 short clarifying question.\n"
        "- Never invent SKUs or prices.\n\n"
        f"Catalog: {MOCK_PRODUCTS}\n\n"
        f"User: {state['user_message']}\n"
        "Answer:"
    )
    state["response"] = llm.invoke(prompt).content.strip()
    return state


def marketing_agent(state: ChatState):
    prompt = (
        "You are the Marketing/Promotions Agent.\n"
        "Use ONLY the promotions list below.\n"
        "- Recommend relevant promotions.\n"
        "- Be concise.\n"
        "- Do not invent promotions.\n\n"
        f"Promotions: {MOCK_PROMOS}\n\n"
        f"User: {state['user_message']}\n"
        "Answer:"
    )
    state["response"] = llm.invoke(prompt).content.strip()
    return state


def tech_agent(state: ChatState):
    prompt = (
        "You are the Technical Support Agent.\n"
        "- Give step-by-step troubleshooting.\n"
        "- Ask for device/model if missing.\n"
        "- Keep it short and practical.\n"
        "- You may reference FAQ if relevant.\n\n"
        f"FAQ: {MOCK_FAQ}\n\n"
        f"User: {state['user_message']}\n"
        "Answer:"
    )
    state["response"] = llm.invoke(prompt).content.strip()
    return state


def _extract_order_id(text: str) -> Optional[str]:
    # accepts "order 1001", "#1001", "1001"
    m = re.search(r"(?:order\s*#?\s*)?(\d{4,})", text.lower())
    return m.group(1) if m else None


def _wants_return(text: str) -> bool:
    t = text.lower()
    return any(k in t for k in ["return", "refund", "send back", "exchange", "rma"])


def _wants_add_note(text: str) -> Optional[str]:
    # "add note: ..." / "note: ..."
    m = re.search(r"(?:add\s+note:|note:)\s*(.+)$", text, re.IGNORECASE)
    return m.group(1).strip() if m else None


def order_agent(state: ChatState):
    msg = state["user_message"]
    order_id = _extract_order_id(msg)
    if not order_id:
        state["response"] = "Sure—please provide your order number (e.g., 1001)."
        return state

    order = ORDERS_DB.get(order_id)
    if not order:
        state["response"] = f"I can’t find order {order_id} in the demo database. Please confirm the order number."
        return state

    # WRITE op #1: create return request
    if _wants_return(msg):
        if order["return_requested"]:
            state["response"] = f"A return request is already on file for order {order_id}. If you want to add details, say: 'note: <your message>'."
            return state

        order["return_requested"] = True
        order["notes"].append({"type": "return_request", "text": "Return requested via chat", "ts": "2026-01-01"})
        state["response"] = (
            f"Return request created for order {order_id}. "
            f"Current status: {order['status']}. Carrier: {order['carrier']}. "
            "If you want, tell me the reason (e.g., 'note: wrong item received')."
        )
        return state

    # WRITE op #2: add note to order
    note = _wants_add_note(msg)
    if note:
        order["notes"].append({"type": "note", "text": note, "ts": "2026-01-01"})
        state["response"] = f"Added your note to order {order_id}. Current status: {order['status']}. ETA: {order['eta']}."
        return state

    # READ op: order status
    state["response"] = (
        f"Order {order_id} status: {order['status']}. "
        f"ETA: {order['eta']}. Carrier: {order['carrier']}. "
        f"Return requested: {'Yes' if order['return_requested'] else 'No'}."
    )
    return state


def route(state: ChatState):
    intent = (state.get("intent") or "").strip().lower()
    if intent == "sales":
        return "sales"
    if intent == "marketing":
        return "marketing"
    if intent == "technical_support":
        return "tech"
    if intent == "order_logistics":
        return "order"
    return END


graph = StateGraph(ChatState)
graph.add_node("router", router_agent)
graph.add_node("sales", sales_agent)
graph.add_node("marketing", marketing_agent)
graph.add_node("tech", tech_agent)
graph.add_node("order", order_agent)

graph.add_conditional_edges(
    "router",
    route,
    {"sales": "sales", "marketing": "marketing", "tech": "tech", "order": "order", END: END},
)

graph.set_entry_point("router")
graph.add_edge("sales", END)
graph.add_edge("marketing", END)
graph.add_edge("tech", END)
graph.add_edge("order", END)

app_graph = graph.compile()


# =============================
# FastAPI
# =============================
app = FastAPI(title="ElectroMart AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # lock down for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    intent: str
    response: str


class Product(BaseModel):
    sku: str
    name: str
    category: str
    price: int
    stock: int


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    result = app_graph.invoke({"user_message": req.message})
    return {"intent": result.get("intent", ""), "response": result["response"]}


@app.get("/products", response_model=List[Product])
def get_products():
    return MOCK_PRODUCTS


# =============================
# Realtime WebRTC (Unified Interface)
# Browser -> Backend (SDP)
# Backend -> OpenAI /v1/realtime/calls
# =============================
@app.post("/realtime/call")
async def realtime_call(request: Request):
    """
    Browser sends raw SDP (Content-Type: application/sdp)
    We wrap it in multipart/form-data with fields:
      - sdp: raw sdp text
      - session: JSON string
    Then POST to OpenAI /v1/realtime/calls and return the answer SDP.
    """
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not set")

    offer_bytes = await request.body()
    if not offer_bytes:
        raise HTTPException(status_code=400, detail="Missing SDP body")

    # IMPORTANT: OpenAI expects plain SDP text, not bytes
    offer_sdp = offer_bytes.decode("utf-8", errors="ignore")

    session_obj = {
    "type": "transcription",
    "audio": {
        "input": {
            "format": {"type": "audio/pcm", "rate": 24000},
            "transcription": {"model": "whisper-1"},
            "turn_detection": {"type": "server_vad"},
            # optional but helpful
            "noise_reduction": {"type": "near_field"},
        }
    },
}

    # IMPORTANT: send as multipart FORM FIELDS (no filename)
    # In httpx, use files with (None, value) to avoid filename.
    multipart = [
        ("sdp", (None, offer_sdp, "application/sdp")),
        ("session", (None, json.dumps(session_obj), "application/json")),
    ]

    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}

    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            "https://api.openai.com/v1/realtime/calls",
            headers=headers,
            files=multipart,
        )

    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.text)

    # Return answer SDP as plain text
    return Response(content=r.text, media_type="text/plain")

# =============================
# TTS endpoint (deterministic speech for routed answer)
# =============================
class TTSRequest(BaseModel):
    text: str
    voice: Optional[str] = None


@app.post("/tts")
async def tts(req: TTSRequest):
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not set")

    text = (req.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Missing text")

    voice = (req.voice or OPENAI_TTS_VOICE).strip()

    payload = {
        "model": OPENAI_TTS_MODEL,
        "input": text[:4096],
        "voice": voice,
    }

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            "https://api.openai.com/v1/audio/speech",
            headers=headers,
            json=payload,
        )

    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.text)

    # ✅ CORRECT: return FastAPI Response with raw bytes
    return Response(
        content=r.content,
        media_type="audio/mpeg",
    )


# =============================
# Run
# =============================
# uvicorn main:app --reload --port 8000
