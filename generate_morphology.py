
import sys
import os
import re

# Add backend to path to import concepts
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from concepts import CONCEPT_DEFINITIONS

def generate_morphology_data(output_file="backend/data/vocabulary_expanded.txt"):
    print(f"Generating Training Data from {len(CONCEPT_DEFINITIONS)} concepts...")
    
    with open(output_file, "w", encoding="utf-8") as f:
        count = 0
        for data in CONCEPT_DEFINITIONS.values():
            words = data.get('synonyms', [])
            root_word = data.get('sinhala', '')
            
            # Ensure root word is in the list
            if root_word and root_word not in words:
                words.append(root_word)
                
            for word in words:
                if not word: continue
                word = word.strip()
                
                # Rule 0: Skip Multi-Word Phrases (Enforce 2-word lines)
                if ' ' in word:
                    continue
                
                # --- STRICT GRAMMAR CHECK ---
                
                # Rule 1: Skip English words
                if re.search(r'[a-zA-Z]', word):
                    f.write(f"{word} {word}\n") # Still write identity for lookup
                    continue
                
                # Rule 2: Skip Numbers
                if word.isdigit():
                    f.write(f"{word} {word}\n")
                    continue

                # Rule 3: Skip Adverbs / Particles (Do not inflect)
                STOP_WORDS = { 'පසුව', 'නැවත', 'ආයෙත්', 'පරිස්සමින්', 'හෙට', 'අද', 'ඊයේ', 'දැන්', 'එපා', 'බෑ', 'නෑ', 'ඔව්', 
                               'ඉක්මනට', 'වඩා', 'කවදාවත්', 'ළඟ', 'මෙහෙ', 'එහෙ', 'ඇයි', 'කවුද', 'මොකද්ද' }
                if word in STOP_WORDS:
                    f.write(f"{word} {word}\n")
                    continue

                # Rule 4: VERB Handling
                # Common Verb Endings: නවා, න්න, වා (Past: කෑවා, බිව්වා)
                # Heuristic: If it looks like a verb, SKIP noun suffixes.
                is_verb = False
                if word.endswith("නවා") or word.endswith("න්න") or word.endswith("මු") or word.endswith("බිව්වා") or word.endswith("කෑවා") or word.endswith("ගියා"):
                    is_verb = True
                
                # WRITE: Root -> Root (Identity) - ALWAYS Valid
                f.write(f"{word} {word}\n")

                if is_verb:
                    # Verbs only have specific forms, we don't 'generate' them blindly here.
                    continue 

                # --- NOUN SUFFIX GENERATION (Only for Valid Nouns) ---
                
                # 1. Indefinite / Pluralish (add 'ක්' or 'ක')
                if not word.endswith("ක්"):
                     f.write(f"{word}ක් {word}\n") # e.g., Potha -> Pothak
                     f.write(f"{word}ක {word}\n")  # e.g., Potha -> Pothaka
                
                # 1.b ANIMATE Indefinite (add 'ෙක්')
                # If word ends in 'a' (living things often do 'Balla'), change to 'ek'
                if word.endswith("ා"):
                    stem = word[:-1]
                    f.write(f"{stem}ෙක් {word}\n") # Balla -> Ballek
                    f.write(f"{stem}ට {word}\n")   # Balla -> Ballata (Dative)
                    f.write(f"{stem}ගේ {word}\n")  # Balla -> Ballage (Genitive)
                    f.write(f"{stem}ෙන් {word}\n") # Balla -> Ballen (Instrumental)
                else:
                    # Generic 'ek' add (Riskier, but AI handles noise)
                    if not word.endswith("ක්") and not word.endswith("්"):
                        f.write(f"{word}ෙක් {word}\n") 

                # 2. Dative 'to' (add 'ට')
                if not word.endswith("ට"):
                    f.write(f"{word}ට {word}\n") # e.g., Potha -> Pothata
                
                # 3. Genitive 'of' (add 'ගේ')
                if not word.endswith("ගේ"):
                    f.write(f"{word}ගේ {word}\n") # e.g., Potha -> Pothage
                
                # 4. Instrumental/Locative (add 'ෙන්', 'ේ')
                f.write(f"{word}ෙන් {word}\n") 
                f.write(f"{word}ේ {word}\n") 
                
                # 5. Colloquial variations
                f.write(f"{word}ම {word}\n") # Emphasis 'ma'
                
                count += 5 # Approx suffixes generated per noun
        
        # Add SPECIFIC Fixes for Known Issues (like 'Bus eke')
        f.write("බස් එකේ බස් එක\n")
        f.write("කාර් එක කාර්\n")
        f.write("එකක් එක\n") # Force 'Ekak' -> 'Eka'
        
    print(f"✅ Generated and Cleaned {count} patterns in {output_file}")

if __name__ == "__main__":
    generate_morphology_data()
