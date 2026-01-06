# ElectroMart AI: Multi-Agent Voice System

An intelligent multi-agent orchestrator built for the ElectroMart consumer electronics store. [cite_start]This system uses **LangGraph** to route customer inquiries between specialized agents (Sales, Marketing, Technical Support, and Logistics) with context retention and agent handoffs[cite: 1, 2].

## 🚀 Features
* [cite_start]**Intelligent Routing**: Orchestrator agent with >85% intent classification accuracy[cite: 2].
* [cite_start]**Multi-Agent Architecture**: Specialized agents for Sales, Marketing, Tech Support, and Order Logistics[cite: 4, 5].
* [cite_start]**Database Operations**: Supports reading order status and writing return requests/notes[cite: 4, 5].
* [cite_start]**Multimodal**: Supports both text-based chat and Realtime WebRTC/TTS capabilities[cite: 5].

## 🛠️ Tech Stack
* [cite_start]**Backend**: FastAPI, LangGraph, LangChain, OpenAI GPT-4o-mini[cite: 4, 5].
* [cite_start]**Frontend**: React (Vite), CSS3[cite: 1, 3].
* [cite_start]**Observability**: LangSmith/Langfuse for agent tracing.

## 📦 Setup Instructions

### Backend
1. Navigate to the backend directory: `cd backend`
2. Create a virtual environment: `python -m venv venv`
3. Activate venv:
   - Windows: `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. [cite_start]Create a `.env` file based on `.env.example` and add your `OPENAI_API_KEY`.
6. Run the server: `uvicorn app:app --reload`

### Frontend
1. Navigate to the frontend directory: `cd frontend`
2. Install packages: `npm install`
3. Start the development server: `npm run dev`

## 🏗️ Architecture
[cite_start]Details on design decisions, agent handoffs, and state management can be found in the [ARCHITECTURE.md](./ARCHITECTURE.md) file.
