from google.adk.agents import LlmAgent, InvocationContext
from google.adk.tools import FunctionTool
import asyncio
import os
import uuid
from datetime import datetime
import sys

# Ajout du répertoire parent au path pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import des agents experts
from Expert_Finance.agent import get_agent as get_agent_finance
from Expert_Guide_Acquereur.agent import get_agent as get_agent_guide_acquereur
from Expert_Materiaux_Prestataire.agent import create_timeout_resistant_agent as get_agent_materiaux_prestataire

class ChefOrchestrateur:
    """Agent orchestrateur qui coordonne les experts spécialisés"""
    
    def __init__(self):
        self.experts = {}
        self.initialize_experts()
    
    def initialize_experts(self):
        """Initialise tous les agents experts"""
        try:
            # Initialisation des agents experts
            self.experts['finance'] = get_agent_finance()
            self.experts['guide_acquereur'] = get_agent_guide_acquereur()
            self.experts['materiaux_prestataire'] = get_agent_materiaux_prestataire()
            
            print("✅ Tous les agents experts initialisés avec succès")
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation des agents: {e}")
    
    async def create_invocation_context(self, agent):
        """Crée un contexte d'invocation pour un agent"""
        try:
            # Création des objets requis
            session_service = type('SessionService', (), {'name': 'chef_orchestrateur_service'})()
            session = type('Session', (), {
                'id': str(uuid.uuid4()),
                'created_at': datetime.now()
            })()
            invocation_id = str(uuid.uuid4())
            
            # Création du contexte
            context = InvocationContext(
                session_service=session_service,
                invocation_id=invocation_id,
                agent=agent,
                session=session
            )
            
            return context
            
        except Exception as e:
            print(f"❌ Erreur lors de la création du contexte: {e}")
            # Tentative avec model_construct
            try:
                context = InvocationContext.model_construct(
                    session_service={"name": "chef_orchestrateur_service"},
                    invocation_id=str(uuid.uuid4()),
                    agent=agent,
                    session={"id": str(uuid.uuid4()), "created_at": datetime.now()}
                )
                return context
            except Exception as e2:
                print(f"❌ model_construct échoué: {e2}")
                raise
    
    async def route_to_expert(self, question: str, expert_type: str):
        """Route une question vers l'expert approprié"""
        if expert_type not in self.experts:
            return f"❌ Expert '{expert_type}' non disponible"
        
        expert = self.experts[expert_type]
        context = await self.create_invocation_context(expert)
        
        try:
            response_parts = []
            event_count = 0
            
            async for event in expert.run_async(context):
                event_count += 1
                
                # Extraction du contenu de l'événement
                if hasattr(event, 'content') and event.content:
                    content = str(event.content)
                    response_parts.append(content)
                elif hasattr(event, 'message') and event.message:
                    content = str(event.message)
                    response_parts.append(content)
                elif hasattr(event, 'text') and event.text:
                    content = str(event.text)
                    response_parts.append(content)
                
                # Limitons les événements
                if event_count >= 50:
                    break
            
            if response_parts:
                return "".join(response_parts)
            else:
                return f"⚠️ Aucune réponse de l'expert {expert_type}"
                
        except Exception as e:
            return f"❌ Erreur avec l'expert {expert_type}: {e}"
    
    def analyze_question(self, question: str):
        """Analyse la question pour déterminer quel expert utiliser"""
        question_lower = question.lower()
        
        # Mots-clés pour chaque expert
        finance_keywords = [
            'finance', 'budget', 'coût', 'prix', 'argent', 'euros', 'dh', 'dirhams',
            'capacité', 'emprunt', 'crédit', 'banque', 'frais', 'taxes', 'fiscalité',
            'revenus', 'charges', 'apport', 'mensualité'
        ]
        
        guide_keywords = [
            'acheter', 'acquisition', 'immobilier', 'appartement', 'maison', 'terrain',
            'promoteur', 'fnpi', 'livraison', 'réception', 'compromis', 'notaire',
            'étapes', 'processus', 'checklist', 'vérification', 'conseils'
        ]
        
        materiaux_keywords = [
            'matériaux', 'matériel', 'construction', 'bâtiment', 'ciment', 'sable',
            'briques', 'bois', 'métal', 'plomberie', 'électricité', 'isolation',
            'fournisseur', 'prestataire', 'vendeur', 'tachrone', 'grillage', 'fibre'
        ]
        
        # Calcul des scores
        finance_score = sum(1 for keyword in finance_keywords if keyword in question_lower)
        guide_score = sum(1 for keyword in guide_keywords if keyword in question_lower)
        materiaux_score = sum(1 for keyword in materiaux_keywords if keyword in question_lower)
        
        # Détermination de l'expert principal
        scores = {
            'finance': finance_score,
            'guide_acquereur': guide_score,
            'materiaux_prestataire': materiaux_score
        }
        
        max_score = max(scores.values())
        if max_score == 0:
            return 'guide_acquereur'  # Expert par défaut
        
        # Retourne l'expert avec le score le plus élevé
        for expert, score in scores.items():
            if score == max_score:
                return expert
    
    async def process_question(self, question: str):
        """Traite une question en la routant vers l'expert approprié"""
        print(f"🤖 **Question reçue:** {question}")
        
        # Analyse de la question
        expert_type = self.analyze_question(question)
        print(f"🎯 **Expert sélectionné:** {expert_type}")
        
        # Routage vers l'expert
        response = await self.route_to_expert(question, expert_type)
        
        return {
            'expert_utilise': expert_type,
            'reponse': response,
            'question_originale': question
        }
    
    def expert_finance(self, question: str) -> str:
        """Consulte l'expert en finance pour les questions de budget, emprunt, coûts, fiscalité"""
        import asyncio
        return asyncio.run(self.route_to_expert(question, 'finance'))
    
    def expert_guide_acquereur(self, question: str) -> str:
        """Consulte l'expert guide acquéreur pour les questions d'acquisition, étapes, promoteurs"""
        import asyncio
        return asyncio.run(self.route_to_expert(question, 'guide_acquereur'))
    
    def expert_materiaux_prestataire(self, question: str) -> str:
        """Consulte l'expert matériaux/prestataires pour les questions de matériaux, fournisseurs, construction"""
        import asyncio
        return asyncio.run(self.route_to_expert(question, 'materiaux_prestataire'))

# Création de l'agent orchestrateur
def create_chef_orchestrateur():
    """Crée l'agent orchestrateur principal"""
    
    # Lecture des instructions depuis le fichier txt
    def lire_instructions():
        """Lit les instructions depuis le fichier instructions.txt"""
        chemin_instructions = os.path.join(os.path.dirname(__file__), "instructions.txt")
        
        try:
            with open(chemin_instructions, 'r', encoding='utf-8') as fichier:
                return fichier.read()
        except FileNotFoundError:
            print(f"Erreur: Le fichier {chemin_instructions} n'a pas été trouvé.")
            return "Vous êtes le Chef Orchestrateur qui coordonne les experts spécialisés."
        except Exception as e:
            print(f"Erreur lors de la lecture du fichier: {e}")
            return "Vous êtes le Chef Orchestrateur qui coordonne les experts spécialisés."
    
    instructions = lire_instructions()
    
    # Création de l'agent orchestrateur avec les outils des experts
    chef_instance = ChefOrchestrateur()
    
    # Création des outils pour les experts
    finance_tool = FunctionTool(chef_instance.expert_finance)
    guide_tool = FunctionTool(chef_instance.expert_guide_acquereur)
    materiaux_tool = FunctionTool(chef_instance.expert_materiaux_prestataire)
    
    # Création de l'agent orchestrateur
    agent = LlmAgent(
        name="Chef_Orchestrateur",
        model="gemini-2.5-flash",
        instruction=instructions,
        tools=[finance_tool, guide_tool, materiaux_tool]
    )
    
    return agent

# Instance globale du chef orchestrateur
chef_orchestrateur = ChefOrchestrateur()
root_agent = create_chef_orchestrateur()

async def test_chef_orchestrateur():
    """Test complet du chef orchestrateur"""
    
    print("🎯 CHEF ORCHESTRATEUR - Test Complet")
    print("=" * 70)
    
    # Tests avec différents types de questions
    questions = [
        "Je gagne 15000 DH par mois, quelle est ma capacité d'emprunt ?",
        
        "Quelles sont les étapes pour acheter un appartement au Maroc ?",
        
        "Je cherche du ciment pour ma construction, où puis-je en trouver ?",
        
        "Combien coûte l'achat d'un appartement de 800000 DH avec tous les frais ?",
        
        "Comment vérifier qu'un promoteur est fiable et membre de la FNPI ?",
        
        "J'ai besoin de matériaux de construction et de conseils pour mon projet immobilier."
    ]
    
    print(f"🎯 Test avec {len(questions)} questions...")
    
    for i, question in enumerate(questions, 1):
        print(f"\n{'='*70}")
        print(f"📋 QUESTION {i}/{len(questions)}")
        print('='*70)
        
        result = await chef_orchestrateur.process_question(question)
        
        print(f"🎯 Expert utilisé: {result['expert_utilise']}")
        print(f"📋 Réponse: {result['reponse'][:200]}...")
        
        # Pause entre les questions
        await asyncio.sleep(1)
    
    print(f"\n{'='*70}")
    print("🎉 TEST TERMINÉ")
    print("✅ Le Chef Orchestrateur est opérationnel !")
    print('='*70)

def run_chef_test():
    """Lance le test du chef orchestrateur"""
    try:
        # Gestion de l'environnement asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import nest_asyncio
                nest_asyncio.apply()
                task = loop.create_task(test_chef_orchestrateur())
                return task
            else:
                asyncio.run(test_chef_orchestrateur())
        except RuntimeError:
            asyncio.run(test_chef_orchestrateur())
    except Exception as e:
        print(f"❌ Erreur lors de l'exécution: {e}")
        import traceback
        traceback.print_exc()

# Point d'entrée principal
if __name__ == "__main__":
    print("🚀 LANCEMENT DU CHEF ORCHESTRATEUR")
    print("="*70)
    run_chef_test()
else:
    print("📦 Module Chef Orchestrateur importé.")
    print(f"✅ Chef orchestrateur créé avec {len(chef_orchestrateur.experts)} experts")
    print("💡 Utilisez run_chef_test() pour lancer le test complet.")
    print("💡 Ou utilisez directement 'chef_orchestrateur.process_question()'")








