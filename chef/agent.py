from google.adk.agents import LlmAgent
from google.adk.tools import agent_tool
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from Expert_Finance.agent import get_agent as get_agent_finance
from Expert_Guide_Acquereur.agent import get_agent as get_agent_guide_acquereur
from Expert_Materiaux_Prestataire.agent import create_timeout_resistant_agent as get_agent_materiaux_prestataire

def lire_instructions():
    chemin_instructions = os.path.join(os.path.dirname(__file__), "instructions.txt")
    
    with open(chemin_instructions, 'r', encoding='utf-8') as fichier:
        return fichier.read()

def create_chef_orchestrateur():
    
    print("Initialisation des agents experts...")
    
    try:
        agent_finance = get_agent_finance()
        agent_guide_acquereur = get_agent_guide_acquereur()
        agent_materiaux_prestataire = get_agent_materiaux_prestataire()
        
        print("Agents experts initialisés avec succès")
        
        finance_tool = agent_tool.AgentTool(agent=agent_finance)
        acquereur_tool = agent_tool.AgentTool(agent=agent_guide_acquereur)
        materiaux_prestataire_tool = agent_tool.AgentTool(agent=agent_materiaux_prestataire)
        print("AgentTools créés avec succès")
        
        instructions = lire_instructions()
        chef_agent = LlmAgent(
            name="Chef_Orchestrateur",
            model="gemini-2.5-flash",
            instruction=instructions,
            tools=[finance_tool, acquereur_tool, materiaux_prestataire_tool]
        )
        
        print("Chef Orchestrateur créé avec succès")
        print(f"Outils disponibles: {len(chef_agent.tools)} experts")
        
        return chef_agent
        
    except Exception as e:
        print(f"Erreur lors de la création du Chef Orchestrateur: {e}")
        raise

try:
    root_agent = create_chef_orchestrateur()
    print("Chef Orchestrateur prêt à fonctionner!")
except Exception as e:
    print(f"Échec de l'initialisation: {e}")
    root_agent = None

def get_agent():
    if root_agent is None:
        return create_chef_orchestrateur()
    return root_agent

