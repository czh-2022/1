import os
import requests
import json
from loguru import logger
from dotenv import load_dotenv
from database import SessionLocal
from models_db import KnowledgeBaseFile
import datetime

load_dotenv()

DIFY_API_KEY = os.getenv("DIFY_DATASET_API_KEY")
DIFY_BASE_URL = os.getenv("DIFY_BASE_URL", "https://api.dify.ai/v1")

# Ensure dataset exists or use existing ID
DATASET_ID = os.getenv("DIFY_DATASET_ID")

def upload_file_to_dify(file_path: str):
    """
    Upload a single file to Dify Knowledge Base via API.
    Ref: https://docs.dify.ai/guides/knowledge-base/create-knowledge-via-api
    """
    if not DIFY_API_KEY or not DATASET_ID:
        logger.warning("Dify configuration missing. Skipping sync.")
        return False

    url = f"{DIFY_BASE_URL}/datasets/{DATASET_ID}/document/create_by_file"
    
    headers = {
        "Authorization": f"Bearer {DIFY_API_KEY}"
    }
    
    filename = os.path.basename(file_path)
    
    try:
        # 1. Prepare file
        files = {
            'file': (filename, open(file_path, 'rb'), 'text/markdown')
        }
        
        # 2. Prepare metadata (indexing rules)
        data = {
            'indexing_technique': 'high_quality',
            'process_rule': json.dumps({
                'rules': {
                    'pre_processing_rules': [{'id': 'remove_extra_spaces', 'enabled': True}],
                    'segmentation': {'separator': '\n', 'max_tokens': 500, 'chunk_overlap': 50}
                },
                'mode': 'automatic'
            })
        }
        
        logger.info(f"Uploading {filename} to Dify Dataset {DATASET_ID}...")
        response = requests.post(url, headers=headers, files=files, data=data)
        
        if response.status_code == 200:
            doc_info = response.json()
            logger.success(f"Uploaded {filename}: {doc_info['document']['id']}")
            return doc_info['document']['id']
        else:
            logger.error(f"Failed to upload {filename}: {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Exception during upload: {e}")
        return None

def run_sync_process():
    """
    Main pipeline: Clean -> Upload -> Update DB
    """
    from rag_pipeline.cleaner import process_directory
    
    # Paths
    raw_dir = "dify_assets/knowledge"
    clean_dir = "dify_assets/processed"
    
    # 1. Clean
    processed_files = process_directory(raw_dir, clean_dir)
    
    # 2. Sync
    db = SessionLocal()
    results = []
    
    for file_path in processed_files:
        filename = os.path.basename(file_path)
        
        # Check if already synced (Logic can be improved to check hash)
        kb_file = db.query(KnowledgeBaseFile).filter(KnowledgeBaseFile.filename == filename).first()
        
        dify_id = upload_file_to_dify(file_path)
        
        status = "synced" if dify_id else "error"
        
        if not kb_file:
            kb_file = KnowledgeBaseFile(filename=filename, status=status)
            db.add(kb_file)
        else:
            kb_file.status = status
            kb_file.last_synced_at = datetime.datetime.now()
            if dify_id:
                kb_file.dify_document_id = dify_id
        
        results.append({"file": filename, "status": status})
    
    db.commit()
    db.close()
    return results

if __name__ == "__main__":
    run_sync_process()
