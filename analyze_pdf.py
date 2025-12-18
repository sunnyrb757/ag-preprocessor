
import fitz  # pymupdf

pdf_path = "9780190082277_Print Christianity and Migration (2).pdf"

def analyze_pdf(path):
    doc = fitz.open(path)
    
    print(f"File: {path}")
    print(f"Pages: {len(doc)}")
    
    # 1. Inspect TOC
    print("\n--- Table of Contents ---")
    toc = doc.get_toc()
    for level, title, page in toc:
        print(f"{'  ' * (level-1)}- {title} (p. {page})")
        
    if not toc:
        print("NO TOC FOUND!")

    # 2. Inspect Sample Page (e.g., page 20 or first chapter start)
    sample_page_num = toc[0][2] - 1 if toc and toc[0][2] > 0 else 10
    if sample_page_num < 0 or sample_page_num >= len(doc):
        sample_page_num = 0
        
    page = doc[sample_page_num]
    print(f"\n--- Analysis of Page {sample_page_num + 1} ---")
    
    # Text Analysis
    text_blocks = page.get_text("dict")["blocks"]
    print(f"Number of blocks: {len(text_blocks)}")
    
    for i, block in enumerate(text_blocks):
        if block["type"] == 0: # text
            for line in block["lines"]:
                for span in line["spans"]:
                    # Print span details to help identify footnotes/superscripts
                    print(f"Size: {span['size']:.2f} | Flags: {span['flags']} | Font: {span['font']} | Text: {span['text'][:50]}...")
        if i > 5: # Limit output
            print("... (truncating blocks) ...")
            break

if __name__ == "__main__":
    analyze_pdf(pdf_path)
