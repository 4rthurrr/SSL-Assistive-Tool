# Design Excellence Diagram

Copy the code below into a Mermaid Live Editor or use a Markdown viewer that supports Mermaid to generate your image.

### **Diagram: Hybrid Concept-Based NLP Architecture**

This flowchart demonstrates your **Individual Contribution**: The 4-Step Pipeline that handles both known words (Rule-Based) and unknown words (AI Word2Vec).

```mermaid
flowchart TD
    %% Nodes
    Input([🗣️ Input: "මට තේ එකක් ඕන"]) --> Tokenizer[Step 1: Tokenizer]
    Tokenizer --> Tokens[Tokens: "මට", "තේ", "එකක්", "ඕන"]
    Tokens --> Mapper{Step 2: \nConcept Mapping}
    
    %% Logic Flow
    Mapper -- Found in Registry (e.g. ඕන) --> ConceptID[✅ Concept ID]
    Mapper -- Unknown Word --> OOV[⚠️ RAW_TOKEN]
    
    OOV --> AI_Layer{Step 3: \nWord2Vec AI Layer}
    AI_Layer -- Similarity > 60% --> Normalized[✨ AI Normalized Concept]
    AI_Layer -- No Match --> Fail[❌ Ignored]
    
    %% Re-Convergence
    ConceptID --> Sequencer[Step 4: \nSSL Grammar Reordering]
    Normalized --> Sequencer
    
    Sequencer --> FinalSeq([🏁 Final Sequence: \nI, TEA, WANT])
    FinalSeq --> VideoGen[🎥 Video Generator]

    %% Styling
    classDef ai fill:#e1f5fe,stroke:#01579b,stroke-width:2px;
    classDef core fill:#fff9c4,stroke:#fbc02d,stroke-width:2px;
    classDef input fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px;
    
    class AI_Layer,Normalized ai;
    class Mapper,ConceptID,Sequencer core;
    class Input,VideoGen input;
```

### **How to explain this diagram:**
1.  **Green Path (Rule-Based):** Shows how taught words go straight to accurate Concept IDs.
2.  **Blue Path (AI Innovation):** Shows how "Unknown words" don't break the system; they go through your **Word2Vec Layer** to get normalized.
3.  **Convergence:** Both paths meet at the **Grammar Reordering** step, ensuring the final output is always structural Sign Language.
