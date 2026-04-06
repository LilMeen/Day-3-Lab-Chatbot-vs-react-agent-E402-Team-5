# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyen Hoang Khai Minh
- **Student ID**: 2A202600159
- **Date**: 06/04/2026

---

## I. Technical Contribution (15 Points)

I was responsible for the full backend/server layer of the Lab 3 system. My scope included API design, module architecture, AI-service integration, session/history persistence, and runtime stability handling.

- **Modules Implemented**:
	- `server/src/module/chat/*`
	- `server/src/module/info/*`
	- Root integration in `server/src/app.module.ts`
	- Bootstrap + CORS setup in `server/src/main.ts`

- **Code Highlights**:
	- Implemented MVC-style module separation with Controller/Service/Repository pattern.
	- Built `POST /chat`, `GET /chat/chat-history`, `GET /chat/chat-sessions`.
	- Added model-routing support (`baseline` vs `agent`) from server to AI services.
	- Added outbound timeout + abort logic when server calls AI services (`AI_SERVICE_TIMEOUT_MS`).
	- Implemented file-based chat session storage in `server/chat_history/*.txt` with role-tagged lines.
	- Implemented `GET /info/movie-schedules` flow: `movieId` -> normalized movie URL -> ai-services schedule endpoint.
	- Added flattening compatibility logic for grouped schedule response to keep frontend payload simple and stable.

- **How backend interacts with ReAct flow**:
	- Backend acts as orchestration layer between frontend and Python ai-services.
	- Frontend sends user message + selected model to NestJS.
	- NestJS persists user message, forwards message to selected AI endpoint:
		- `.../api/v1/baseline` for direct LLM answer
		- `.../api/v1/agent` for ReAct tool-based reasoning
	- NestJS stores assistant reply, returns `sessionId` + reply to UI, and exposes session/history retrieval APIs.

---

## II. Debugging Case Study (10 Points)

During implementation, I faced multiple integration failures. The most critical one was model/endpoint mismatch and runtime instability that caused chat failures and indefinite loading behavior.

- **Problem Description**:
	- Server returned `502` because chat repository called wrong ai-services routes and wrong request payload shape.
	- User-side symptom: message stuck in loading, no immediate visible response.
	- New chat sometimes still displayed old session history.

- **Observed Runtime Signals**:
	- `AI service returned status 404` from NestJS when forwarding to ai-services.
	- `EADDRINUSE` on port `3000` and process conflicts on `8000` caused stale runtime behavior.
	- Baseline model sometimes showed quota errors from wrong provider instance.

- **Diagnosis**:
	- Mismatch between expected ai-services contract and NestJS outbound request.
	- Multiple stale processes produced non-deterministic behavior (request hitting old instance).
	- UI state depended too heavily on delayed history fetch, so first messages could appear to disappear.

- **Solution**:
	- Fixed server outbound URL and body mapping to ai-services contract.
	- Added timeout + abort controller for upstream AI calls to avoid infinite waiting.
	- Refactored frontend session/history synchronization (with optimistic user message behavior) to keep chat visible during pending state.
	- Standardized startup verification by checking active listeners before running dev servers.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

Based on backend integration/testing, I observed clear practical differences between baseline chatbot and ReAct agent behavior.

1.  **Reasoning**: How did the `Thought` block help the agent compared to a direct Chatbot answer?
		- ReAct agent gives more grounded answers when question requires external data/tool usage (schedule, location, movie-specific details).
		- Baseline can generate fluent replies but often stays generic when real-time data retrieval is needed.

2.  **Reliability**: In which cases did the Agent actually perform *worse* than the Chatbot?
		- Agent pipeline is more complex and sensitive to tool/service failures.
		- When upstream dependency fails, baseline may still respond quickly while agent may degrade if tool chain is unstable.

3.  **Observation**: How did the environment feedback (observations) influence the next steps?
		- Observations are critical in ReAct loops; they guide subsequent action/tool choice.
		- In backend terms, good observation payloads and stable API contracts directly improve final answer quality.

---

## IV. Future Improvements (5 Points)

- **Scalability**:
	- Move chat history from text files to PostgreSQL with indexed tables (`sessions`, `messages`) and pagination.
	- Add Redis cache for hot session metadata and request throttling.

- **Safety**:
	- Introduce strict request validation/guardrails for model selection and user input.
	- Add structured error taxonomy and fallback responses to avoid leaking raw provider errors to users.

- **Performance**:
	- Add connection pooling, structured logging, and metrics (latency, timeout ratio, upstream failure rate).
	- Use async queues for expensive tool calls and add circuit breaker around external AI services.
	- Add integration tests for full path: frontend -> server -> ai-services -> persistence.

---
