# Agents Service pour Aqar IA

Service d'agents intelligents spécialisés dans l'immobilier au Maroc.

## 📋 Vue d'ensemble
Système d'agents IA coordonnés pour assister dans toutes les étapes de l'acquisition immobilière au Maroc.

## ��️ Architecture
- **Chef Orchestrateur** : Coordination et routage intelligent des questions
- **Expert Finance** : Budget, emprunt, coûts, fiscalité
- **Expert Guide Acquéreur** : Acquisition, étapes, promoteurs, conseils
- **Expert Matériaux** : Matériaux, fournisseurs, construction

## ⚙️ Installation et Configuration
```bash
# Cloner le projet
git clone [repository-url]
cd mon_projet_adk

# Installer les dépendances
pip install -r requirements.txt
```

## 🔧 Variables d'Environnement
```bash
# Configuration Google ADK
GOOGLE_API_KEY=your_api_key
GOOGLE_PROJECT_ID=your_project_id
# Configuration Vertex AI Search
VERTEX_SEARCH_DATASTORE_ID=your_datastore_id
```

## 🤖 Aperçu des Agents

### Chef Orchestrateur
- Analyse et route les questions vers l'expert approprié
- Coordonne les réponses des différents experts
- Fournit des réponses unifiées

### Expert Finance
- Calcul de capacité d'emprunt
- Analyse de la fiscalité immobilière
- Conseils budgétaires

### Expert Guide Acquéreur
- Étapes d'acquisition immobilière
- Vérification des promoteurs FNPI
- Checklists de livraison

### Expert Matériaux
- Recherche de matériaux de construction
- Fournisseurs et prestataires
- Base de données Tachrone

## �� Utilisation Docker
```bash
# Construire l'image
docker build -t aqar-ia-agents .

# Lancer le service
docker run -p 8000:8000 aqar-ia-agents
```

## �� Lancement
```bash
python chef/agent.py
```

## 📄 Licence
MIT License - Voir le fichier LICENSE pour plus de détails.