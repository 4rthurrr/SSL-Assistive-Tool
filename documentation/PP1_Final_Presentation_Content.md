
# PP1 Presentation Slides Content
**Date:** 12/30/2025
**Student ID:** IT22091352
**Component:** Concept-Based Sinhala NLP & SSL Mapping Engine

---

## SLIDE 1: INDIVIDUAL COMPONENT
**Individual Title:** Concept-Based Sinhala NLP & SSL Mapping Engine

### 1. How the Solution Will Address the Sub-Problem / Prototype
*   **Sub-Problem:** Deaf students face "Diglossia" (gap between spoken & written Sinhala), making existing text-to-speech tools ineffective for colloquial input.
*   **Solution Address:** Implemented a **Concept-Based Semantic Engine** that standardizes colloquial Sinhala (e.g., "Mata bada gini") into language-neutral Concept IDs before translation.
*   **Prototype Status:** fully functional **4-Step NLP Pipeline** (Tokenization → Mapping → Normalization → Grammar) is implemented and integrated with the video player.

### 2. User Requirements Addressed by the Solution
*   **Colloquial Support:** System successfully processes spoken-style Sinhala input often used by children.
*   **Real-Time Visualization:** Generates Sign Language video sequences in <200ms.
*   **Multi-View Output:** Implemented 3 verification modes based on user needs: **Normal Video**, **Skeleton View**, and **AI Avatar**.

---

## SLIDE 2: INDIVIDUAL COMPONENT
**Individual Title:** Concept-Based Sinhala NLP & SSL Mapping Engine

### 3. Design Excellence / Contribution
*   **Hybrid NLP Architecture:** Combines satisfactory **Rule-Based accuracy** for core vocabulary with **Word2Vec Embeddings** (planned) for unknown synonyms to prevent AI hallucinations.
*   **Concept-ID Scalability:** Decouples the "Word" from the "Sign Video" using unique IDs (`CONCEPT_WANT`), allowing easy future expansion to Tamil/English without code changes.
*   **Child-Centric Design:** Integrated gamified feedback (Confetti/Animations) directly into the translation workflow.

### 4. User Feedback on Prototype
*   **Feedback:** "Pure AI models tend to guess incorrect sings for similar words (e.g. Smile vs Want)."
*   **Response:** We shifted the core engine to a **Deterministic Rule-Based System** to ensure 100% accuracy for taught syllabus words.
*   **Future Action:** The remaining 50% will focus on upgrading the current AI avatar to a **3D Culturally-Adapted Avatar** (School Uniform) to be friendlier for children.

---

## SLIDE 3: ENTIRE PROJECT (FINAL SLIDE)
**Project Title:** AI-Powered Sinhala Sign Language Assistive Technology Platform

### 1. Commercialization / Sustainability of Solution
*   **Freemium Model:** Basic translation text-to-sign is free for accessibility.
*   **Sustainability:** Partnering with Special Education Units (gov/private) for long-term deployment and maintenance.

### 2. Customer Persona
*   **Primary:** Deaf/Hearing-impaired students (Grades 1-5).
*   **Secondary:** Special Education Teachers & Parents.

### 3. Market Size
*   **Reach:** Target audience of ~400,000+ Deaf community members in Sri Lanka.
*   **Expansion:** Scalable infrastructure suitable for South Asian Sign Languages.

### 4. What is Unique in Your Solution
*   **Semantic Accuracy:** Translates *meaning* rather than keywords (solving the Diglossia issue).
*   **Cultural Avatar:** Moving beyond generic 3D models to a specific Sri Lankan child character.
*   **Gamified Learning:** Not just a translator, but an interactive learning companion.

### 5. How Will the Cost Be Recovered?
*   **Premium Features:** Subscription for "Advanced Vocabulary Packs" and "Progress Analytics" for schools.
*   **Licensing:** B2B licensing to educational institutes for the "Learning Games" module.
