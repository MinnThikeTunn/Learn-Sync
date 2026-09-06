# LearnSync AI

The Context-Aware Adaptive Learning, Virtual Folder Resource Manager & Workload Co-Pilot.


## Core Learning Lifecycle

1. **Ingest & Remember**: Student uploads course documents into a **Virtual Folder**; the system parses the document into atomic **Knowledge Components** and establishes **Document Memory**.
2. **Learn (Study Tab)**: Student actively engages with the material through multimodal synthesis (**Study Session**) tailored to their cognitive learning style and Workload Score.
3. **Revise (Review Tab)**: Completing the study session triggers the **Study-to-Review Handoff**, queueing the topic into the **2357 Spaced Schedule** for active recall revision (**Review Session**) and long-term FSRS retention.

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

**Student Profile**:
A domain entity extending auth credentials with cognitive learning style, target retention, and onboarding status.
_Avoid_: User account, user settings, profile data

**Onboarding Gate**:
A prerequisite setup state in the client that blocks access to the Cockpit until learning style and target retention are configured.
_Avoid_: Setup wizard, signup form, intro flow

**2357 Spaced Schedule**:
A 4-stage early-acquisition review interval progression (Days 1, 3, 5, 7) initiated upon completing a lesson in the Study tab before graduating to dynamic FSRS retention tracking.
_Avoid_: Simple Leitner, fixed timer, revision checklist

**Study-to-Review Handoff**:
The explicit student-triggered transition in the Study tab that transitions a freshly studied document topic into the Day 1 Spaced Repetition queue.
_Avoid_: Auto-queue, passive bookmarking, manual card assignment

**Blurting**:
An active recall practice in the Review tab where a student reproduces unprompted knowledge from memory, semantically graded by AI against source document Knowledge Components.
_Avoid_: Brain dump, free writing, open quiz

**Hybrid 2357-FSRS Engine**:
The dual-phase scheduling pipeline combining rigid 2357 acquisition intervals for new knowledge with elastic FSRS retrievability scaling adjusted by Workload Score W(t).
_Avoid_: Custom algorithm, hybrid scheduler

**Document Memory**:
The persistent semantic index and atomic Knowledge Component breakdown extracted from course documents uploaded into a Virtual Folder.
_Avoid_: File cache, uploaded docs, vector store

**Study Session**:
An interactive multimodal learning engagement in the Study tab where a student absorbs a topic via learning-style-tailored artifacts prior to scheduled revision.
_Avoid_: Lesson view, reading time, study page

**Review Session**:
An active recall revision engagement in the Review tab where a student tests retention on due Knowledge Components via 2357 Flashcards, Blurting, or Feynman exercises.
_Avoid_: Revision page, quiz time, test tab

**Academic Discipline**:
The subject matter domain (such as Medicine, Computer Science, Law, Life Sciences, Business, or Humanities) associated with a Course or Virtual Folder, scoping the generation of discipline-appropriate learning artifacts.
_Avoid_: Subject tag, department name, major category

**Mind Map**:
A radial and hierarchical semantic diagram visually organizing concepts, anatomical structures, or legal doctrines outward from a central Knowledge Component into categorized branches.
_Avoid_: Bubble chart, spider graph, concept drawing

**Process Flow**:
A sequential, chronological diagram capturing algorithmic state transitions, clinical protocols, or causal pipelines.
_Avoid_: Step chart, flowchart drawing, pipeline map

**Interactive Simulation**:
A kinesthetic learning engagement providing active manipulation and immediate causal feedback tailored to the course discipline, encompassing Clinical Case Simulations, Procedural Sequencing Labs, Decision Dilemmas, and Interactive Code Labs.
_Avoid_: Quiz game, multiple choice test, interactive widget

**Critical Decision Micro-Task**:
A rapid, single-action kinesthetic challenge served in Busy Mode (W(t) > 0.70) delivering instant tactile feedback in under 60 seconds without multi-step cognitive overhead.
_Avoid_: Quick question, flash quiz, bite-sized test

**Learner Agent Orchestrator**:
The central coordinator managing autonomous learner subagents across all VARK modalities. Implements the Spawn-Multi-Subagent Pattern to spawn dedicated agents or concurrently fan out across all learner styles.
_Avoid_: Master agent, parent bot, controller script

**Learner Subagent**:
A dedicated autonomous agent specializing in a single VARK modality (Visual, Auditory, Read/Write, Kinesthetic) and discipline context, using OpenRouter free-tier LLMs with deterministic template fallback.
_Avoid_: Worker node, child process, sub-bot

**Concurrent Multi-Agent Fan-Out**:
A parallel architectural execution pattern where the orchestrator dispatches and executes multiple specialized subagents simultaneously via a thread pool to generate complete multi-modal learning packages.
_Avoid_: Batch processing, bulk generator, loop execution
