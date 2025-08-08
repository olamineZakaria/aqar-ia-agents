from google.adk.agents import LlmAgent
import os

# Lecture des instructions depuis le fichier txt
def lire_instructions():
    """Lit les instructions depuis le fichier instructions.txt"""
    chemin_instructions = os.path.join(os.path.dirname(__file__), "instructions.txt")
    
    try:
        with open(chemin_instructions, 'r', encoding='utf-8') as fichier:
            return fichier.read()
    except FileNotFoundError:
        print(f"Erreur: Le fichier {chemin_instructions} n'a pas été trouvé.")
        return ""
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier: {e}")
        return ""

# Lecture des instructions depuis le fichier
instructions = lire_instructions()

# Définition de l'agent expert en finance
agent = LlmAgent(
    name="Agent_Expert_Finance",
    model="gemini-2.5-flash", 
    instruction=instructions,
    tools=[],
)

def get_agent():
    """Retourne l'agent expert en finance"""
    return agent

root_agent = agent