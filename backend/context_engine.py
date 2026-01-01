"""
Local Context Engine - No External API Required
Handles English to Sinhala translation and text preprocessing locally
"""

from nlp_grammar import sinhala_map

# Build reverse map: English -> Sinhala (for English input support)
english_to_sinhala = {}
for sinhala_word, english_word in sinhala_map.items():
    # Store lowercase English key -> Sinhala word
    eng_lower = english_word.lower()
    if eng_lower not in english_to_sinhala:
        english_to_sinhala[eng_lower] = sinhala_word

# ---------------------------------------------------------
# COMPREHENSIVE SYNONYM MAP
# Maps various English word forms (tenses, synonyms, plurals)
# to the specific Sinhala words supported by our system.
# ---------------------------------------------------------
synonym_map = {
    # --- PRONOUNS & PEOPLE ---
    "i": "මම", "me": "මට", "my": "මගේ", "mine": "මගේ", "myself": "මම",
    "you": "ඔයා", "your": "ඔයාගේ", "yours": "ඔයාගේ", "yourself": "ඔයාම",
    "he": "එයා", "him": "එයා", "his": "එයාගේ", "himself": "එයාම",
    "she": "එයා", "her": "එයා", "hers": "එයාගේ", "herself": "එයාම", # Mapping She to Eya (common usage) or specific words
    "they": "එයාලා", "them": "එයාලා", "their": "එයාලාගේ", "themselves": "එයාලාම",
    "we": "අපි", "us": "අපි", "our": "අපේ", "ours": "අපේ", "ourselves": "අපිම",
    
    "mother": "අම්මා", "mom": "අම්මා", "mum": "අම්මා", "mommy": "අම්මා", "mama": "අම්මා",
    "father": "තාත්තා", "dad": "තාත්තා", "daddy": "තාත්තා", "papa": "තාත්තා", "pop": "තාත්තා",
    "sister": "අක්කා", "sis": "අක්කා", # Defaulting to elder sister if unspecified, or nangi
    "younger sister": "නංගි", "little sister": "නංගි",
    "elder sister": "අක්කා", "big sister": "අක්කා",
    "brother": "අයියා", "bro": "අයියා",
    "younger brother": "මල්ලි", "little brother": "මල්ලි",
    "elder brother": "අයියා", "big brother": "අයියා",
    "grandmother": "ආච්චි", "grandma": "ආච්චි", "granny": "ආච්චි", "nana": "ආච්චි",
    "grandfather": "සීයා", "grandpa": "සීයා", "granddad": "සීයා",
    "husband": "සැමියා", "hubby": "සැමියා",
    "wife": "බිරිඳ", "spouse": "බිරිඳ",
    "uncle": "මාමා",
    "aunt": "නැන්දා", "aunty": "නැන්දා",
    "son": "පුතා", "boy": "පුතා", "male": "පිරිමි",
    "daughter": "දුව", "girl": "දුව", "female": "කාන්තාව",
    "baby": "බිළිඳා", "infant": "බිළිඳා", "toddler": "බිළිඳා",
    "child": "ළමයා", "kid": "ළමයා", "children": "ළමයි", "kids": "ළමයි",
    "friend": "යාළුවා", "friends": "යාළුවෝ", "buddy": "යාළුවා", "mate": "යාළුවා", "pal": "යාළුවා",
    "teacher": "ගුරුතුමා", "professor": "ගුරුතුමා", "lecturer": "ගුරුතුමා", "sir": "සර්", "madam": "මිස්", "miss": "මිස්",
    "student": "ශිෂ්‍යයා", "pupil": "ශිෂ්‍යයා", "learner": "ශිෂ්‍යයා",
    "doctor": "දොස්තර", "physician": "දොස්තර", "medic": "දොස්තර",
    "police": "පොලිස්", "cop": "පොලිස්", "officer": "පොලිස්",
    "thief": "හොරා", "robber": "හොරා", "burglar": "හොරා",
    "man": "මිනිහා", "guy": "මිනිහා", "gentleman": "මිනිහා",
    "woman": "කාන්තාව", "lady": "කාන්තාව",
    "person": "පුද්ගලයා", "people": "මිනිස්සු", "humans": "මිනිස්සු",
    "player": "ක්‍රීඩකයා", "athlete": "ක්‍රීඩකයා",

    # --- VERBS (Present, Continuous, Past) ---
    "eat": "කනවා", "eating": "කනවා", "eats": "කනවා", "ate": "කෑවා", "eaten": "කෑවා", "consume": "කනවා",
    "drink": "බොනවා", "drinking": "බොනවා", "drinks": "බොනවා", "drank": "බිව්වා", "drunk": "බිව්වා", "sip": "බොනවා",
    "go": "යනවා", "going": "යනවා", "goes": "යනවා", "went": "ගියා", "gone": "ගියා", "leave": "යනවා", "depart": "යනවා",
    "come": "එනවා", "coming": "එනවා", "comes": "එනවා", "came": "ආවා", "arrive": "එනවා",
    "run": "දුවනවා", "running": "දුවනවා", "runs": "දුවනවා", "ran": "දිව්වා", "jog": "දුවනවා", "sprint": "දුවනවා",
    "walk": "ඇවිදිනවා", "walking": "ඇවිදිනවා", "walks": "ඇවිදිනවා", "walked": "ඇවිද්දා", "stroll": "ඇවිදිනවා",
    "play": "සෙල්ලම් කරනවා", "playing": "සෙල්ලම් කරනවා", "plays": "සෙල්ලම් කරනවා", "played": "සෙල්ලම් කළා",
    "sleep": "නිදා ගන්නවා", "sleeping": "නිදා ගන්නවා", "sleeps": "නිදා ගන්නවා", "slept": "නිදා ගත්තා", "nap": "නිදා ගන්නවා",
    "study": "පාඩම් කරනවා", "studying": "පාඩම් කරනවා", "studies": "පාඩම් කරනවා", "studied": "පාඩම් කළා", "learn": "පාඩම් කරනවා",
    "read": "කියවනවා", "reading": "කියවනවා", "reads": "කියවනවා",
    "write": "ලියනවා", "writing": "ලියනවා", "writes": "ලියනවා", "wrote": "ලිව්වා", "written": "ලිව්වා",
    "watch": "බලනවා", "watching": "බලනවා", "watches": "බලනවා", "watched": "බැලුවා", "look": "බලනවා",
    "see": "දකිනවා", "seeing": "දකිනවා", "sees": "දකිනවා", "saw": "දැක්කා", "seen": "දැක්කා", "view": "දකිනවා",
    "hear": "ඇහෙනවා", "hearing": "ඇහෙනවා", "hears": "ඇහෙනවා", "heard": "ඇහුනා", "listen": "අහනවා", "listening": "අහනවා",
    "speak": "කතා කරනවා", "speaking": "කතා කරනවා", "speaks": "කතා කරනවා", "spoke": "කතා කළා", "spoken": "කතා කළා",
    "talk": "කතා කරනවා", "talking": "කතා කරනවා", "talks": "කතා කරනවා", "talked": "කතා කළා", "chat": "කතා කරනවා",
    "think": "හිතනවා", "thinking": "හිතනවා", "thinks": "හිතනවා", "thought": "හිතුවා", "guess": "හිතනවා",
    "tell": "කියනවා", "telling": "කියනවා", "tells": "කියනවා", "told": "කිව්වා", "say": "කියනවා", "said": "කිව්වා",
    "cook": "උයනවා", "cooking": "උයනවා", "cooks": "උයනවා", "cooked": "ඉව්වා", "prepare": "උයනවා",
    "dance": "නටනවා", "dancing": "නටනවා", "dances": "නටනවා", "danced": "නැටුවා",
    "jump": "පනිනවා", "jumping": "පනිනවා", "jumps": "පනිනවා", "jumped": "පැන්නා", "hop": "පනිනවා",
    "sit": "වාඩි වෙනවා", "sitting": "වාඩි වෙනවා", "sits": "වාඩි වෙනවා", "sat": "වාඩි වුනා", "seat": "වාඩි වෙනවා",
    "stand": "නැගිටිනවා", "standing": "නැගිටිනවා", "stands": "නැගිටිනවා", "stood": "නැගිට්ටා", "rise": "නැගිටිනවා", "get up": "නැගිටිනවා",
    "swim": "පීනනවා", "swimming": "පීනනවා", "swims": "පීනනවා", "swam": "පීනුවා",
    "teach": "උගන්වනවා", "teaching": "උගන්වනවා", "teaches": "උගන්වනවා", "taught": "ඉගැන්නුවා", "educate": "උගන්වනවා",
    "help": "උදව් කරනවා", "helping": "උදව් කරනවා", "helps": "උදව් කරනවා", "helped": "උදව් කළා", "assist": "උදව් කරනවා", "support": "උදව් කරනවා",
    "love": "ආදරෙයි", "loving": "ආදරෙයි", "loves": "ආදරෙයි", "loved": "ආදරෙයි", "adore": "ආදරෙයි",
    "like": "කැමතියි", "liking": "කැමතියි", "likes": "කැමතියි", "liked": "කැමතියි", "enjoy": "කැමතියි",
    "want": "ඕන", "wants": "ඕන", "wanted": "ඕන", "desire": "ඕන",
    "need": "ඕන", "needs": "ඕන", "needed": "ඕන", "require": "ඕන",
    "give": "දෙනවා", "giving": "දෙනවා", "gives": "දෙනවා", "gave": "දුන්නා", "given": "දුන්නා", "offer": "දෙනවා",
    "take": "ගන්නවා", "taking": "ගන්නවා", "takes": "ගන්නවා", "took": "ගත්තා", "taken": "ගත්තා", "grab": "ගන්නවා",
    "buy": "ගන්නවා", "buying": "ගන්නවා", "buys": "ගන්නවා", "bought": "ගත්තා", "purchase": "ගන්නවා",
    "sell": "විකුණනවා", "selling": "විකුණනවා", "sells": "විකුණනවා", "sold": "විකුනුවා",
    "make": "හදනවා", "making": "හදනවා", "makes": "හදනවා", "made": "හැදුවා", "create": "හදනවා", "build": "හදනවා",
    "open": "අරිනවා", "opening": "අරිනවා", "opens": "අරිනවා", "opened": "ඇරියා", "unlock": "අරිනවා",
    "close": "වහනවා", "closing": "වහනවා", "closes": "වහනවා", "closed": "වැහුවා", "shut": "වහනවා",
    "wash": "සෝදනවා", "washing": "සෝදනවා", "washes": "සෝදනවා", "washed": "සේදුවා", "clean": "සෝදනවා",
    "bathe": "නානවා", "bathing": "නානවා", "bathes": "නානවා", "bathed": "නෑවා", "shower": "නානවා",
    "cry": "අඬනවා", "crying": "අඬනවා", "cries": "අඬනවා", "cried": "අඬුවා", "weep": "අඬනවා",
    "laugh": "හිනාවෙනවා", "laughing": "හිනාවෙනවා", "laughs": "හිනාවෙනවා", "laughed": "හිනා වුනා", "giggle": "හිනාවෙනවා",
    "smile": "හිනා වෙනවා", "smiling": "හිනා වෙනවා", "smiles": "හිනා වෙනවා", "smiled": "හිනා වුනා", "grin": "හිනා වෙනවා",
    "fight": "රණ්ඩු වෙනවා", "fighting": "රණ්ඩු වෙනවා", "fights": "රණ්ඩු වෙනවා", "fought": "රණ්ඩු වුනා", "argue": "රණ්ඩු වෙනවා",
    "draw": "අඳිනවා", "drawing": "අඳිනවා", "draws": "අඳිනවා", "drew": "ඇන්දා", "sketch": "අඳිනවා",
    "cut": "කපනවා", "cutting": "කපනවා", "cuts": "කපනවා", "chop": "කපනවා", "slice": "කපනවා",
    "bring": "ගෙනෙනවා", "bringing": "ගෙනෙනවා", "brings": "ගෙනෙනවා", "brought": "ගෙනාවා", "fetch": "ගෙනෙනවා",
    "carry": "ගෙනියනවා", "carrying": "ගෙනියනවා", "carries": "ගෙනියනවා", "carried": "ගෙනිච්චා", "transport": "ගෙනියනවා",
    "break": "කඩනවා", "breaking": "කඩනවා", "breaks": "කඩනවා", "broke": "කැඩුවා", "broken": "කැඩුවා", "smash": "කඩනවා",
    "boil": "තම්බනවා", "boiling": "තම්බනවා", "boils": "තම්බනවා", "boiled": "තැම්බුවා",
    "understand": "තේරෙනවා", "understanding": "තේරෙනවා", "understood": "තේරුනා", "comprehend": "තේරෙනවා", "know": "මම දන්නවා",
    "feel": "දැනෙනවා", "feeling": "දැනෙනවා", "feels": "දැනෙනවා", "felt": "දැනුනා", "sense": "දැනෙනවා",
    "wear": "අඳිනවා", "wearing": "අඳිනවා", "wore": "ඇන්දා", # Adinawa can be Draw or Wear? Used Draw previously but usually Adinawa is wear too.
    "put": "දානවා", "putting": "දානවා", "puts": "දානවා", "put": "දැම්මා", "place": "දානවා",
    "stop": "නවත්වන්න", "stopping": "නවත්වන්න", "stops": "නවත්වන්න", "stopped": "නැවැත්තුවා", "halt": "නවත්වන්න", "pause": "නවත්වන්න",
    "scald": "පුච්චනවා", "burn": "පුච්චනවා",
    "scratch": "කසනවා", "scratching": "කසනවා", "scratched": "කැසුවා", "itch": "කසනවා",
    "call": "කතා කරනවා", "phone": "කතා කරනවා", # Context specific
    "work": "වැඩ කරනවා", "working": "වැඩ කරනවා", "works": "වැඩ කරනවා", "worked": "වැඩ කළා", "job": "වැඩ",

    # --- TIME & DATE ---
    "today": "අද",
    "tomorrow": "හෙට",
    "yesterday": "ඊයේ",
    "now": "දැන්", "currently": "දැන්", "presently": "දැන්",
    "morning": "උදේ", "am": "උදේ",
    "evening": "සවස", "afternoon": "සවස", "pm": "සවස",
    "night": "රාත්‍රිය", "tonight": "රාත්‍රිය",
    "day": "දවස", "days": "දවස",
    "week": "සතිය", "weeks": "සතිය",
    "month": "මාසය", "months": "මාස",
    "year": "අවුරුද්ද", "years": "අවුරුද්ද",
    "time": "කාලය", "hour": "පැය", "minute": "විනාඩි", "second": "තත්පර",
    "monday": "සඳුදා", "mon": "සඳුදා",
    "tuesday": "අඟහරුවාදා", "tue": "අඟහරුවාදා",
    "wednesday": "බදාදා", "wed": "බදාදා",
    "thursday": "බ්‍රහස්පතින්දා", "thu": "බ්‍රහස්පතින්දා",
    "friday": "සිකුරාදා", "fri": "සිකුරාදා",
    "saturday": "සෙනසුරාදා", "sat": "සෙනසුරාදා",
    "sunday": "ඉරිදා", "sun": "ඉරිදා",
    "january": "ජනවාරි", "jan": "ජනවාරි",
    "february": "පෙබරවාරි", "feb": "පෙබරවාරි",
    "march": "මාර්තු", "mar": "මාර්තු",
    "april": "අප්‍රේල්", "apr": "අප්‍රේල්",
    "may": "මැයි",
    "june": "ජූනි", "jun": "ජූනි",
    "july": "ජූලි", "jul": "ජූලි",
    "august": "අගෝස්තු", "aug": "අගෝස්තු",
    "september": "සැප්තැම්බර්", "sep": "සැප්තැම්බර්",
    "october": "ඔක්තෝබර්", "oct": "ඔක්තෝබර්",
    "november": "නොවැම්බර්", "nov": "නොවැම්බර්",
    "december": "දෙසැම්බර්", "dec": "දෙසැම්බර්",

    # --- ANIMALS ---
    "dog": "බල්ලා", "puppy": "බල්ලා", "canine": "බල්ලා",
    "cat": "පූසා", "kitten": "පූසා", "kitty": "පූසා", "feline": "පූසා",
    "bird": "කුරුල්ලා", "birds": "කුරුල්ලෝ", "parrot": "කුරුල්ලා",
    "fish": "මාළුවා", "fishes": "මාළු",
    "lion": "සිංහයා", "lions": "සිංහයෝ",
    "elephant": "අලියා", "elephants": "අලි", "tusker": "අලියා",
    "monkey": "වඳුරා", "monkeys": "වඳුරෝ", "ape": "වඳුරා",
    "rabbit": "හාවා", "rabbits": "හාවෝ", "bunny": "හාවා", "hare": "හාවා",
    "snake": "නයා", "snakes": "නයින්", "serpent": "නයා", "cobra": "නයා",
    "cow": "එළදෙන", "cows": "එළදෙනුන්", "cattle": "එළ හරකා", "bull": "එළ හරකා",
    "crocodile": "කිඹුලා", "alligator": "කිඹුලා",
    "tortoise": "ඉබ්බා", "turtle": "ඉබ්බා",
    "squirrel": "ලේනා",
    
    # --- PLACES ---
    "home": "ගෙදර", "house": "ගෙදර", "residence": "ගෙදර", "apartment": "ගෙදර",
    "school": "පාසල", "college": "පාසල", "university": "පාසල", "campus": "පාසල",
    "hospital": "රෝහල", "clinic": "රෝහල", "dispensary": "රෝහල",
    "shop": "කඩේ", "store": "කඩේ", "market": "කඩේ", "supermarket": "කඩේ", "mall": "කඩේ",
    "temple": "පන්සල",
    "church": "පල්ලිය", "chapel": "පල්ලිය",
    "bank": "බැංකුව",
    "road": "පාර", "street": "වීදිය", "highway": "පාර", "way": "පාර", "path": "මාර්ගය",
    "police station": "පොලිසිය",
    "station": "දුම්රිය ස්ථානය", "railway": "දුම්රිය ස්ථානය",
    "airport": "ගුවන් තොටුපල",
    "bus stop": "බස් නැවතුම", "bus stand": "බස් නැවතුම",
    "garden": "වත්ත", "park": "වත්ත",
    "room": "කාමරය",

    # --- FOOD & OBJECTS ---
    "food": "කෑම", "meal": "කෑම", "dish": "කෑම",
    "rice": "බත්",
    "water": "වතුර", "liquid": "වතුර",
    "tea": "තේ",
    "milk": "කිරි",
    "carrot": "කැරට්",
    "bread": "පාන්",
    "fruit": "පලතුරු",
    "vegetable": "එළවළු",
    "book": "පොත", "books": "පොත්", "novel": "පොත",
    "pen": "පෑන", "pens": "පෑන්",
    "pencil": "පැන්සල",
    "bag": "බෑගය", "backpack": "බෑගය",
    "phone": "ෆෝන් එක", "telephone": "දුරකථනය", "mobile": "ෆෝන් එක",
    "computer": "පරිගණකය", "pc": "පරිගණකය", "laptop": "ලැප්ටොප් එක",
    "car": "කාර් එක", "vehicle": "වාහනය", "auto": "කාර් එක",
    "bus": "බස් එක",
    "train": "කෝච්චිය",
    "bicycle": "බයිසිකලය", "bike": "බයිසිකලය", "cycle": "බයිසිකලය",
    "motorcycle": "මෝටර් සයිකලය", "motorbike": "මෝටර් සයිකලය",
    "plane": "ප්ලේන් එක", "airplane": "ප්ලේන් එක", "flight": "ප්ලේන් එක",
    "boat": "බෝට්ටුව", "ship": "බෝට්ටුව",
    "table": "මේසය", "desk": "මේසය",
    "chair": "පුටුව", "seat": "පුටුව",
    "bed": "ඇඳ",
    "door": "දොර", "gate": "දොර",
    "window": "ජනේලය",
    "tree": "ගස", "plant": "ගස",
    "flower": "මල", "blossom": "මල",
    "sun": "හිරු",
    "moon": "හඳ",
    "ball": "බෝලය",
    "cup": "කෝප්පය", "mug": "කෝප්පය",
    "plate": "පීරිසිය", "dish": "පීරිසිය",
    "spoon": "හැන්ද",
    "knife": "පිහිය",

    # --- BODY PARTS ---
    "head": "ඔළුව",
    "hand": "අත", "hands": "අත", "arm": "අත",
    "leg": "කකුල", "legs": "කකුල", "foot": "කකුල", "feet": "කකුල",
    "eye": "ඇස", "eyes": "ඇස්",
    "ear": "කන", "ears": "කන",
    "nose": "නහය",
    "mouth": "කට", "lips": "කට",
    "tooth": "දත්", "teeth": "දත්",
    "hair": "කොණ්ඩය",
    "stomach": "බඩ", "belly": "බඩ", "tummy": "බඩ",
    "face": "මුහුණ",

    # --- ADJECTIVES & ADVERBS ---
    "good": "හොඳ", "fine": "හොඳ", "nice": "ලස්සන", "great": "හොඳ", "excellent": "හොඳ",
    "bad": "නරක", "terrible": "නරක", "awful": "නරක",
    "big": "ලොකු", "large": "ලොකු", "huge": "ලොකු",
    "small": "පොඩි", "tiny": "පොඩි", "little": "පොඩි",
    "happy": "සතුටුයි", "joy": "සතුට", "glad": "සතුටුයි",
    "sad": "දුකයි", "unhappy": "දුකයි", "sorrow": "දුක",
    "beautiful": "ලස්සන", "pretty": "ලස්සන", "lovely": "ලස්සන",
    "ugly": "කැත",
    "fast": "වේගවත්", "quick": "වේගවත්", "rapid": "වේගවත්",
    "slow": "සෙමින්",
    "hot": "උණුසුම්",
    "cold": "සීතල", "cool": "සීතල",
    "new": "අලුත්",
    "old": "පරණ", # inanimate
    "young": "තරුණ",
    "rich": "පොහොසත්", "wealthy": "පොහොසත්",
    "poor": "දුප්පත්",
    "clean": "පිරිසිදු",
    "dirty": "කිහිරි", # or use negation
    "hungry": "බඩගිනි",
    "thirsty": "තිබහයි",
    "tired": "මහන්සියි",
    "sick": "අසනීප", "ill": "අසනීප",
    "strong": "ශක්තිමත්",
    "weak": "දුර්වල",
    "easy": "ලේසියි",
    "hard": "අමාරු", "difficult": "අමාරු",
    "red": "රතු",
    "blue": "නිල්",
    "green": "කොළ",
    "yellow": "කහ",
    "black": "කලු",
    "white": "සුදු",
    "orange": "තැඹිලි",
    "pink": "රෝස",
    "purple": "දම්",
    "brown": "දුඹුරු",
    
    # --- COMMON PHRASES & PARTICLES ---
    "yes": "ඔව්", "yeah": "ඔව්", "yep": "ඔව්", "ok": "හරි", "okay": "හරි",
    "no": "නෑ", "nope": "නෑ", "not": "නෑ",
    "hello": "හායි", "hi": "හායි", "hey": "හායි", "greetings": "ආයුබෝවන්",
    "thank you": "ස්තූතියි", "thanks": "ස්තූතියි",
    "please": "කරුණාකර",
    "sorry": "සමාවෙන්න", "apologize": "සමාවෙන්න",
    "bye": "බායි", "goodbye": "බායි",
    "how": "කොහොමද",
    "what": "මොකක්ද",
    "where": "කොහෙද",
    "when": "කවද්ද",
    "why": "ඇයි",
    "who": "කවුද",
    "with": "සමග", # Might not be in backend but good for stripping
    "and": "සහ",
    "to": "ට",
    "in": "තුල",
    "on": "මත",
    "for": "සඳහා",
    "of": "ගේ",
}

# Merge synonym_map into english_to_sinhala (Priority given to synonym_map overrides)
for eng, sin in synonym_map.items():
    english_to_sinhala[eng] = sin


def is_sinhala(text):
    """Check if text contains Sinhala characters"""
    for char in text:
        if '\u0D80' <= char <= '\u0DFF':
            return True
    return False


def translate_english_to_sinhala(text):
    """
    Translates English text to Sinhala using local dictionary.
    Returns Sinhala sentence that can be processed by NLP grammar.
    """
    # Normalize text: lowercase
    text_lower = text.lower()
    
    # Handle multi-word phrases first (greedy matching)
    # This is a simple phrase replacer
    phrases = {
        "good morning": "සුබ උදෑසනක්",
        "good night": "සුබ රාත්‍රියක්",
        "good evening": "සුබ සැන්දෑවක්",
        "how are you": "කොහොමද",
        "thank you": "ස්තූතියි",
        "bus stop": "බස් නැවතුම",
        "bus stand": "බස් නැවතුම",
        "train station": "දුම්රිය ස්ථානය",
        "police station": "පොලිසිය",
        "i know": "මම දන්නවා",
        "don't know": "දන්නේ නෑ",
        "dont know": "දන්නේ නෑ",
    }
    
    for phrase, replacement in phrases.items():
        if phrase in text_lower:
            text_lower = text_lower.replace(phrase, replacement)
            
    words = text_lower.split()
    translated_words = []
    
    for word in words:
        # Remove punctuation
        clean_word = word.strip('.,!?;:\'\"()[]{}')
        
        # Check dictionary
        if clean_word in english_to_sinhala:
            translated_words.append(english_to_sinhala[clean_word])
        else:
            # If word is not found, try stemming (remove 's', 'ing', 'ed')
            # Very basic stemmer fallback
            root = clean_word
            if clean_word.endswith('s') and clean_word[:-1] in english_to_sinhala:
                translated_words.append(english_to_sinhala[clean_word[:-1]])
            elif clean_word.endswith('ing') and clean_word[:-3] in english_to_sinhala:
                translated_words.append(english_to_sinhala[clean_word[:-3]])
            elif clean_word.endswith('ed') and clean_word[:-2] in english_to_sinhala:
                translated_words.append(english_to_sinhala[clean_word[:-2]])
            else:
                # Keep original if truly not found
                translated_words.append(clean_word)
    
    return ' '.join(translated_words)


def process_input(user_text):
    """
    LOCAL Context Engine - Comprehensive Dictionary Version
    """
    if not user_text or not user_text.strip():
        return user_text
    
    text = user_text.strip()
    
    # Check if input is already Sinhala
    if is_sinhala(text):
        print(f"DEBUG [LOCAL]: Input is Sinhala, passing through: '{text}'")
        return text
    
    # Input is English - translate to Sinhala
    translated = translate_english_to_sinhala(text)
    print(f"DEBUG [LOCAL]: English '{text}' -> Sinhala '{translated}'")
    
    return translated


# For backward compatibility
def get_available_vocabulary():
    """Returns a string list of available Sinhala words from the grammar map."""
    return ", ".join(sinhala_map.keys())
