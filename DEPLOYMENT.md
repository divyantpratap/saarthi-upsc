# 🚀 Deployment Guide - UPSC AI Mentor

## Deployment Options

### 1. Local Development (Recommended for Testing)

```bash
# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env and add GEMINI_API_KEY

# Ingest data
python ingest_data.py --mode all

# Run application
streamlit run app.py
```

Access at: `http://localhost:8501`

### 2. Streamlit Cloud (Free Hosting)

#### Prerequisites
- GitHub account
- Gemini API key

#### Steps

1. **Push to GitHub**
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin <your-repo-url>
git push -u origin main
```

2. **Deploy on Streamlit Cloud**
- Go to https://share.streamlit.io
- Click "New app"
- Select your repository
- Set main file: `app.py`
- Click "Deploy"

3. **Add Secrets**
- In Streamlit Cloud dashboard, go to "Settings" → "Secrets"
- Add:
```toml
GEMINI_API_KEY = "your_api_key_here"
```

4. **Pre-populate Database (Optional)**
- Run locally: `python ingest_data.py --mode all`
- Commit the `data/embeddings/` directory
- Push to GitHub

**Note**: Streamlit Cloud has storage limitations. For large databases, consider other options.

### 3. Docker Deployment

#### Create Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8501

# Run application
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

#### Create docker-compose.yml

```yaml
version: '3.8'

services:
  upsc-chatbot:
    build: .
    ports:
      - "8501:8501"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
```

#### Deploy

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### 4. AWS Deployment

#### Option A: EC2

1. **Launch EC2 Instance**
   - Ubuntu 22.04 LTS
   - t2.medium or larger
   - Open port 8501

2. **Setup**
```bash
# SSH into instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# Install dependencies
sudo apt update
sudo apt install python3-pip git -y

# Clone repository
git clone <your-repo-url>
cd UPSC

# Install Python packages
pip3 install -r requirements.txt

# Setup environment
echo "GEMINI_API_KEY=your_key" > .env

# Ingest data
python3 ingest_data.py --mode all

# Run with nohup
nohup streamlit run app.py --server.port=8501 &
```

3. **Access**
   - http://your-ec2-ip:8501

#### Option B: ECS (Elastic Container Service)

1. Build and push Docker image to ECR
2. Create ECS task definition
3. Deploy to ECS cluster
4. Use Application Load Balancer for HTTPS

### 5. Google Cloud Platform

#### Cloud Run

1. **Build Container**
```bash
gcloud builds submit --tag gcr.io/PROJECT_ID/upsc-chatbot
```

2. **Deploy**
```bash
gcloud run deploy upsc-chatbot \
  --image gcr.io/PROJECT_ID/upsc-chatbot \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY=your_key
```

### 6. Heroku

1. **Create Procfile**
```
web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
```

2. **Deploy**
```bash
heroku create upsc-ai-mentor
heroku config:set GEMINI_API_KEY=your_key
git push heroku main
```

## Production Considerations

### 1. Security

- **API Keys**: Use environment variables, never commit
- **HTTPS**: Use SSL/TLS in production
- **Authentication**: Add user authentication if needed
- **Rate Limiting**: Implement to prevent abuse

### 2. Performance

- **Caching**: Enable Streamlit caching
- **Database**: Use persistent storage for ChromaDB
- **CDN**: Use CDN for static assets
- **Load Balancing**: For multiple instances

### 3. Monitoring

- **Logging**: Configure proper logging
- **Metrics**: Monitor API usage, response times
- **Alerts**: Set up alerts for errors
- **Analytics**: Track user interactions

### 4. Backup

```bash
# Backup ChromaDB
tar -czf chroma_backup_$(date +%Y%m%d).tar.gz data/embeddings/

# Backup to S3 (example)
aws s3 cp chroma_backup_*.tar.gz s3://your-bucket/backups/
```

### 5. Scaling

- **Horizontal**: Multiple app instances with shared database
- **Vertical**: Increase instance size for more resources
- **Database**: Consider managed vector database (Pinecone, Weaviate)

## Environment Variables

Required:
```bash
GEMINI_API_KEY=your_gemini_api_key
```

Optional:
```bash
LOG_LEVEL=INFO
CHROMA_DB_PATH=./data/embeddings/chroma_db
CHUNK_SIZE=500
TOP_K_RESULTS=5
```

## Cost Estimation

### Gemini API
- **Free Tier**: 60 requests/minute
- **Paid**: $0.00025 per 1K characters

### Hosting
- **Streamlit Cloud**: Free (with limitations)
- **AWS EC2 t2.medium**: ~$30/month
- **Google Cloud Run**: Pay per use (~$10-50/month)
- **Heroku**: $7-25/month

### Storage
- **ChromaDB**: ~1GB for 10K documents
- **S3/Cloud Storage**: ~$0.023/GB/month

## Maintenance

### Regular Tasks
```bash
# Update dependencies
pip install -r requirements.txt --upgrade

# Update data
python ingest_data.py --mode web --articles 50

# Backup database
./backup_database.sh

# Check logs
tail -f logs/upsc_chatbot.log
```

### Monitoring Script

```bash
#!/bin/bash
# monitor.sh

# Check if app is running
if ! pgrep -f "streamlit run app.py" > /dev/null; then
    echo "App not running, restarting..."
    nohup streamlit run app.py &
fi

# Check disk space
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "Warning: Disk usage is ${DISK_USAGE}%"
fi
```

## Troubleshooting

### App won't start
```bash
# Check logs
streamlit run app.py --logger.level=debug

# Verify installation
python verify_installation.py
```

### Database errors
```bash
# Reset database
python ingest_data.py --reset
```

### Memory issues
- Reduce `CHUNK_SIZE` in config
- Reduce `TOP_K_RESULTS`
- Increase instance memory

## Support

For deployment issues:
1. Check logs in `logs/` directory
2. Review error messages
3. Verify environment variables
4. Check API quotas
5. Open GitHub issue

---

**Good luck with your deployment! 🚀**

