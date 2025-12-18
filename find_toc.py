
import fitz

def find_toc_page(path):
    doc = fitz.open(path)
    print(f"Total Pages: {len(doc)}")
    
    # Scan first 20 pages for "Contents" keyword
    for i in range(20):
        if i >= len(doc): break
        text = doc[i].get_text().lower()
        if "contents" in text or "table of contents" in text:
            print(f"Found 'Contents' keyword on Page {i+1} (Index {i})")
            print("-" * 20)
            print(doc[i].get_text()[:500]) # Print first 500 chars
            print("-" * 20)

if __name__ == "__main__":
    find_toc_page("9780190082277_Print Christianity and Migration (2).pdf")
