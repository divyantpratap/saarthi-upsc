# 📖 Complete Usage Guide - UPSC AI Mentor

## Table of Contents
1. [Installation](#installation)
2. [Configuration](#configuration)
3. [Data Ingestion](#data-ingestion)
4. [Using the Chatbot](#using-the-chatbot)
5. [Practice Questions](#practice-questions)
6. [Advanced Features](#advanced-features)
7. [Tips & Best Practices](#tips--best-practices)

## Installation

### System Requirements
- Python 3.8 or higher
- 4GB RAM minimum (8GB recommended)
- 2GB free disk space
- Internet connection for API calls

### Step-by-Step Installation

```bash
# 1. Clone or download the project
cd UPSC

# 2. Create virtual environment (recommended)
python -m venv venv

# 3. Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Download NLP models (optional)
python -m spacy download en_core_web_sm
```

## Configuration

### 1. Get Gemini API Key

1. Visit: https://makersuite.google.com/app/apikey
2. Sign in with Google account
3. Click "Create API Key"
4. Copy the generated key

### 2. Setup Environment Variables

Create a `.env` file in the project root:

```bash
GEMINI_API_KEY=your_actual_api_key_here
```

### 3. Customize Settings (Optional)

Edit `config/settings.py` to customize:

```python
# Chunking
CHUNK_SIZE = 500  # Increase for longer contexts
CHUNK_OVERLAP = 50  # Overlap between chunks

# Retrieval
TOP_K_RESULTS = 5  # Number of contexts to retrieve
SIMILARITY_THRESHOLD = 0.7  # Minimum similarity score

# LLM
GEMINI_TEMPERATURE = 0.7  # 0.0 = deterministic, 1.0 = creative
GEMINI_MAX_OUTPUT_TOKENS = 2048  # Max response length
```

## Data Ingestion

### Method 1: Command Line (Recommended)

#### Process PDFs Only
```bash
# 1. Add PDFs to data/raw/ directory
# 2. Run ingestion
python ingest_data.py --mode pdf
```

#### Scrape Web Content Only
```bash
python ingest_data.py --mode web --articles 30
```

#### Process Everything
```bash
python ingest_data.py --mode all --articles 50
```

#### Reset and Start Fresh
```bash
python ingest_data.py --mode all --reset
```

### Method 2: Web Interface

1. Run the app: `streamlit run app.py`
2. Navigate to "📚 Data Ingestion" page
3. Upload PDFs or configure web scraping
4. Click "Process"

### Recommended Data Sources

#### PDFs to Download
1. **Polity**: Indian Polity by M. Laxmikanth
2. **History**: 
   - India's Struggle for Independence (Bipan Chandra)
   - Ancient India (R.S. Sharma)
3. **Geography**: 
   - Certificate Physical Geography (G.C. Leong)
   - India: Physical Environment (NCERT Class 11)
4. **Economy**: Indian Economy by Ramesh Singh
5. **NCERT**: All Class 6-12 textbooks
6. **Current Affairs**: Monthly magazines (Yojana, Kurukshetra)

#### Web Sources (Auto-scraped)
- Insights on India (Current Affairs)
- IASbaba (Daily Updates)
- PIB (Government Press Releases)

## Using the Chatbot

### Basic Usage

1. Launch the app:
```bash
streamlit run app.py
```

2. Type your question in the chat input
3. View the AI-generated answer with sources

### Topic Filtering

Use the sidebar to filter by specific topics:
- History
- Geography
- Polity
- Economy
- Environment
- Science & Technology
- Current Affairs
- Ethics
- International Relations
- Internal Security

### Example Questions

**Polity:**
- "What is the structure of Indian Parliament?"
- "Explain the fundamental rights in the Constitution"
- "What are the powers of the President?"

**History:**
- "Describe the causes of the 1857 revolt"
- "What was the role of Gandhi in the freedom struggle?"

**Geography:**
- "Explain the monsoon system in India"
- "What are the major soil types in India?"

**Current Affairs:**
- "What are the recent government schemes?"
- "Explain the latest budget highlights"

## Practice Questions

### Generating Questions

1. Navigate to "📝 Practice Questions" page
2. Select topic and difficulty
3. Click "Generate New Question"

### Answering Questions

1. Read the generated question
2. Write your answer in the text area
3. Click "Submit Answer"
4. Get AI evaluation with:
   - Score out of 10
   - Strengths
   - Areas for improvement
   - Missing points

### Tips for Practice

- **Time yourself**: 2-3 minutes for short answers
- **Structure**: Use intro-body-conclusion format
- **Keywords**: Include relevant technical terms
- **Examples**: Support with facts and figures
- **Review**: Compare with model answers

## Advanced Features

### Custom Prompts

Modify prompts in `config/settings.py`:

```python
SYSTEM_PROMPT = """Your custom system prompt here"""

QA_PROMPT_TEMPLATE = """
Context: {context}
Question: {question}
Your custom instructions...
"""
```

### Batch Processing

Process multiple questions at once:

```python
from src.rag.rag_pipeline import RAGPipeline

pipeline = RAGPipeline()
questions = [
    "What is UPSC?",
    "Explain Indian Constitution",
    "What are fundamental rights?"
]

results = pipeline.batch_query(questions)
```

### Export Conversations

Save chat history for later review:

```python
import json

# In Streamlit app
chat_history = st.session_state.chat_history

with open('my_chat_history.json', 'w') as f:
    json.dump(chat_history, f, indent=2)
```

## Tips & Best Practices

### For Best Results

1. **Be Specific**: Ask clear, specific questions
2. **Use Keywords**: Include relevant UPSC terminology
3. **Check Sources**: Always verify source citations
4. **Cross-Reference**: Compare with standard textbooks
5. **Regular Updates**: Add new PDFs and scrape web content regularly

### Data Management

1. **Organize PDFs**: Name files clearly (e.g., "Laxmikanth_Polity_Ch1.pdf")
2. **Regular Backups**: Backup your ChromaDB database
3. **Clean Data**: Remove duplicate or low-quality PDFs
4. **Update Regularly**: Scrape web content weekly for current affairs

### Performance Optimization

1. **Chunk Size**: Smaller chunks (300-500) for precise answers
2. **Top K**: Use 3-5 contexts for faster responses
3. **Batch Processing**: Process multiple PDFs at once
4. **Cache**: Enable caching in settings for repeated queries

### Common Issues

**Slow Responses:**
- Reduce `TOP_K_RESULTS` to 3
- Use smaller `CHUNK_SIZE`
- Check internet connection

**Irrelevant Answers:**
- Increase `SIMILARITY_THRESHOLD`
- Add more relevant PDFs
- Use topic filtering

**API Errors:**
- Check API key in .env
- Verify API quota
- Check Gemini API status

## Monitoring & Maintenance

### Check Database Stats

```bash
python -c "from src.rag.chroma_db import ChromaDBManager; db = ChromaDBManager(); db.print_stats()"
```

### View Logs

```bash
# Check logs directory
ls logs/

# View latest log
tail -f logs/upsc_chatbot.log
```

### Reset Database

```bash
python ingest_data.py --reset
```

## Getting Help

1. Check README.md for overview
2. Review QUICKSTART.md for setup
3. Check logs for error messages
4. Open GitHub issue for bugs
5. Review source code for customization

---

**Happy Learning! 🎓**

