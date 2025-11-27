import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import torch
from openai import OpenAI
import json
import ast

# Load config
with open("config.json") as config:
    openai_key = json.load(config)["openaiKey"]

client = OpenAI(api_key=openai_key)

class ConferenceTalkSearcher:
    def __init__(self, embedding_type="free"):
        """
        Initialize the searcher with either 'free' or 'openai' embeddings.
        embedding_type: 'free' or 'openai'
        """
        self.embedding_type = embedding_type
        
        if embedding_type == "free":
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            if torch.cuda.is_available():
                self.model = self.model.to('cuda')
        
    def load_embeddings(self, csv_file):
        """Load embeddings from CSV file."""
        df = pd.read_csv(csv_file)
        # Convert string embeddings to numpy arrays
        df['embedding'] = df['embedding'].apply(lambda x: np.array(ast.literal_eval(x)))
        return df
    
    def query_to_embedding(self, query):
        """Convert a query string to an embedding."""
        if self.embedding_type == "free":
            return self.model.encode(query, convert_to_numpy=True, normalize_embeddings=True)
        else:
            # Use OpenAI API for query embedding
            response = client.embeddings.create(
                input=query,
                model="text-embedding-3-small"
            )
            return np.array(response.data[0].embedding)
    
    def cosine_similarity(self, vec1, vec2):
        """Calculate cosine similarity between two vectors."""
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
    
    def search(self, query, csv_file, top_k=3):
        """
        Search for the top_k most similar talks to the query.
        
        Returns:
            List of (talk_info, similarity_score) tuples
        """
        # Load embeddings
        df = self.load_embeddings(csv_file)
        
        # Convert query to embedding
        query_embedding = self.query_to_embedding(query)
        
        # Calculate similarities
        similarities = []
        for idx, row in df.iterrows():
            sim = self.cosine_similarity(query_embedding, row['embedding'])
            similarities.append((idx, sim))
        
        # Sort by similarity and get top_k
        similarities.sort(key=lambda x: x[1], reverse=True)
        top_indices = [idx for idx, _ in similarities[:top_k]]
        
        results = []
        for idx in top_indices:
            sim_score = similarities[[i[0] for i in similarities].index(idx)][1]
            results.append((df.iloc[idx], sim_score))
        
        return results
    
    def generate_answer(self, query, results):
        """
        Use ChatGPT to generate an answer based on retrieved talks.
        
        results: List of (talk_info, similarity_score) from search()
        """
        # Build context from retrieved talks
        context = "Here are the most relevant talks:\n\n"
        for i, (talk, score) in enumerate(results, 1):
            context += f"Talk {i} (Similarity: {score:.3f}):\n"
            context += f"Title: {talk['title']}\n"
            context += f"Speaker: {talk['speaker']}\n"
            context += f"Content: {talk['text'][:500]}...\n\n"
        
        # Create prompt
        system_prompt = """You are a helpful assistant that answers questions about LDS General Conference talks. 
Answer the user's question ONLY using the provided talks as references. 
Do not use outside knowledge or information. 
If the talks don't contain relevant information, say so."""
        
        user_message = f"""{context}

Question: {query}

Please answer this question using only the talks provided above."""
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content


def run_tests():
    """Run the lab assignment tests."""
    
    questions = [
        "How can I gain a testimony of Jesus Christ?",
        "What are some ways to deal with challenges in life and find a purpose?",
        "How can I fix my car if it won't start?",
        "What does Elder Uchtdorf often talk about?",
        "What is a common theme from the April 2024 conference?"
    ]
    
    # Test with both embedding types and all dataset types
    for embedding_type in ["free", "openai"]:
        print(f"\n{'='*60}")
        print(f"TESTING WITH {embedding_type.upper()} EMBEDDINGS")
        print(f"{'='*60}")
        
        searcher = ConferenceTalkSearcher(embedding_type=embedding_type)
        dataset_types = []
        if embedding_type == "free":
            dataset_types = [
			(f"{embedding_type}/free_talks.csv", "Full Talks"),
			(f"{embedding_type}/free_paragraphs.csv", "Paragraphs"),
			(f"{embedding_type}/free_3_clusters.csv", "3-Clusters")
		]
               
        if embedding_type == "openai":
            dataset_types = [
			(f"{embedding_type}/openai_talks.csv", "Full Talks"),
			(f"{embedding_type}/openai_paragraphs.csv", "Paragraphs"),
			(f"{embedding_type}/openai_3_clusters.csv", "3-Clusters")
		]
        
        for csv_file, dataset_name in dataset_types:
            print(f"\n--- {dataset_name} ---")
            for question in questions:
                print(f"\nQ: {question}")
                results = searcher.search(question, csv_file, top_k=3)
                
                for i, (talk, score) in enumerate(results, 1):
                    print(f"  {i}. {talk['title']} {talk['speaker']} (Score: {score:.3f})")


def run_rag_demo():
    """Run RAG generation for selected questions."""
    questions = [
        "How can I gain a testimony of Jesus Christ?",
        "What are some ways to deal with challenges in life and find a purpose?",
        "What does Elder Uchtdorf often talk about?"
    ]
    
    # Use free embeddings for this demo (faster, still good results)
    searcher = ConferenceTalkSearcher(embedding_type="free")
    
    for question in questions:
        print(f"\n{'='*60}")
        print(f"Question: {question}")
        print(f"{'='*60}")
        
        # Search using paragraphs
        results = searcher.search(question, "free/free_paragraphs.csv", top_k=3)
        
        # Generate answer
        answer = searcher.generate_answer(question, results)
        print(f"\nAnswer:\n{answer}")
        


if __name__ == "__main__":
    # Uncomment one to run:
    run_tests()  # Run all comparisons
    # run_rag_demo()  # Generate answers
