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

1.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

2.  Run the processor:
    ```bash
    python processor.py
    ```

   *Note: Modify `CHAPTER_CONFIG` in `processor.py` to match your specific book's structure.*

## Output

The script generates `Cleaned_Audiobook_Final_v3.pdf` (or similar versioned output), ready for TTS import.
