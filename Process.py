# Process.py V25 CORRIGÉ RENDER - Cognee optimisé sans blocage
import os
import logging
import asyncio
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from langchain.memory import ConversationBufferMemory
import json
import re
import gc
import threading
from datetime import datetime
import signal
import sys

# Configuration du logging TRÈS RÉDUITE pour Render
logging.basicConfig(
    level=logging.ERROR,  # Seulement les erreurs critiques
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# COGNEE: Import avec gestion d'erreur robuste
COGNEE_AVAILABLE = False
COGNEE_READY = False

try:
    import cognee
    COGNEE_AVAILABLE = True
    logger.error("✅ Cognee importé")  # Utiliser ERROR pour être sûr de voir le log
except ImportError as e:
    logger.error(f"⚠️ Cognee non disponible: {e}")
except Exception as e:
    logger.error(f"❌ Erreur import Cognee: {e}")

# Variables d'environnement SÉCURISÉES
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LLM_API_KEY = os.getenv("LLM_API_KEY") or OPENAI_API_KEY
COGNEE_ENABLED = os.getenv("COGNEE_ENABLED", "false").lower() == "true"  # Désactivé par défaut

if not OPENAI_API_KEY:
    logger.error("❌ OPENAI_API_KEY manquant")
    sys.exit(1)

# Configuration environnement
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
if LLM_API_KEY:
    os.environ["LLM_API_KEY"] = LLM_API_KEY

# Store mémoire ULTRA OPTIMISÉ
memory_store: Dict[str, ConversationBufferMemory] = {}
memory_lock = threading.Lock()
MAX_SESSIONS = 50  # Réduit encore plus
MAX_MESSAGES = 5   # Réduit encore plus

# Gestionnaire Cognee ULTRA SIMPLIFIÉ
class MinimalCogneeManager:
    """Gestionnaire Cognee minimal pour éviter les timeouts"""
    
    def __init__(self):
        self.enabled = COGNEE_AVAILABLE and COGNEE_ENABLED
        self.ready = False
        self.initialization_attempted = False
        
    async def try_initialize(self):
        """Tentative d'initialisation NON-BLOQUANTE"""
        if not self.enabled or self.initialization_attempted:
            return
            
        self.initialization_attempted = True
        
        try:
            # Timeout TRÈS COURT pour l'initialisation
            await asyncio.wait_for(self._quick_init(), timeout=3.0)
            self.ready = True
            logger.error("✅ Cognee prêt")
        except asyncio.TimeoutError:
            logger.error("⏱️ Timeout init Cognee - Mode fallback")
            self.enabled = False
        except Exception as e:
            logger.error(f"❌ Init Cognee échoué: {e}")
            self.enabled = False
    
    async def _quick_init(self):
        """Initialisation rapide"""
        if COGNEE_AVAILABLE:
            # Configuration minimale
            await cognee.priming()
            # Pas de population de base - trop lent pour Render
    
    async def quick_search(self, query: str, user_id: str) -> Optional[str]:
        """Recherche rapide avec timeout court"""
        if not self.enabled or not self.ready:
            return None
            
        try:
            results = await asyncio.wait_for(
                cognee.search(query, user=user_id), 
                timeout=2.0  # Timeout TRÈS court
            )
            
            if results and len(results) > 0:
                return str(results[0])[:200]  # Limite la taille
                
        except asyncio.TimeoutError:
            logger.error("⏱️ Timeout Cognee search")
        except Exception as e:
            logger.error(f"❌ Erreur Cognee: {e}")
            
        return None

# Instance globale
cognee_manager = MinimalCogneeManager()

# Gestionnaire mémoire ULTRA OPTIMISÉ
class UltraOptimizedMemoryManager:
    """Gestionnaire mémoire ultra léger"""
    
    @staticmethod
    def get_memory(wa_id: str) -> ConversationBufferMemory:
        """Obtient mémoire avec nettoyage agressif"""
        with memory_lock:
            # Nettoyage préventif
            if len(memory_store) >= MAX_SESSIONS:
                UltraOptimizedMemoryManager.aggressive_cleanup()
            
            if wa_id not in memory_store:
                memory_store[wa_id] = ConversationBufferMemory(
                    memory_key="history",
                    return_messages=True
                )
            
            memory = memory_store[wa_id]
            
            # Trim automatique
            messages = memory.chat_memory.messages
            if len(messages) > MAX_MESSAGES:
                memory.chat_memory.messages = messages[-MAX_MESSAGES:]
            
            return memory
    
    @staticmethod
    def aggressive_cleanup():
        """Nettoyage agressif"""
        memory_store.clear()
        gc.collect()

# Détecteur de patterns ULTRA SIMPLIFIÉ
class SimplePatternDetector:
    """Détecteur de patterns simple et rapide"""
    
    # Patterns pré-compilés
    AGGRESSIVE_PATTERN = re.compile(r'\b(merde|nul|batard)\b', re.IGNORECASE)
    PAYMENT_PATTERN = re.compile(r'\b(payé|paiement|virement|argent)\b', re.IGNORECASE)
    CPF_PATTERN = re.compile(r'\bcpf\b', re.IGNORECASE)
    DELAY_PATTERN = re.compile(r'(\d+)\s*(mois|semaines?)', re.IGNORECASE)
    
    @staticmethod
    def quick_analysis(message: str) -> Dict[str, Any]:
        """Analyse rapide du message"""
        
        # Agressivité (priorité absolue)
        if SimplePatternDetector.AGGRESSIVE_PATTERN.search(message):
            return {
                "priority": "AGRESSIVITE",
                "response": "Être impoli ne fera pas avancer la situation plus vite. Bien au contraire. Souhaites-tu que je te propose un poème ou une chanson d'amour pour apaiser ton cœur ? 💌",
                "final": True
            }
        
        # Paiement avec délai CPF
        if (SimplePatternDetector.PAYMENT_PATTERN.search(message) and 
            SimplePatternDetector.CPF_PATTERN.search(message)):
            
            delay_match = SimplePatternDetector.DELAY_PATTERN.search(message)
            if delay_match:
                delay_months = int(delay_match.group(1))
                if delay_months >= 2:
                    return {
                        "priority": "CPF_DELAI_DEPASSE",
                        "response": """Juste avant que je transmette ta demande 🙏

Est-ce que tu as déjà été informé par l'équipe que ton dossier CPF faisait partie des quelques cas bloqués par la Caisse des Dépôts ?

👉 Si oui, je te donne directement toutes les infos liées à ce blocage.
Sinon, je fais remonter ta demande à notre équipe pour vérification ✅""",
                        "final": True
                    }
        
        return {"priority": "NORMAL", "final": False}

# Processeur principal SIMPLIFIÉ
async def process_message_ultra_fast(message: str, wa_id: str, matched_bloc: str) -> Dict[str, Any]:
    """Processeur ultra rapide"""
    
    # 1. Analyse rapide des patterns
    pattern_result = SimplePatternDetector.quick_analysis(message)
    
    if pattern_result["final"]:
        return {
            "response": pattern_result["response"],
            "source": "pattern_detection",
            "priority": pattern_result["priority"]
        }
    
    # 2. Essayer Cognee rapidement (si activé)
    cognee_response = None
    if cognee_manager.enabled:
        # Initialisation paresseuse NON-BLOQUANTE
        if not cognee_manager.ready and not cognee_manager.initialization_attempted:
            asyncio.create_task(cognee_manager.try_initialize())
        
        if cognee_manager.ready:
            cognee_response = await cognee_manager.quick_search(message, wa_id)
    
    if cognee_response:
        return {
            "response": cognee_response,
            "source": "cognee",
            "priority": "COGNEE_FOUND"
        }
    
    # 3. Utiliser le bloc n8n si disponible
    if matched_bloc and matched_bloc.strip():
        return {
            "response": matched_bloc,
            "source": "n8n_bloc",
            "priority": "N8N_BLOC"
        }
    
    # 4. Fallback minimal
    return {
        "response": """Salut 👋

Je vais faire suivre ta demande à notre équipe ! 😊

🕐 Notre équipe est disponible du lundi au vendredi, de 9h à 17h.
On te tiendra informé dès que possible ✅""",
        "source": "fallback",
        "priority": "FALLBACK"
    }

# Gestionnaire d'arrêt propre
def signal_handler(signum, frame):
    """Gestionnaire d'arrêt propre"""
    logger.error("🛑 Arrêt du serveur")
    memory_store.clear()
    gc.collect()
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

# Application FastAPI ULTRA OPTIMISÉE
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Cycle de vie simplifié"""
    logger.error("🚀 Démarrage serveur ultra optimisé")
    yield
    logger.error("🛑 Arrêt serveur")
    memory_store.clear()
    gc.collect()

app = FastAPI(
    title="JAK Company API V25 ULTRA OPTIMISÉ",
    version="25.0",
    lifespan=lifespan,
    docs_url=None,  # Désactiver Swagger pour économiser
    redoc_url=None  # Désactiver ReDoc pour économiser
)

# CORS minimal
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

# ENDPOINT PRINCIPAL ULTRA RAPIDE
@app.post("/")
async def ultra_fast_endpoint(request: Request):
    """Endpoint principal ultra optimisé"""
    
    try:
        # Parse avec timeout court
        body = await asyncio.wait_for(request.json(), timeout=5.0)
        
        message = body.get("message_original", body.get("message", ""))
        matched_bloc = body.get("matched_bloc_response", "")
        wa_id = body.get("wa_id", "default")
        
        if not message:
            return JSONResponse({
                "matched_bloc_response": "Message vide",
                "status": "error"
            })
        
        # Gestion mémoire ultra rapide
        memory = UltraOptimizedMemoryManager.get_memory(wa_id)
        memory.chat_memory.add_user_message(message)
        
        # Traitement ultra rapide
        result = await asyncio.wait_for(
            process_message_ultra_fast(message, wa_id, matched_bloc),
            timeout=8.0  # Timeout global court
        )
        
        # Ajouter réponse à la mémoire
        memory.chat_memory.add_ai_message(result["response"])
        
        # Nettoyage immédiat
        gc.collect()
        
        return JSONResponse({
            "matched_bloc_response": result["response"],
            "confidence": 0.8,
            "processing_type": result["priority"],
            "escalade_required": False,
            "status": "ultra_fast_success",
            "source": result["source"],
            "cognee_enabled": cognee_manager.enabled,
            "cognee_ready": cognee_manager.ready
        })
        
    except asyncio.TimeoutError:
        logger.error("⏱️ Timeout global")
        return _ultra_fast_error_response("timeout")
    except Exception as e:
        logger.error(f"❌ Erreur: {str(e)}")
        return _ultra_fast_error_response("error")

def _ultra_fast_error_response(error_type: str):
    """Réponse d'erreur ultra rapide"""
    return JSONResponse({
        "matched_bloc_response": """Salut 👋

Je rencontre un petit problème technique. Notre équipe va regarder ça ! 😊

🕐 Horaires : Lundi-Vendredi, 9h-17h""",
        "confidence": 0.1,
        "processing_type": f"error_{error_type}",
        "escalade_required": True,
        "status": "error_fast_fallback"
    })

# ENDPOINTS DE MONITORING MINIMALISTES
@app.get("/health")
async def health():
    """Health check ultra simple"""
    return JSONResponse({
        "status": "healthy",
        "version": "25.0_ULTRA_FAST",
        "cognee_enabled": cognee_manager.enabled,
        "cognee_ready": cognee_manager.ready,
        "sessions": len(memory_store)
    })

@app.get("/")
async def root():
    """Root endpoint"""
    return JSONResponse({"message": "JAK Company API V25 - Ultra Fast"})

@app.post("/reset")
async def reset():
    """Reset rapide"""
    with memory_lock:
        memory_store.clear()
    gc.collect()
    return JSONResponse({"status": "reset_ok"})

# Point d'entrée
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    
    # Configuration ultra optimisée pour Render
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        workers=1,  # UN SEUL WORKER
        log_level="error",  # Logs minimaux
        access_log=False,  # Pas de logs d'accès
        timeout_keep_alive=30,  # Timeout court
        timeout_graceful_shutdown=10  # Arrêt rapide
    )