# 🤖 STEve – ST Engineering Chatbot

An AI-powered chatbot for ST Engineering, built using **React (frontend)** and **Flask (backend)** with **Google Gemini API integration**. It features a lightweight **RAG (Retrieval-Augmented Generation)** component that enhances response quality by searching a curated FAQ database.

---

## Live Demo

- **Frontend (Netlify):** https://your-netlify-link.netlify.app  
- **Backend (Render):** https://ste-chatbot-bryan-low.onrender.com

---

## Project Structure

```
ste-chatbot/
├── backend/                   # Flask server + Gemini & RAG logic
│   ├── app.py                 # Main backend application
│   ├── owasp_faq.csv          # FAQ data for retrieval
│   ├── requirements.txt       # Python dependencies
│   └── .env.example           # Environment variable template
└── frontend/                  # React + Vite chatbot interface
    ├── src/
    │   └── components/
    │       └── ChatWidget.jsx # Main chatbot widget
    ├── public/
    └── ...
```

---

## Local Setup

### Prerequisites

- Node.js (v18+)
- Python 3.9+
- Git

---

### Backend (Flask + Gemini)

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file with your Gemini API key:
   ```
   GEMINI_API_KEY=your_google_gemini_api_key
   ```

4. Start the Flask backend:
   ```bash
   python app.py
   ```

---

### 💬 Frontend (React + Vite)

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. In `ChatWidget.jsx`, set the backend URL to:
   ```js
   const API_URL = 'http://localhost:5000';
   ```

4. Start the frontend:
   ```bash
   npm run dev
   ```
---

## Approach

1. **Classification**: Each user message is classified as "valid" or "unclear" using Gemini.
2. **RAG Search**: For valid messages, the question is checked against the FAQ using TF-IDF and cosine similarity.
3. **Response Generation**:
   - If similarity > 0.75: exact FAQ answer is returned.
   - Otherwise: Gemini generates a contextual reply using conversation history.

---

## RAG Component Details

- **Vectorization**: `TfidfVectorizer` from scikit-learn
- **Similarity**: Cosine similarity
- **Threshold**: 0.75 confidence to trigger RAG response
- **Data Source**: `owasp_faq.csv` – modifiable CSV with FAQ question/answer pairs
