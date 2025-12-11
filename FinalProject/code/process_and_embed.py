import os
import pandas as pd
from sentence_transformers import SentenceTransformer
import torch
from datetime import datetime
import re

def load_books(books_dir="Books"):
    """
    Load all book files from the directory structure.
    Expected structure: Books/Book-Name/chapter-*.txt
    Returns a DataFrame with text chunks, source book, and chapter info.
    """
    data = []
    
    for book_folder in os.listdir(books_dir):
        book_path = os.path.join(books_dir, book_folder)
        if not os.path.isdir(book_path):
            continue
        
        # Clean up book name (e.g., "Mythical-Man-Month" -> "Mythical Man-Month")
        book_name = book_folder.replace("-", " ")
        
        for file in os.listdir(book_path):
            if file.endswith(".txt"):
                file_path = os.path.join(book_path, file)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Extract chapter/section info from filename
                    # e.g., "chapter-5-about-management.txt" -> "Chapter 5: About Management"
                    chapter_info = extract_chapter_info(file)
                    
                    # Split content into meaningful chunks (by paragraphs)
                    chunks = chunk_text(content)
                    
                    for i, chunk in enumerate(chunks):
                        data.append({
                            'book': book_name,
                            'chapter': chapter_info,
                            'filename': file,
                            'chunk_id': i,
                            'text': chunk.strip()
                        })
                
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
    
    return pd.DataFrame(data)

def extract_chapter_info(filename):
    """Extract chapter information from filename."""
    # Remove .txt
    name = filename.replace('.txt', '')
    # Replace hyphens with spaces and capitalize
    name = name.replace('-', ' ').title()
    return name

def chunk_text(text, min_chunk_size=100):
    """
    Split text into chunks by double newlines (paragraphs).
    Ensures chunks are meaningful and not too small.
    """
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        # If adding this paragraph would exceed reasonable size, save current chunk
        if len(current_chunk) + len(para) > 800 and current_chunk:
            chunks.append(current_chunk)
            current_chunk = para
        else:
            if current_chunk:
                current_chunk += "\n\n" + para
            else:
                current_chunk = para
    
    if current_chunk:
        chunks.append(current_chunk)
    
    # Filter out chunks that are too small
    chunks = [c for c in chunks if len(c) > min_chunk_size]
    
    return chunks

def generate_embeddings(output_dir="embeddings"):
    """
    Generate and save embeddings for all book texts.
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        
        print("Loading books from directory...")
        df = load_books("Books")
        
        if df.empty:
            print("No books found. Check your Books directory structure.")
            return
        
        print(f"Loaded {len(df)} text chunks from {df['book'].nunique()} books")
        print(f"Books: {', '.join(df['book'].unique())}")
        
        # Initialize the sentence transformer model
        print("\nInitializing embedding model...")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Move model to GPU if available
        if torch.cuda.is_available():
            model = model.to('cuda')
            print("Using GPU for encoding")
        else:
            print("Using CPU for encoding")
        
        # Generate embeddings
        print("\nGenerating embeddings...")
        texts = df['text'].tolist()
        embeddings = model.encode(
            texts,
            batch_size=32,
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=True
        )
        
        df['embedding'] = [emb.tolist() for emb in embeddings]
        
        # Save to CSV
        output_file = os.path.join(output_dir, "course_readings.csv")
        df.to_csv(output_file, index=False)
        print(f"\nEmbeddings saved to '{output_file}'")
        print(f"Total chunks: {len(df)}")
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    print("CS 428 Midterm Grading System - Book Embedding Generator")
    print("=" * 60)
    print(f"Start time: {datetime.now().strftime('%H:%M:%S')}")
    
    generate_embeddings()
    
    print(f"End time: {datetime.now().strftime('%H:%M:%S')}")