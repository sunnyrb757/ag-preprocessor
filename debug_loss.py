
import fitz

def inspect_page(path, page_idx):
    doc = fitz.open(path)
    page = doc[page_idx]
    
    print(f"--- Page {page_idx} (Physical {page_idx+1}) Analysis ---")
    blocks = page.get_text("dict")["blocks"]
    
    for b in blocks:
        if "lines" not in b: continue
        bbox = b["bbox"]
        y0 = bbox[1]
        
        print(f"BLOCK Y={y0:.1f}")
        for line in b["lines"]:
            for span in line["spans"]:
                txt = span["text"].strip()
                if not txt: continue
                print(f"  [{span['size']:.2f}] '{txt}'")

if __name__ == "__main__":
    import sys
    pages = [14, 15]
    if len(sys.argv) > 1:
        pages = [int(p) for p in sys.argv[1:]]
        
    for p in pages:
        inspect_page("input/9780197556689_Print No Justice, No Peace (2).pdf", p)
