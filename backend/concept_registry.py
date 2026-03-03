
import os
import re

class ConceptRegistry:
    def __init__(self, dataset_root):
        self.dataset_root = dataset_root
        self.concepts = {} # "CONCEPT_RUN": {data}
        self.label_to_concept = {} # "run": "CONCEPT_RUN"
        self._scan_dataset()

    def _scan_dataset(self):
        """
        Recursively scans the dataset root to build the registry.
        Structure: Category / Concept / Files
        """
        if not os.path.exists(self.dataset_root):
            print(f"❌ Dataset root not found: {self.dataset_root}")
            return

        print(f"📂 Scanning Dataset at: {self.dataset_root}")
        
        # Traverse Categories (Verbs, Nouns, etc.)
        for category in os.listdir(self.dataset_root):
            cat_path = os.path.join(self.dataset_root, category)
            if not os.path.isdir(cat_path):
                continue
                
            # Traverse Concepts (Run, Home, etc.)
            for concept_label in os.listdir(cat_path):
                concept_path = os.path.join(cat_path, concept_label)
                if not os.path.isdir(concept_path):
                    continue
                    
                # We have a valid concept folder
                # ID Strategy: CONCEPT_{LABEL_UPPER}
                # Sanitize label for ID
                clean_label = re.sub(r'[^a-zA-Z0-9]', '', concept_label).upper()
                concept_id = f"CONCEPT_{clean_label}"
                
                # Check for assets inside
                assets = [f for f in os.listdir(concept_path) if f.lower().endswith(('.mp4', '.mov', '.avi'))]
                
                if assets:
                    # Pick first asset as representative (or store all)
                    primary_asset = os.path.join(concept_path, assets[0])
                    
                    self.concepts[concept_id] = {
                        "id": concept_id,
                        "label": concept_label, # "Run"
                        "category": category,   # "Verbs"
                        "path": primary_asset,
                        "dir_path": concept_path
                    }
                    self.label_to_concept[concept_label.lower()] = concept_id
                    
        print(f"✅ Registry Built: {len(self.concepts)} concepts found.")

    def get_concept(self, concept_id):
        return self.concepts.get(concept_id)

    def get_all_concepts(self):
        return self.concepts

    def get_concept_by_label(self, label):
        return self.label_to_concept.get(label.lower())

# Singleton Interop
_registry = None

def get_registry():
    global _registry
    if _registry is None:
        # Resolve dataset path relative to this file
        base_dir = os.path.dirname(os.path.abspath(__file__))
        dataset_path = os.path.join(base_dir, "Dataset - Original")
        _registry = ConceptRegistry(dataset_path)
    return _registry
