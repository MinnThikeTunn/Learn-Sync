# Multi-Discipline Adaptive Modalities: Universal Mind Maps and Interactive Simulations

We expand LearnSync AI's multimodal learning engine to support all academic disciplines (Medicine, Healthcare, Life Sciences, Law, Business, Humanities, and STEM) by establishing **Mind Maps** for visual learners and generalized **Interactive Simulations** (clinical triage, procedural sequencing, decision dilemmas, and code labs) for kinesthetic learners.

## Context
Previously, LearnSync AI's multimodal generator treated kinesthetic learning exclusively as an in-browser Python code editor (`CODE_LAB`, `MICRO_SNIPPET`) and visual learning as a linear flowchart (`DIAGRAM`). 

In real university settings, students across non-IT disciplines (e.g., Medical students studying pathology, Nursing students studying pharmacology, Biology students studying metabolic cycles, and Law students studying constitutional law) derived zero value from Python editors. Furthermore, visual learners require spatial, radial conceptual chunking (**Mind Maps**) to grasp complex hierarchical taxonomies rather than purely sequential flowcharts.

## Decision
1. **Discipline Scoping & Domain Classification**:
   - Courses and Virtual Folders can define an `academic_discipline` (`medicine`, `life_sciences`, `law`, `business`, `humanities`, `computer_science`, or `general`).
   - If unconfigured, the RAG synthesis pipeline automatically infers the discipline from the uploaded document text and extracted Knowledge Components.
2. **Visual Modality Expansion (Mind Map vs. Process Flow)**:
   - Visual artifacts support two explicit semantic forms:
     - **Mind Map**: Rendered via Mermaid `mindmap` syntax for radial concept clustering, anatomical relationships, and diagnostic classifications.
     - **Process Flow**: Rendered via Mermaid `flowchart` syntax for sequential protocols, metabolic pathways, or algorithms.
   - The Study Hub provides an interactive dual-view toggle between both visual representations.
3. **Universal Kinesthetic Archetypes (Interactive Simulation)**:
   - Replace the code-only sandbox with a polymorphic **Interactive Simulation** model supporting four discipline-tailored archetypes:
     - **Clinical Case Simulation** (Medicine & Healthcare): Patient presentation, vital signs HUD, diagnostic investigation choices, and physiological outcome feedback.
     - **Procedural Sequencing Lab** (Life Sciences, Chemistry, Surgical Protocols): Interactive drag-and-order mechanism sequencing with step validation.
     - **Decision Dilemma** (Law, Business, Ethics): Precedent and strategy decision trees with consequence narratives.
     - **Interactive Code Lab** (Computer Science & Engineering): Preserved runnable code sandbox with assertion testing.
4. **Simulation State Machine & Workload Progression**:
   - In Free Mode ($W(t) \le 0.55$), Clinical Simulations follow a 3-Stage Progressive Pipeline:
     1. Presentation & Initial Impression
     2. Diagnostic Workup (with dynamic vital signs adjustment)
     3. Definitive Management & Follow-up
   - In Busy Mode ($W(t) > 0.70$), simulations collapse into a 60-second **Critical Decision Micro-Task** (e.g. emergency drug call, single crucial enzyme/step checkpoint, or instant objection ruling) providing active tactile feedback without cognitive exhaustion.
5. **Deterministic Mind Map Tree Compilation**:
   - To prevent LLM indentation errors or syntax breaking on complex medical/legal symbols, the LLM outputs a structured JSON concept tree, compiled deterministically into clean Mermaid `mindmap` syntax.
6. **Formative Assessment & Memory Model Handoff**:
   - The Study tab remains a safe, formative environment. Completing an Interactive Simulation successfully provides an initial stability boost to the Knowledge Component when transitioning through the Study-to-Review Handoff into the 2357 Spaced Schedule.

## Consequences
- Expands LearnSync AI's addressable student base to all university faculties with zero friction.
- Eliminates cognitive mismatch by providing discipline-native interactive environments.
- Eliminates 100% of Mermaid syntax parsing crashes through deterministic JSON tree compilation.
- Enhances visual memory consolidation through native Mermaid mindmap rendering.
- Preserves full backward compatibility with existing IT and computer science courses.
