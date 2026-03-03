import re
import os
from loguru import logger

def clean_markdown(content: str) -> str:
    """
    Standardize markdown content for better RAG processing.
    """
    # Remove multiple newlines
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    # Remove trailing whitespace
    content = "\n".join([line.rstrip() for line in content.split("\n")])
    
    # Ensure headers have space (e.g., #Header -> # Header)
    content = re.sub(r'^(#{1,6})([^ \n])', r'\1 \2', content, flags=re.MULTILINE)
    
    return content.strip()

def process_directory(input_dir: str, output_dir: str):
    """
    Process all markdown files in input_dir and save cleaned versions to output_dir.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    processed_files = []
    
    for filename in os.listdir(input_dir):
        if not filename.endswith(".md"):
            continue
            
        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename)
        
        try:
            with open(input_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            cleaned = clean_markdown(content)
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(cleaned)
                
            logger.info(f"Processed: {filename}")
            processed_files.append(output_path)
            
        except Exception as e:
            logger.error(f"Failed to process {filename}: {e}")
            
    return processed_files
