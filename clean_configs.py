import json
import glob
import os
import re

def clean_config(path):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    clean_chapters = []
    seen_titles = set()
    
    for chap in data.get("chapters", []):
        title = chap["title"].strip()
        
        # Filter 1: Too short
        if len(title) < 4:
            continue
            
        # Filter 2: All lowercase (likely a wrapped partial line)
        if title.islower():
            continue
            
        # Filter 3: Duplicates
        if title in seen_titles:
            continue
            
        # Filter 4: Starts with number/dot redundancy (e.g. "1. Introduction" stored as title "1. Introduction")
        # The processor finds "Introduction", but "1. Introduction" is also fine.
        # But things like "11." are bad.
        if re.match(r'^\d+[\.\s]*$', title):
             continue

        seen_titles.add(title)
        clean_chapters.append(chap)
    
    data["chapters"] = clean_chapters
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
    print(f"Cleaned {os.path.basename(path)}: {len(clean_chapters)} chapters remaining.")

def main():
    configs = glob.glob("configs/*.json")
    for cfg in configs:
        if "template" in cfg or "default" in cfg: continue
        clean_config(cfg)

if __name__ == "__main__":
    main()
