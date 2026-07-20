"""
ChromaDB vector database manager for UPSC knowledge base
"""
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from typing import List, Dict, Optional
from loguru import logger
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.settings import (
    CHROMA_DB_PATH, COLLECTION_NAME, EMBEDDING_MODEL,
    TOP_K_RESULTS, SIMILARITY_THRESHOLD
)


class ChromaDBManager:
    """Manage ChromaDB vector database for RAG"""
    
    def __init__(self, db_path: Optional[str] = None, collection_name: Optional[str] = None):
        self.db_path = db_path or CHROMA_DB_PATH
        self.collection_name = collection_name or COLLECTION_NAME
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=self.db_path,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Initialize embedding function
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL
        )
        
        # Get or create collection
        self.collection = self._get_or_create_collection()
        
        logger.info(f"ChromaDB initialized at {self.db_path}")
        logger.info(f"Collection: {self.collection_name} (Count: {self.collection.count()})")
    
    def _get_or_create_collection(self):
        """Get existing collection or create new one"""
        try:
            collection = self.client.get_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function
            )
            logger.info(f"Loaded existing collection: {self.collection_name}")
        except:
            collection = self.client.create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function,
                metadata={"description": "UPSC knowledge base"}
            )
            logger.info(f"Created new collection: {self.collection_name}")
        
        return collection
    
    def add_documents(self, documents: List[Dict], batch_size: int = 100):
        """Add documents to the collection in batches"""
        if not documents:
            logger.warning("No documents to add")
            return
        
        logger.info(f"Adding {len(documents)} documents to ChromaDB...")
        
        # Prepare data for ChromaDB
        ids = []
        texts = []
        metadatas = []
        
        for idx, doc in enumerate(documents):
            # Generate unique ID
            doc_id = f"{doc.get('source', 'unknown')}_{doc.get('chunk_id', idx)}"
            ids.append(doc_id)
            
            # Extract text
            texts.append(doc.get('text', doc.get('content', '')))
            
            # Prepare metadata (ChromaDB requires simple types)
            metadata = {
                "source": str(doc.get('source', 'unknown')),
                "topic": str(doc.get('topic', 'General')),
                "title": str(doc.get('title', ''))[:500],  # Limit length
                "chunk_id": int(doc.get('chunk_id', idx)),
            }
            
            # Add optional fields
            if 'url' in doc:
                metadata['url'] = str(doc['url'])[:500]
            if 'date' in doc:
                metadata['date'] = str(doc['date'])
            if 'page' in doc:
                metadata['page'] = int(doc['page'])
            
            metadatas.append(metadata)
        
        # Add in batches
        for i in range(0, len(documents), batch_size):
            batch_ids = ids[i:i + batch_size]
            batch_texts = texts[i:i + batch_size]
            batch_metadatas = metadatas[i:i + batch_size]
            
            try:
                self.collection.add(
                    ids=batch_ids,
                    documents=batch_texts,
                    metadatas=batch_metadatas
                )
                logger.info(f"Added batch {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1}")
            except Exception as e:
                logger.error(f"Error adding batch: {e}")
        
        logger.success(f"✓ Added {len(documents)} documents. Total count: {self.collection.count()}")
    
    def query(self, query_text: str, n_results: int = TOP_K_RESULTS, 
              topic_filter: Optional[str] = None) -> Dict:
        """Query the collection"""
        try:
            # Prepare where clause for filtering
            where_clause = None
            if topic_filter:
                where_clause = {"topic": topic_filter}
            
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=where_clause
            )
            
            return results
        
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}

    def get_relevant_context(self, query: str, n_results: int = TOP_K_RESULTS,
                            topic_filter: Optional[str] = None) -> List[Dict]:
        """Get relevant context for a query with formatted results"""
        results = self.query(query, n_results, topic_filter)

        if not results["documents"][0]:
            return []

        # Format results
        contexts = []
        for i, doc in enumerate(results["documents"][0]):
            context = {
                "text": doc,
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i],
                "relevance_score": 1 - results["distances"][0][i]  # Convert distance to similarity
            }

            # Filter by similarity threshold
            if context["relevance_score"] >= SIMILARITY_THRESHOLD:
                contexts.append(context)

        return contexts

    def delete_collection(self):
        """Delete the collection"""
        try:
            self.client.delete_collection(name=self.collection_name)
            logger.warning(f"Deleted collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Failed to delete collection: {e}")

    def reset_collection(self):
        """Reset the collection (delete and recreate)"""
        self.delete_collection()
        self.collection = self._get_or_create_collection()
        logger.info("Collection reset successfully")

    def get_stats(self) -> Dict:
        """Get collection statistics"""
        count = self.collection.count()

        # Get sample to analyze topics
        if count > 0:
            sample = self.collection.get(limit=min(100, count))
            topics = {}
            sources = {}

            for metadata in sample["metadatas"]:
                topic = metadata.get("topic", "Unknown")
                source = metadata.get("source", "Unknown")

                topics[topic] = topics.get(topic, 0) + 1
                sources[source] = sources.get(source, 0) + 1

            return {
                "total_documents": count,
                "topics": topics,
                "sources": sources,
                "collection_name": self.collection_name,
                "db_path": self.db_path
            }

        return {
            "total_documents": 0,
            "collection_name": self.collection_name,
            "db_path": self.db_path
        }

    def print_stats(self):
        """Print collection statistics"""
        stats = self.get_stats()

        print("\n" + "="*50)
        print("CHROMADB STATISTICS")
        print("="*50)
        print(f"Collection: {stats['collection_name']}")
        print(f"Total Documents: {stats['total_documents']}")

        if stats['total_documents'] > 0:
            print("\nTopics:")
            for topic, count in stats.get('topics', {}).items():
                print(f"  - {topic}: {count}")

            print("\nSources:")
            for source, count in stats.get('sources', {}).items():
                print(f"  - {source}: {count}")

        print("="*50 + "\n")


def main():
    """Test ChromaDB manager"""
    db = ChromaDBManager()

    # Print stats
    db.print_stats()

    # Test with sample documents
    sample_docs = [
        {
            "text": "The Indian Constitution was adopted on 26th November 1949 and came into effect on 26th January 1950.",
            "source": "test_polity.pdf",
            "topic": "Polity",
            "title": "Indian Constitution",
            "chunk_id": 0
        },
        {
            "text": "The Himalayas are the highest mountain range in the world, formed by the collision of Indian and Eurasian plates.",
            "source": "test_geography.pdf",
            "topic": "Geography",
            "title": "Indian Geography",
            "chunk_id": 0
        }
    ]

    # Add sample documents
    # db.add_documents(sample_docs)

    # Test query
    query = "When was the Indian Constitution adopted?"
    print(f"\nQuery: {query}")
    contexts = db.get_relevant_context(query, n_results=3)

    if contexts:
        print(f"\nFound {len(contexts)} relevant contexts:")
        for i, ctx in enumerate(contexts, 1):
            print(f"\n{i}. Relevance: {ctx['relevance_score']:.2f}")
            print(f"   Source: {ctx['metadata']['source']}")
            print(f"   Topic: {ctx['metadata']['topic']}")
            print(f"   Text: {ctx['text'][:100]}...")
    else:
        print("No relevant contexts found")


if __name__ == "__main__":
    main()

