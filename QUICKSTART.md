# 🚀 Quick Start Guide - UPSC AI Mentor

Get your UPSC AI chatbot running in 5 minutes!

## Step 1: Install Dependencies (2 minutes)

```bash
# Install Python packages
pip install -r requirements.txt
```

## Step 2: Get Gemini API Key (1 minute)

1. Visit: https://makersuite.google.com/app/apikey
2. Click "Create API Key"
3. Copy your API key

## Step 3: Configure Environment (30 seconds)

```bash
# Create .env file
echo "GEMINI_API_KEY=your_api_key_here" > .env
```

Replace `your_api_key_here` with your actual API key.

## Step 4: Add Data (1 minute)

**Option A: Quick Test (No PDFs needed)**
```bash
# Scrape web content only
python ingest_data.py --mode web --articles 10
```

**Option B: With PDFs**
```bash
# 1. Add PDFs to data/raw/ folder
# 2. Run ingestion
python ingest_data.py --mode all
```

## Step 5: Launch App (30 seconds)

```bash
streamlit run app.py
```

The app will open at: http://localhost:8501

## 🎉 You're Ready!

Try asking:
- "What is the structure of Indian Parliament?"
- "Explain the fundamental rights in Indian Constitution"
- "What are the recent government schemes?"

## 📚 Recommended PDFs to Add

1. **Polity**: Indian Polity by M. Laxmikanth
2. **History**: India's Struggle for Independence by Bipan Chandra
3. **Geography**: Certificate Physical Geography by G.C. Leong
4. **Economy**: Indian Economy by Ramesh Singh
5. **NCERT**: Class 6-12 textbooks (History, Geography, Polity, Science)

## 🔧 Troubleshooting

### Error: "GEMINI_API_KEY not found"
- Make sure you created `.env` file with your API key
- Check that the file is in the project root directory

### Error: "No documents in database"
- Run data ingestion first: `python ingest_data.py --mode web`

### App won't start
- Check if port 8501 is available
- Try: `streamlit run app.py --server.port 8502`

## 💡 Tips

1. **Start Small**: Begin with web scraping (no PDFs needed)
2. **Add PDFs Gradually**: Add 5-10 PDFs at a time
3. **Test Queries**: Try different types of questions
4. **Check Sources**: Always verify the source citations
5. **Practice Mode**: Use the Practice Questions page for exam prep

## 📖 Next Steps

1. Explore the **Data Ingestion** page to upload more PDFs
2. Try the **Practice Questions** page for exam preparation
3. Adjust settings in `config/settings.py` for customization
4. Read the full README.md for advanced features

## 🆘 Need Help?

- Check README.md for detailed documentation
- Review error logs in `logs/` directory
- Open an issue on GitHub

---

**Happy Learning! 🎓**

