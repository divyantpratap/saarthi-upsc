"""
Gemini 2.5 Flash LLM client for UPSC chatbot
"""
import google.generativeai as genai
from typing import List, Dict, Optional
from loguru import logger
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.settings import (
    GEMINI_API_KEY, GEMINI_MODEL, GEMINI_TEMPERATURE,
    GEMINI_TOP_P, GEMINI_TOP_K, GEMINI_MAX_OUTPUT_TOKENS,
    SYSTEM_PROMPT, QA_PROMPT_TEMPLATE
)


class GeminiClient:
    """Client for Gemini 2.5 Flash API"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or GEMINI_API_KEY
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found. Please set it in .env file")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        
        # Initialize model
        self.model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            generation_config={
                "temperature": GEMINI_TEMPERATURE,
                "top_p": GEMINI_TOP_P,
                "top_k": GEMINI_TOP_K,
                "max_output_tokens": GEMINI_MAX_OUTPUT_TOKENS,
            }
        )
        
        logger.info(f"Gemini client initialized with model: {GEMINI_MODEL}")
    
    def generate_response(self, prompt: str, stream: bool = False) -> str:
        """Generate response from Gemini"""
        try:
            if stream:
                response = self.model.generate_content(prompt, stream=True)
                full_response = ""
                for chunk in response:
                    if chunk.text:
                        full_response += chunk.text
                return full_response
            else:
                response = self.model.generate_content(prompt)
                return response.text
        
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return f"Error generating response: {str(e)}"
    
    def generate_rag_response(self, query: str, contexts: List[Dict], 
                             stream: bool = False) -> str:
        """Generate response using RAG (Retrieval-Augmented Generation)"""
        
        # Format contexts
        context_text = self._format_contexts(contexts)
        
        # Build prompt
        prompt = self._build_rag_prompt(query, context_text)
        
        # Generate response
        response = self.generate_response(prompt, stream=stream)
        
        return response
    
    def _format_contexts(self, contexts: List[Dict]) -> str:
        """Format retrieved contexts for prompt"""
        if not contexts:
            return "No relevant context found in the knowledge base."
        
        formatted = []
        for i, ctx in enumerate(contexts, 1):
            metadata = ctx.get('metadata', {})
            text = ctx.get('text', '')
            relevance = ctx.get('relevance_score', 0)
            
            source = metadata.get('source', 'Unknown')
            topic = metadata.get('topic', 'General')
            
            formatted.append(f"""
[Context {i}] (Relevance: {relevance:.2f})
Source: {source} | Topic: {topic}
Content: {text}
""")
        
        return "\n".join(formatted)
    
    def _build_rag_prompt(self, query: str, context: str) -> str:
        """Build complete RAG prompt"""
        prompt = f"""{SYSTEM_PROMPT}

{QA_PROMPT_TEMPLATE.format(context=context, question=query)}"""
        
        return prompt
    
    def chat(self, message: str, chat_history: Optional[List[Dict]] = None) -> str:
        """Chat with conversation history"""
        try:
            # Start chat session
            chat = self.model.start_chat(history=[])
            
            # Add history if provided
            if chat_history:
                for msg in chat_history:
                    role = msg.get('role', 'user')
                    content = msg.get('content', '')
                    
                    if role == 'user':
                        chat.send_message(content)
            
            # Send current message
            response = chat.send_message(message)
            return response.text
        
        except Exception as e:
            logger.error(f"Chat error: {e}")
            return f"Error in chat: {str(e)}"
    
    def generate_answer_with_sources(self, query: str, contexts: List[Dict]) -> Dict:
        """Generate answer with source citations"""
        
        # Generate main answer
        answer = self.generate_rag_response(query, contexts)
        
        # Extract sources
        sources = []
        for ctx in contexts:
            metadata = ctx.get('metadata', {})
            source_info = {
                "source": metadata.get('source', 'Unknown'),
                "topic": metadata.get('topic', 'General'),
                "title": metadata.get('title', ''),
                "relevance": ctx.get('relevance_score', 0),
                "url": metadata.get('url', '')
            }
            
            # Avoid duplicates
            if source_info not in sources:
                sources.append(source_info)
        
        return {
            "answer": answer,
            "sources": sources,
            "num_contexts": len(contexts)
        }


def main():
    """Test Gemini client"""
    try:
        client = GeminiClient()
        
        # Test simple generation
        print("Testing simple generation...")
        response = client.generate_response("What is UPSC? Answer in 2 sentences.")
        print(f"\nResponse: {response}\n")
        
        # Test RAG response with mock contexts
        print("Testing RAG response...")
        mock_contexts = [
            {
                "text": "UPSC stands for Union Public Service Commission. It conducts Civil Services Examination for IAS, IPS, IFS.",
                "metadata": {"source": "test.pdf", "topic": "UPSC Basics"},
                "relevance_score": 0.95
            }
        ]
        
        rag_response = client.generate_rag_response(
            "What is UPSC?",
            mock_contexts
        )
        print(f"\nRAG Response: {rag_response}\n")
        
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure to set GEMINI_API_KEY in .env file")


if __name__ == "__main__":
    main()
