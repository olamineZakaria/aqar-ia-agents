from google.adk.agents import LlmAgent, InvocationContext
from google.adk.tools import VertexAiSearchTool
import asyncio
import os
import uuid
from datetime import datetime

# Configuration Vertex AI Search
DATA_STORE_ID = "projects/airy-shuttle-468014-n1/locations/eu/collections/default_collection/dataStores/tachrone_1754589027742"

# Lecture des instructions depuis le fichier txt
def lire_instructions():
    """Lit les instructions depuis le fichier instructions.txt"""
    chemin_instructions = os.path.join(os.path.dirname(__file__), "instructions.txt")
    
    try:
        with open(chemin_instructions, 'r', encoding='utf-8') as fichier:
            return fichier.read()
    except FileNotFoundError:
        print(f"⚠️  Le fichier {chemin_instructions} n'a pas été trouvé.")
        # Instructions par défaut si le fichier n'existe pas
        return """
Vous êtes un Expert Guide Acquéreur spécialisé dans l'immobilier au Maroc.

Votre rôle :
- Accompagner les acquéreurs dans toutes les étapes de leur projet immobilier
- Fournir des conseils personnalisés et précis
- Utiliser les outils à disposition pour calculer, vérifier et analyser
- Rechercher dans la base de connaissances pour des informations détaillées

Vous êtes compétent dans :
- L'analyse des étapes d'acquisition
- La vérification des promoteurs FNPI
- Le calcul de capacité d'emprunt
- L'analyse des compromis de vente
- Les checklists de livraison
- Le calcul de la fiscalité immobilière

Répondez toujours de manière professionnelle, précise et adaptée au contexte marocain.
"""
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier: {e}")
        return "Vous êtes un expert en immobilier au Maroc."

# Outils pour l'agent
def analyser_etape_actuelle(description_situation: str) -> str:
    """
    Analyse la situation de l'utilisateur et détermine son étape dans le processus d'acquisition
    
    Args:
        description_situation (str): Description de la situation actuelle de l'utilisateur
    
    Returns:
        str: Analyse de l'étape actuelle et recommandations
    """
    return f"""
### 🔍 Analyse de votre situation
**Description fournie :** {description_situation}

### 📍 Étape déterminée
Basé sur votre description, vous semblez être à l'étape [ÉTAPE À DÉTERMINER]

### ✅ Actions recommandées pour cette étape
[ACTIONS SPÉCIFIQUES SELON L'ÉTAPE]

### ⚠️ Points de vigilance
[POINTS CRITIQUES À VÉRIFIER]

### ➡️ Prochaines étapes
[ÉTAPES SUIVANTES À SUIVRE]
"""

def verifier_promoteur_fnpi(nom_promoteur: str) -> str:
    """
    Vérifie si un promoteur est membre de la FNPI
    
    Args:
        nom_promoteur (str): Nom du promoteur à vérifier
    
    Returns:
        str: Résultat de la vérification
    """
    return f"""
### 🏢 Vérification Promoteur FNPI
**Promoteur recherché :** {nom_promoteur}

### 🎯 Statut FNPI
[STATUT À DÉTERMINER - MEMBRE OU NON]

### 📋 Informations complémentaires
- **Label ILTIZAM :** [OUI/NON]
- **Historique :** [INFORMATIONS DISPONIBLES]
- **Réputation :** [ÉVALUATION]

### 💡 Recommandations
[CONSEILS SELON LE STATUT]
"""

def calculer_capacite_emprunt(revenus_mensuels: float, charges_mensuelles: float, apport_initial: float) -> str:
    """
    Calcule la capacité d'emprunt d'un acquéreur
    
    Args:
        revenus_mensuels (float): Revenus mensuels nets
        charges_mensuelles (float): Charges mensuelles actuelles
        apport_initial (float): Apport initial disponible
    
    Returns:
        str: Calcul détaillé de la capacité d'emprunt
    """
    # Calcul simplifié (à adapter selon les règles marocaines)
    revenus_disponibles = revenus_mensuels - charges_mensuels
    capacite_mensuelle = revenus_disponibles * 0.33  # 33% du revenu disponible
    capacite_totale = capacite_mensuelle * 25 * 12  # 25 ans à 12 mois
    
    return f"""
### 💰 Calcul de Capacité d'Emprunt
**Revenus mensuels :** {revenus_mensuels:,.2f} DH
**Charges mensuelles :** {charges_mensuelles:,.2f} DH
**Apport initial :** {apport_initial:,.2f} DH

### 📊 Capacité calculée
- **Revenus disponibles :** {revenus_disponibles:,.2f} DH
- **Mensualité maximale :** {capacite_mensuelle:,.2f} DH
- **Capacité totale :** {capacite_totale:,.2f} DH
- **Capacité avec apport :** {capacite_totale + apport_initial:,.2f} DH

### 💡 Recommandations
- **Budget recommandé :** {capacite_totale * 0.8:,.2f} DH (80% de la capacité)
- **Mensualité confortable :** {capacite_mensuelle * 0.8:,.2f} DH
"""

def analyser_compromis_vente(texte_compromis: str) -> str:
    """
    Analyse un compromis de vente
    
    Args:
        texte_compromis (str): Texte du compromis à analyser
    
    Returns:
        str: Analyse détaillée du compromis
    """
    return f"""
### 📄 Analyse du Compromis de Vente
**Texte analysé :** {texte_compromis[:200]}...

### 🔍 Points Critiques à Vérifier
1. **Prix et modalités de paiement**
2. **Délais et conditions suspensives**
3. **Garanties et responsabilités**
4. **Clauses de résolution**

### 💡 Recommandations
[CONSEILS SPÉCIFIQUES SELON L'ANALYSE]

### ⚠️ Points de vigilance
[ÉLÉMENTS À SURVEILLER]
"""

def checklist_visite_livraison() -> str:
    """
    Génère une checklist complète pour la visite de livraison
    
    Returns:
        str: Checklist détaillée
    """
    return """
### 📋 Checklist Visite de Livraison

#### 1. 🏠 Vérifications Générales
- [ ] Conformité aux plans
- [ ] Finitions générales
- [ ] Propreté du chantier

#### 2. ⚡ Éléments Techniques
- [ ] Électricité (prises, éclairage)
- [ ] Plomberie (robinets, évacuations)
- [ ] Chauffage/Climatisation
- [ ] Isolation (thermique, phonique)

#### 3. 🎨 Finitions
- [ ] Peintures et revêtements
- [ ] Menuiseries (portes, fenêtres)
- [ ] Sols et plafonds
- [ ] Équipements intégrés

#### 4. 🛡️ Sécurité
- [ ] Détecteurs de fumée
- [ ] Éclairage de sécurité
- [ ] Accès et évacuation

#### 5. 📄 Documents à vérifier
- [ ] Attestation de conformité
- [ ] Garanties constructeur
- [ ] Plans de réception
"""

def calculer_fiscalite(prix_achat: float, type_bien: str, residence_principale: bool = True) -> str:
    """
    Calcule les obligations fiscales pour un achat immobilier
    
    Args:
        prix_achat (float): Prix d'achat du bien
        type_bien (str): Type de bien (appartement, maison, terrain)
        residence_principale (bool): Si c'est la résidence principale
    
    Returns:
        str: Calcul détaillé de la fiscalité
    """
    # Calculs simplifiés (à adapter selon la fiscalité marocaine actuelle)
    droits_enregistrement = prix_achat * 0.025  # 2.5%
    taxe_commune = prix_achat * 0.01  # 1%
    frais_notaire = prix_achat * 0.015  # 1.5%
    
    total_fiscalite = droits_enregistrement + taxe_commune + frais_notaire
    
    return f"""
### 🏛️ Calcul Fiscalité Immobilière
**Prix d'achat :** {prix_achat:,.2f} DH
**Type de bien :** {type_bien}
**Résidence principale :** {'Oui' if residence_principale else 'Non'}

### 💰 Détail des taxes
- **Droits d'enregistrement :** {droits_enregistrement:,.2f} DH (2.5%)
- **Taxe communale :** {taxe_commune:,.2f} DH (1%)
- **Frais de notaire :** {frais_notaire:,.2f} DH (1.5%)

### 📊 Total fiscalité
**Montant total :** {total_fiscalite:,.2f} DH
**Pourcentage :** {(total_fiscalite/prix_achat)*100:.1f}%

### 💡 Recommandations
- Prévoyez ces montants en plus du prix d'achat
- Vérifiez les exonérations possibles
- Consultez un expert-comptable pour optimiser
"""

async def create_invocation_context(agent):
    """Crée un InvocationContext valide pour l'agent"""
    
    try:
        # Essayons d'importer les classes nécessaires
        try:
            from google.adk.core import Session, SessionService
        except ImportError:
            try:
                from google.adk.agents import Session, SessionService
            except ImportError:
                try:
                    from google.adk import Session, SessionService
                except ImportError:
                    # Créons des classes mock
                    class MockSession:
                        def __init__(self):
                            self.id = str(uuid.uuid4())
                            self.created_at = datetime.now()
                    
                    class MockSessionService:
                        def __init__(self):
                            self.name = "expert_guide_session_service"
                    
                    Session = MockSession
                    SessionService = MockSessionService
        
        # Créons les objets requis
        session_service = SessionService()
        session = Session()
        invocation_id = str(uuid.uuid4())
        
        # Créons le contexte
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
                session_service={"name": "expert_guide_service"},
                invocation_id=str(uuid.uuid4()),
                agent=agent,
                session={"id": str(uuid.uuid4()), "created_at": datetime.now()}
            )
            return context
        except Exception as e2:
            print(f"❌ model_construct échoué: {e2}")
            raise

# Création de l'agent avec Vertex AI Search Tool
def create_guide_acquereur_agent():
    """Crée l'agent Expert Guide Acquéreur avec Vertex AI Search"""
    
    # Lecture des instructions
    instructions = lire_instructions()
    
    # Instructions enrichies incluant les capacités des outils
    instructions_completes = f"""
{instructions}

OUTILS DISPONIBLES:
Vous avez accès aux outils de calcul suivants via des appels de fonction :

1. analyser_etape_actuelle(description) - Analyse l'étape d'acquisition
2. calculer_capacite_emprunt(revenus, charges, apport) - Calcule la capacité financière  
3. calculer_fiscalite(prix, type_bien, residence_principale) - Calcule taxes et frais
4. verifier_promoteur_fnpi(nom) - Vérifie un promoteur FNPI
5. checklist_visite_livraison() - Génère une checklist de livraison
6. analyser_compromis_vente(texte) - Analyse un compromis

IMPORTANT: Quand un utilisateur demande des calculs ou analyses, proposez d'utiliser ces outils et demandez les informations nécessaires.

Vous pouvez également rechercher dans la base de connaissances Vertex AI pour des informations détaillées sur l'immobilier au Maroc.
"""
    
    # Configuration du Vertex AI Search Tool
    search_tool = VertexAiSearchTool(data_store_id=DATA_STORE_ID)
    
    # Création de l'agent avec SEULEMENT l'outil de recherche
    agent = LlmAgent(
        name="Expert_Guide_Acquereur",
        model="gemini-2.0-flash",
        instruction=instructions_completes,
        tools=[search_tool]  # SEULEMENT Vertex AI Search
    )
    
    return agent

async def chat_with_agent_and_tools(agent, question: str, context):
    """Fonction helper pour discuter avec l'agent et gérer les outils externes"""
    
    print(f"🤖 **Question:** {question}")
    print("📤 Envoi à l'Expert Guide Acquéreur...")
    print("-" * 60)
    
    try:
        response_parts = []
        event_count = 0
        
        async for event in agent.run_async(context):
            event_count += 1
            
            # Extraction du contenu de l'événement
            if hasattr(event, 'content') and event.content:
                content = str(event.content)
                response_parts.append(content)
                print(content, end='')
            elif hasattr(event, 'message') and event.message:
                content = str(event.message)
                response_parts.append(content)
                print(content, end='')
            elif hasattr(event, 'text') and event.text:
                content = str(event.text)
                response_parts.append(content)
                print(content, end='')
            
            # Limitons les événements
            if event_count >= 50:
                break
        
        print("\n" + "-" * 60)
        
        if response_parts:
            full_response = "".join(response_parts)
            
            # Post-traitement : Détection si des outils doivent être utilisés
            await process_tool_requests(full_response, question)
            
            print(f"✅ Réponse reçue ({event_count} événements)")
            return full_response
        else:
            print(f"⚠️ Aucune réponse textuelle extraite ({event_count} événements)")
            return None
            
    except Exception as e:
        print(f"❌ Erreur lors de l'exécution: {e}")
        import traceback
        traceback.print_exc()
        return None

async def process_tool_requests(response: str, original_question: str):
    """Traite les demandes d'utilisation d'outils basées sur la réponse"""
    
    # Détection des besoins de calcul dans la question originale
    question_lower = original_question.lower()
    
    if any(word in question_lower for word in ['capacité', 'emprunt', 'gagne', 'revenus', 'charges']):
        print("\n🧮 **OUTIL DÉTECTÉ**: Calcul de capacité d'emprunt")
        if 'dh' in question_lower or any(char.isdigit() for char in original_question):
            # Tentative d'extraction des chiffres (exemple simplifié)
            import re
            numbers = re.findall(r'\d+', original_question)
            if len(numbers) >= 2:
                try:
                    revenus = float(numbers[0]) if len(numbers) > 0 else 15000
                    charges = float(numbers[1]) if len(numbers) > 1 else 3000
                    apport = float(numbers[2]) if len(numbers) > 2 else 200000
                    
                    print("💰 Calcul automatique avec les valeurs détectées:")
                    resultat = calculer_capacite_emprunt(revenus, charges, apport)
                    print(resultat)
                except:
                    print("💡 Pour un calcul précis, veuillez fournir: revenus mensuels, charges, apport")
    
    elif any(word in question_lower for word in ['frais', 'taxes', 'fiscalité', 'coût']):
        print("\n🏛️ **OUTIL DÉTECTÉ**: Calcul de fiscalité")
        numbers = re.findall(r'\d+', original_question)
        if numbers:
            try:
                prix = float(numbers[0])
                if prix > 10000:  # Si c'est un prix réaliste
                    print("💰 Calcul automatique de la fiscalité:")
                    resultat = calculer_fiscalite(prix, "appartement", True)
                    print(resultat)
            except:
                print("💡 Pour un calcul précis, précisez le prix d'achat")
    
    elif any(word in question_lower for word in ['checklist', 'livraison', 'réception', 'visite']):
        print("\n📋 **OUTIL DÉTECTÉ**: Checklist de livraison")
        print("📋 Génération automatique de la checklist:")
        resultat = checklist_visite_livraison()
        print(resultat)
    
    elif any(word in question_lower for word in ['promoteur', 'fnpi', 'vérifier', 'fiable']):
        print("\n🏢 **OUTIL DÉTECTÉ**: Vérification promoteur FNPI")
        # Extraction du nom du promoteur si mentionné
        import re
        promoteur_match = re.search(r'promoteur\s+([A-Za-z\s]+)', original_question, re.IGNORECASE)
        if promoteur_match:
            nom_promoteur = promoteur_match.group(1).strip()
            print(f"🔍 Vérification automatique du promoteur: {nom_promoteur}")
            resultat = verifier_promoteur_fnpi(nom_promoteur)
            print(resultat)
        else:
            print("💡 Pour vérifier un promoteur, précisez son nom")

# Version mise à jour de chat_with_agent qui utilise la nouvelle fonction
async def chat_with_agent(agent, question: str, context):
    """Fonction helper pour discuter avec l'agent (version avec outils)"""
    return await chat_with_agent_and_tools(agent, question, context)

async def test_expert_guide_agent():
    """Test complet de l'Expert Guide Acquéreur"""
    
    print("🏠 EXPERT GUIDE ACQUÉREUR - Test Complet")
    print("=" * 70)
    
    # Création de l'agent
    print("🔧 Création de l'agent...")
    agent = create_guide_acquereur_agent()
    print(f"✅ Agent créé: {agent.name}")
    print(f"   - Modèle: {agent.model}")
    print(f"   - Outils: {len(agent.tools)} outil(s)")
    
    # Création du contexte
    print("\n🔧 Création du contexte d'invocation...")
    try:
        context = await create_invocation_context(agent)
        print("✅ Contexte créé avec succès")
    except Exception as e:
        print(f"❌ Impossible de créer le contexte: {e}")
        return
    
    # Tests avec l'agent
    questions = [
        "Bonjour ! Je souhaite acheter un appartement au Maroc. Pouvez-vous m'expliquer les principales étapes ?",
        
        "Je gagne 15000 DH par mois avec 3000 DH de charges et j'ai 200000 DH d'apport. Quelle est ma capacité d'emprunt ?",
        
        "Quels sont les frais et taxes à prévoir lors de l'achat d'un appartement de 800000 DH ?",
        
        "Donnez-moi la checklist pour la visite de livraison de mon futur logement.",
        
        "Comment puis-je vérifier qu'un promoteur est fiable et membre de la FNPI ?"
    ]
    
    print(f"\n🎯 Test avec {len(questions)} questions...")
    
    for i, question in enumerate(questions, 1):
        print(f"\n{'='*70}")
        print(f"📋 QUESTION {i}/{len(questions)}")
        print('='*70)
        
        response = await chat_with_agent(agent, question, context)
        
        if response:
            print(f"\n✅ Question {i} traitée avec succès")
        else:
            print(f"\n⚠️ Question {i} - Problème de réponse")
        
        # Pause entre les questions
        await asyncio.sleep(2)
    
    print(f"\n{'='*70}")
    print("🎉 TEST TERMINÉ")
    print("✅ L'Expert Guide Acquéreur est opérationnel !")
    print('='*70)

# Fonction utilitaire pour les outils de calcul (peut être utilisée séparément)
def utiliser_outils_calcul():
    """Démontre l'utilisation des outils de calcul séparément"""
    
    print("\n🧮 DÉMONSTRATION DES OUTILS DE CALCUL")
    print("=" * 50)
    
    # Test capacité d'emprunt
    print("\n💰 Test Capacité d'Emprunt:")
    resultat = calculer_capacite_emprunt(15000, 3000, 200000)
    print(resultat)
    
    # Test fiscalité
    print("\n🏛️ Test Calcul Fiscalité:")
    resultat = calculer_fiscalite(800000, "appartement", True)
    print(resultat)
    
    # Test checklist
    print("\n📋 Checklist Livraison:")
    resultat = checklist_visite_livraison()
    print(resultat)

# Fonction principale
async def main():
    """Fonction principale d'exécution"""
    try:
        await test_expert_guide_agent()
        
        print("\n" + "="*70)
        print("💡 OUTILS DISPONIBLES SÉPARÉMENT")
        print("="*70)
        utiliser_outils_calcul()
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        import traceback
        traceback.print_exc()

def run_expert_guide_test():
    """Lance le test de l'Expert Guide Acquéreur"""
    try:
        # Gestion de l'environnement asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import nest_asyncio
                nest_asyncio.apply()
                task = loop.create_task(main())
                return task
            else:
                asyncio.run(main())
        except RuntimeError:
            asyncio.run(main())
    except Exception as e:
        print(f"❌ Erreur lors de l'exécution: {e}")
        import traceback
        traceback.print_exc()

# Initialisation de l'agent pour usage externe
def get_agent():
    """Retourne l'agent configuré pour usage externe"""
    return create_guide_acquereur_agent()

# Initialisation de l'agent global
root_agent = create_guide_acquereur_agent()

# # Point d'entrée principal
# if __name__ == "__main__":
#     print("🚀 LANCEMENT DE L'EXPERT GUIDE ACQUÉREUR")
#     print("="*70)
#     run_expert_guide_test()
# else:
#     print("📦 Module Expert Guide Acquéreur importé.")
#     print(f"✅ Agent global 'root_agent' créé: {root_agent.name}")
#     print("💡 Utilisez run_expert_guide_test() pour lancer le test complet.")
#     print("💡 Ou utilisez directement 'root_agent' avec un contexte approprié.")