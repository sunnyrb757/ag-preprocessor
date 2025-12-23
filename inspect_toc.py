import fitz  # pymupdf
import sys

def inspect_toc(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        print(f"Opened {pdf_path}")
        print(f"Total pages: {len(doc)}")
        
        # Get TOC
        toc = doc.get_toc()
        
        with open("pdf_text_dump.txt", "w", encoding="utf-8") as f:
            if toc:
                f.write("Metadata TOC found:\n")
                for level, title, page in toc:
                    f.write(f"Level {level}: {title} (Page {page})\n")
            else:
                f.write("No Metadata TOC found.\n")

            ranges = [
                (0, 20),    # Preface (7), Ch 1 (9), Ch 2 (16)
                (25, 30),   # Ch 3 (28)
                (50, 60),   # Ch 4 (55)
                (85, 95),   # Ch 5 (89)
                (120, 130), # Ch 6 (124)
                (150, 155), # Ch 7 (152)
                (175, 180), # Ch 8 (177)
                (200, 210), # Ch 9 (204)
                (215, 250)  # Ch 10 (220), Ch 11 (235), Ch 12 (246)
            ]
            
            for start, end in ranges:
                f.write(f"\n--- Pages {start}-{end} Text ---\n")
                for i in range(start, min(end, len(doc))):
                    try:
                        page = doc[i]
                        text = page.get_text()
                        f.write(f"\n--- Page {i+1} ---\n")
                        f.write(text)
                    except Exception as e:
                        f.write(f"\nError reading page {i+1}: {e}\n")
                    
        print("Done. Check pdf_text_dump.txt")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    pdf_path = r"c:\Users\smallick\.gemini\antigravity\scratch\audiobook_preprocessor\input\9780197797082_Print The American Child (1.5).pdf"
    inspect_toc(pdf_path)
