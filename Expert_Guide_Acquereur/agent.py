from google.adk.agents import LlmAgent
from google.adk.tools import VertexAiSearchTool
import os
from dotenv import load_dotenv

load_dotenv()

DATA_STORE_ID = os.getenv("DATA_STORE_ID")

def lire_instructions():
    chemin_instructions = os.path.join(os.path.dirname(__file__), "instructions.txt")
    
    with open(chemin_instructions, 'r', encoding='utf-8') as fichier:
        return fichier.read()



def create_guide_acquereur_agent():
    instructions = lire_instructions()
    
    instructions_completes = f"""
{instructions}

Vous pouvez rechercher dans la base de connaissances Vertex AI pour des informations détaillées sur l'immobilier au Maroc.
"""
    
    search_tool = VertexAiSearchTool(data_store_id=DATA_STORE_ID)
    
    agent = LlmAgent(
        name="Expert_Guide_Acquereur",
        model="gemini-2.0-flash",
        instruction=instructions_completes,
        tools=[search_tool]
    )
    
    return agent

def get_agent():
    return create_guide_acquereur_agent()

root_agent = create_guide_acquereur_agent()