
import fitz

CHAPTERS = [
    ("CHRISTIAN THEOLOGY IN THE AGE OF MIGRATION", "1"),
    ("HUMAN MOBILITY AND GLOBAL MIGRATIONS", "2"),
    ("CATEGORIES OF MIGRATION AND TYPES OF MIGRANT", "3"), # "MIGRANT S" might be typo, generic search
    ("RELIGION(S) AND MIGRATION", "4"),
    ("MIGRATION AND THE SHAPING OF WORLD CHRISTIANITY", "5"),
    ("GOD THE FATHER, THE PRIMORDIAL MIGRANT", "6"),
    ("A CHRISTOLOGY FOR OUR AGE OF MIGRATION", "7"),
    ("THE HOLY SPIRIT, THE POWER OF MIGRATION", "8"),
    ("CHRISTIANITY AS AN INSTITUTIONAL MIGRANT", "9"),
    ("WORSHIP AND POPULAR DEVOTIONS", "10"),
    ("THE ETHICS OF MUTUAL HOSPITALITY", "11"),
    ("HOME LAND, FOREIGN LAND, OUR LAND", "12"),
    ("MIGRATION AND MEMORY", "13"),
    ("PEOPLE ON THE MOVE", "14"), # Epilogue usually? User numbered it 14.
]

def locate_chapters(path):
    doc = fitz.open(path)
    print(f"Scanning {len(doc)} pages...")
    
    found_count = 0
    
    for i in range(len(doc)):
        text = doc[i].get_text()
        # Simple verify
        
        for title, num in CHAPTERS:
            # We look for the Title in parsed text
            # To be robust, we normalize spaces
            clean_page = " ".join(text.split()).upper()
            if title in clean_page:
                # Heuristic: Check if font size is large? 
                # For now just check presence.
                print(f"Match: Ch {num} '{title[:20]}...' on Page {i+1} (Index {i})")
                # We don't break because a title might appear in TOC/Preface too.
                # We need the *first* occurrence after the TOC (Page 7).
                
if __name__ == "__main__":
    locate_chapters("9780190082277_Print Christianity and Migration (2).pdf")
