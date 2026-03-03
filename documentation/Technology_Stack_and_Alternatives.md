# Technology Stack & Alternatives Analysis

This document details the technologies **Selected** for this system and compares them against similar alternatives that were **Rejected**, providing justification for the research panel.

---

## 1. Backend Framework ⚙️

| **Feature** | **Selected: Flask (Python)** | **Alternative: Django / FastAPI** | **Alternative: Node.js** |
| :--- | :--- | :--- | :--- |
| **Type** | Micro-framework | Full-Stack / Async | Asynchronous Event-Driven |
| **Why Selected?** | **Lightweight & Flexible.** We needed to integrate heavy Python AI libraries (Gensim, OpenCV). Flask is the standard for wrapping AI models. | **Rejected:** Too heavy (Django) or unnecessary complexity (FastAPI) for a simple REST API. | **Rejected:** Great for web, but terrible for running Python AI models directly. |

---

## 2. AI / NLP Engine 🧠

| **Feature** | **Selected: Word2Vec (Gensim)** | **Alternative: BERT / GPT (Transformers)** | **Alternative: Simple Dictionary (Rule-Based)** |
| :--- | :--- | :--- | :--- |
| **Type** | Static Embeddings (Fast) | Contextual Embeddings (Heavy) | Exact Match Lookups |
| **Why Selected?** | **Efficiency on Small Data.** We trained it on just 6,000 morphological variations. It runs on any CPU. | **Rejected:** Requires millions of data points and expensive GPUs. Overkill for simple synonyms. | **Rejected:** Too brittle. Fails completely if a user types a word slightly differently (e.g., "Pothak"). |

---

## 3. Frontend Framework 💻

| **Feature** | **Selected: React.js** | **Alternative: Angular** | **Alternative: Pure HTML/JS** |
| :--- | :--- | :--- | :--- |
| **Type** | Component-Based Library | Full MVC Framework | Basic Scripting |
| **Why Selected?** | **Component Reuse.** We built reusable components like `<AvatarCanvas />`. The **Virtual DOM** ensures high FPS for animations. | **Rejected:** Steeper learning curve and boilerplate code. | **Rejected:** Becomes unmanageable ("Spaghetti Code") for complex 3D apps. |

---

## 4. 3D Rendering Engine 🧊

| **Feature** | **Selected: React Three Fiber (R3F)** | **Alternative: Unity WebGL** | **Alternative: Babylon.js** |
| :--- | :--- | :--- | :--- |
| **Type** | Declarative WebGL Wrapper | Game Engine Export | Imperative WebGL Engine |
| **Why Selected?** | **Native React Integration.** We can control the 3D bones using standard React State (Variables), making logic simple. | **Rejected:** Black box. Hard to talk to from React. huge file size (20MB+). | **Rejected:** More verbose code compared to the elegance of R3F. |

---

## 5. Animation Strategy 💃

| **Feature** | **Selected: Mathematical Rigging (FK)** | **Alternative: Pre-recorded Videos** | **Alternative: Deepfakes (GANs)** |
| :--- | :--- | :--- | :--- |
| **Type** | Real-time Calculation | Playback | AI Generation |
| **Why Selected?** | **Dynamic Speed/Control.** We can slow down signs for learners. Zero storage cost. | **Rejected:** Massive storage needed for thousands of word clips. Cannot change speed. | **Rejected:** Requires high-end Server GPUs. Not kid-friendly (uncanny valley). |

---

## 📝 Summary Statement for Presentation
*"We selected a **Flask + React + Word2Vec** stack to prioritize **Accessibility** (Web-based), **Performance** (Low resource), and **Robustness** (Handlers morphological variations). We rejected heavy transformers and game engines to ensure the tool can run on standard school computers without dedicated GPUs."*
