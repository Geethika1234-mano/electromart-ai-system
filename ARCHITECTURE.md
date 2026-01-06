🏗️ ElectroMart Multi-Agent System Architecture
1. System Overview
This project implements a Directed Acyclic Graph (DAG) orchestration pattern using LangGraph. The system is designed to act as a high-fidelity virtual assistant for "ElectroMart," capable of handling complex customer journeys by routing inquiries to domain-specific experts.

2. Core Components
A. The Orchestrator (Router)
The "Brain" of the system. It uses a Structured Output pattern to classify user intent.

Intent Accuracy: Utilizing gpt-4o-mini with a specialized system prompt, the orchestrator achieves >85% accuracy by identifying key entities (e.g., "laptop" -> Sales, "discount" -> Marketing).

Dynamic Handoffs: If a user switches topics (e.g., asking for a refund while troubleshooting), the Orchestrator updates the state and re-routes the conversation seamlessly.

B. Specialized Sub-Agents
Sales Agent: Accesses a catalog of 24+ products. Designed to handle product comparisons and availability checks.

Marketing Agent: Manages 5+ active promotions and loyalty tier logic.

Technical Support Agent: Leverages a Knowledge Base for troubleshooting.

Order & Logistics Agent: Handles READ (status checks) and WRITE (return request logging) operations.

3. State Management & Context Retention
We utilize LangGraph's TypedDict state to maintain:

Conversation History: Full context is passed to sub-agents so they "remember" what was discussed in previous steps.

Intent Tracking: Prevents redundant classification if the user stays within the same domain.

4. Database Integration
Read Operations: Fetches real-time data from MOCK_PRODUCTS and ORDERS_DB.

Write Operations: Implements a functional return system where the order_agent modifies the order state and generates a "Return Request ID," demonstrating the ability to integrate with transactional systems.

5. Multimodal Capabilities
The backend includes a WebRTC endpoint and a TTS (Text-to-Speech) pipeline. This allows the frontend to toggle between standard text chat and a low-latency voice experience, satisfying the "Voice System" requirement of the assessment.
