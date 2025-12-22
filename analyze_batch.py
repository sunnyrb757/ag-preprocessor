import fitz
import re
import json
import os
import glob

INPUT_DIR = "input"
CONFIG_DIR = "configs"

def analyze_pdf(pdf_path):
    print(f"Analyzing {os.path.basename(pdf_path)}...")
    doc = fitz.open(pdf_path)
    filename = os.path.basename(pdf_path)
    stem = os.path.splitext(filename)[0]
    
    toc_page_idx = -1
    toc_content = []
    
    # 1. Find TOC Page (Scan first 20 pages)
    for i in range(min(20, len(doc))):
        text = doc[i].get_text().upper()
        if "CONTENTS" in text or "TABLE OF CONTENTS" in text:
            # Simple heuristic: must be short-ish title, not in middle of text
            lines = text.split('\n')
            if any(x.strip() in ["CONTENTS", "TABLE OF CONTENTS"] for x in lines[:5]):
                toc_page_idx = i
                print(f"  Found TOC at Page {i}")
                break
    
    if toc_page_idx == -1:
        print("  [WARN] Could not find TOC. Skipping.")
        return None

    # 2. Extract TOC Entries
    # Heuristic: Scan TOC page(s) for lines ending in numbers
    # We'll scan TOC page + next 2 pages just in case it's long
    chapters = []
    
    # Checking TOC structure
    # Usually: "Chapter Title ..... 123"
    
    pages_to_scan = [toc_page_idx]
    if toc_page_idx + 1 < len(doc): pages_to_scan.append(toc_page_idx + 1)
    if toc_page_idx + 2 < len(doc): pages_to_scan.append(toc_page_idx + 2)
    
    # 2. Extract TOC Entries
    # Improved Strategy: Sort all text spans by Y, then grouped into lines
    pages_to_scan = [toc_page_idx]
    if toc_page_idx + 1 < len(doc): pages_to_scan.append(toc_page_idx + 1)
    if toc_page_idx + 2 < len(doc): pages_to_scan.append(toc_page_idx + 2)
    
    all_spans = []
    for p_idx in pages_to_scan:
        page_dict = doc[p_idx].get_text("dict")
        for b in page_dict["blocks"]:
            if "lines" not in b: continue
            for line in b["lines"]:
                for span in line["spans"]:
                    # Store (y0, x0, text, size)
                    all_spans.append({
                        "y": span["bbox"][1],
                        "x": span["bbox"][0],
                        "text": span["text"].strip(),
                        "size": span["size"],
                        "page": p_idx
                    })
    
    # Sort by Page, then Y, then X
    all_spans.sort(key=lambda s: (s["page"], s["y"], s["x"]))
    
    # Group into lines (Tolerance of 5 units for Y)
    lines = []
    if all_spans:
        current_line = [all_spans[0]]
        for span in all_spans[1:]:
            last = current_line[-1]
            if span["page"] == last["page"] and abs(span["y"] - last["y"]) < 5:
                current_line.append(span)
            else:
                lines.append(current_line)
                current_line = [span]
        lines.append(current_line)
    
    raw_lines = []
    for line_spans in lines:
        # Sort spans in line by X
        line_spans.sort(key=lambda s: s["x"])
        full_text = " ".join([s["text"] for s in line_spans]).strip()
        if full_text:
            raw_lines.append(full_text)

    # Parse Lines
    # Regex for "Title ... Num"
    # Matches: "1. Introduction 5", "Chapter 1: The End ... 20"
    entry_regex = re.compile(r'^(.*?)\s+[\.\s]*(\d+)$')
    
    part_context = "Part 1" # Default
    chapter_num = 1
    
    for line in raw_lines:
        line = line.strip()
        # Skip literal "Contents" header
        if "CONTENTS" in line.upper() and len(line) < 20: continue
        
        # Check for Part headers (often don't have page numbers, or separate)
        if re.match(r'^PART\s+[IVX]+', line.upper()) or re.match(r'^PART\s+\d+', line.upper()):
             part_context = line.title()
             continue

        # Check for Ch entry
        match = entry_regex.search(line)
        if match:
            title_part = match.group(1).strip()
            page_num_str = match.group(2)
            
            # Clean title part (remove dots at end)
            title_part = re.sub(r'[\.\s]+$', '', title_part)
            
            # Heuristic: If title is super short or looks like page number, skip
            if len(title_part) < 3: continue
            
            # Special Types
            special_type = None
            if "PREFACE" in title_part.upper(): special_type = "preface"
            if "BIBLIOGRAPHY" in title_part.upper(): continue # Skip bib in config (auto-detected)
            if "INDEX" in title_part.upper(): continue

            chap_config = {
                "part": part_context,
                "num": str(chapter_num),
                "title": title_part,
            }
            if special_type:
                chap_config["special_type"] = special_type
            
            chapters.append(chap_config)
            
            if not special_type:
                chapter_num += 1

    if not chapters:
        print("  [WARN] No chapters extracted from TOC.")
        return None

    # Construct Config
    config = {
        "metadata": {
            "title": stem.replace("_", " "),
            "author": "Unknown",
            "filename_pattern": stem
        },
        "settings": {
            "toc_end_page": toc_page_idx + len(pages_to_scan), # scan offset
            "header_margin": 60,
            "footer_margin": 60,
            "footnote_size_thresh": 9.0
        },
        "chapters": chapters
    }
    
    return config

def main():
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)
        
    pdf_files = glob.glob(os.path.join(INPUT_DIR, "*.pdf"))
    
    for pdf_path in pdf_files:
        # Skip if config exists? No, overwrite for now or checking
        # if "Christianity" in pdf_path: continue # Skip the one we did manually
        
        config = analyze_pdf(pdf_path)
        if config:
            out_name = os.path.basename(pdf_path).replace(".pdf", ".json")
            out_path = os.path.join(CONFIG_DIR, out_name)
            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
            print(f"  Generated config: {out_path}")
            print(f"  Detected {len(config['chapters'])} chapters.")

if __name__ == "__main__":
    main()
