# System Flow Diagram: "මට පොතක් ඕන" 📊

Use this diagram in your presentation to explain **exactly** what happens inside the code when a user types "Mata Pothak Ona".

## ⚡ The Technical Flow

```mermaid
graph LR
    %% Nodes
    User([👤 User Input])
    Input["`මට පොතක් ඕන`"]
    
    subgraph "Phase 1: Context Engine (AI Layer)"
        Split(Split Sentence)
        Check1{"Word: `මට` (Mata)"}
        Check2{"Word: `පොතක්` (Pothak)"}
        Check3{"Word: `ඕන` (Ona)"}
        
        Direct1[Direct Map Found]
        Unknown[❌ Direct Map Failed]
        AI_Fix[🧠 <b>Word2Vec Model</b><br/>Input: `Pothak`<br/>Closest: `Potha` (92%)]
        Direct3[Direct Map Found]
    end

    subgraph "Phase 2: NLP Engine (Grammar Layer)"
        Tokens[Clean List: `Mata`, `Potha`, `Ona`]
        Mapper(Map to Concept IDs)
        Sequence["Final Sequence:<br/>[CONCEPT_ME, CONCEPT_BOOK, CONCEPT_WANT]"]
    end

    subgraph "Phase 3: Avatar Engine (Rendering Layer)"
        Fetch[📂 Fetch Assets:<br/>`me.mp4`, `book.mp4`, `want.mp4`]
        Stitch_Logic[🎬 <b>Video Stitcher</b><br/>Algorithmic Concatenation]
        R3F[React Three Fiber<br/>Play Result]
    end

    %% Edge Connections
    User --> Input --> Split
    Split --> Check1 & Check2 & Check3
    
    Check1 -- "Known" --> Direct1
    Check2 -- "Unknown!" --> Unknown --> AI_Fix
    Check3 -- "Known" --> Direct3
    
    Direct1 & AI_Fix & Direct3 --> Tokens
    Tokens --> Mapper --> Sequence
    Sequence --> Fetch --> Stitch_Logic --> R3F
    
    %% Styling
    style AI_Fix fill:#f9f,stroke:#333,stroke-width:2px,color:black
    style Stitch_Logic fill:#bbf,stroke:#333,stroke-width:2px,color:black
    style Input fill:#ff9,stroke:#333,color:black
```

## 🗣️ How to Explain This Slide
1.  **Start:** "The user types *'Mata Pothak Ona'*."
2.  **The Problem:** "The system knows *'Potha'* (Book), but it doesn't strictly know *'Pothak'* (A Book)."
3.  **The AI Solution (Pink Box):** "Our **Input Handling Layer** sees the unknown word. It asks the **Word2Vec Model**, which calculates that *'Pothak'* is 92% similar to *'Potha'*. It autocorrects it."
4.  **The Result:** "The corrected tokens are sent to the **Video Engine**, which stitches the clips for 'Me', 'Book', and 'Want' seamlessly."

## ⏱️ The 20-Second Pitch (Read this aloud)
*"When a user enters a complex sentence like **'Mata Pothak Ona'**, our system works in three fast layers.*

*First, the **Context Engine** detects that 'Pothak' is an unknown variation. Using our **Word2Vec** model, it intelligently maps it to the root word 'Potha' with 92% confidence.*

*Then, the **NLP Layer** converts these words into Concept IDs.*

*Finally, the **Avatar Engine** retrieves the corresponding animations and algorithmically stitches them together to play a fluid Sign Language sentence."*
