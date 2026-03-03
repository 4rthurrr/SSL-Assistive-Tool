# Technology-Specific Demo Inputs

Use these 15 inputs to demonstrate the specific power of each component in your system.

---

## 1. To Demonstrate: **The AI Model (Word2Vec)**
**Goal:** Show that the system understands word variations (Morphology) that exist in the real world but NOT in the dictionary.

1.  **Input:** `මට පොතක් ඕන` (Mata Pothak Ona)
    *   *Why:* `Pothak` (A Book) -> AI maps to `Potha` (Book).
2.  **Input:** `බල්ලෙක් ඉන්නවා` (Ballek Innawa)
    *   *Why:* `Ballek` (A Dog) -> AI maps to `Balla` (Dog). *Note: Use 'එතන බල්ලෙක් ඉන්නවා' if strictly testing context.* (Actually stick to supported verbs: `බල්ලෙක් දුවනවා` is safer). **Use: `බල්ලෙක් දුවනවා`**
3.  **Input:** `අම්මාට දෙන්න` (Ammata Denna)
    *   *Why:* `Ammata` (To Mother) -> AI/Rules map to `Amma` (Mother).
4.  **Input:** `ගෙදරට යන්න` (Gedarata Yanna)
    *   *Why:* `Gedarata` (To Home) -> Maps to `Gedara` (Home).
5.  **Input:** `මල්ලිත් එක්ක` (Mallith Ekka) - *Advanced*
    *   *Why:* Testing if `Mallith` (Brother too) maps to `Malli`. Or try: `පාසලට` (Pasalata - To School). **Use: `පාසලට යන්න`** (Pasalata Yanna).

---

## 2. To Demonstrate: **The NLP Engine (Grammar Logic)**
**Goal:** Show how the system handles sentence structure and tokenization (Subject-Object-Verb).

1.  **Input:** `මම බත් කනවා` (Mama Bath Kanawa)
    *   *Why:* Classic Subject (`Mama`) + Object (`Bath`) + Verb (`Kanawa`).
2.  **Input:** `තාත්තා හෙට එනවා` (Thaththa Heta Enawa)
    *   *Why:* Handling Time (`Heta`) in the correct slot.
3.  **Input:** `නංගි පොත කියවනවා` (Nangi Potha Kiyawanawa)
    *   *Why:* Distinct Subject (`Nangi`) doing action on Object (`Potha`).



---

## 3. To Demonstrate: **Video Stitcher & 3D Avatar (Visual Flow)**
**Goal:** Show smooth transitions and long-sequence capability.

1.  **Input:** `අද මම පාසල් යනවා` (Ada Mama Pasal Yanawa)
    *   *Why:* 4 distinct concepts stitched together.
2.  **Input:** `අම්මා කෑම උයනවා` (Amma Kaama Uyanawa)
    *   *Why:* Real-world daily scenario.
3.  **Input:** `තාත්තා වැඩට යනවා` (Thaththa Wadata Yanawa)
    *   *Why:* `Wadata` (To work) + `Yanawa`. Good flow.
4.  **Input:** `මම වතුර බොනවා` (Mama Wathura Bonawa)
    *   *Why:* Very clear, distinct signs for dynamic avatar movement.
5.  **Input:** `සුබ උදෑසනක්` (Suba Udesanak)
    *   *Why:* Greeting. Often a single long sign or compound, good for showing avatar fidelity.

---

## ⚡ Cross-Lingual Bonus (Context Engine)
1.  `I want water`
2.  `Good Morning`
3.  `Where is the bus`
4.  `I love mother`
5.  `Hospital is near`
