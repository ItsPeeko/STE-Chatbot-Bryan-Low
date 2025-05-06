from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
from dotenv import load_dotenv
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv()

# Load company FAQ
faq_df = pd.read_csv("owasp_faq.csv", encoding='ISO-8859-1')

# Preprocess questions to lowercase
faq_df["question_clean"] = faq_df["question"].str.lower()

# Fit and transform on the cleaned version
vectorizer = TfidfVectorizer().fit(faq_df["question_clean"])
faq_vectors = vectorizer.transform(faq_df["question_clean"])

app = Flask(__name__)
CORS(app)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# --- CLASSIFICATION PROMPT ---
def classify_message(user_input):
    prompt = (
        "You are a classification agent. Your task is to classify the following user message as either:\n\n"
        "- valid: if it is a genuine help request, technical question, or meaningful sentence.\n"
        "- unclear: if it is a greeting, nonsense, or not actionable.\n\n"
        "Respond with only one word: valid or unclear.\n\n"
        f"User: {user_input}"
    )

    response = requests.post(
        GEMINI_ENDPOINT,
        params={"key": GEMINI_API_KEY},
        headers={"Content-Type": "application/json"},
        json={
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
    )

    if response.status_code == 200:
        label = response.json()['candidates'][0]['content']['parts'][0]['text'].strip().lower()
        return label
    else:
        print("Classification API error:", response.text)
        return "error"

def retrieve_faq_answer(user_input, top_k=1):
    user_vec = vectorizer.transform([user_input.lower()])
    similarities = cosine_similarity(user_vec, faq_vectors).flatten()
    top_indices = similarities.argsort()[-top_k:][::-1]
    top_score = similarities[top_indices[0]]

    print(f"[RAG] Top match score: {top_score:.4f}")

    if top_score > 0.75:
        matched = faq_df.iloc[top_indices[0]]['answer']
        print(f"[RAG] Matched FAQ: {faq_df.iloc[top_indices[0]]['question']} → {matched}")
        return matched, top_score
    else:
        if top_score > 0.3:
            print("[RAG] Match too weak. Skipping RAG injection, but logging for debug.")
        else:
            print("[RAG] No relevant FAQ match found.")
        return None, top_score



def generate_response(history, extra_context=None):
    system_prompt = (
        "You are STEve, a knowledgeable assistant working for ST Engineering Singapore. "
        "You are helpful, concise, and professional, with deep knowledge in cybersecurity, careers, and company services. "
        "Avoid repeating generic greetings like 'how can I help you today?' and instead give direct answers."
    )

    if extra_context:
        ## To show taht RAG answer is used and gemini does not remove it due to other system prompts ##
        system_prompt += (
            f"\n\nHere is some verified internal info (marked as '[RAG answer]') that you can cite when relevant:\n"
            f"[RAG answer] {extra_context}"
        )
        print("[RAG] Injecting extra context into Gemini:")
        print(extra_context)

    contents = [{"role": "user", "parts": [{"text": system_prompt}]}] + history

    response = requests.post(
        GEMINI_ENDPOINT,
        params={"key": GEMINI_API_KEY},
        headers={"Content-Type": "application/json"},
        json={ "contents": contents }
    )

    if response.status_code == 200:
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    else:
        print("Generation API error:", response.text)
        return "Sorry, there was an issue generating a response."


@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_input = data.get('message')
        state = data.get('state', 'initial')  # 'initial', 'ready'

        if state == 'ready':
            history = data.get('history')
            original_question = data.get('original_question') or ""

            if not original_question.strip():
                print("[RAG] No original question provided. Skipping RAG.")
                return jsonify({'reply': "I'm here to help with questions about ST Engineering. Could you clarify what you're looking for?"})

            label = classify_message(original_question)
            if label != "valid":
                return jsonify({'reply': "I'm not sure I understood that. Could you rephrase or ask something related to ST Engineering?"})

            def is_rag_answer_generic(answer: str):
                generic_keywords = ["please contact us", "check our careers page", "i do not have"]
                return any(phrase in answer.lower() for phrase in generic_keywords)

            if not history:
                return jsonify({'reply': "Missing conversation context."}), 400

            matched_faq, match_score = retrieve_faq_answer(original_question)

            if match_score > 0.75 and matched_faq:
                print("[RAG] High confidence match. Returning RAG answer directly.")
                final_reply = matched_faq
            else:
                print("[RAG] Skipping RAG injection. Letting Gemini answer freely.")
                final_reply = generate_response(history)

            return jsonify({'reply': final_reply})


        if not user_input:
            return jsonify({'reply': "I didn't receive any message."}), 400


        # Otherwise classify message first
        label = classify_message(user_input)
        if label == "valid":
            return jsonify({'reply': "Got it! Just before I answer — have you checked the FAQ page? It might already contain what you're looking for.", 'status': 'awaiting_confirmation'})
        elif label == "unclear":
            return jsonify({'reply': "Sorry, I didn’t quite understand that. Could you rephrase your question?", 'status': 'unclear'})
        else:
            return jsonify({'reply': "Sorry, I'm having trouble understanding your message. Try again later."})

    except Exception as e:
        print("Internal server error:", str(e))
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
