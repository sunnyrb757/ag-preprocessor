
import fitz  # pymupdf
import re
import unicodedata
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Configuration
CHAPTER_CONFIG = [
    # Preface
    {"part": "Front", "num": "0", "title": "Preface", "special_type": "preface"},
    # Part 1
    {"part": "Part 1", "num": "1", "title": "CHRISTIAN THEOLOGY IN THE AGE OF MIGRATION"},
    {"part": "Part 1", "num": "2", "title": "HUMAN MOBILITY AND GLOBAL MIGRATIONS"},
    {"part": "Part 1", "num": "3", "title": "CATEGORIES OF MIGRATION AND TYPES OF MIGRANT"},
    {"part": "Part 1", "num": "4", "title": "RELIGION(S) AND MIGRATION"},
    {"part": "Part 1", "num": "5", "title": "MIGRATION AND THE SHAPING OF WORLD CHRISTIANITY"},
    # Part 2
    {"part": "Part 2", "num": "6", "title": "GOD THE FATHER, THE PRIMORDIAL MIGRANT"},
    {"part": "Part 2", "num": "7", "title": "A CHRISTOLOGY FOR OUR AGE OF MIGRATION"},
    {"part": "Part 2", "num": "8", "title": "THE HOLY SPIRIT, THE POWER OF MIGRATION"},
    {"part": "Part 2", "num": "9", "title": "CHRISTIANITY AS AN INSTITUTIONAL MIGRANT"},
    {"part": "Part 2", "num": "10", "title": "WORSHIP AND POPULAR DEVOTIONS"},
    {"part": "Part 2", "num": "11", "title": "THE ETHICS OF MUTUAL HOSPITALITY"},
    {"part": "Part 2", "num": "12", "title": "HOME LAND, FOREIGN LAND, OUR LAND"},
    {"part": "Part 2", "num": "13", "title": "MIGRATION AND MEMORY"},
    {"part": "Part 2", "num": "14", "title": "EPILOGUE: PEOPLE ON THE MOVE"},
]

class Chapter:
    def __init__(self, config, start_page_idx, end_page_idx=None):
        self.config = config
        self.title = config["title"]
        if config.get("special_type") == "preface":
            self.full_header = "Preface"
        else:
            self.full_header = f"{config['part']} - {config['num']}. {config['title']}"
        self.start_page_idx = start_page_idx
        self.end_page_idx = end_page_idx
        self.content = []

class PDFPreprocessor:
    def __init__(self, pdf_path):
        self.doc = fitz.open(pdf_path)
        self.chapters = []
        self.toc_end_page = 8 # Skip TOC to find real Preface
        
        # Heuristics
        self.header_margin = 60
        self.footer_margin = 60
        self.footnote_size_thresh = 9.0

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
                # Double check position?
                return i
        return len(self.doc)

    def locate_chapters(self):
        print("Locating chapters...")
        current_search_idx = self.toc_end_page
        
        for i, config in enumerate(CHAPTER_CONFIG):
            # Use a distinctive substring of the title to avoid false positives in text
            # Taking the first 20-30 chars is usually safe for headers
            search_term = config["title"]
            
            # Special handling for potentially "typo'd" titles (MIGRANT S vs MIGRANTS)
            if "TYPES OF MIGRANT" in search_term: 
                search_term = "CATEGORIES OF MIGRATION"

            page_idx = self.find_chapter_start(search_term, current_search_idx)
            
            if page_idx is not None:
                # If finding Preface, check if we found the Title Page running header instead?
                # Usually Preface is distinct.
                print(f"  Found '{config['num']}. {config['title'][:20]}...' at Page {page_idx} (Physical {page_idx+1})")
                
                # Close previous chapter
                if self.chapters:
                    self.chapters[-1].end_page_idx = page_idx
                
                # Create new
                self.chapters.append(Chapter(config, page_idx))
                current_search_idx = page_idx + 1
            else:
                # If Preface is optional, don't crash, just print warning
                if config["title"] == "Preface":
                    print(f"  [WARN] Could not find Preface. Skipping.")
                else:
                    print(f"  [ERROR] Could not find chapter: {config['title']}")
        
        # Find Bibliography to close the last chapter
        bib_idx = self.find_bibliography_start(current_search_idx)
        print(f"  Found Bibliography at Page {bib_idx} (Physical {bib_idx+1})")
        
        if self.chapters:
            self.chapters[-1].end_page_idx = bib_idx



    def normalize_text(self, text):
        """Standardize text to remove invisible characters/artifacts"""
        # 1. Normalize unicode (NFKC -> compatible decomposition)
        text = unicodedata.normalize('NFKC', text)
        
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
                        if f"Chapter {chapter_context.config['num']}" in full_line: continue

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
            print(f"Processing {chap.full_header}...")
            # Safety clamp
            end = chap.end_page_idx if chap.end_page_idx else len(self.doc)
            
            for i in range(chap.start_page_idx, end):
                txt = self.process_page_content(self.doc[i], chapter_context=chap)
                if txt: chap.content.append(txt)
                
        self.export_pdf("Cleaned_Audiobook_Final_v3.pdf")

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

        # 1. Page 1: Title Page
        story.append(Spacer(1, 100))
        story.append(Paragraph("Christianity and Migration", style_title))
        story.append(Spacer(1, 20))
        story.append(Paragraph("Peter C. Phan", style_author))
        story.append(PageBreak())

        # 2. Page 2: Table of Contents
        story.append(Paragraph("Table of Contents", style_h1))
        story.append(Spacer(1, 20))
        for chap in self.chapters:
             # Skip Preface in TOC? Or include? User said "list that is the table of contents"
             # Usually Preface is in TOC.
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

if __name__ == "__main__":
    p = PDFPreprocessor("9780190082277_Print Christianity and Migration (2).pdf")
    p.run()
