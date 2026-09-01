# Hybrid 2357-FSRS Spaced Repetition & Study-to-Review Workflow

We adopt a two-phase spaced repetition architecture: initial early-acquisition pacing governed by the 2357 Method (Days 1, 3, 5, 7), seamlessly graduating into workload-coupled Free Spaced Repetition Scheduler (FSRS) with dynamic memory stability and difficulty modeling.

## Context
Students ingesting academic documents into Virtual Folders require an intuitive learning pipeline: they first consume multimodal study artifacts in the Study tab (`/study`), then transition their acquired knowledge into active spaced revision in the Review tab (`/review`). 

Traditional FSRS can produce unpredictable initial intervals for freshly introduced concepts, while purely static interval tables fail to adapt to long-term memory stability or student exam crunch (Workload Score $W(t)$). Grounded by research from Birmingham City University on the 2357 Method and Ebbinghaus forgetting curves, an optimal learning loop requires structured early interval reinforcement paired with flexible long-term retention.

## Decision
1. **Document Ingestion & Candidate KC Generation**: When a document is uploaded, backend parsers extract atomic Knowledge Components (KCs) and generate candidate flashcard/active recall pairs in the background, associated with the document and virtual folder.
2. **Study-to-Review Handoff**: Interacting with or completing a study session in the Study tab triggers an explicit completion handoff. This activates the document's candidate cards into **Day 0** of the **2357 Spaced Schedule**, scheduling their first active recall review for tomorrow (**Day 1**).
3. **Hybrid 2357-FSRS Graduation**:
   - **Acquisition Phase (Stages 1–4)**: Cards advance through explicit 2357 milestone intervals (Day 1 $\rightarrow$ Day 3 $\rightarrow$ Day 5 $\rightarrow$ Day 7) upon successful review (Rating $\ge$ Good).
   - **Lapse / Penalty**: Failing a card (Rating = Again) resets it to Day 1 or triggers Leech quarantine if lapses $\ge 4$.
   - **Graduation Phase**: Upon completing the Day 7 review, the card graduates into the continuous FSRS algorithm ($S, D, R$) with Workload Score $W(t)$ elasticity.
4. **Multimodal Active Recall Suite**: The Review tab (`/review`) provides three complementary active recall modalities:
   - **Flashcard Deck**: 2357/FSRS cards with flip interaction and 4-grade rating (Again, Hard, Good, Easy).
   - **Blurting Scratchpad**: Unprompted free-form recall against a document chunk with AI semantic grading (retained concepts vs missed nuances).
   - **Feynman Technique**: Conversational explanation evaluated for clarity and jargon-free simplicity.

## Consequences
- Guarantees immediate, predictable revision intervals immediately following a lesson.
- Eliminates cognitive load on students to manually schedule flashcards.
- Preserves long-term memory durability through algorithmic FSRS graduation.
- Fully aligns UI/UX between document storage (`/folders`), multimodal learning (`/study`), and active recall (`/review`).
