# LearnSync AI

The Context-Aware Adaptive Learning, Virtual Folder Resource Manager & Workload Co-Pilot.

## Language

**Workload Score (W(t))**:
A continuous 3-day lookahead score in [0.0, 1.0] computed from deadline density, event weights, and external cognitive activity signals.
_Avoid_: Stress score, busy level, pressure index

**Free Mode**:
The comprehensive learning state active when W(t) <= 0.55, delivering deep interactive diagrams, podcasts, and code sandboxes.
_Avoid_: Normal mode, relaxed mode, standard mode

**Busy Mode**:
The bite-sized, low-cognitive-load state active when W(t) > 0.70, delivering cheat-sheets, 30-second audio recaps, and 90-second micro-tasks.
_Avoid_: Exam mode, crunch mode, stress mode

**Hysteresis Dead-Band**:
The 0.55–0.70 W(t) interval where the active mode is strictly retained to prevent rapid state oscillation.
_Avoid_: Buffer zone, transition zone, neutral state

**Virtual Folder**:
A logical, nested organizational node bound to a course module that scopes document retrieval and study prioritization.
_Avoid_: Category, directory, tag group, subject folder

**Knowledge Component (KC)**:
An atomic unit of course curriculum whose latent mastery state is tracked via Bayesian Knowledge Tracing.
_Avoid_: Skill, topic item, concept tag

**Leech**:
A flashcard failed 4 or more times, automatically paused from the active review queue for LLM-driven simplification.
_Avoid_: Hard card, difficult prompt, failure card

**Burnout Guard**:
An automated monitoring layer that replaces standard study sessions with low-barrier B=MAP micro-tasks during acute deadline clusters.
_Avoid_: Stress blocker, anti-burnout filter

**Reciprocal Rank Fusion (RRF)**:
A hybrid ranking algorithm combining dense vector embeddings and sparse BM25 keyword matching within virtual folder scopes.
_Avoid_: Hybrid search, blended search

**Federated Edge Aggregation**:
An on-device model optimization framework employing local gradient descent and Differential Privacy before central parameter aggregation.
_Avoid_: Distributed ML, edge cloud sync, client upload
