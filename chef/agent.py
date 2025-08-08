from google.adk.agents import LlmAgent
from google.adk.tools import agent_tool
import os
import sys

# Ajout du répertoire parent au path pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import des agents experts
from Expert_Finance.agent import get_agent as get_agent_finance
from Expert_Guide_Acquereur.agent import get_agent as get_agent_guide_acquereur
from Expert_Materiaux_Prestataire.agent import create_timeout_resistant_agent as get_agent_materiaux_prestataire

def lire_instructions():
    """Lit les instructions depuis le fichier instructions.txt"""
    chemin_instructions = os.path.join(os.path.dirname(__file__), "instructions.txt")
    
    try:
        with open(chemin_instructions, 'r', encoding='utf-8') as fichier:
            return fichier.read()
    except FileNotFoundError:
        print(f"⚠️ Fichier {chemin_instructions} non trouvé, utilisation des instructions par défaut")
        return """Vous êtes le Chef Orchestrateur qui coordonne les experts spécialisés.
        
        Vous avez accès à 3 experts :
        - finance_tool : Expert en finance pour les questions de budget, emprunt, coûts, fiscalité, capacité d'emprunt
        - acquereur_tool : Expert guide acquéreur pour les questions d'acquisition immobilière, étapes, promoteurs, FNPI
        - materiaux_prestataire_tool : Expert matériaux/prestataires pour les questions de construction, fournisseurs, matériaux
        
        Analysez chaque question et utilisez l'expert le plus approprié selon le domaine de la question.
        
        Pour les questions financières (budget, emprunt, coûts) → utilisez finance_tool
        Pour les questions d'acquisition immobilière (étapes, promoteurs) → utilisez acquereur_tool  
        Pour les questions de construction/matériaux → utilisez materiaux_prestataire_tool
        """
    except Exception as e:
        print(f"❌ Erreur lecture instructions: {e}")
        return "Vous êtes le Chef Orchestrateur qui coordonne les experts spécialisés."

def create_chef_orchestrateur():
    """Crée l'agent orchestrateur principal avec AgentTools"""
    
    print("🔧 Initialisation des agents experts...")
    
    try:
        # Initialisation des agents experts
        agent_finance = get_agent_finance()
        agent_guide_acquereur = get_agent_guide_acquereur()
        agent_materiaux_prestataire = get_agent_materiaux_prestataire()
        
        print("✅ Agents experts initialisés avec succès")
        
        # Création des AgentTools
        finance_tool = agent_tool.AgentTool(agent=agent_finance)
        acquereur_tool = agent_tool.AgentTool(agent=agent_guide_acquereur)
        materiaux_prestataire_tool = agent_tool.AgentTool(agent=agent_materiaux_prestataire)
        print("✅ AgentTools créés avec succès")
        
        # Lecture des instructions
        instructions = lire_instructions()
        
        # Création de l'agent orchestrateur principal
        chef_agent = LlmAgent(
            name="Chef_Orchestrateur",
            model="gemini-2.5-flash",
            instruction=instructions,
            tools=[finance_tool, acquereur_tool, materiaux_prestataire_tool]
        )
        
        print("✅ Chef Orchestrateur créé avec succès")
        print(f"📋 Outils disponibles: {len(chef_agent.tools)} experts")
        
        return chef_agent
        
    except Exception as e:
        print(f"❌ Erreur lors de la création du Chef Orchestrateur: {e}")
        raise

# Création de l'agent orchestrateur principal
try:
    root_agent = create_chef_orchestrateur()
    print("🎯 Chef Orchestrateur prêt à fonctionner!")
except Exception as e:
    print(f"❌ Échec de l'initialisation: {e}")
    root_agent = None

# Export de l'agent pour utilisation externe
def get_agent():
    """Retourne l'agent orchestrateur"""
    if root_agent is None:
        return create_chef_orchestrateur()
    return root_agent

if __name__ == "__main__":
    if root_agent:
        print("🚀 Chef Orchestrateur initialisé avec succès!")
        print("💡 Utilisez get_agent() pour obtenir l'instance de l'agent")
    else:
        print("❌ Échec de l'initialisation du Chef Orchestrateur")