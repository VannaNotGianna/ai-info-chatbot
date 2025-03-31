import os
import json
import openai
import requests
import faiss
import numpy as np
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI
from sklearn.feature_extraction.text import TfidfVectorizer
import creds

#load api
load_dotenv()
client = OpenAI(api_key=creds.apikeysecret)

#Web Scraper
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MyScraperBot/1.0)"}
SITEMAP_URL = "https://www.able.co/sitemap.xml"

CACHE_FILE = "data/cache.json"
INDEX_FILE = "data/vector_store.index"
DOCS_FILE = "data/docs.json"
RAW_TEXT_FILE = "data/raw_text.json"

#load or init cache
def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=4)

def get_urls_from_sitemap():
    response = requests.get(SITEMAP_URL, headers=HEADERS)
    if response.status_code != 200:
        return []
    soup = BeautifulSoup(response.text, "xml")
    return [loc.text for loc in soup.find_all("loc")]

def extract_text_from_page(url):
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        return ""
    soup = BeautifulSoup(response.text, "html.parser")
    return " ".join([tag.get_text(strip=True) for tag in soup.find_all(["h1", "h2", "h3", "p"])])

def scrape_and_save():
    urls = get_urls_from_sitemap()
    existing_data = []
    if os.path.exists(RAW_TEXT_FILE):
        with open(RAW_TEXT_FILE, "r", encoding="utf-8") as f:
            existing_data = json.load(f)
    existing_urls = {entry["url"] for entry in existing_data}
    
    new_data = []
    for url in urls:
        if url not in existing_urls:
            text = extract_text_from_page(url)
            if text:
                new_data.append({"url": url, "content": text})
    
    if new_data:
        all_data = existing_data + new_data
        with open(RAW_TEXT_FILE, "w", encoding="utf-8") as f:
            json.dump(all_data, f, indent=4, ensure_ascii=False)
        print("New data scraped and saved!")
    else:
        print("No new data found.")

def generate_embeddings(texts):
    embeddings = [client.embeddings.create(input=t, model="text-embedding-3-small").data[0].embedding for t in texts]
    return np.array(embeddings, dtype=np.float32)

def build_vector_store():
    with open(RAW_TEXT_FILE, "r", encoding="utf-8") as f:
        docs = json.load(f)
    texts = [doc["content"] for doc in docs]
    
    if os.path.exists(INDEX_FILE):
        index = faiss.read_index(INDEX_FILE)
        existing_size = index.ntotal
        new_embeddings = generate_embeddings(texts[existing_size:])
        if new_embeddings.shape[0] > 0:
            index.add(new_embeddings)
            faiss.write_index(index, INDEX_FILE)
            print("FAISS index updated with new data!")
        else:
            print("No new data to update FAISS index.")
    else:
        embeddings = generate_embeddings(texts)
        index = faiss.IndexFlatL2(embeddings.shape[1])
        index.add(embeddings)
        faiss.write_index(index, INDEX_FILE)
        print("New FAISS index built!")
    
    with open(DOCS_FILE, "w", encoding="utf-8") as f:
        json.dump(docs, f, indent=4)
    print("Document store updated!")

def query_chatbot(question):
    cache = load_cache()
    if question in cache:
        print("(Cached Response)")
        return cache[question]
    
    index = faiss.read_index(INDEX_FILE)
    with open(DOCS_FILE, "r", encoding="utf-8") as f:
        docs = json.load(f)
    
    question_embedding = np.array(
        [client.embeddings.create(input=question, model="text-embedding-3-small").data[0].embedding],
        dtype=np.float32
    )
    
    D, I = index.search(question_embedding, k=3)
    if D[0][0] > 1.0:
        return "I couldn't find an exact answer on Able's website, but I can try to help! Could you clarify?"
    
    context = "\n".join([docs[i]["content"] for i in I[0]])
    
    prompt = f"""
    You are a helpful assistant. Answer the following question based on the provided context:
    Context: {context}
    Question: {question}
    """
    
    response = client.chat.completions.create(
        model="gpt-4o", messages=[{"role": "user", "content": prompt}]
    ).choices[0].message.content.strip()
    
    cache[question] = response
    save_cache(cache)
    return response

if __name__ == "__main__":
    scrape_and_save()
    build_vector_store()
    print("Owl AI: Hi there! 👋 I'm Owl AI, your assistant for all things Able.")
    print("Ask me anything, and I'll do my best to help! Type 'exit' to stop.")
    while True:
        query = input("\nYou: ")
        if query.lower() == "exit":
            print("Owl AI: Goodbye! Have a great day! 😊")
            break
        print(f"Owl AI: {query_chatbot(query)}")
