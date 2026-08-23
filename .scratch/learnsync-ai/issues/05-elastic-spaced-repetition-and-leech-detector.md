# 05: Elastic Spaced Repetition (py-fsrs), Leech Detection & RabbitMQ Consumer

**What to build:**
Implement the spaced-repetition flashcard service wrapping the `py-fsrs` scheduling algorithm. Dynamically couple review intervals and target retention ($R_c$) to workload signals: when consuming a `workload.spike.detected` event from RabbitMQ (Busy Mode), lower target retention $R_c$ to 80% and expand intervals by $1.75\times$ (reducing daily reviews by up to 45%). Detect and auto-pause leeches ($\ge 4$ failures) from the review deck and request LLM simplification.

**Blocked by:**
- 01: Supabase Backend Schema & Folder-Scoped Vector RPC Initialization
- 03: Rolling Workload Engine W(t), Hysteresis State Machine & RabbitMQ Publisher

**Status:** ready-for-agent

- [ ] `py-fsrs` integration calculates stability, difficulty, lapses, and next due date per flashcard rating.
- [ ] RabbitMQ consumer reacts to `workload.spike.detected` by dynamically scaling target retention $R_c = 80\%$ and expanding interval multiplier to $1.75\times$.
- [ ] Leech detection flags cards with $\ge 4$ failure lapses, pauses them from the active queue, and creates LLM rewrite prompts.
- [ ] Flashcard reviews and outcome logs persist to `flashcards` and `review_logs` tables in Supabase.
- [ ] Unit tests verify interval expansion calculations, leech pausing, and recovery to standard parameters ($R_c = 90\%$) in Free Mode.
