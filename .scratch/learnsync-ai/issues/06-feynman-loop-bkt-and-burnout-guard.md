# 06: Active Recall Feynman Loop, BKT Mastery & Burnout Guard (B=MAP)

**What to build:**
Build the Active Recall Feynman Loop and Burnout Guard intervention service. The Feynman loop prompts students to explain concepts in plain language, runs automated precision-gap analysis against folder source texts, and automatically converts identified misconceptions into localized flashcards while updating Knowledge Component Bayesian Knowledge Tracing (BKT) mastery in Supabase. The Burnout Guard monitors acute deadline clusters ($\ge 3$ deadlines in 48h or 0 free slots in 2 days) and triggers 90-second $B=MAP$ micro-tasks via RabbitMQ.

**Blocked by:**
- 01: Supabase Backend Schema & Folder-Scoped Vector RPC Initialization
- 04: Grounded Multimodal Adaptive Learning Engine (4 Styles x 2 Modes)
- 05: Elastic Spaced Repetition (py-fsrs), Leech Detection & RabbitMQ Consumer

**Status:** ready-for-agent

- [ ] Feynman prompt generator produces plain-language analogies for active virtual folder topics.
- [ ] Precision-gap analysis evaluates student explanations against source documents, identifying missing concepts and misconceptions.
- [ ] Automatically converts detected knowledge gaps into new folder-scoped flashcards.
- [ ] Bayesian Knowledge Tracing updates $P(L_t)$ posterior mastery probabilities in `student_kc_mastery`.
- [ ] Burnout Guard detects critical deadline density and emits low-barrier 90-second $B=MAP$ micro-task prompts over RabbitMQ.
- [ ] Unit & integration tests verify precision-gap parsing, card generation, and BKT mastery state transitions.
