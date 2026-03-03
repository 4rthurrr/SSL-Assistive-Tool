# 🎙️ Final 2-Minute Presentation Script
**Goal:** Explain the entire system simply in English.
**Time:** 2 Minutes (Approx. 250-300 words).

---

## 0:00 - 0:30 | Introduction (The "Why")
**[SLIDE 1: Title Slide with Project Name]**

"Good Morning. My research project is the **AI-Powered Sinhala Sign Language Assistive Platform for Deaf Children.**

The problem we are solving is the **Communication Gap**. Deaf children in Sri Lanka struggle to learn because there are no digital tools that translate Sinhala Text into Sign Language efficiently. Existing tools are either too expensive or don't support Sinhala grammar.

My solution is a web-based platform that translates complex Sinhala sentences into 3D Sign Language animations in real-time."

---

## 0:30 - 1:10 | System Architecture (The "How")
**[SLIDE 2: The System Flow Diagram (Horizontal)]**
*(Point to the Diagram I created for you)*

"Here is how the system works. It has three main layers:

1.  **First, the Input Layer:** When a user types a complex sentence like *'Mata Pothak Ona'*, our **Context Engine** activates.
2.  **Second, the AI Layer:** The system detects that *'Pothak'* is a variation. Using our custom **Word2Vec Model**, it intelligently maps it to the root concept *'Book'* with 92% confidence.
3.  **Third, the Output Layer:** The system retrieves the correct 3D animation clips and uses a **Video Stitching Algorithm** to merge them into one fluid sentence."

---

## 1:10 - 1:40 | Technologies Used
**[SLIDE 3: Technology Stack Table]**

"To build this, we used a **Hybrid Tech Stack**:

*   **Frontend:** We used **React.js** with **Three Fiber** to render the 3D Avatar directly in the browser, making it accessible on any school computer.
*   **Backend:** We used **Flask** to handle the heavy AI logic.
*   **The Brain:** We trained a **Word2Vec** model specifically on Sinhala morphology to handle the complex grammar rules."

---

## 1:40 - 2:00 | Design Excellence & Conclusion
**[SLIDE 4: Design Excellence Bullet Points]**

"My key individual contributions are:
1.  **The Context Engine:** Which allows the system to understand synonyms and grammar variations, not just exact words.
2.  **The Concept ID System:** A universal key that connects language to video, enabling future cross-lingual support.

In conclusion, this tool bridges the gap between text and sign, empowering deaf children to learn independently. Thank you."

---
## 🖼️ Image Suggestions for Slides
1.  **Slide 2:** Use `documentation/System_Flow_Diagram.md` (Rendered).
2.  **Slide 3:** A screenshot of the `Technology_Stack_and_Alternatives.md` table.
3.  **Slide 4:** A screenshot of the **Accuracy Report** table (`Scientific_Accuracy_Report.md`) to prove your 81% accuracy claims.
