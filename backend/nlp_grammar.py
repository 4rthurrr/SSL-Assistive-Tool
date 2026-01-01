from sinling import SinhalaTokenizer, SinhalaStemmer

# --- 1. සිංහල -> ඉංග්‍රීසි මැප් එක (Your Dataset Keys) ---
# වම් පැත්තේ සිංහල වචන, දකුණු පැත්තේ ඔබේ Folder Names
    # --- Complete Sinhala -> English Dataset Mapping ---
sinhala_map = {
    # --- TIME & DAYS (කාලය) ---
    "හෙට": "Tomorrow", "ඊයේ": "Yesterday", "අද": "Today", "දැන්": "Now",
    "උදේ": "Morning", "උදෑසන": "Morning", "රාත්‍රිය": "Night", "රෑ": "Night",
    "සවස": "Evening", "හවස": "Evening", "තත්පර": "Seconds", "විනාඩි": "Minutes", "පැය": "Hour",
    "සතිය": "Week", "මාසය": "Month", "අවුරුද්ද": "Year", "කාලය": "Time", "දවස": "Day", "දින": "Day",
    "අනිද්දා": "Day after tomorrow", "වෙලාව": "Time",
    "සඳුදා": "Monday", "අඟහරුවාදා": "Tuesday", "බදාදා": "Wednesday", "බ්‍රහස්පතින්දා": "Thursday",
    "සිකුරාදා": "Friday", "සෙනසුරාදා": "Saturday", "ඉරිදා": "Sunday",
    "සුබ උදෑසනක්": "Good morning", "සුබ රාත්‍රියක්": "Good night", "සුබ සැන්දෑවක්": "Good evening",

    # --- VERBS (ක්‍රියා පද) ---
    "වැඩ කරනවා": "Work", "වැඩ": "Work",
    "ලියනවා": "Write", "ලියන්න": "Write", "ලිව්වා": "Write",
    "බලනවා": "Watch", "බලන්න": "Watch", "බැලුවා": "Watch", "පේනවා": "See", "දැක්කා": "See", "Watch": "Watch",
    "සෝදනවා": "Wash", "සෝදන්න": "Wash", "සේදුවා": "Wash",
    "ඇවිදිනවා": "Walk", "ඇවිදින්න": "Walk", "ඇවිද්දා": "Walk",
    "ඕන": "Want", "අවශ්‍යයි": "Want", "ඕනේ": "Want",
    "තේරෙනවා": "Understand", "තේරුම් ගන්න": "Understand", "තේරුනා": "Understand", "තේරුණා": "Understand",
    "විශ්වාස කරනවා": "Trust", "විශ්වාස": "Trust",
    "පාවිච්චි කරනවා": "Use", "භාවිතා කරනවා": "Use", "භාවිතා": "Use",
    "විසි කරනවා": "Throw", "විසි කරන්න": "Throw", "විසි කළා": "Throw",
    "පණිවිඩය": "Text", "මැසේජ් කරනවා": "Text", "මැසේජ්": "Text",
    "හිතනවා": "Think", "හිතන්න": "Think", "හිතුවා": "Think",
    "කියනවා": "Tell", "කියන්න": "Tell", "කිව්වා": "Tell",
    "යනවා": "Visit", "Visit": "Visit", # Note: 'Go' is mapped below specifically
    "ඉරනවා": "Tear", "ඉරන්න": "Tear", "ඉරුවා": "Tear",
    "කතා කරනවා": "Talk", "කතා කරන්න": "Talk", "කතා කළා": "Talk", "කතා": "Talk",
    "නවත්වන්න": "Stop", "නවතින්න": "Stop", "නැවැත්තුවා": "Stop",
    "පීනනවා": "Swim", "පීනන්න": "Swim", "පීනුවා": "Swim",
    "උගන්වනවා": "Teach", "උගන්වන්න": "Teach", "ඉගැන්නුවා": "Teach",
    "ගන්නවා": "Take", "ගන්න": "Take", "ගත්තා": "Take", "Buy": "Buy", "මිලදී ගන්නවා": "Buy", "මිලදී ගත්තා": "Buy",
    "හිනා වෙනවා": "Smile", "හිනා": "Smile", "Smile": "Smile", "හිනාවෙනවා": "Laugh", "හිනා වුනා": "Laugh",
    "අතු ගානවා": "Sweep", "අතු ගාන්න": "Sweep", "අතු ගෑවා": "Sweep",
    "නිදා ගන්නවා": "Sleep", "නිදාගන්න": "Sleep", "නිදාගන්නවා": "Sleep", "නිදා ගත්තා": "Sleep", "බුදියනවා": "Sleep",
    "පාඩම් කරනවා": "Study", "පාඩම් කරන්න": "Study", "පාඩම් කළා": "Study",
    "පෙන්වනවා": "Show", "පෙන්වන්න": "Show", "පෙන්නුවා": "Show",
    "තෝරනවා": "Select", "තෝරන්න": "Select", "තේරුවා": "Select", "තෝරාගන්නවා": "Select", "Choose": "Choose",
    "දකිනවා": "See", "දකින්න": "See",
    "වාඩි වෙනවා": "Sit", "ඉඳගන්න": "Sit", "වාඩි වුනා": "Sit", "වාඩිවෙනවා": "Sit", "වාඩිවෙන්න": "Sit",
    "විකුණනවා": "Sell", "විකුණන්න": "Sell", "විකුනුවා": "Sell",
    "හොයනවා": "Search", "හොයන්න": "Search", "හෙව්වා": "Search",
    "ඉක්මනට": "Quickly", "වේගයෙන්": "Quickly", "වේගවත්": "Fast",
    "කසනවා": "Scratch", "කසන්න": "Scratch", "කැසුවා": "Scratch",
    "දුවනවා": "Run", "දුවන්න": "Run", "දිව්වා": "Run",
    "දානවා": "Put", "දාන්න": "Put", "දැම්මා": "Put",
    "අදිනවා": "Pull", "අදින්න": "Pull", "ඇද්දා": "Pull",
    "ඇණවුම් කරනවා": "Order", "ඇණවුම් කරන්න": "Order", "ඇණවුම් කළා": "Order",
    "සෙල්ලම් කරනවා": "Play", "සෙල්ලම් කරන්න": "Play", "සෙල්ලම් කළා": "Play", "සෙල්ලම්": "Play", "Play": "Play",
    "චූ කරනවා": "Peeing", "චූ කරන්න": "Peeing",
    "හමුවෙනවා": "Meet", "හමුවෙන්න": "Meet", "හමු වුනා": "Meet",
    "අරිනවා": "Open", "විවෘත කරනවා": "Open", "ඇරියා": "Open",
    "හදනවා": "Make", "හදන්න": "Make", "හැදුවා": "Make",
    "ආදරෙයි": "Love", "ආදරය": "Love", "ආදරය කරනවා": "Love",
    "අහනවා": "Listen", "අහන්න": "Listen", "ඇහුවා": "Listen", "ඇහුම්කන් දෙනවා": "Listen",
    "ඉඩ දෙනවා": "Let", "ඉඩ දෙන්න": "Let", "Allow": "Allow",
    "කැමතියි": "Like", "කැමති": "Like",
    "මඟ පෙන්වනවා": "Lead", "Guide": "Guide",
    "තට්ටු කරනවා": "Knock", "තට්ටු කරන්න": "Knock", "තට්ටු කළා": "Knock",
    "ගහනවා": "Hit", "ගහන්න": "Hit", "ගැහුවා": "Hit",
    "මම දන්නවා": "I know", "දන්නවා": "I know",
    "කොහොමද": "How",
    "පනිනවා": "Jump", "පනින්න": "Jump", "පැන්නා": "Jump",
    "උදව්": "Help", "උදව් කරනවා": "Help", "උදව් කරන්න": "Help", "උදව් කළා": "Help", "Help": "Help",
    "එල්ලනවා": "Hang", "එල්ලන්න": "Hang", "එල්ලුවා": "Hang",
    "දෙනවා": "Give", "දෙන්න": "Give", "දුන්නා": "Give",
    "යනවා": "Go", "යන්න": "Go", "ගියා": "Go", "යමු": "Go", "යන්නම්": "Go",
    "නැගිටිනවා": "Get up", "නැගිටින්න": "Get up", "නැගිට්ටා": "Get up",
    "අනුගමනය කරනවා": "Follow", "අනුගමනය කරන්න": "Follow", "අනුගමනය කළා": "Follow",
    "ඇහෙනවා": "Hear", "ඇහුනා": "Hear",
    "දැනෙනවා": "Feel", "දැනුනා": "Feel",
    "රණ්ඩු වෙනවා": "Fight", "රණ්ඩු වෙන්න": "Fight", "රණ්ඩු වුනා": "Fight",
    "මාරු කරනවා": "Exchange", "මාරු කරන්න": "Exchange", "මාරු කළා": "Exchange",
    "ඇතුල් වෙනවා": "Enter", "ඇතුල් වෙන්න": "Enter", "ඇතුල් වුනා": "Enter",
    "මකනවා": "Erase", "මකන්න": "Erase", "මැකුවා": "Erase",
    "කනවා": "Eat", "කෑවා": "Eat", "කන්න": "Eat", "කමු": "Eat",
    "බොනවා": "Drink", "බිව්වා": "Drink", "බොන්න": "Drink", "බොමු": "Drink",
    "නටනවා": "Dance", "නටන්න": "Dance", "නැටුවා": "Dance",
    "ඉවරයි": "Done", "ඉවර": "Done",
    "කපනවා": "Cut", "කපන්න": "Cut", "කැපුවා": "Cut",
    "අඳිනවා": "Draw", "අඳින්න": "Draw", "ඇන්දා": "Draw",
    "අඬනවා": "Cry", "අඬන්න": "Cry", "අඬුවා": "Cry",
    "වහනවා": "Cover", "වහන්න": "Cover", "වැහුවා": "Cover",
    "පිටපත් කරනවා": "Copy", "පිටපත් කරන්න": "Copy", "පිටපත් කළා": "Copy",
    "කහිනවා": "Cough", "කහින්න": "Cough", "කැස්සා": "Cough",
    "ක්ලික් කරනවා": "Click", "ක්ලික් කරන්න": "Click", "ක්ලික් කළා": "Click",
    "උයනවා": "Cook", "උයන්න": "Cook", "ඉව්වා": "Cook",
    "සම්බන්ධ කරනවා": "Connect", "සම්බන්ධ කරන්න": "Connect", "සම්බන්ධ කළා": "Connect",
    "වෙනස් කරනවා": "Change", "වෙනස් කරන්න": "Change", "වෙනස් කළා": "Change",
    "එනවා": "Come", "එන්න": "Come", "ආවා": "Come", "එමු": "Come", "එන්නම්": "Come",
    "ගෙනියනවා": "Carry", "ගෙනියන්න": "Carry", "ගෙනිච්චා": "Carry",
    "ගෙනෙනවා": "Bring", "ගෙනෙන්න": "Bring", "ගෙනාවා": "Bring",
    "කඩනවා": "Break", "කඩන්න": "Break", "කැඩුවා": "Break",
    "තම්බනවා": "Boil", "තම්බන්න": "Boil", "තැම්බුවා": "Boil",
    "නානවා": "Bathe", "නාන්න": "Bathe", "නෑවා": "Bathe", "සිරුර සෝදනවා": "Bathe",
    "කියවනවා": "Read", "කියවන්න": "Read", "පාඩම් කරනවා": "Study", "ඉගෙනගන්න": "Study",
    "ලියනවා": "Write", "ලියන්න": "Write", "ලිව්වා": "Write", "ලියවන්න": "Write",
    "බලනවා": "Watch", "බලන්න": "Watch", "බැලුවා": "Watch", "නරඹන්න": "Watch", "පේනවා": "See", "දැක්කා": "See", "දකිනවා": "See", "Watch": "Watch",
    "සෝදනවා": "Wash", "සෝදන්න": "Wash", "සේදුවා": "Wash",
    "ඇවිදිනවා": "Walk", "ඇවිදින්න": "Walk", "ඇවිද්දා": "Walk", "ගමන් කරනවා": "Walk",
    "වැඩ කරනවා": "Work", "වැඩ": "Work", "රැකියාව කරනවා": "Work",
    "කතා කරනවා": "Talk", "කතා කරන්න": "Talk", " කියන්න": "Talk", "කතා": "Talk", "Speak": "Talk", "Say": "Talk",


    # --- VEHICLES (වාහන) ---
    "වාහනය": "Vehicle", "වාහනේ": "Vehicle", "වාහන": "Vehicle",
    "වෑන් එක": "Van", "වෑන්": "Van", "වෑන් රථය": "Van",
    "කෝච්චිය": "Train", "දුම්රිය": "Train", "කෝච්චි": "Train",
    "ප්ලේන් එක": "Plane", "ගුවන් යානය": "Plane", "ප්ලේන්": "Plane",
    "ටයර් එක": "Tire", "ටයර්": "Tire", "රෝදය": "Tire",
    "මෝටර් සයිකලය": "Motorcycle", "මෝටර් සයිකල්": "Motorcycle", "බයික් එක": "Motorcycle",
    "කාර් එක": "Car", "කාර්": "Car", "කාර් රථය": "Car",
    "බස් එක": "Bus", "බස්": "Bus", "බස් රථය": "Bus",
    "බෝට්ටුව": "Boat", "බෝට්ටු": "Boat",
    "බයිසිකලය": "Bicycle", "බයිසිකල්": "Bicycle", "පාපැදිය": "Bicycle",

    # --- PREPOSITIONS (නිපාත) ---
    "උඩ": "Up", "ඉහළ": "Up",
    "ට": "To", "වෙත": "To",
    "වෙනකම්": "Until", "තුරු": "Until",
    "වඩා": "Than",
    "උඩින්": "Over",
    "එළියෙ": "Out", "පිටත": "Out",
    "මත": "On",
    "ඇතුලේ": "Inside", "ඇතුළත": "Inside",
    "ළඟ": "Near", "අසල": "Near",
    "වටේ": "Around", "වටා": "Around",
    "තුල": "In",
    "පස්සේ": "After", "පසුව": "After",

    # --- PLACES (ස්ථාන) ---
    "දුම්රිය ස්ථානය": "Train station", "ස්ටේෂන් එක": "Train station", "දුම්රියපොළ": "Train station",
    "කඩේ": "Shop", "කඩ": "Shop", "වෙළඳසැල": "Shop", "සාප්පුව": "Shop",
    "පන්සල": "Temple", "පන්සල්": "Temple", "ආරාමය": "Temple",
    "පාර": "Road", "මාර්ගය": "Road", "වීදිය": "Street",
    "පොලිසිය": "Police station", "පොලිස් ස්ථානය": "Police station",
    "අල්ලපු ගෙදර": "Next door",
    "ස්ථානය": "Location", "තැන": "Location",
    "ගෙදර": "House", "නිවස": "House", "ගේ": "House", "ගෙවල්": "House", "Home": "House", "ගෙය": "House",
    "පාසල": "School", "ඉස්කෝලේ": "School", "විදුහල": "School",
    "රෝහල": "Hospital", "ඉස්පිරිතාලෙ": "Hospital", "හොස්පිට්ල්": "Hospital", "සුවසෙවන": "Hospital",
    "පල්ලිය": "Church", "පල්ලි": "Church",
    "බැංකුව": "Bank", "බැංකු": "Bank",
    "බස් නැවතුම": "Bus station", "බස් ස්ටෑන්ඩ් එක": "Bus station",
    "ගුවන් තොටුපල": "Airport", "එයාර්පෝට්": "Airport",

    # --- MONTHS (මාස) ---
    "අවුරුද්ද": "Year",
    "සැප්තැම්බර්": "September",
    "ඔක්තෝබර්": "October",
    "මැයි": "May",
    "මාසය": "Month", "මාස": "Months",
    "නොවැම්බර්": "November",
    "මාර්තු": "March",
    "පෙබරවාරි": "February",
    "අගෝස්තු": "August",
    "ජූලි": "July",
    "දෙසැම්බර්": "December",
    "ජනවාරි": "January",
    "ජූනි": "June",
    "අප්‍රේල්": "April",

    # --- PEOPLE (පුද්ගලයින්) ---
    "මිනිස්සු": "People", "ජනතාව": "People",
    "බිරිඳ": "Wife", "නෝනා": "Wife", "වයිෆ්": "Wife", "භාර්යාව": "Wife",
    "නංගි": "Younger sister", "නංගී": "Younger sister", "නංගියේ": "Younger sister",
    "මල්ලි": "Younger bro", "මල්ලී": "Younger bro", "මල්ලියේ": "Younger bro",
    "අපි": "Us", "අපිට": "Us", "අපේ": "Our",
    "මාමා": "Uncle", "මාමේ": "Uncle",
    "හොරා": "Thief",
    "සහෝදරිය": "Sister",
    "පුතා": "Son", "පුතේ": "Son", "පිරිමි ළමයා": "Son",
    "නෑනා": "Sister in law",
    "නෑදෑයෝ": "Relations",
    "මිනිහා": "Man", "පිරිමි": "Man", "පුද්ගලයා": "Man",
    "ක්‍රීඩකයා": "Player",
    "අම්මා": "Mother", "අම්මේ": "Mother", "අම්ම": "Mother", "මව": "Mother", "මෑණියන්": "Mother",
    "ඇය": "She", "ඇයව": "She",
    "කාන්තාව": "Lady", "ගෑණු": "Lady", "වනිතාව": "Lady",
    "පොලිස්": "Police", "රාළහාමි": "Police",
    "සැමියා": "Husband", "මහත්තයා": "Husband",
    "ආච්චි": "Grand mother", "ආච්චී": "Grand mother", "කිරි අම්මා": "Grand mother", "ආච්චියේ": "Grand mother",
    "මුනුපුරා": "Grand son",
    "සීය": "Grand father", "සීයා": "Grand father", "සීයේ": "Grand father", "මුත්තා": "Grand father",
    "තාත්තා": "Father", "තාත්තේ": "Father", "තාත්ත": "Father", "පියා": "Father", "අප්පච්චි": "Father", "තාත්තාම": "Father", "තාත්තාගේ": "Father",
    "පවුල": "Family",
    "අක්කා": "Elder sister", "අක්කේ": "Elder sister", "අක්ක": "Elder sister",
    "දොස්තර": "Doctor", "වෛද්‍යවරයා": "Doctor",
    "පවුල්": "Families",
    "අයියා": "Elder bro", "අයියේ": "Elder bro", "අයිය": "Elder bro",
    "දුව": "Daughter", "දුවේ": "Daughter", "පැංචි": "Daughter",
    "ළමයා": "Child", "බබා": "Child", "දරුවා": "Child", "පොඩ්ඩා": "Child",
    "මස්සිනා": "Brother in law",
    "සහෝදරයා": "Bro",
    "බිළිඳා": "Baby",
    "නැන්දා": "Aunt", "නැන්දේ": "Aunt",
    "මම": "I", "මට": "I", "මා": "I", "මාව": "I",
    "ගුරුවරයා": "Teacher", "ගුරුතුමා": "Teacher", "සර්": "Teacher", "ගුරුවරිය": "Teacher", "ගුරුතුමී": "Teacher", "මිස්": "Teacher", "ගුරුමිය": "Teacher",
    "ඔයා": "You", "ඔබ": "You", "තමුසේ": "You", "ඔහේ": "You",
    "එයා": "He", "ඔහු": "He", "ඔහුව": "He",
    "එයාලා": "They", "ඔවුන්": "They", "ඒගොල්ලෝ": "They",
    "කාගෙද": "Whose", "කාටද": "Whom", "කවුද": "Who", "කව්ද": "Who",

    # --- NUMBERS (ඉලක්කම්) ---
    "අඩු කිරීම": "Subtraction",
    "ගුණ කිරීම": "Multiplication",
    "සමානයි": "Equal",
    "ගණන් කරනවා": "Count", "ගණන් කරන්න": "Count",
    "බෙදීම": "Divide",
    "හත": "7. seven", "7": "7. seven",
    "නවය": "9. nine", "9": "9. nine",
    "එකතු කිරීම": "Addition",
    "අට": "8. eight", "8": "8. eight",
    "පහ": "5. five", "5": "5. five",
    "හය": "6. six", "6": "6. six",
    "විස්ස": "20. twenty", "20": "20. twenty",
    "හතර": "4. four", "4": "4. four",
    "දෙක": "2. two", "2": "2. two",
    "දහඅට": "18. eighteen", "18": "18. eighteen",
    "තුන": "3. three", "3": "3. three",
    "දහනවය": "19. nineteen", "19": "19. nineteen",
    "දහහත": "17. seventeen", "17": "17. seventeen",
    "දහසය": "16. sixteen", "16": "16. sixteen",
    "පහළොව": "15. fifteen", "15": "15. fifteen",
    "දහහතර": "14. fourteen", "14": "14. fourteen",
    "දහතුන": "13. thirteen", "13": "13. thirteen",
    "දොළහ": "12. twelve", "12": "12. twelve",
    "එකොළහ": "11. eleven", "11": "11. eleven",
    "එක": "1. one", "1": "1. one",
    "දහය": "10. ten", "10": "10. ten",

    # --- NOUNS & OBJECTS ---
    "ජනේලය": "Window", "ජනෙල්": "Window",
    "කාලගුණය": "Weather",
    "දුරකථනය": "Telephone", "ටෙලිෆෝන්": "Telephone",
    "තාක්ෂණය": "Technology",
    "කණ්ඩායම": "Team", "Group": "Group",
    "ගස": "Tree", "ගහ": "Tree", "ගස්": "Tree",
    "තේ": "Tea",
    "මේසය": "Table", "මේස": "Table",
    "ඇඳුම": "Suit",
    "ව්‍යුහය": "Structure",
    "වීදිය": "Street",
    "ෂර්ට් එක": "Shirt", "කමිසය": "Shirt",
    "ලේනා": "Squirrel",
    "සමාජය": "Society",
    "සිංදුව": "Song", "ගීතය": "Song",
    "සංඥා භාෂාව": "Sign language",
    "ලකුණ": "Sign", "Point": "Point",
    "සාරිය": "Saree",
    "සාය": "Skirt",
    "වැලි": "Sand",
    "මුද්ද": "Ring",
    "ප්‍රශ්නය": "Problem",
    "රේඩියෝව": "Radio",
    "සාක්කුව": "Pocket",
    "පැන්සල": "Pencil",
    "මාර්ගය": "Path",
    "ෆෝන් එක": "Phone", "ජංගම දුරකථනය": "Phone", "Cell phone": "Cell phone",
    "සාමය": "Peace",
    "කොටස": "Part",
    "තීන්ත": "Paint",
    "හරි": "Ok", "හොඳයි": "Ok",
    "කිසිවක් නැත": "None",
    "මගේ": "My",
    "ජාලය": "Network",
    "චිත්‍රපටිය": "Movie", "ෆිල්ම් එක": "Movie",
    "සල්ලි": "Money", "මුදල්": "Money",
    "හඳ": "Moon", "චන්ද්‍රයා": "Moon",
    "මනස": "Mind",
    "කිරි": "Milk",
    "මැද": "Middle",
    "ලැප්ටොප් එක": "Laptop", "ලැප්ටොප්": "Laptop",
    "අගුල": "Lock",
    "යතුර": "Key",
    "ලැයිස්තුව": "List",
    "අන්තර්ජාලය": "Internet", "ඉන්ටර්නෙට්": "Internet",
    "බලපෑම": "Impact",
    "කීයද": "How much",
    "සෞඛ්‍යය": "Health",
    "කොච්චරද": "How many",
    "කන්ද": "Hill",
    "තොප්පිය": "Hat",
    "තුවක්කුව": "Gun",
    "කෑම": "Food", "ආහාර": "Food",
    "මල": "Flower", "මල්": "Flower",
    "ඇස්": "Eyes",
    "මුහුණ": "Face",
    "උණ": "Fever",
    "අලියා": "Elephant", "අලි": "Elephant", "අලියෙක්": "Elephant",
    "ඇස": "Eye",
    "සංස්කෘතිය": "Culture",
    "දොර": "Door", "දොරවල්": "Door",
    "කිඹුලා": "Crocodile", "කිඹුලෝ": "Crocodile", "කිඹුලෙක්": "Crocodile",
    "පරිගණකය": "Computer", "කොම්පියුටරය": "Computer",
    "එළදෙන": "Cow", "එළ හරකා": "Cow", "එළදෙනුන්": "Cow",
    "ඇඳුම්": "Clothing",
    "ළමයි": "Children",
    "තේරීම": "Choice",
    "දාමය": "Chain", "මාලය": "Chain",
    "විදුලි පංකාව": "Ceiling fan", "ෆෑන් එක": "Ceiling fan",
    "පූසා": "Cat", "බළලා": "Cat", "පූසෝ": "Cat", "පූසෙක්": "Cat",
    "කාඩ් එක": "Card",
    "කැමරාව": "Camera",
    "පොත": "Book", "පොත්": "Book",
    "ඇඳ": "Bed",
    "ලිපිය": "Article",
    "බෑගය": "Bag", "බෑග් එක": "Bag",
    "ඔළුව": "Head", "අත": "Hand", "කකුල": "Leg", "කන": "Ear", "නහය": "Nose", "කට": "Mouth",
    "දත්": "Teeth", "බඩ": "Stomach", "කොණ්ඩය": "Hair",
    "පෑන": "Pen", "ගුරුතුමා": "Teacher", "ගුරුතුමී": "Teacher", "සර්": "Teacher", "මිස්": "Teacher",
    "ශිෂ්‍යයා": "Student", "ඩෙස්ක් එක": "Desk", "පුටුව": "Chair", "පුටු": "Chair",
    "පෑන්": "Pen",
    "පීරිසිය": "Plate", "පිඟාන": "Plate", "කෝප්පය": "Cup", "හැන්ද": "Spoon", "පිහිය": "Knife",
    "බත්": "Rice",
    "වතුර": "Water", "ජලය": "Water", "පානීය ජලය": "Water",
    "බෙහෙත්": "Medicine", "ඖෂධ": "Medicine",
    "පොත": "Book", "පොත්": "Book", "ග්‍රන්ථය": "Book",
    "බල්ලා": "Dog", "බල්ලෝ": "Dog",
    "කුරුල්ලා": "Bird", "කුරුල්ලෝ": "Bird",
    "මාළුවා": "Fish", "මාළු": "Fish",
    "සිංහයා": "Lion", "සිංහයෝ": "Lion",
    "වඳුරා": "Monkey", "වඳුරෝ": "Monkey",
    "හාවා": "Rabbit", "හාවෝ": "Rabbit", "හාවෙක්": "Rabbit",
    "නයා": "Snake", "නයින්": "Snake",
    "ඉබ්බා": "Tortoise",
    "කැරට්": "Carrot",
    "යාළුවා": "Friend", "යාළුවෝ": "Friend", "යාළුවෙ": "Friend", "මිතුරේ": "Friend",
    "බෙදාගෙන": "Share",

    # --- INTERJECTION & DETERMINER & CONJUNCTION ---
    "ඔව්": "Yes",
    "නෑ": "No", "නැහැ": "No", "එපා": "No", "නෑ": "No",
    "හෝ": "Or", "නැත්නම්": "Or",

    # --- ADJECTIVES (විශේෂණ) ---
    "කැත": "Ugly",
    "වැරදි": "Wrong",
    "තද": "Tight",
    "සාදරයෙන් පිළිගනිමු": "Welcome",
    "තිබහයි": "Thirsty", "තිබහ": "Thirsty",
    "ශක්තිමත්": "Strong",
    "මෘදු": "Soft",
    "ජ්‍යෙෂ්ඨ": "Senior",
    "එකම": "Same",
    "පොහොසත්": "Rich", "සල්ලි තියෙන": "Rich",
    "වර්තමාන": "Present", 
    "ඉක්මන්": "Quick",
    "පොඩි": "Small", "පුංචි": "Small",
    "පරණ": "Old", "වයසක": "Old",
    "ධනාත්මක": "Positive",
    "අතීත": "Past",
    "ලස්සන": "Nice", "Beautiful": "Beautiful",
    "හොඳ නෑ": "Not good",
    "ඊළඟ": "Next",
    "බුරුල්": "Loose",
    "අඩු": "Low", "Less": "Less",
    "ස්වාධීන": "Independent",
    "උස": "High",
    "නිරෝගී": "Healthy",
    "අමාරු": "Hard", "Difficult": "Difficult",
    "සතුටුයි": "Happy", "සතුට": "Happy", "සන්තෝසයි": "Happy",
    "දුක": "Sad", "කණගාටු": "Sad", "දුකයි": "Sad",
    "බය": "Fear", "භය": "Fear",
    "තරහයි": "Angry", "කේන්තිය": "Angry", "කෝපය": "Angry",
    "ආදරෙයි": "Love", "ආදරය": "Love", "ආදරය කරනවා": "Love", "කැමතියි": "Like", 
    "මහන්සි": "Tired", "කලුගැට": "Tired",
    "පිරුණු": "Full",
    "ඩබල්": "Double",
    "හොඳ": "Good", "හොඳයි": "Good",
    "නොමිලේ": "Free",
    "වේගවත්": "Fast", "වේගයෙන්": "Fast",
    "මහත": "Fat",
    "ගැඹුරු": "Deep",
    "වෙනස්": "Different",
    "බිහිරි": "Deaf",
    "පරිස්සමින්": "Careful",
    "සීතල": "Cold",
    "නරක": "Bad",

    # --- ADVERBS & QUESTIONS (ක්‍රියා විශේෂණ / ප්‍රශ්න) ---
    "ඇයි": "Why", "හේතුව මොකද්ද": "Why",
    "කොහෙද": "Where", "කොයි තැන": "Where",
    "කවද්ද": "When",
    "මොකද්ද": "What", "මොනවද": "What",
    "කවදාවත්": "Never",
    "කැමති නෑ": "Not like (dislike)",
    "මෙහෙ": "Here", "මෙතන": "Here",
    "වෙනුවට": "Instead",
    "දන්නේ නෑ": "Dont know",
    "පැහැදිලිව": "Clearly",
    "බෑ": "Cant", "බැහැ": "Cant",
    "එපා": "Dont",
    "පුළුවන්": "Can",
    "තවද": "Also",
    "නැවත": "Again",

    # --- COLORS (පාට) ---
    "රතු": "Red", "නිල්": "Blue", "කොළ": "Green", "කහ": "Yellow", "කලු": "Black", "සුදු": "White",
    "තැඹිලි": "Orange", "රෝස": "Pink", "දම්": "Purple", "දුඹුරු": "Brown",
    "පාට": "Color", "වර්ණ": "Color",
    "රත්තරන්": "Gold",
    "අළු": "Grey", "අළු පාට": "Grey",

    # --- GREETINGS ---
    "ස්තූතියි": "Thank you",
    "කොහොමද": "How are you", "සැප සනීප": "How are you",
    "හායි": "Hello",
    "ආයුබෝවන්": "Ayubowan",
    "හරි": "Alright"
}


# අතීත කාලය හඟවන වචන (Past Tense Markers)
past_tense_indicators = ["ගියා", "කෑවා", "බිව්වා", "දිව්වා", "බැලුවා", "දුන්නා", "ආවා", "කළා", "ලිව්වා", "සේදුවා", "ඇවිද්දා", "විසි කළා", "හිතුවා", "කිව්වා", "ඉරුවා", "කතා කළා", "නැවැත්තුවා", "පීනුවා", "ඉගැන්නුවා", "ගත්තා", "හිනා වුනා", "අතු ගෑවා", "නිදා ගත්තා", "පාඩම් කළා", "පෙන්නුවා", "තේරුවා", "දැක්කා", "වාඩි වුනා", "විකුනුවා", "හෙව්වා", "කැසුවා", "දැම්මා", "ඇද්දා", "ඇණවුම් කළා", "සෙල්ලම් කළා", "හමු වුනා", "ඇරියා", "හැදුවා", "ඇහුවා", "තට්ටු කළා", "ගැහුවා", "පැන්නා", "උදව් කළා", "එල්ලුවා", "නැගිට්ටා", "අනුගමනය කළා", "ඇහුනා", "දැනුනා", "රණ්ඩු වුනා", "මාරු කළා", "ඇතුල් වුනා", "මැකුවා", "නැටුවා", "කැපුවා", "ඇන්දා", "අඬුවා", "වැහුවා", "පිටපත් කළා", "කැස්සා", "ක්ලික් කළා", "ඉව්වා", "සම්බන්ධ කළා", "වෙනස් කළා", "ගෙනිච්චා", "ගෙනාවා", "මිලදී ගත්තා", "කැඩුවා", "තැම්බුවා", "නෑවා"]

# Initialize Stemmer
stemmer = SinhalaStemmer()

# Pre-compute stem map for performance (optional but good)
# This maps the STEM of a key to the VALUE
stem_map = {}
for k, v in sinhala_map.items():
    try:
        s = stemmer.stem(k)[0]
        if s not in stem_map: # Keep first occurrence or handle collisions?
            stem_map[s] = v
    except:
        pass

# --- Reverse Map for Display (English -> Sinhala) ---
# We want the 'canonical' (first) Sinhala word for each English key
reverse_sinhala_map = {}
for k, v in sinhala_map.items():
    if v not in reverse_sinhala_map:
        reverse_sinhala_map[v] = k

# Manual overrides for special logic words if needed
reverse_sinhala_map["Done"] = "ඉවරයි"
reverse_sinhala_map["No"] = "නෑ"
reverse_sinhala_map["I"] = "මම" # Ensure "I" is mapped to "මම" distinctly if needed

def find_best_match(word):
    # 1. Exact match
    if word in sinhala_map:
        return sinhala_map[word]
        
    # 1.5 Check if word is already a valid English Key (Fallback)
    # This handles cases where translation returns English or user inputs English
    if word in sinhala_map.values():
        return word
    
    # 2. Stem match
    try:
        stem = stemmer.stem(word)[0]
        if stem in stem_map:
            return stem_map[stem]
    except:
        pass
        
    return None

def process_single_sentence(tokens):
    """Processes a single list of tokens (one sentence) and returns SVO ordered list."""
    ssl_sequence = []
    time_word = None
    verb_words = []
    is_past = False
    is_negative = False
    
    # All Verbs List for Grammar Check
    verbs_list = [
        "Work", "Write", "Watch", "Wash", "Walk", "Want", "Understand", "Trust", "Use", "Throw", 
        "Text", "Think", "Tell", "Visit", "Tear", "Talk", "Stop", "Swim", "Teach", "Take", 
        "Smile", "Sweep", "Sleep", "Study", "Show", "Select", "See", "Sit", "Sell", "Search", 
        "Scratch", "Run", "Put", "Pull", "Order", "Play", "Peeing", "Meet", "Open", "Look", 
        "Make", "Love", "Listen", "Let", "Like", "Lead", "Laugh", "Knock", "Hit", "Know", 
        "Jump", "Help", "Guide", "Go", "Give", "Hang", "Get up", "Follow", "Hear", "Feel", 
        "Fight", "Exchange", "Enter", "Erase", "Eat", "Drink", "Dance", "Done", "Cut", 
        "Draw", "Cry", "Cover", "Copy", "Cough", "Click", "Cook", "Connect", "Change", 
        "Come", "Carry", "Choose", "Bring", "Buy", "Break", "Boil", "Bathe", "Allow", "Can", "Cant", "Dont know"
    ]

    # All Time Words List
    time_list = [
        "Tomorrow", "Yesterday", "Today", "Now", "Morning", "Night", 
        "October", "September", "May", "November", "March", "June", 
        "January", "July", "February", "December", "August", "April", "Year", "Month"
    ]

    for word in tokens:
        # 1. අතීත කාලයද බලනවා
        if word in past_tense_indicators:
            is_past = True
        # 2. නැත/එපා (Negation) ද බලනවා
        if word in ["නැහැ", "එපා", "නෑ", "නැත"]:
            is_negative = True
            continue # මෙය අන්තිමට එකතු කරන්න ඕන
            
        # 3. වචනය Map එකේ තියෙනවද බලනවා (Smart Lookup)
        mapped_key = find_best_match(word)
        
        if mapped_key:
            # A. කාලය (Time) නම් මුලට ගන්න variable එකක තියාගන්නවා
            if mapped_key in time_list:
                time_word = mapped_key
            
            # B. ක්‍රියා පදය (Verb) නම් අගට ගන්න
            elif mapped_key in verbs_list:
                verb_words.append(mapped_key)
    
            # C. අනිත් වචන (Nouns/Subject/Object) කෙලින්ම ලිස්ට් එකට
            else:
                ssl_sequence.append(mapped_key)
    
    # --- SSL වාක්‍ය ගොඩනැගීම (Reordering) ---
    final_list = []

    if time_word:
        final_list.append(time_word)
        
    # Rule 2: කර්තෘ (Subject) - First noun in the sequence
    if ssl_sequence:
        final_list.append(ssl_sequence[0]) # Subject
    
    # Rule 3: කර්මය (Objects) - Remaining nouns (Now comes BEFORE Verb - SOV)
    if len(ssl_sequence) > 1:
        final_list.extend(ssl_sequence[1:]) # Objects

    # Rule 4: ක්‍රියා පදය (Verb) - Now comes LAST (SOV)
    if verb_words:
        final_list.extend(verb_words)

    # Rule 5: අතීත කාල නම් 'Done' එකතු කිරීම
    if is_past:
        final_list.append("Done")
        
    # Rule 6: විරුද්ධ පදයක් නම් 'No' එකතු කිරීම
    if is_negative:
        final_list.append("No")
        
    return final_list

def get_ssl_sequence(text):
    tokenizer = SinhalaTokenizer()
    
    # Split by period AND comma to handle multiple clauses
    # Treat commas as sentence breaks for SSL grammar purposes
    formatted_text = text.replace(".", " . ").replace(",", " . ")
    sentences = formatted_text.split(".")
    
    combined_sequence = []
    
    for sentence in sentences:
        if not sentence.strip():
            continue
            
        tokens = tokenizer.tokenize(sentence)
        sentence_sequence = process_single_sentence(tokens)
        combined_sequence.extend(sentence_sequence)
        
    return combined_sequence

def get_ssl_display_sequence(english_sequence):
    """
    Converts a sequence of English keys (e.g. ['I', 'House', 'Go', 'Done'])
    back to Sinhala words for display (e.g. ['මම', 'ගෙදර', 'යනවා', 'ඉවරයි']).
    """
    display_sequence = []
    for word in english_sequence:
        # Try to find in reverse map, otherwise keep original (fallback)
        sinhala_word = reverse_sinhala_map.get(word, word)
        display_sequence.append(sinhala_word)
    return display_sequence