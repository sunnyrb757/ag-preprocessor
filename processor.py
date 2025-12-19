import fitz  # pymupdf
import re
import unicodedata
import json
import argparse
import os
import glob
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

class Chapter:
    def __init__(self, config, start_page_idx, end_page_idx=None):
        self.config = config
        self.title = config["title"]
        if config.get("special_type") == "preface":
            self.full_header = "Preface"
        elif config.get("special_type") == "front_matter":
            self.full_header = "Title Page & Table of Contents"
        else:
            self.full_header = f"{config['part']} - {config['num']}. {config['title']}"
        self.start_page_idx = start_page_idx
        self.end_page_idx = end_page_idx
        self.content = []

class PDFPreprocessor:
    def __init__(self, pdf_path, config, output_dir):
        self.doc = fitz.open(pdf_path)
        self.config = config
        self.output_dir = output_dir
        self.filename = os.path.basename(pdf_path)
        self.chapters = []
        
        # Load Settings
        settings = config.get("settings", {})
        self.toc_end_page = settings.get("toc_end_page", 9)
        self.header_margin = settings.get("header_margin", 60)
        self.footer_margin = settings.get("footer_margin", 60)
        self.footnote_size_thresh = settings.get("footnote_size_thresh", 9.0)
        
        self.footnote_count = 0

    def normalize_text(self, text):
        """Standardize text to remove invisible characters/artifacts"""
        # 1. Normalize unicode (NFC -> Canonical Composition to preserve accents)
        text = unicodedata.normalize('NFC', text)
        
        # 2. Explicitly remove common PDF artifacts
        replacements = {
            '\u200b': '',  # Zero-width space
            '\u00ad': '',  # Soft hyphen
            '\u2011': '-', # Non-breaking hyphen
            '\u202f': ' ', # Narrow non-breaking space
            '\u00a0': ' ', # Non-breaking space
            '\uf0b7': '-', # Bullet points (sometimes)
            '\u2013': '-', # En dash
            '\u2014': '-', # Em dash
        }
        for src, dest in replacements.items():
            text = text.replace(src, dest)
            
        # 3. Strip excessive whitespace created by replacements
        return re.sub(r'\s+', ' ', text).strip()

    def find_chapter_start(self, title_fragment, start_search_idx):
        """Scans pages to find the first occurrence of the title fragment"""
        # Normalize title fragment for search (remove punctuation, upper case, normalize space)
        target = re.sub(r'[^\w\s]', '', title_fragment).upper()
        target = re.sub(r'\s+', ' ', target).strip()
        
        for i in range(start_search_idx, len(self.doc)):
            # Get text from page
            text = self.doc[i].get_text("text")
            clean_text = re.sub(r'[^\w\s]', '', text).upper()
            clean_text = re.sub(r'\s+', ' ', clean_text).strip()
            
            # Check match using simplified string
            if target in clean_text:
                return i
        return None

    def find_bibliography_start(self, start_search_idx):
        for i in range(start_search_idx, len(self.doc)):
            text = self.doc[i].get_text("text").upper()
            if "BIBLIOGRAPHY" in text and len(text) < 1000: # Title page usually short-ish or top of page
                return i
        return len(self.doc)

    def locate_chapters(self):
        print(f"[{self.filename}] Locating chapters...")
        current_search_idx = self.toc_end_page
        
        chapter_configs = self.config.get("chapters", [])

        for i, config in enumerate(chapter_configs):
            # Special handling for Front Matter
            if config.get("special_type") == "front_matter":
                self.chapters.append(Chapter(config, 0))
                continue
            
            # Use a distinctive substring of the title
            search_term = config["title"]
            
            # Special handling for potentially "typo'd" titles (can be moved to config later if needed)
            if "TYPES OF MIGRANT" in search_term: 
                search_term = "CATEGORIES OF MIGRATION"

            page_idx = self.find_chapter_start(search_term, current_search_idx)
            
            if page_idx is not None:
                # If finding Preface, ensure we distinguish from TOC
                print(f"  Found '{config.get('num', '')}. {config['title'][:20]}...' at Page {page_idx} (Physical {page_idx+1})")
                
                # Close previous chapter
                if self.chapters:
                    self.chapters[-1].end_page_idx = page_idx
                
                # Create new
                self.chapters.append(Chapter(config, page_idx))
                current_search_idx = page_idx + 1
            else:
                if config["title"] == "Preface":
                    print(f"  [WARN] Could not find Preface. Skipping.")
                else:
                    print(f"  [ERROR] Could not find chapter: {config['title']}")
        
        # Find Bibliography to close the last chapter
        bib_idx = self.find_bibliography_start(current_search_idx)
        print(f"  Found Bibliography at Page {bib_idx} (Physical {bib_idx+1})")
        
        if self.chapters:
            self.chapters[-1].end_page_idx = bib_idx

    def process_page_content(self, page, chapter_context=None):
        blocks = page.get_text("dict")["blocks"]
        clean_text = []
        page_h = page.rect.height
        
        for b in blocks:
            if "lines" not in b: continue
            
            # 1. Spacer Filter
            y0, y1 = b["bbox"][1], b["bbox"][3]
            if y0 < self.header_margin or y1 > (page_h - self.footer_margin):
                continue
            
            block_content = []
            for line in b["lines"]:
                line_text_parts = []
                for span in line["spans"]:
                    # 2. Size Filter
                    if span["size"] < self.footnote_size_thresh:
                        self.footnote_count += 1
                        continue
                    line_text_parts.append(span["text"])
                
                if line_text_parts:
                    full_line = " ".join(line_text_parts).strip()
                    
                    # NORMALIZE HERE
                    full_line = self.normalize_text(full_line)
                    
                    if not full_line: continue

                    # 3. Regex Filter: Isolated Numbers
                    if re.match(r'^[\s-]*\d+[\s-]*$', full_line) or re.match(r'^page\s+\d+$', full_line, re.IGNORECASE):
                        continue
                    
                    # 4. Context Filter: Running Headers
                    if chapter_context:
                        # Check Title
                        if chapter_context.title.lower() in full_line.lower(): 
                             if len(full_line) < len(chapter_context.title) + 10: continue
                        # Check "Chapter X"
                        if f"Chapter {chapter_context.config.get('num', '')}" in full_line: continue

                    block_content.append(full_line)
            
            if block_content:
                clean_text.append(" ".join(block_content))
                
        return "\n\n".join(clean_text)

    def run(self):
        self.locate_chapters()
        
        if not self.chapters:
            print("No chapters found. Aborting.")
            return

        for chap in self.chapters:
            # print(f"Processing {chap.full_header}...")
            # Safety clamp
            end = chap.end_page_idx if chap.end_page_idx else len(self.doc)
            
            for i in range(chap.start_page_idx, end):
                txt = self.process_page_content(self.doc[i], chapter_context=chap)
                if txt: chap.content.append(txt)
        
        # Output filename
        base_name = os.path.splitext(self.filename)[0] + "_cleaned.pdf"
        out_path = os.path.join(self.output_dir, base_name)
        
        print(f"[{self.filename}] Footnotes removed: {self.footnote_count}")
        self.export_pdf(out_path)

    def export_pdf(self, path):
        # Register TrueType Font for Unicode support (Windows path)
        try:
            pdfmetrics.registerFont(TTFont('Arial', 'C:\\Windows\\Fonts\\arial.ttf'))
            font_name = 'Arial'
        except Exception as e:
            print(f"Warning: Could not load Arial font ({e}). Falling back to Helvetica.")
            font_name = 'Helvetica'

        doc = SimpleDocTemplate(path, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        style_h1 = ParagraphStyle('Head1', parent=styles['Heading1'], fontName=font_name, fontSize=16, spaceAfter=20)
        style_body = ParagraphStyle('Body', parent=styles['BodyText'], fontName=font_name, spaceAfter=12, leading=14, fontSize=12)
        style_title = ParagraphStyle('TitleP', parent=styles['Title'], fontName=font_name, fontSize=24, spaceAfter=20, alignment=1) # Center
        style_author = ParagraphStyle('AuthorP', parent=styles['Normal'], fontName=font_name, fontSize=18, spaceAfter=20, alignment=1)
        style_toc = ParagraphStyle('TOC', parent=styles['Normal'], fontName=font_name, fontSize=12, spaceAfter=6)

        metadata = self.config.get("metadata", {})
        title = metadata.get("title", self.filename)
        author = metadata.get("author", "")

        # 1. Page 1: Title Page
        story.append(Spacer(1, 100))
        story.append(Paragraph(title, style_title))
        if author:
            story.append(Spacer(1, 20))
            story.append(Paragraph(author, style_author))
        story.append(PageBreak())

        # 2. Page 2: Table of Contents
        story.append(Paragraph("Table of Contents", style_h1))
        story.append(Spacer(1, 20))
        for chap in self.chapters:
             story.append(Paragraph(chap.full_header, style_toc))
        story.append(PageBreak())

        # 3. Chapters (Narrative)
        for i, chap in enumerate(self.chapters):
            # Add Explicit Header
            story.append(Paragraph(chap.full_header, style_h1))
            story.append(Spacer(1, 10))
            
            full_text = "\n\n".join(chap.content)
            paras = full_text.split('\n\n')
            for p in paras:
                if p.strip():
                    p = p.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    story.append(Paragraph(p, style_body))
            
            if i < len(self.chapters) - 1:
                story.append(PageBreak())
        
        doc.build(story)
        print(f"Exported to {path}")

def load_config_for_file(pdf_filename, config_dir):
    """Finds a matching config file by searching for filename_pattern match"""
    configs = glob.glob(os.path.join(config_dir, "*.json"))
    
    # Priority 1: Exact stem match? (optional, but good practice)
    # Priority 2: Pattern match from within JSON
    
    for cfg_path in configs:
        try:
            with open(cfg_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                pattern = data.get("metadata", {}).get("filename_pattern", "")
                if pattern and pattern in pdf_filename:
                    return data
        except Exception as e:
            print(f"Error reading config {cfg_path}: {e}")
            
    # Priority 3: Default
    default_path = os.path.join(config_dir, "default.json")
    if os.path.exists(default_path):
        with open(default_path, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audiobook PDF Preprocessor")
    parser.add_argument("--input_dir", default="input", help="Directory containing source PDFs")
    parser.add_argument("--output_dir", default="output", help="Directory to save cleaned PDFs")
    parser.add_argument("--config_dir", default="configs", help="Directory containing JSON configs")
    args = parser.parse_args()

    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    pdf_files = glob.glob(os.path.join(args.input_dir, "*.pdf"))
    
    if not pdf_files:
        print(f"No PDF files found in {args.input_dir}")
        exit()
        
    for pdf_path in pdf_files:
        print(f"\n--- Processing {os.path.basename(pdf_path)} ---")
        config = load_config_for_file(os.path.basename(pdf_path), args.config_dir)
        
        if not config:
            print("No matching configuration found. Using default structure.")
            # Could define a minimal default here or skip
            continue
            
        print(f"Using config: {config['metadata'].get('title', 'Unknown')}")
        
        processor = PDFPreprocessor(pdf_path, config, args.output_dir)
        processor.run()
