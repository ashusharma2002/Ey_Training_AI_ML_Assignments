# 🏦 FinSight — Financial RAG System (Streamlit)

An AI Research Analyst that answers questions about Apple's SEC 10-K filing using RAG.

## 🚀 Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 🌐 Deploy on Streamlit Cloud

1. Push this repo to GitHub
2. Go to share.streamlit.io
3. Connect your GitHub repo
4. Add secrets in Streamlit Cloud dashboard:
   - AZURE_OPENAI_ENDPOINT
   - AZURE_OPENAI_KEY
   - AZURE_OPENAI_DEPLOYMENT

## 🛠️ Tech stack
- Streamlit · LangChain · FAISS · HuggingFace · Azure OpenAI GPT-4o
