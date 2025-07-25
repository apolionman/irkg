from app.services.lam_feedback_layer import *
import os
from dotenv import load_dotenv
from openai import OpenAI

client = OpenAI()
load_dotenv('/app/.env')

OPEN_AI_KEY = os.getenv('OPENAI_API_KEY')

async def decision_making_layer(query: str):
    """ Uses LLM with retrieved feedback to decide an action """

    # Retrieve relevant past feedback
    past_feedbacks = retrieve_relevant_context(query)

    context = "\n".join(past_feedbacks)

    prompt = f"""
    You are an AI Scientist designed to support Drug Discovery, Precision Medicine, and Laboratory Automation.
    You have access to a knowledge base containing laboratory workflows, equipment usage, and scientific methodologies.

    **Query:**
    "{query}"

    **Context from Knowledge Base:**
    {context}

    --- Decision Rules ---
    - If the query asks to **activate, calibrate, turn on, start, or execute** any lab machine, return:
      {{"action": "execute", "machine": "<detected_machine_name>", "task": "<task_description>"}}

    - If the query is about **creating a workflow** for an experiment, return:
      {{"action": "generate_workflow", "workflow_steps": ["Step 1", "Step 2", "Step 3"]}}

    - If the query asks for **scientific information** or lab-related details, return:
      {{"action": "provide_information", "details": "{context}"}}

    --- Output Format (JSON) ---
    Respond only with a structured JSON object matching one of the three actions above.
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": prompt}]
    )

    return response.choices[0].message.content