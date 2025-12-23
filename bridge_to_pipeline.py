import sys
import os
import asyncio
import glob
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Add external_repo to path so we can import from it
current_dir = os.path.dirname(os.path.abspath(__file__))
external_repo_path = os.path.join(current_dir, "external_repo")
sys.path.append(external_repo_path)

try:
    from tools.load_book_from_files import load_book_from_files
except ImportError as e:
    print(f"Error importing load_book_from_files: {e}")
    print(f"Make sure external_repo is in {external_repo_path} and dependencies are installed.")
    sys.exit(1)

def get_latest_output(output_dir):
    """Finds the most recently modified processed pair (json, txt)."""
    json_files = glob.glob(os.path.join(output_dir, "*_cleaned.json"))
    if not json_files:
        return None, None
    
    # Sort by modification time
    latest_json = max(json_files, key=os.path.getmtime)
    
    # Expect corresponding text file
    # Note: local preprocessor logic: base.replace('.pdf', '.txt')
    # If json is 'base_cleaned.json', text should be 'base_cleaned.txt'
    # Wait, the preprocessor outputs:
    # PDF: base_cleaned.pdf
    # JSON: base_cleaned.json
    # TXT: base_cleaned.txt
    
    # So if we have X_cleaned.json, we expect X_cleaned.txt
    
    base_path = os.path.splitext(latest_json)[0] 
    # latest_json is "..._cleaned.json", base_path is "..._cleaned"
    
    # Construct expected txt path
    # If original was "file.pdf", output is "file_cleaned.json" and "file_cleaned.txt"
    # So simply replacing .json with .txt should work
    latest_txt = latest_json.replace('.json', '.txt')
    
    if os.path.exists(latest_txt):
        return latest_json, latest_txt
    else:
        print(f"Found JSON {latest_json} but missing text file {latest_txt}")
        return None, None

async def main():
    parser = argparse.ArgumentParser(description="Bridge to AI Audiobook Generator")
    parser.add_argument("--json", help="Path to TOC JSON file")
    parser.add_argument("--text", help="Path to Cleaned Text file")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run (no upload)")
    parser.add_argument("--update", action="store_true", help="Force update of existing chapters")
    parser.add_argument("--output-dir", default="output", help="Directory showing recent outputs")
    
    args = parser.parse_args()
    
    json_path = args.json
    text_path = args.text
    
    if not json_path or not text_path:
        print("No input files provided, looking for latest output...")
        json_path, text_path = get_latest_output(args.output_dir)
        
    if not json_path or not text_path:
        print("Could not find valid input files.")
        return

    print(f"Using JSON: {json_path}")
    print(f"Using TEXT: {text_path}")
    
    # Load .env explicitly
    load_dotenv()
    
    # Check for API Key
    if not os.environ.get("XI_API_KEY") and not args.dry_run:
        print("WARNING: XI_API_KEY not found in environment variables.")
        # We let the external script handle the error or we can try to load .env manually if needed, 
        # but load_book_from_files calls load_dotenv() so it should be fine if .env exists in CWD.
    
    try:
        success = await load_book_from_files(
            toc_json_path=json_path,
            clean_text_path=text_path,
            dry_run=args.dry_run,
            clear_existing=args.update
        )
        if success:
            print("Bridge execution completed successfully.")
        else:
            print("Bridge execution failed.")
            
    except Exception as e:
        print(f"An error occurred during execution: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
