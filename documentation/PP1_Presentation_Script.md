# PP1 Presentation Script (Time: ~2 Minutes)
**Speaker:** [Your Name]
**Component:** Concept-Based Sinhala NLP & SSL Mapping Engine

---

### **Slide 1: Component & Core Implementation (40 Seconds)**

"Good morning everyone. My component is the **Concept-Based Sinhala NLP & SSL Mapping Engine**.

**[Point to 'Problem Statement' or Text on Slide 1]**
The core problem I address is **Sinhala Diglossia**. Deaf children often write how they speak (e.g., *'Mata bada gini'*), but existing tools fail because they only understand formal textbook Sinhala.

**[Point to Architecture/Pipeline Diagram Image]**
To solve this, I built a quantitative **4-Step NLP Pipeline**. As you can see in this diagram:
1.  We tokenize the input.
2.  We map colloquial words to **Semantic Concept IDs** (like `CONCEPT_WANT`), ignoring grammar mistakes.
3.  We reorder them to Sign Language syntax (SOV).
4.  Finally, we generate the video.

**[Point to Output Mode Images]**
We successfully implemented this engine with **3 Verification Modes**: Normal Video, Skeleton View, and an experimental AI Avatar, ensuring the output is always verifiable."

---

### **Slide 2: Design Excellence & Feedback (40 Seconds)**

**[Point to Code/Innovation Bullet Points]**
"For **Design Excellence**, my key contribution is the **Hybrid NLP Architecture**.
Unlike basic translators, we use a **Deterministic Rule-Based Engine** for 100% accuracy on taught vocabulary, while keeping a **Word2Vec AI Layer** to handle unknown synonyms. This prevents the 'hallucinations' we often see in pure AI models.

**[Point to User Feedback Chart/Quote]**
Regarding **User Feedback**, initial testing revealed that while the pure AI model was innovative, it sometimes guessed signs—for example, confusing 'Want' with 'Smile'.
Based on this, we shifted to a **Strict Rule-Based Core** for the prototype.
**[Point to Future Plan]**
For the next 50%, my focus is replacing the current skeleton with a **3D Child-Friendly Avatar** wearing a Sri Lankan school uniform to make it culturally relevant for our young users."

---

### **Slide 3: Commercialization & Sustainability (40 Seconds)**

"Finally, looking at the **Entire Project Sustainability**.

**[Point to Market Stats]**
We are targeting the **400,000+ Deaf community** in Sri Lanka, focusing specifically on Primary Education (Grades 1-5).

**[Point to SaaS/Business Model]**
Our Unique Selling Point is that we are not just a translator, but a **Gamified Learning Companion**.
We plan to recover costs through a **Freemium Model**:
1.  **Basic Translation** remains free for accessibility.
2.  **Premium Analytics** and 'Learning Games' will be licensed to Special Education Schools (B2B) and parents (B2C).

This ensures the project is both socially impactful and financially sustainable. Thank you."

---
*(Total Word Count: ~280 words. At normal speaking speed, this is exactly 2 minutes.)*
