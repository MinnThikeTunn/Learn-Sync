# 04: Grounded Multimodal Adaptive Learning Engine (4 Styles x 2 Modes)

**What to build:**
Create the LLM-powered Adaptive Learning Engine that synthesizes personalized study artifacts using Grounded RRF hybrid retrieval restricted to the student's active `folder_id`. The engine modulates representation according to the 4 learning styles (Visual, Auditory, Read/Write, Kinesthetic) and adapts depth and brevity according to active workload mode (Free Mode comprehensive vs. Busy Mode bite-sized cheat-sheets/30s recaps).

**Blocked by:**
- 01: Supabase Backend Schema & Folder-Scoped Vector RPC Initialization
- 02: Docling Syllabus Parser & Virtual Folder Ingestion Pipeline
- 03: Rolling Workload Engine W(t), Hysteresis State Machine & RabbitMQ Publisher

**Status:** ready-for-agent

- [ ] Folder-scoped context assembler invokes Supabase `match_folder_chunks` RPC to ground prompts in course material.
- [ ] Free Mode ($W(t) \le 0.55$) generates deep artifacts: Mermaid diagrams (Visual), Socratic audio dialogue (Auditory), comprehensive notes (Read/Write), and code labs (Kinesthetic).
- [ ] Busy Mode ($W(t) > 0.70$) applies Pareto 80/20 filtering to generate core primitive cheat-sheets (Visual), 30-second audio recaps (Auditory), bullet summaries (Read/Write), and micro-snippets (Kinesthetic).
- [ ] Insufficient retrieval confidence gracefully notifies the user rather than hallucinating unsupported facts.
- [ ] End-to-end unit and generation tests verify artifact structure across all 8 (4 styles $\times$ 2 modes) combinations.
