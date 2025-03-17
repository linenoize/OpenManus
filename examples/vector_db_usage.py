#!/usr/bin/env python3
"""
Example script demonstrating the use of the vector database tool in OpenManus.
This script shows how to use semantic search for more intelligent information retrieval.

Features demonstrated:
1. Creating and using the VectorDBTool
2. Working with different vector database backends (FAISS, ChromaDB)
3. Basic operations: creating collections, adding documents, searching, etc.
4. Comparing results between different backends
"""

import sys
import os
import json
import logging
from pprint import pprint
from datetime import datetime

# Add the parent directory to sys.path to import OpenManus modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from src.tools.vector_db_tool import VectorDBTool
except ImportError as e:
    logger.error(f"Error importing VectorDBTool: {e}")
    logger.error("Please install the required dependencies:")
    logger.error("  pip install faiss-cpu sentence-transformers")
    sys.exit(1)

def run_with_backend(backend="faiss"):
    """Run vector database operations with a specific backend."""
    logger.info(f"Running vector database demo with {backend.upper()} backend")
    
    try:
        # Initialize a vector database tool with the specified backend
        vector_db = VectorDBTool(
            model_name="all-MiniLM-L6-v2",
            base_path=f"data/examples/vector_db/{backend}",
            backend=backend
        )
    except (ImportError, ValueError) as e:
        logger.error(f"Failed to initialize {backend} backend: {e}")
        return None
        
    logger.info(f"Available backends: {vector_db.available_backends()}")
    logger.info(f"Current backend: {vector_db.current_backend()}")
    
    return vector_db

def main():
    print("OpenManus Vector Database Tool Demo")
    print("=" * 60)
    
    # Create data directory if it doesn't exist
    os.makedirs("data/examples/vector_db", exist_ok=True)
    
    # Initialize with FAISS backend (default)
    vector_db = run_with_backend("faiss")
    if not vector_db:
        logger.error("FAISS backend is required but not available")
        sys.exit(1)
        
    # Try ChromaDB backend if available
    try:
        chroma_db = run_with_backend("chroma")
        print("\nMultiple vector database backends available:")
        print(f"  - FAISS: {vector_db is not None}")
        print(f"  - ChromaDB: {chroma_db is not None}")
        print("\nUsing default FAISS backend for the rest of the demo.\n")
    except (ImportError, ValueError):
        print("\nOnly FAISS backend is available. To try ChromaDB:")
        print("  pip install chromadb\n")
    collection_name = "semantic_search_demo"
    
    # 1. Create a collection
    print("\n1. Creating vector collection...")
    vector_db.create_collection(collection_name)
    print(f"Collection '{collection_name}' created.")
    
    # 2. Add documents to the collection
    print("\n2. Adding documents to the collection...")
    documents = [
        {
            "text": "The Transformer architecture uses self-attention mechanisms to process sequential data more efficiently than recurrent neural networks.",
            "metadata": {"topic": "machine learning", "type": "architecture", "source": "research paper"}
        },
        {
            "text": "BERT is a pre-trained Transformer model that has revolutionized natural language processing tasks.",
            "metadata": {"topic": "nlp", "type": "model", "source": "research paper"}
        },
        {
            "text": "GPT models are autoregressive language models based on the Transformer architecture that generate text by predicting the next token.",
            "metadata": {"topic": "nlp", "type": "model", "source": "research paper"}
        },
        {
            "text": "Neural networks consist of layers of neurons that process information through weighted connections.",
            "metadata": {"topic": "machine learning", "type": "architecture", "source": "textbook"}
        },
        {
            "text": "Convolutional Neural Networks (CNNs) are particularly effective for image processing and computer vision tasks.",
            "metadata": {"topic": "computer vision", "type": "architecture", "source": "textbook"}
        },
        {
            "text": "Reinforcement learning is a type of machine learning where agents learn to make decisions by receiving rewards or penalties.",
            "metadata": {"topic": "reinforcement learning", "type": "paradigm", "source": "course"}
        },
        {
            "text": "Tesla's self-driving cars use a combination of computer vision, deep learning, and reinforcement learning to navigate roads.",
            "metadata": {"topic": "autonomous vehicles", "type": "application", "source": "news"}
        },
        {
            "text": "Climate change is accelerating and requires immediate action to reduce carbon emissions.",
            "metadata": {"topic": "climate change", "type": "environmental", "source": "report"}
        }
    ]
    
    # Add documents one by one to show the process
    for i, doc in enumerate(documents):
        doc_id = vector_db.add_text(
            collection_name=collection_name,
            text=doc["text"],
            metadata=doc["metadata"]
        )
        print(f"  Added document {i+1}/{len(documents)} with ID: {doc_id}")
    
    # 3. Get collection statistics
    print("\n3. Collection statistics:")
    stats = vector_db.get_collection_stats(collection_name)
    pprint(stats)
    
    # 4. Semantic search - example 1: Machine learning architectures
    print("\n4. Semantic search example 1 - Machine learning architectures:")
    query1 = "deep learning neural network architectures"
    results1 = vector_db.search(collection_name, query1, k=3)
    
    print(f"Query: '{query1}'")
    print(f"Found {len(results1)} results:")
    for i, result in enumerate(results1):
        print(f"\nResult {i+1} (Similarity: {result['similarity']:.4f}):")
        print(f"Text: {result['text']}")
        print(f"Metadata: {result['metadata']}")
    
    # 5. Semantic search - example 2: NLP models
    print("\n5. Semantic search example 2 - NLP models:")
    query2 = "large language models for text generation"
    results2 = vector_db.search(collection_name, query2, k=3)
    
    print(f"Query: '{query2}'")
    print(f"Found {len(results2)} results:")
    for i, result in enumerate(results2):
        print(f"\nResult {i+1} (Similarity: {result['similarity']:.4f}):")
        print(f"Text: {result['text']}")
        print(f"Metadata: {result['metadata']}")
    
    # 6. Semantic search - example 3: Reinforcement learning
    print("\n6. Semantic search example 3 - Reinforcement learning:")
    query3 = "autonomous agents learning from rewards"
    results3 = vector_db.search(collection_name, query3, k=2)
    
    print(f"Query: '{query3}'")
    print(f"Found {len(results3)} results:")
    for i, result in enumerate(results3):
        print(f"\nResult {i+1} (Similarity: {result['similarity']:.4f}):")
        print(f"Text: {result['text']}")
        print(f"Metadata: {result['metadata']}")
    
    # 7. Filter results by metadata (post-processing)
    print("\n7. Filtering results by metadata:")
    query = "neural networks"
    raw_results = vector_db.search(collection_name, query, k=5)
    
    # Filter for textbook sources only
    textbook_results = [r for r in raw_results if r["metadata"].get("source") == "textbook"]
    
    print(f"Query: '{query}'")
    print(f"All results: {len(raw_results)}")
    print(f"Textbook results: {len(textbook_results)}")
    
    for i, result in enumerate(textbook_results):
        print(f"\nTextbook Result {i+1} (Similarity: {result['similarity']:.4f}):")
        print(f"Text: {result['text']}")
    
    # 8. Update metadata
    print("\n8. Updating metadata:")
    # Get the first document about transformers
    transformer_results = vector_db.search(collection_name, "transformer architecture", k=1)
    if transformer_results:
        doc_id = transformer_results[0]["id"]
        print(f"Updating document {doc_id}")
        vector_db.update_metadata(
            collection_name, 
            doc_id, 
            {"importance": "high", "updated": True}
        )
        
        # Get the updated document
        updated_doc = vector_db.get_by_id(collection_name, doc_id)
        print("Updated metadata:")
        pprint(updated_doc["metadata"])
    
    # 9. Demonstrate persistence of the vector database
    print("\n9. Demonstrating persistence:")
    print(f"The vector database is persisted to disk at: {vector_db.base_path}")
    print("If you run this script again, the collection will be loaded from disk.")
    
    # 10. Clean up (optional)
    if input("\nDelete the collection? (y/n): ").lower() == 'y':
        vector_db.delete_collection(collection_name)
        print(f"Collection '{collection_name}' deleted.")
    else:
        print(f"Collection '{collection_name}' kept for future use.")
    
    print("\nVector database demo complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()