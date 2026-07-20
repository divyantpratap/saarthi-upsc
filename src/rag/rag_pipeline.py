"""
Complete RAG (Retrieval-Augmented Generation) Pipeline
Combines ChromaDB retrieval with Gemini LLM
"""
from typing import List, Dict, Optional
from loguru import logger
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.rag.chroma_db import ChromaDBManager
from src.llm.gemini_client import GeminiClient
from config.settings import TOP_K_RESULTS, RERANK_TOP_K


class RAGPipeline:
    """Complete RAG pipeline for UPSC chatbot"""
    
    def __init__(self, db_manager: Optional[ChromaDBManager] = None,
                 llm_client: Optional[GeminiClient] = None):
        """Initialize RAG pipeline"""
        self.db = db_manager or ChromaDBManager()
        self.llm = llm_client or GeminiClient()
        
        logger.info("RAG Pipeline initialized")
    
    def query(self, question: str, topic_filter: Optional[str] = None,
              n_results: int = TOP_K_RESULTS, include_sources: bool = True) -> Dict:
        """
        Complete RAG query pipeline
        
        Args:
            question: User's question
            topic_filter: Optional topic filter (e.g., "Polity", "History")
            n_results: Number of contexts to retrieve
            include_sources: Whether to include source citations
        
        Returns:
            Dictionary with answer, sources, and metadata
        """
        try:
            logger.info(f"Processing query: {question[:50]}...")
            
            # Step 1: Retrieve relevant contexts
            contexts = self.db.get_relevant_context(
                query=question,
                n_results=n_results,
                topic_filter=topic_filter
            )
            
            if not contexts:
                return {
                    "answer": "I couldn't find relevant information in the knowledge base to answer this question. Please try rephrasing or ask about a different topic.",
                    "sources": [],
                    "num_contexts": 0,
                    "status": "no_context"
                }
            
            logger.info(f"Retrieved {len(contexts)} relevant contexts")
            
            # Step 2: Re-rank contexts (optional - take top K)
            contexts = self._rerank_contexts(contexts, question)[:RERANK_TOP_K]
            
            # Step 3: Generate answer using LLM
            if include_sources:
                result = self.llm.generate_answer_with_sources(question, contexts)
                result["status"] = "success"
            else:
                answer = self.llm.generate_rag_response(question, contexts)
                result = {
                    "answer": answer,
                    "sources": [],
                    "num_contexts": len(contexts),
                    "status": "success"
                }
            
            logger.success("Query processed successfully")
            return result
        
        except Exception as e:
            logger.error(f"RAG pipeline error: {e}")
            return {
                "answer": f"An error occurred while processing your question: {str(e)}",
                "sources": [],
                "num_contexts": 0,
                "status": "error"
            }
    
    def _rerank_contexts(self, contexts: List[Dict], query: str) -> List[Dict]:
        """
        Re-rank contexts based on relevance
        Currently uses simple relevance score sorting
        Can be enhanced with cross-encoder models
        """
        # Sort by relevance score (already computed)
        sorted_contexts = sorted(
            contexts,
            key=lambda x: x.get('relevance_score', 0),
            reverse=True
        )
        
        return sorted_contexts
    
    def batch_query(self, questions: List[str], **kwargs) -> List[Dict]:
        """Process multiple questions"""
        results = []
        for question in questions:
            result = self.query(question, **kwargs)
            results.append(result)
        return results
    
    def get_topic_summary(self, topic: str, max_points: int = 5) -> str:
        """Get a summary of key points for a topic"""
        query = f"What are the key points about {topic} for UPSC preparation?"
        result = self.query(query, topic_filter=topic, n_results=10)
        return result["answer"]
    
    def practice_question(self, topic: Optional[str] = None) -> Dict:
        """Generate a practice question for a topic"""
        if topic:
            prompt = f"Generate a UPSC-style practice question on {topic}"
        else:
            prompt = "Generate a UPSC-style practice question"
        
        # Get relevant context
        contexts = self.db.get_relevant_context(prompt, n_results=3, topic_filter=topic)
        
        # Generate question
        question = self.llm.generate_response(
            f"Based on UPSC syllabus, generate one practice question on {topic or 'any topic'}. "
            "Include the question and a brief model answer."
        )
        
        return {
            "question": question,
            "topic": topic or "General",
            "contexts": contexts
        }
    
    def explain_concept(self, concept: str, detail_level: str = "medium") -> Dict:
        """Explain a concept with varying detail levels"""
        detail_prompts = {
            "brief": "Explain in 2-3 sentences",
            "medium": "Explain in detail with examples",
            "comprehensive": "Provide a comprehensive explanation with examples, facts, and UPSC relevance"
        }
        
        detail_instruction = detail_prompts.get(detail_level, detail_prompts["medium"])
        
        query = f"{concept}. {detail_instruction}"
        return self.query(query)
    
    def compare_concepts(self, concept1: str, concept2: str) -> Dict:
        """Compare two concepts"""
        query = f"Compare and contrast {concept1} and {concept2} for UPSC preparation"
        return self.query(query, n_results=8)


def main():
    """Test RAG pipeline"""
    try:
        # Initialize pipeline
        pipeline = RAGPipeline()
        
        # Test query
        print("\n" + "="*60)
        print("TESTING RAG PIPELINE")
        print("="*60)
        
        question = "What is the structure of Indian Parliament?"
        print(f"\nQuestion: {question}\n")
        
        result = pipeline.query(question)
        
        print("Answer:")
        print("-" * 60)
        print(result["answer"])
        print("-" * 60)
        
        if result["sources"]:
            print(f"\nSources ({len(result['sources'])}):")
            for i, source in enumerate(result["sources"], 1):
                print(f"{i}. {source['source']} (Topic: {source['topic']}, Relevance: {source['relevance']:.2f})")
        
        print(f"\nStatus: {result['status']}")
        print(f"Contexts used: {result['num_contexts']}")
        
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure to:")
        print("1. Set GEMINI_API_KEY in .env file")
        print("2. Add documents to ChromaDB first")


if __name__ == "__main__":
    main()
