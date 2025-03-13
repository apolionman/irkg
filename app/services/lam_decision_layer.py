from app.services.lam_feedback_layer import *
import os
from dotenv import load_dotenv
from openai import OpenAI

client = OpenAI()
load_dotenv('/home/dgx/dgx_irkg_be/.env')

OPEN_AI_KEY = os.getenv('OPENAI_API_KEY')

async def decision_making_layer(query: str):
    """ Uses LLM with retrieved feedback to decide an action """

    # Retrieve relevant past feedback
    past_feedbacks = retrieve_relevant_context(query)

    context = "\n".join(past_feedbacks)

    prompt = f"""
    You are an intelligent AI agent with memory.
    Here is past feedback related to this query:

    {context}

    Now, analyze the user's input and determine the best action.

    Query: {query}

    If the query is about calibrating the CELLINK X6, return:
    {{"action": "calibrate_cellink_x6"}}

    If the query is about running an SQL query, return:
    {{"action": "run_sql_query"}}

    Otherwise, return:
    {{"action": "provide_instructions", "instructions": "Unfortunately, I don't have explicit instructions for this."}}

    Use the provided context if it helps:
    {context}

    Respond with structured JSON output:
    {{"action": "decided_action"}}
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": prompt}]
    )

    return response.choices[0].message.content