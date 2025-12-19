# Audiobook PDF Preprocessor

A Python tool to clean and restructure PDF books for optimal use with Text-to-Speech (TTS) engines like ElevenLabs.

## Features

*   **Front Matter Generation**: Automatically creates a clean Title Page and Table of Contents.
*   **Smart Chapter Detection**: Identifies Preface, Chapters, and Epilogue based on configuration.
*   **Content Cleaning**:
    *   Removes footnotes, superscripts, and citations.
    *   Removes headers, footers, and page numbers.
    *   Excludes Bibliography and Indexes.
*   **Encoding Fixes**: Normalizes text to Unicode NFC and uses Arial font to preserve accents.
*   **Linear Pagination**: Ensures every chapter starts on a new page.

## Usage

### 1. Setup
*   Place your source PDFs in the `input/` folder.
*   (Optional) Create a configuration file in `configs/` for each book if you need custom chapter titles (see `configs/template.json`).

### 2. Run
Run the processor to clean all PDFs in the input folder:

```bash
python processor.py
```

Arguments:
*   `--input_dir`: Directory containing source PDFs (default: `input`)
*   `--output_dir`: Directory to save cleaned PDFs (default: `output`)
*   `--config_dir`: Directory containing JSON configs (default: `configs`)

### 3. Output
Cleaned PDFs will be saved to `output/` with `_cleaned` appended to the filename.
The script will print the number of footnotes removed for each book.

## Configuration
To handle different chapter structures, create a JSON file in `configs/` that matches your PDF's filename.

**Example (`configs/mybook.json`):**
```json
{
    "metadata": {
        "title": "My Book Title",
        "author": "Author Name",
        "filename_pattern": "Unique Part of Filename"
    },
    "settings": {
        "toc_end_page": 10
    },
    "chapters": [
        {"part": "Part 1", "num": "1", "title": "Chapter One"},
        {"part": "Part 1", "num": "2", "title": "Chapter Two"}
    ]
}
```
