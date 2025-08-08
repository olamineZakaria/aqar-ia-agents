from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
import requests
import json
import logging
from typing import Optional, Dict, Any
import time
import os

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Configuration avec timeouts ajustés ===
API_BASE_URL = "http://localhost:7000"
REQUEST_TIMEOUT = 10  # Réduit de 30 à 10 secondes
MAX_RETRIES = 2
RETRY_DELAY = 1  # secondes

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

def api_query(action: str, query: str = "", filters: str = "{}") -> str:
    """
    Interroge l'API Tachrone avec gestion avancée des timeouts
    
    Args:
        action (str): search_matieres, search_prestataires, filter_matieres, filter_prestataires, stats
        query (str): Terme de recherche
        filters (str): Filtres JSON
    
    Returns:
        str: Résultats formatés de la recherche
    """
    return TachroneAPIManager.execute_with_retry(action, query, filters)

class TachroneAPIManager:
    """Gestionnaire singleton pour les appels API Tachrone"""
    
    _instance = None
    _session = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._session = requests.Session()
            # Note: Le timeout global sur la session n'est pas utilisé directement
            # par requests.get() si un timeout local est spécifié.
            # Il est conservé ici par bonne pratique.
        return cls._instance
    
    @classmethod
    def execute_with_retry(cls, action: str, query: str, filters: str) -> str:
        """Exécute la requête avec retry automatique"""
        manager = cls()
        
        for attempt in range(MAX_RETRIES + 1):
            try:
                logger.info(f"Tentative {attempt + 1}/{MAX_RETRIES + 1}: {action} - '{query}'")
                return manager._single_request(action, query, filters)
                
            except requests.exceptions.Timeout:
                if attempt < MAX_RETRIES:
                    logger.warning(f"Timeout tentative {attempt + 1}, retry dans {RETRY_DELAY}s...")
                    time.sleep(RETRY_DELAY)
                    continue
                else:
                    return manager._handle_timeout_error(action, query)
                    
            except requests.exceptions.ConnectionError:
                return manager._handle_connection_error()
                
            except Exception as e:
                logger.error(f"Erreur tentative {attempt + 1}: {e}")
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY)
                    continue
                else:
                    return f"Erreur persistante après {MAX_RETRIES + 1} tentatives: {str(e)}"
        
        return "Erreur inattendue dans le système de retry"
    
    def _single_request(self, action: str, query: str, filters: str) -> str:
        """Exécute une seule requête"""
        valid_actions = ["search_matieres", "search_prestataires", "filter_matieres", "filter_prestataires", "stats"]
        if action not in valid_actions:
            return f"Action invalide: {action}. Utilisez: {', '.join(valid_actions)}"
        
        filter_params = {}
        if filters and filters.strip() != "{}":
            try:
                filter_params = json.loads(filters)
            except json.JSONDecodeError:
                return "Erreur: Format JSON invalide pour les filtres"
        
        url, params = self._build_request_optimized(action, query, filter_params)
        if isinstance(url, str) and url.startswith("Erreur"):
            return url
        
        start_time = time.time()
        # Le timeout est spécifié ici, pour chaque requête
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        
        elapsed = time.time() - start_time
        logger.info(f"Requête réussie en {elapsed:.2f}s")
        
        data = response.json()
        return self._format_response_compact(action, data, query)
    
    def _build_request_optimized(self, action: str, query: str, filter_params: dict):
        """Construction optimisée des requêtes"""
        if action == "search_matieres":
            if not query.strip():
                return "Erreur: Terme de recherche requis pour search_matieres", None
            return f"{API_BASE_URL}/ai/search", {
                "query": query.strip()[:100],
                "limit": min(filter_params.get("limit", 5), 10) # Limite à 5 pour une réponse détaillée
            }
        
        elif action == "search_prestataires":
            if not query.strip():
                return "Erreur: Terme de recherche requis pour search_prestataires", None
            return f"{API_BASE_URL}/ai/prestataires/search", {
                "query": query.strip()[:100],
                "limit": min(filter_params.get("limit", 8), 10)
            }
        
        elif action == "filter_matieres":
            params = {
                "page": filter_params.get("page", 1),
                "page_size": min(filter_params.get("page_size", 8), 15) # Limite à 8 pour une réponse détaillée
            }
            for key in ["location", "entreprise", "search"]:
                if filter_params.get(key):
                    params[key] = str(filter_params[key])[:50]
            if filter_params.get("has_images") is not None:
                params["has_images"] = bool(filter_params["has_images"])
            if query.strip():
                params["search"] = query.strip()[:50]
            
            return f"{API_BASE_URL}/matieres", params
        
        elif action == "filter_prestataires":
            params = {
                "page": filter_params.get("page", 1),
                "page_size": min(filter_params.get("page_size", 15), 20)
            }
            for key in ["name", "category", "search"]:
                if filter_params.get(key):
                    params[key] = str(filter_params[key])[:50]
            if filter_params.get("rating_min"):
                params["rating_min"] = int(filter_params["rating_min"])
            if query.strip():
                params["search"] = query.strip()[:50]
            
            return f"{API_BASE_URL}/prestataires", params
        
        elif action == "stats":
            return f"{API_BASE_URL}/ai/stats", {}
        
        return "Erreur: Action non reconnue", None
    
    def _format_response_compact(self, action: str, data: dict, query: str = "") -> str:
        """Formatage détaillé des réponses pour les matériaux."""
        try:
            if action == "search_matieres":
                ### MODIFIÉ : FORMATAGE DÉTAILLÉ POUR SEARCH_MATIERES ###
                results = data.get("results", [])
                if not results:
                    return f"❌ Aucun résultat pour '{query}'. Essayez des termes plus généraux."
                
                items = []
                # On limite aux 5 premiers résultats pour ne pas surcharger
                for i, item in enumerate(results[:5], 1):
                    # Extraction complète des données
                    title = item.get("title", "Titre non disponible")
                    prix = item.get("prix", "N/A")
                    par = item.get("par", "unité")
                    quantite_min = item.get("quantité_min", "N/A")
                    location = item.get("location", "Lieu non spécifié")
                    livraison = "Oui" if item.get("livraison") else "Non"
                    description = item.get("description", "Aucune description.")[:120] + "..."
                    avis = item.get("avis", "Aucun avis")
                    entreprise = item.get("entreprise", "Vendeur non spécifié")
                    image_urls = item.get("image_urls", [])

                    # Formatage détaillé de chaque item
                    item_details = [
                        f"{i}. **{title}**",
                        f"   - **Vendeur :** {entreprise}",
                        f"   - **Prix :** {prix} (par {par}) | **Qté min :** {quantite_min}",
                        f"   - **Lieu :** {location} | **Livraison :** {livraison}",
                        f"   - **Avis :** {avis}",
                        f"   - **Description :** {description}",
                    ]
                    if image_urls:
                        # On affiche la première URL et on indique s'il y en a d'autres.
                        more_images_text = f" (et {len(image_urls) - 1} autre(s))" if len(image_urls) > 1 else ""
                        item_details.append(f"   - **Image principale :** {image_urls[0]}{more_images_text}")
                    items.append("\n".join(item_details))
                    
                
                count = len(results)
                header = f"🎯 **{count} résultat(s) trouvé(s)** pour '{query[:30]}{'...' if len(query) > 30 else ''}'"
                # Séparer chaque résultat par un double saut de ligne pour la lisibilité
                return f"{header}\n\n" + "\n\n".join(items)

            elif action == "search_prestataires":
                results = data.get("results", [])
                if not results:
                    return f"❌ Aucun résultat pour '{query}'. Essayez des termes plus généraux."
                
                items = []
                for i, item in enumerate(results[:8], 1): # Limite à 8
                    name = item.get("name", "Sans nom")[:60]
                    rating = f"⭐{item['rating']}" if item.get("rating") else "Non noté"
                    items.append(f"{i}. **{name}** | {rating}")
                
                count = len(results)
                header = f"🎯 **{count} résultat(s)** pour '{query[:30]}{'...' if len(query) > 30 else ''}'"
                return f"{header}\n\n" + "\n".join(items)

            elif action == "filter_matieres":
                ### MODIFIÉ : FORMATAGE DÉTAILLÉ POUR FILTER_MATIERES ###
                items_data = data.get("data", [])
                total = data.get("total_count", 0)
                
                if not items_data:
                    return "❌ Aucun résultat avec ces critères"
                
                formatted_items = []
                for i, item in enumerate(items_data, 1):
                    # Extraction complète des données
                    title = item.get("title", "Titre non disponible")
                    prix = item.get("prix", "N/A")
                    par = item.get("par", "unité")
                    quantite_min = item.get("quantité_min", "N/A")
                    location = item.get("location", "Lieu non spécifié")
                    livraison = "Oui" if item.get("livraison") else "Non"
                    description = item.get("description", "Aucune description.")[:120] + "..."
                    avis = item.get("avis", "Aucun avis")
                    entreprise = item.get("entreprise", "Vendeur non spécifié")
                    image_urls = item.get("image_urls", [])

                    # Formatage détaillé de chaque item
                    item_details = [
                        f"{i}. **{title}**",
                        f"   - **Vendeur :** {entreprise}",
                        f"   - **Prix :** {prix} (par {par}) | **Qté min :** {quantite_min}",
                        f"   - **Lieu :** {location} | **Livraison :** {livraison}",
                        f"   - **Avis :** {avis}",
                        f"   - **Description :** {description}",
                    ]
                    if image_urls:
                        # On affiche la première URL et on indique s'il y en a d'autres.
                        more_images_text = f" (et {len(image_urls) - 1} autre(s))" if len(image_urls) > 1 else ""
                        item_details.append(f"   - **Image principale :** {image_urls[0]}{more_images_text}")
                    formatted_items.append("\n".join(item_details))
                
                header = f"📊 **{total} résultats trouvés** (affichage de {len(items_data)})"
                return f"{header}\n\n" + "\n\n".join(formatted_items)
            
            elif action == "filter_prestataires":
                items = data.get("data", [])
                total = data.get("total_count", 0)
                if not items:
                    return "❌ Aucun résultat avec ces critères"
                
                formatted = []
                for i, item in enumerate(items[:8], 1): # Max 8
                    name = item.get("name", "Sans nom")[:50]
                    rating = f" ⭐{item['rating']}" if item.get("rating") else ""
                    formatted.append(f"{i}. {name}{rating}")
                
                return f"📊 **{total} résultats trouvés**\n\n" + "\n".join(formatted)
            
            elif action == "stats":
                total = data.get("total_items", 0)
                companies = data.get("companies", {}).get("count", 0)
                locations = data.get("locations", {}).get("count", 0)
                return f"📊 **Base Tachrone:** {total:,} matières | {companies:,} entreprises | {locations:,} villes"
            
            return "Format de réponse non reconnu"
            
        except Exception as e:
            logger.error(f"Erreur de formatage: {e}")
            return f"Erreur de formatage: {str(e)}"
    
    def _handle_timeout_error(self, action: str, query: str) -> str:
        """Gestion spécialisée des timeouts avec suggestions"""
        suggestions = []
        if action in ["search_matieres", "search_prestataires"]:
            suggestions = [
                f"✅ Essayez avec moins de mots: au lieu de '{query}', utilisez juste les mots-clés principaux",
                "✅ Vérifiez l'orthographe du terme recherché",
                "✅ Utilisez des termes plus généraux (ex: 'grillage' au lieu de 'grillage fibre verre')"
            ]
        else: # filter_*
            suggestions = [
                "✅ Réduisez le nombre de filtres appliqués",
                "✅ Essayez avec une recherche plus simple d'abord"
            ]
        
        return f"""⏱️ **Timeout de connexion** lors de la recherche.

🔧 **Solutions suggérées:**
{chr(10).join(suggestions)}

💡 La base de données est peut-être temporairement surchargée. Réessayez dans quelques instants."""
    
    def _handle_connection_error(self) -> str:
        """Gestion des erreurs de connexion"""
        return f"""🔌 **Problème de connexion** à l'API Tachrone ({API_BASE_URL})

✅ **Vérifications:**
• Le serveur API est-il démarré ?
• L'URL {API_BASE_URL} est-elle correcte ?
• Pas de problème réseau ?

🔄 Vous pouvez réessayer ou me demander une recherche différente."""


# === Prompt optimisé pour gérer les timeouts ===
# prompt_with_timeout_handling = """
# Tu es Alex Matériel Pro, expert en matériel de construction avec accès à la base Tachrone.

# 🔧 **Outil disponible:** api_query avec actions:
# - search_matieres: recherche de matériaux
# - search_prestataires: recherche de prestataires  
# - filter_matieres/filter_prestataires: filtrage avancé
# - stats: statistiques générales

# 📋 **Stratégie en cas de problème:**
# 1. Si timeout → Suggère une recherche plus simple
# 2. Si pas de résultats → Propose des alternatives
# 3. Si termes complexes → Décompose la recherche

# 💡 **Exemples d'optimisation:**
# - "Grillage Fibre de Verre Bleu 90G/M2" → Recherche "grillage fibre" puis affine
# - Recherche spécifique qui échoue → Essaie les mots-clés principaux

# 🎯 **Objectif:** Toujours fournir une réponse utile, même si la recherche exacte échoue.
# """

def create_timeout_resistant_agent():
    """Crée un agent résistant aux timeouts"""
    try:
        # Test rapide de connectivité
        test_response = requests.get(f"{API_BASE_URL}/health", timeout=3)
        logger.info(f"✅ API disponible: {test_response.status_code}")
    except Exception as e:
        logger.warning(f"⚠️ API potentiellement indisponible ou erreur de connexion: {e}")
    
    # Lecture des instructions depuis le fichier
    instructions = lire_instructions()
    
    # Créer l'agent en passant directement la fonction
    agent = LlmAgent(
        name="TachroneAgentOptimized",
        model="gemini-2.5-flash", # Assurez-vous d'utiliser un modèle compatible
        instruction=instructions,
        tools=[api_query] # ADK wrappe automatiquement api_query en FunctionTool
    )
    
    return agent


# Exemple d'initialisation
root_agent = create_timeout_resistant_agent()

# Pour tester, vous pouvez décommenter les lignes suivantes:
# if __name__ == '__main__':
#     print("Agent 'Alex Matériel Pro' initialisé.")
#     # Test direct de la fonction de formatage
#     # test_search_results = {'results': [{'title': 'Sable de rivière 0/4', 'prix': '25 EUR', 'par': 'tonne', 'quantité_min': '1 tonne', 'location': 'Lyon', 'livraison': True, 'description': 'Sable lavé pour béton et maçonnerie.', 'avis': '4.5/5', 'entreprise': 'SABLIERE DU RHONE', 'image_urls': ['url1.jpg', 'url2.jpg']}]}
#     # formatted_output = TachroneAPIManager()._format_response_compact("search_matieres", test_search_results, "sable")
#     # print("\n--- EXEMPLE DE SORTIE FORMATÉE ---")
#     # print(formatted_output)
#     # print("---------------------------------\n")

#     # response = root_agent.chat("cherche moi du sable de rivière")
#     # print(response)