import faiss
import numpy as np
import json
import os
import openai
from langchain.embeddings.openai import OpenAIEmbeddings
from dotenv import load_dotenv
load_dotenv('.env')

# Initialize OpenAI Embeddings
embeddings = OpenAIEmbeddings()

# FAISS Index File
FAISS_INDEX_FILE = "feedback_index.faiss"
FAISS_DATA_FILE = "feedback_data.json"

# Create FAISS index (dimension = 1536 for OpenAI embeddings)
dimension = 1536
index = faiss.IndexFlatL2(dimension)

# Load previous stored data
if os.path.exists(FAISS_INDEX_FILE):
    faiss.read_index(FAISS_INDEX_FILE)
if os.path.exists(FAISS_DATA_FILE):
    with open(FAISS_DATA_FILE, "r") as f:
        feedback_data = json.load(f)
else:
    feedback_data = {}

def store_feedback(action: str, result: str):
    """ Stores feedback locally in FAISS """
    
    feedback_text = f"Action: {action}\nResult: {result}"
    
    # Convert feedback to embedding
    feedback_vector = embeddings.embed_query(feedback_text)

    # Convert to numpy array and add to FAISS
    vector_np = np.array([feedback_vector], dtype=np.float32)
    index.add(vector_np)

    # Store corresponding feedback text
    feedback_id = len(feedback_data)
    feedback_data[feedback_id] = feedback_text

    # Save FAISS index and data
    faiss.write_index(index, FAISS_INDEX_FILE)
    with open(FAISS_DATA_FILE, "w") as f:
        json.dump(feedback_data, f)
    
    return "Feedback stored successfully."

def retrieve_past_feedback(query: str, top_k=3):
    """ Retrieves top-k similar feedback from FAISS """
    
    # Convert query to embedding
    query_vector = np.array([embeddings.embed_query(query)], dtype=np.float32)

    # Search FAISS for similar vectors
    D, I = index.search(query_vector, top_k)

    # Retrieve corresponding feedback texts
    similar_feedbacks = [feedback_data.get(i, "No relevant feedback") for i in I[0] if i in feedback_data]

    return similar_feedbacks

async def decision_making_layer(query: str):
    """ Uses LLM with retrieved feedback to decide an action """

    # Retrieve relevant past feedback
    past_feedbacks = retrieve_past_feedback(query)

    context = "\n".join(past_feedbacks)

    prompt = f"""
    You are an intelligent AI agent with memory.
    Here is past feedback related to this query:

    {context}

    Now, analyze the user's input and determine the best action.

    Query: {query}

    Respond with structured JSON output:
    {{"action": "decided_action"}}
    """

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "system", "content": prompt}],
        api_key=os.getenv('OPEN_API_KEY')
    )

    return response['choices'][0]['message']['content']
