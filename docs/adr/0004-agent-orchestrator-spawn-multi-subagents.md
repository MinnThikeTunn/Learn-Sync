# ADR 0004: Distributed Agent Orchestrator & Spawn-Multi-Subagent Pattern

## Status
Accepted

## Context
LearnSync AI synthesizes personalized study artifacts tailored to a student's learning style (Visual, Auditory, Read/Write, Kinesthetic) and academic discipline. Previously, synthesis logic was centralized within a monolithic method in the RAG service. As we expanded to support diverse academic disciplines (Medicine with live vitals HUD, Life Sciences with procedural sequencing, Law/Business with decision dilemmas, and CS with code sandboxes), maintaining distinct prompting strategies, syntax validations, and rate-limited model integrations within a single function became unscalable.

Furthermore, students and study sessions benefit from multi-modal learning packages where all modalities are generated concurrently for a topic, requiring parallel execution across specialized agents.

## Decision
We implemented a **Distributed Multi-Agent Architecture** following the **Spawn-Multi-Subagent Design Pattern**:

1. **`LearnerAgentOrchestrator`**:
   - Manages the lifecycle and registry of specialized learner subagents.
   - Provides targeted single subagent spawning via `spawn_agent(style, context)`.
   - Provides parallel concurrent multi-agent fan-out via `spawn_all_subagents(context)` utilizing a thread pool (`ThreadPoolExecutor`).

2. **Dedicated Autonomous Subagents**:
   - `VisualLearnerAgent`: Generates semantic mind maps (`mindmap`) and sequential process flows (`flowchart TD`) following the `mermaid-diagrams` skill rules (syntax sanitization, escaped nodes, dual views).
   - `AuditoryLearnerAgent`: Generates Socratic dialogue transcripts (Professor & Student) and rapid verbal recap podcasts.
   - `ReadWriteLearnerAgent`: Generates structured Markdown study guides with formal conceptual sections and 3-Bullet Pareto takeaways.
   - `KinestheticLearnerAgent`: Generates polymorphic interactive simulations (Clinical Case Triage with live Vitals HUD, Chronological Procedural Sequencing Labs, Strategic Decision Dilemmas, and Interactive Code Labs).

3. **OpenRouter Free Tier Integration with Deterministic Resilience**:
   - Integrated `OpenRouterService` connecting to OpenRouter's free models (`meta-llama/llama-3.3-70b-instruct:free`, `google/gemini-2.0-flash-exp:free`, `deepseek/deepseek-r1:free`).
   - Standardized fallback hierarchy: OpenRouter $\rightarrow$ Gemini $\rightarrow$ Grounded Deterministic Template. If zero API keys are supplied or rate limits occur, subagents fail gracefully to deterministic synthesis without breaking tests or user flows.

## Consequences

### Positive
- **Modularity & Separation of Concerns**: Each subagent manages its own prompt schemas, validation rules, and discipline-specific behaviors in isolation.
- **Concurrent Efficiency**: Multi-modal packages are synthesized in parallel rather than serially, reducing total latency from $O(N)$ to $O(1)$.
- **Zero-Key Resilience**: Zero external API dependencies required for development and continuous integration test suites.
- **Full Backward Compatibility**: Preserves all existing frontend contracts, schemas, and endpoints.

### Neutral
- Orchestrator handles deep-copying of context objects to prevent state mutation across concurrent threads.
