# What is a "Concept ID"? 🆔

The **Concept ID** (e.g., `CONCEPT_MOTHER`) is the **Universal Key** that connects the different parts of your system. It solves the problem of "Many Words, One Meaning".

## 1. The Core Purpose: Synonym Normalization 🔗
In Sinhala, there are many ways to say the same thing:
*   *Input 1:* "Amma" (අම්මා)
*   *Input 2:* "Maw" (මව)
*   *Input 3:* "Ammi" (අම්මි)

If we treated these as different words, we would need 3 different videos.
**Concept ID Solution:** All of these map to **ONE** ID: `CONCEPT_MOTHER`.

## 2. The Bridge between Modules 🌉
The Concept ID is the common language spoken by all your engines:

| Engine | What it sees |
| :--- | :--- |
| **User Input** | "Mata **Pothak** Ona" |
| **AI Layer** | Maps "Pothak" -> "Potha" |
| **NLP Layer** | Maps "Potha" -> **`CONCEPT_BOOK`** |
| **Avatar Layer** | Looks up **`CONCEPT_BOOK`** -> Plays `book.mp4` |

## 3. Why is this Novel? 🧪
Most simple translators map `Word -> Video` directly.
Your system maps `Word -> Concept -> Video`.
*   **Advantage:** This allows you to support **Cross-Lingual Input** (English "Book" also maps to `CONCEPT_BOOK`) without duplicating video assets.

---
**Viva Answer:** *"The Concept ID is an abstract representation of meaning that decouples the surface language (Sinhala/English) from the visual output (Sign Video). It acts as a normalization layer for synonyms."*
