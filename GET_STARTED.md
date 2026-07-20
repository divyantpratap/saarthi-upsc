# 🎯 Get Started with UPSC AI Mentor

## What You've Built

A complete, production-ready RAG (Retrieval-Augmented Generation) chatbot for UPSC preparation featuring:

✅ **Gemini 2.5 Flash** integration for intelligent responses  
✅ **ChromaDB** vector database for semantic search  
✅ **Parallel PDF processing** (100 pages in <2 minutes)  
✅ **Web scraping** from 3 trusted UPSC sources  
✅ **Modern Streamlit UI** with chat interface  
✅ **Practice questions** with AI evaluation  
✅ **Source citations** for transparency  

## 📋 Prerequisites Checklist

Before you start, make sure you have:

- [ ] Python 3.8 or higher installed
- [ ] Internet connection
- [ ] Gemini API key (free from Google)
- [ ] 2GB free disk space
- [ ] Basic command line knowledge

## 🚀 Installation Steps

### Step 1: Verify Installation

```bash
# Run verification script
python verify_installation.py
```

This will check:
- Python version
- Directory structure
- Required files
- Dependencies status

### Step 2: Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt
```

This installs:
- google-generativeai (Gemini API)
- chromadb (Vector database)
- streamlit (Web interface)
- PyPDF2, pdfplumber, PyMuPDF (PDF processing)
- BeautifulSoup4 (Web scraping)
- And 20+ other packages

**Expected time**: 2-5 minutes

### Step 3: Get Gemini API Key

1. Visit: https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated key

**Free tier includes**: 60 requests/minute (sufficient for personal use)

### Step 4: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env file and add your API key
# Windows: notepad .env
# Mac/Linux: nano .env
```

Add this line:
```
GEMINI_API_KEY=your_actual_api_key_here
```

### Step 5: Add Data

You have two options:

#### Option A: Quick Start (No PDFs needed)
```bash
# Scrape web content only (takes 2-3 minutes)
python ingest_data.py --mode web --articles 20
```

This will scrape:
- Insights on India (current affairs)
- IASbaba (daily updates)
- PIB (government releases)

#### Option B: Full Setup (With PDFs)
```bash
# 1. Add PDFs to data/raw/ directory
# Recommended: Laxmikanth Polity, NCERT books, previous papers

# 2. Process everything
python ingest_data.py --mode all --articles 30
```

**Expected time**: 5-10 minutes depending on PDF count

### Step 6: Launch the App

```bash
streamlit run app.py
```

The app will automatically open in your browser at:
```
http://localhost:8501
```

## 🎓 First Steps in the App

### 1. Check Database Status
- Look at the sidebar
- Click "Refresh Stats"
- Verify documents are loaded

### 2. Ask Your First Question
Try these examples:
- "What is the structure of Indian Parliament?"
- "Explain fundamental rights in the Constitution"
- "What are the recent government schemes?"

### 3. Explore Features
- **Topic Filter**: Select specific UPSC topics
- **Show Sources**: Toggle source citations
- **Number of Contexts**: Adjust retrieval depth

### 4. Try Practice Mode
- Navigate to "📝 Practice Questions"
- Select a topic
- Generate a question
- Write your answer
- Get AI evaluation

### 5. Add More Data
- Go to "📚 Data Ingestion"
- Upload PDFs or scrape more content
- Build your knowledge base

## 📚 Recommended PDFs to Add

### Essential Books (Priority 1)
1. **Indian Polity** by M. Laxmikanth
2. **Indian Economy** by Ramesh Singh
3. **Certificate Physical Geography** by G.C. Leong
4. **India's Struggle for Independence** by Bipan Chandra

### NCERT Textbooks (Priority 2)
- Class 6-12: History, Geography, Polity, Science
- Focus on Class 11-12 for depth

### Current Affairs (Priority 3)
- Previous year question papers
- Monthly magazines (Yojana, Kurukshetra)
- Government reports

## 🔧 Common Issues & Solutions

### Issue: "GEMINI_API_KEY not found"
**Solution**: 
```bash
# Make sure .env file exists in project root
# Check that API key is correctly set
cat .env  # Mac/Linux
type .env  # Windows
```

### Issue: "No documents in database"
**Solution**:
```bash
# Run data ingestion
python ingest_data.py --mode web --articles 10
```

### Issue: "Module not found" errors
**Solution**:
```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

### Issue: Port 8501 already in use
**Solution**:
```bash
# Use different port
streamlit run app.py --server.port 8502
```

### Issue: Slow responses
**Solution**:
- Reduce contexts in sidebar (try 3 instead of 5)
- Check internet connection
- Verify API quota

## 📖 Documentation Guide

- **README.md**: Project overview and features
- **QUICKSTART.md**: 5-minute setup guide
- **USAGE_GUIDE.md**: Comprehensive usage instructions
- **DEPLOYMENT.md**: Production deployment options
- **PROJECT_SUMMARY.md**: Technical architecture details

## 🎯 Next Steps

### Week 1: Build Your Knowledge Base
- [ ] Add 10-15 essential PDFs
- [ ] Scrape web content weekly
- [ ] Test with various questions
- [ ] Familiarize with interface

### Week 2: Regular Usage
- [ ] Ask 10-20 questions daily
- [ ] Practice with generated questions
- [ ] Review source citations
- [ ] Add more PDFs as needed

### Week 3: Optimization
- [ ] Adjust settings in config/settings.py
- [ ] Fine-tune chunk size and retrieval
- [ ] Organize PDFs by topic
- [ ] Create study schedule

### Ongoing
- [ ] Update web content weekly
- [ ] Add new PDFs regularly
- [ ] Track your progress
- [ ] Share feedback

## 💡 Pro Tips

1. **Start Small**: Begin with web scraping, add PDFs gradually
2. **Verify Sources**: Always check source citations
3. **Use Filters**: Topic filters improve accuracy
4. **Practice Daily**: Use practice mode for exam prep
5. **Organize PDFs**: Name files clearly (e.g., "Polity_Ch1.pdf")
6. **Regular Updates**: Scrape web content weekly for current affairs
7. **Backup Data**: Backup your ChromaDB database regularly

## 🆘 Getting Help

1. **Check Logs**: Review `logs/` directory for errors
2. **Run Verification**: `python verify_installation.py`
3. **Read Docs**: Check USAGE_GUIDE.md for details
4. **GitHub Issues**: Open an issue for bugs
5. **Community**: Join UPSC preparation forums

## 🎉 You're Ready!

Your UPSC AI Mentor is now set up and ready to help you prepare for the exam.

**Remember**: This is a tool to supplement your preparation, not replace it. Always verify information with standard textbooks and official sources.

---

**Best of luck with your UPSC preparation! 🎓**

Made with ❤️ for UPSC Aspirants

