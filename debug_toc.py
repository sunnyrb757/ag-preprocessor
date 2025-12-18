
import fitz

def debug_toc_layout(path, page_idx):
    doc = fitz.open(path)
    page = doc[page_idx]
    
    print(f"--- Layout Analysis Page {page_idx + 1} ---")
    
    # "words" returns: (x0, y0, x1, y1, "string", block_no, line_no, word_no)
    words = page.get_text("words")
    
    # Sort by Y (vertical), then X (horizontal) to verify reading order
    words.sort(key=lambda w: (round(w[1], 1), w[0]))
    
    # Print first 50 words to check order
    for w in words[:50]:
        print(f"Y={w[1]:.1f} | X={w[0]:.1f} | Text: {w[4]}")

if __name__ == "__main__":
    debug_toc_layout("9780190082277_Print Christianity and Migration (2).pdf", 6)
