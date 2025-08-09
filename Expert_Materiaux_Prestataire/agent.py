from google.adk.agents import LlmAgent
import requests
import json
import logging
import time
import os

# --- Configuration Robuste ---
# Augmentation significative du délai d'attente pour accommoder un API potentiellement lent.
# C'est le changement le plus critique pour résoudre les timeouts.
REQUEST_TIMEOUT = 30 
MAX_RETRIES = 2
RETRY_DELAY = 2  # Délai légèrement augmenté entre les tentatives.
API_BASE_URL = "http://localhost:7000"

# --- Configuration du Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def lire_instructions():
    """
    Lit les instructions de l'agent à partir d'un fichier externe.
    Cela permet de séparer la logique du prompt.
    """
    chemin_instructions = os.path.join(os.path.dirname(__file__), "instructions.txt")
    try:
        with open(chemin_instructions, 'r', encoding='utf-8') as fichier:
            return fichier.read()
    except FileNotFoundError:
        msg_erreur = f"ERREUR CRITIQUE: Le fichier d'instructions est introuvable à l'adresse {chemin_instructions}."
        logger.critical(msg_erreur)
        # Fournir une instruction de secours pour que l'agent puisse au moins signaler le problème.
        return "Vous êtes un assistant. Votre fichier de configuration est manquant, veuillez signaler cette erreur."
    except Exception as e:
        logger.error(f"Erreur lors de la lecture du fichier d'instructions: {e}")
        return "Vous êtes un assistant. Une erreur est survenue lors de la lecture de vos instructions."

def api_query(action: str, query: str = "", filters: str = "{}") -> str:
    """
    Point d'entrée unique de l'outil pour l'agent LLM.
    Délègue l'exécution au TachroneAPIManager.
    """
    return TachroneAPIManager.execute_with_retry(action, query, filters)

class TachroneAPIManager:
    """
    Gère toutes les interactions avec l'API Tachrone, y compris les tentatives,
    la gestion des erreurs et le formatage des réponses. Implémenté en Singleton.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def execute_with_retry(cls, action: str, query: str, filters: str) -> str:
        """
        Exécute une requête API avec une logique de réessai intégrée.
        C'est la méthode principale appelée par l'outil `api_query`.
        """
        manager = cls()
        
        for attempt in range(MAX_RETRIES + 1):
            try:
                logger.info(f"Tentative {attempt + 1}/{MAX_RETRIES + 1}: Action='{action}', Query='{query}'")
                return manager._single_request(action, query, filters)
                
            except requests.exceptions.Timeout:
                if attempt < MAX_RETRIES:
                    logger.warning(f"Timeout sur la tentative {attempt + 1}. Nouvelle tentative dans {RETRY_DELAY}s...")
                    time.sleep(RETRY_DELAY)
                else:
                    logger.error(f"Timeout persistant après {MAX_RETRIES + 1} tentatives pour l'action '{action}'.")
                    return manager._handle_timeout_error(action, query)
                    
            except requests.exceptions.ConnectionError:
                logger.error(f"Erreur de connexion en essayant de joindre {API_BASE_URL}.")
                return manager._handle_connection_error()

            except requests.exceptions.HTTPError as http_err:
                logger.error(f"Erreur HTTP sur la tentative {attempt + 1}: {http_err}")
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY)
                else:
                    return f"Erreur HTTP persistante: {http_err}. Le serveur répond mais avec une erreur."
                
            except Exception as e:
                logger.error(f"Erreur inattendue sur la tentative {attempt + 1}: {e}", exc_info=True)
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY)
                else:
                    return f"Erreur inattendue et persistante après {MAX_RETRIES + 1} tentatives: {str(e)}"
        
        return "Erreur inattendue dans le système de réessai."
    
    def _single_request(self, action: str, query: str, filters: str) -> str:
        """Exécute une seule requête API validée."""
        valid_actions = ["search_matieres", "search_prestataires", "filter_matieres", "filter_prestataires", "stats"]
        if action not in valid_actions:
            return f"Action invalide: {action}. Utilisez: {', '.join(valid_actions)}"
        
        try:
            filter_params = json.loads(filters) if filters and filters.strip() != "{}" else {}
        except json.JSONDecodeError:
            return "Erreur: Le format JSON fourni pour les filtres est invalide."
        
        url, params = self._build_request_optimized(action, query, filter_params)
        if url.startswith("Erreur"):
            return url
        
        logger.info(f"Exécution de la requête GET vers: {url} avec les paramètres: {params}")
        start_time = time.time()
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        elapsed = time.time() - start_time
        
        response.raise_for_status()
        
        logger.info(f"Requête réussie en {elapsed:.2f}s. Statut: {response.status_code}")
        
        data = response.json()
        return self._format_response_compact(action, data, query)
    
    def _build_request_optimized(self, action: str, query: str, filter_params: dict):
        """Construit l'URL et les paramètres pour chaque action spécifique."""
        base_url = API_BASE_URL
        query = query.strip()
        
        common_params = {
            "page": filter_params.get("page", 1),
            "page_size": min(filter_params.get("page_size", 10), 20)
        }
        if query:
            common_params["search"] = query

        if action == "search_matieres":
            if not query: return "Erreur: Un terme de recherche est requis pour 'search_matieres'.", None
            return f"{base_url}/ai/search", {"query": query, "limit": 5}
        
        elif action == "search_prestataires":
            if not query: return "Erreur: Un terme de recherche est requis pour 'search_prestataires'.", None
            return f"{base_url}/ai/prestataires/search", {"query": query, "limit": 8}
        
        elif action == "filter_matieres":
            params = common_params.copy()
            for key in ["location", "entreprise"]:
                if filter_params.get(key): params[key] = str(filter_params[key])
            if "has_images" in filter_params: params["has_images"] = bool(filter_params["has_images"])
            return f"{base_url}/matieres", params
        
        elif action == "filter_prestataires":
            params = common_params.copy()
            for key in ["name", "category"]:
                 if filter_params.get(key): params[key] = str(filter_params[key])
            if filter_params.get("rating_min"): params["rating_min"] = int(filter_params["rating_min"])
            return f"{base_url}/prestataires", params
        
        elif action == "stats":
            return f"{base_url}/ai/stats", {}
        
        return "Erreur: Action non reconnue lors de la construction de la requête.", None
    
    def _format_response_compact(self, action: str, data: dict, query: str = "") -> str:
        """Formate les données JSON de l'API en une chaîne de caractères lisible."""
        try:
            if action in ["search_matieres", "filter_matieres"]:
                results = data.get("results") if action == "search_matieres" else data.get("data", [])
                total = len(results) if action == "search_matieres" else data.get("total_count", 0)

                if not results: return f"Aucun résultat trouvé pour '{query}' avec les filtres actuels."

                items = []
                for i, item in enumerate(results[:8], 1): # Limiter l'affichage pour la clarté
                    details = [
                        f"{i}. **{item.get('title', 'Titre non disponible')}**",
                        f"   - Vendeur: {item.get('entreprise', 'Non spécifié')}",
                        f"   - Prix: {item.get('prix', 'N/A')} par {item.get('par', 'unité')}",
                        f"   - Lieu: {item.get('location', 'Non spécifié')}"
                    ]
                    items.append("\n".join(details))
                
                header = f"**{total} résultat(s) trouvé(s)** pour '{query}' (affichage de {len(items)}):"
                return f"{header}\n\n" + "\n\n".join(items)

            elif action in ["search_prestataires", "filter_prestataires"]:
                results = data.get("results") if action == "search_prestataires" else data.get("data", [])
                total = len(results) if action == "search_prestataires" else data.get("total_count", 0)
                if not results: return f"Aucun prestataire trouvé pour '{query}' avec les filtres actuels."

                items = [f"{i}. **{p.get('name', 'Sans nom')}** (Note: {p.get('rating', 'N/A')})" for i, p in enumerate(results[:10], 1)]
                header = f"**{total} prestataire(s) trouvé(s)** (affichage de {len(items)}):"
                return f"{header}\n" + "\n".join(items)
            
            elif action == "stats":
                return (
                    f"**Statistiques de la base Tachrone:**\n"
                    f"- **Matières répertoriées :** {data.get('total_items', 0):,}\n"
                    f"- **Entreprises uniques :** {data.get('companies', {}).get('count', 0):,}\n"
                    f"- **Villes couvertes :** {data.get('locations', {}).get('count', 0):,}"
                )
            
            return f"Données reçues, mais format de réponse inconnu pour l'action '{action}'."

        except Exception as e:
            logger.error(f"Erreur lors du formatage de la réponse pour l'action '{action}': {e}", exc_info=True)
            return f"Erreur de formatage de la réponse. Données brutes: {json.dumps(data)}"
    
    def _handle_timeout_error(self, action: str, query: str) -> str:
        """Génère un message d'erreur clair et exploitable pour les timeouts persistants."""
        return (
            f"**ERREUR SYSTÈME : TIMEOUT PERSISTANT**\n"
            f"L'API n'a pas répondu dans le temps imparti ({REQUEST_TIMEOUT * (MAX_RETRIES + 1)}s au total) pour l'action '{action}'.\n"
            f"**Cause probable:** Le service est surchargé ou la recherche est trop complexe.\n"
            f"**Action:** Informez l'utilisateur que le système est lent et de réessayer plus tard. Ne relancez pas de nouvelle recherche."
        )
    
    def _handle_connection_error(self) -> str:
        """Génère un message d'erreur clair pour les échecs de connexion."""
        return (
            f"**ERREUR SYSTÈME : PROBLÈME DE CONNEXION**\n"
            f"Impossible de se connecter à l'API à l'adresse '{API_BASE_URL}'.\n"
            f"**Cause probable:** Le serveur backend est hors ligne ou un problème réseau.\n"
            f"**Action:** Informez l'utilisateur que le service est indisponible. Ne tentez aucune autre commande."
        )

def create_timeout_resistant_agent():
    """Crée et initialise l'agent LLM."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            logger.info(f"Vérification de l'état de l'API réussie. Le service est disponible à {API_BASE_URL}.")
        else:
            logger.warning(f"L'API a répondu avec un statut d'échec: {response.status_code}.")
    except requests.RequestException:
        logger.error(f"Échec de la vérification de l'état. Le serveur à {API_BASE_URL} semble être indisponible.")
    
    instructions = lire_instructions()
    
    agent = LlmAgent(
        name="TachroneAgentOptimized",
        model="gemini-1.5-flash", 
        instruction=instructions,
        tools=[api_query] 
    )
    logger.info("TachroneAgentOptimized créé avec succès.")
    return agent

root_agent = create_timeout_resistant_agent()