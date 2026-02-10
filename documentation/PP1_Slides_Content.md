# PP1 Presentation Slides - Content Draft

## SLIDE 1 – INDIVIDUAL COMPONENT (IMPLEMENTED WORK)

**Title:** Concept-Based Sinhala NLP & SSL Mapping Engine

### 1. How the Solution Addresses the Sub-Problem / Prototype
*   **Sub-Problem:** Deaf children struggle with written Sinhala due to complex grammar (Diglossia) and lack of tools that understand colloquial sentence structures.
*   **Proposed Solution:** A semantic mapping engine to convert arbitrary Sinhala text into gramatically correct Sinhala Sign Language (SSL) sequences.
*   **Implemented Status:**
    *   Developed "Strict Concept Mapping Pipeline" (Tokenization → Semantic Concept Extraction → SSL Reordering). [Implemented]
    *   Created `Concept Registry` mapping colloquial Sinhala keywords/synonyms to 400+ Standardized SSL Concepts. [Implemented]
    *   Integrated hybrid Strategy: Rule-based core for accuracy + Experimental Word2Vec for synonym coverage. [In Progress]
    *   Implemented 3 Output Modes: Normal Video, Skeleton View, and AI Avatar. [Implemented]

### 2. User Requirements Addressed by the Solution
*   **Colloquial Support:** System recognizes spoken-style Sinhala (e.g., "Mata vathura onaa") instead of just formal textbook text. [Implemented]
*   **Real-Time Processing:** Text-to-GLOSS conversion occurs in under 200ms for instant feedback. [Implemented]
*   **Grammar Correction:** Automatically removes tense markers and reorders Sentence Subject-Object-Verb (SOV) to SSL structure where necessary. [Implemented]

---

## SLIDE 2 – INDIVIDUAL COMPONENT (DESIGN & FEEDBACK)

**Title:** Concept-Based Sinhala NLP & SSL Mapping Engine

### 3. Design Excellence / Contribution
*   **Concept-ID Architecture:** Decoupled Input (Sinhala) from Output (Video) using unique IDs (e.g., `CONCEPT_WATER`), allowing easy future expansion to other languages (Tamil/English). [Implemented]
*   **Hybrid Normalization:** 
    *   Strategy A: Static dictionary for high-speed lookup. [Implemented]
    *   Strategy B: Vector Space (Word2Vec) embeddings to infer meanings of unknown words. [In Progress]
*   **Scalability:** Modular Python `nlp_grammar.py` pipeline allows swapping algorithms without breaking the frontend. [Implemented]

### 4. User Feedback on Prototype
*   **Feedback:** "Rule-based translation is 100% accurate for taught vocabulary but fails on unknown words."
*   **Observation:** Users preferred the deterministic accuracy of the Concept Engine over unstable pure-ML outputs during initial testing.
*   **Future Action:** The remaining 50% will focus on expanding the "Knowledge Graph" (Embeddings) and upgrading the AI Avatar to a fully "3D Child-Friendly & Cultural-Friendly" model.

---

## SLIDE 3 – FINAL SLIDE (ENTIRE PROJECT)

**Title:** AI-Powered Sinhala Sign Language Assistive Technology Platform for Deaf / Mute Children

### 1. Commercialization / Sustainability
*   **Readiness:** Functional Prototype (TRL 4) ready for supervised pilot testing.
*   **Sustainability:** Freemium model—Core translation free for accessibility; Premium "Learning Games" & "Analytics" for schools to fund improvements.

### 2. Customer Persona
*   **Primary:** Deaf/Hearing-impaired children (Ages 5-12) in Sri Lanka.
*   **Secondary:** Parents & Special Education Teachers requiring teaching aids.
*   **Tertiary:** General public wanting to communicate with the Deaf community.

### 3. Market Size
*   **Scope:** ~400,000+ Deaf community members in Sri Lanka.
*   **Expansion:** Scalable to other Sign Languages (e.g., Tamil Sign Language) due to Concept-ID design.

### 4. What Is Unique in the Solution
*   **Concept-Based vs Word-Based:** Translates *meaning* (semantics) rather than literal words, avoiding common translation errors.
*   **Child-Centric UI:** Gamified, non-intimidating interface with multiple avatar modes (Normal/Skeleton/AI).
*   **Cultural Relevance:** Future 3D Avatar designed specifically for Sri Lankan cultural context. [Planned]

### 5. How Will the Cost Be Recovered?
*   **Partnerships:** Licensing to Ministry of Education for special schools. [Planned]
*   **Subscription:** Affordable monthly fee for advanced vocabulary packs and progress tracking features. [Planned]
