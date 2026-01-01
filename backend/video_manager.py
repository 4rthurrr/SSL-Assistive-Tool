import os
import random

# Dynamically find the dataset path relative to this file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_ROOT = os.path.join(BASE_DIR, "Dataset - Original")

# Folder Name Redirections (Strict Synonyms & Concept Equivalents only)
# Maps: Specific Word -> Available Video Folder Name
FOLDER_MAPPING = {
    # --- PRONOUNS ---
    "We": "Us",
    "Our": "Us",
    "My": "Me",
    "Myself": "Me",
    
    # --- GREETINGS ---
    "Ayubowan": "Hello", 
    "Welcome": "Hello",
    "Hi": "Hello",
    "Greetings": "Hello",
    
    # --- PLACES ---
    "Home": "House", # Concept: Residence
    
    # --- PEOPLE ---
    "Dad": "Father",
    "Mom": "Mother",
    "Mum": "Mother",
    "Bro": "Brother",
    "Sis": "Sister",
    
    # --- ANIMALS ---
    "Puppy": "Dog",
    "Kitten": "Cat",
    
    # --- ADJECTIVES ---
    "Glad": "Happy",
    "Joy": "Happy",
    "Large": "Big",
    "Tiny": "Small",
    "Ill": "Sick",
    "Difficult": "Hard",
    "Quick": "Fast",
    "Correct": "Right",
    "Wrong": "Bad", # Context dependent, but acceptable
}

def find_video_path(word_key):
    """ 
    Finds the .mp4 video file for a given word key.
    Searches recursively in the Dataset - Original directory.
    Handles strict synonyms only.
    """
    if not os.path.exists(DATASET_ROOT):
        # Fallback to hardcoded path if relative fails
        return None

    # 1. Direct Lookup
    search_key = word_key
    
    # 2. Check Mapping
    if word_key in FOLDER_MAPPING:
        search_key = FOLDER_MAPPING[word_key]
        print(f"🔄 Mapping applied: '{word_key}' -> '{search_key}'")

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
