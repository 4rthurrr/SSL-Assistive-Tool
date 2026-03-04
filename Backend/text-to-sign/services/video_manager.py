import os
import random
from concepts import get_label_by_concept

# Dataset lives at Backend/Dataset - Original
# This file is at Backend/text-to-sign/services/video_manager.py
# so we go up two levels from here to reach Backend root.
_HERE = os.path.dirname(os.path.abspath(__file__))   # .../text-to-sign/services
_ROOT = os.path.dirname(os.path.dirname(_HERE))       # .../Backend
DATASET_ROOT = os.path.join(_ROOT, "Dataset - Original")


def find_video_path(concept_id):
    """ 
    Finds the .mp4 video file for a given CONCEPT ID.
    Resolves Concept ID -> Label (English Folder Name) via concepts.py
    
    Args:
        concept_id (str): E.g. "CONCEPT_HOME"
    """
    if not os.path.exists(DATASET_ROOT):
        return None

    # 1. Resolve Label from Concept
    if concept_id.startswith("CONCEPT_"):
        search_key = get_label_by_concept(concept_id)
        if not search_key:
            print(f"❌ Error: Concept '{concept_id}' has no label definition.")
            return None
        print(f"🔍 Resolving: {concept_id} -> '{search_key}'")
    else:
        # Fallback: Treat as direct key if not a Concept ID (Legacy support if needed)
        search_key = concept_id

    # Get all category text folders (Verbs, Nouns, etc.)
    try:
        categories = [d for d in os.listdir(DATASET_ROOT) if os.path.isdir(os.path.join(DATASET_ROOT, d))]
    except OSError as e:
        print(f"❌ Error accessing dataset: {e}")
        return None
    
    # Search strategies
    # Strategy A: Exact Match (Case Insensitive)
    for category in categories:
        category_path = os.path.join(DATASET_ROOT, category)
        try:
            word_folders = os.listdir(category_path)
            for folder in word_folders:
                if folder.lower() == search_key.lower():
                    # Match found!
                    final_folder_path = os.path.join(category_path, folder)
                    
                    # Find video file inside
                    video_files = [f for f in os.listdir(final_folder_path) if f.lower().endswith(('.mp4', '.mov', '.avi', '.mkv'))]
                    
                    if video_files:
                        video_files.sort() # Consistent selection
                        return os.path.join(final_folder_path, video_files[0])
        except OSError:
            continue
            
    return None

