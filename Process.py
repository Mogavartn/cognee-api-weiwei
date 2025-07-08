# Process.py V24 OPTIMISÉ RENDER - Système hybride optimisé pour déploiement
import os
import logging
import asyncio
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from langchain.memory import ConversationBufferMemory
import json
import re
import gc
import threading
from datetime import datetime

# Configuration du logging optimisée
logging.basicConfig(
    level=logging.WARNING,  # Réduire les logs
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# NOUVEAU: Import Cognee avec gestion d'erreur améliorée
COGNEE_AVAILABLE = False
try:
    import cognee
    COGNEE_AVAILABLE = True
    logger.info("✅ Cognee disponible")
except ImportError as e:
    logger.warning(f"⚠️ Cognee non disponible: {e}")
except Exception as e:
    logger.error(f"❌ Erreur import Cognee: {e}")

# Configuration des variables d'environnement
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LLM_API_KEY = os.getenv("LLM_API_KEY") or OPENAI_API_KEY
COGNEE_ENABLED = os.getenv("COGNEE_ENABLED", "true").lower() == "true"

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is required")

# Configuration globale
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
if LLM_API_KEY:
    os.environ["LLM_API_KEY"] = LLM_API_KEY

# Store pour la mémoire avec nettoyage automatique
memory_store: Dict[str, ConversationBufferMemory] = {}
memory_lock = threading.Lock()

# Gestionnaire Cognee optimisé
class OptimizedCogneeManager:
    """Gestionnaire Cognee optimisé pour Render"""
    
    def __init__(self):
        self.cognee_initialized = False
        self.fallback_mode = not (COGNEE_AVAILABLE and COGNEE_ENABLED)
        self.initialization_lock = asyncio.Lock()
        self.knowledge_populated = False
        
    async def initialize_cognee_lazy(self):
        """Initialisation paresseuse de Cognee"""
        if self.fallback_mode or self.cognee_initialized:
            return
            
        async with self.initialization_lock:
            if self.cognee_initialized:
                return
                
            try:
                logger.info("🔄 Initialisation Cognee...")
                
                # Configuration Cognee optimisée pour Render
                if COGNEE_AVAILABLE:
                    # Configuration minimale pour économiser la mémoire
                    await self._configure_cognee_lightweight()
                    
                    # Peupler la base de connaissances seulement si nécessaire
                    if not self.knowledge_populated:
                        await self._populate_jak_knowledge_optimized()
                        self.knowledge_populated = True
                    
                    self.cognee_initialized = True
                    logger.info("✅ Cognee initialisé (mode optimisé)")
                    
                    # Nettoyage mémoire après initialisation
                    gc.collect()
                    
            except Exception as e:
                logger.error(f"❌ Erreur init Cognee: {str(e)}")
                self.fallback_mode = True
                gc.collect()
    
    async def _configure_cognee_lightweight(self):
        """Configuration Cognee légère pour Render"""
        try:
            # Configuration minimale
            if hasattr(cognee, 'config'):
                # Utiliser des modèles plus légers
                cognee.config.set_embedding_model("text-embedding-3-small")
                # Base de données en mémoire pour économiser l'espace
                cognee.config.set_vector_db_url("sqlite:///:memory:")
        except Exception as e:
            logger.warning(f"⚠️ Configuration Cognee: {e}")
    
    async def _populate_jak_knowledge_optimized(self):
        """Peuple Cognee avec une base de connaissances optimisée"""
        
        # Base de connaissances condensée pour économiser la mémoire
        jak_knowledge = {
            "paiements": """JAK Company - Paiements:
CPF: 45j minimum après émargement. Réforme 2025: <50/2500 dossiers bloqués.
OPCO: 2-6 mois selon organisme.
Direct: 7j après formation complète.""",
            
            "ambassadeur": """Programme Ambassadeur JAK:
1. S'abonner: Instagram/Snapchat
2. Code affiliation: swiy.co/jakpro
3. Contacts: mrqz.to/AffiliationPromotion
4. Commission: jusqu'à 60%. Paiement: 3000€/an max, 3 virements.""",
            
            "formations": """JAK Formations:
100+ formations: Bureautique, Dev Web/3D, Langues, Marketing, Développement personnel.
IMPORTANT: Plus de CPF depuis février 2025.""",
            
            "support": """Support JAK:
Horaires: Lun-Ven 9h-17h
Escalade: ADMIN (paiements), FORMATION (pros/particuliers), ENTREPRISE (B2B)
Réseaux: Instagram/Snapchat"""
        }
        
        try:
            # Ajouter par chunks pour économiser la mémoire
            for key, content in jak_knowledge.items():
                await cognee.add(content, dataset_name=f"jak_{key}")
                await asyncio.sleep(0.1)  # Pause pour éviter la surcharge
            
            # Générer le knowledge graph
            await cognee.cognify()
            logger.info("📚 Base JAK ajoutée (optimisée)")
            
        except Exception as e:
            logger.error(f"❌ Erreur population Cognee: {e}")
            raise
    
    async def try_cognee_search(self, user_message: str, wa_id: str) -> Optional[Dict[str, Any]]:
        """Recherche Cognee optimisée"""
        
        if self.fallback_mode:
            return None
            
        # Initialisation paresseuse
        if not self.cognee_initialized:
            await self.initialize_cognee_lazy()
            
        if not self.cognee_initialized:
            return None
            
        try:
            # Recherche avec timeout pour éviter les blocages
            results = await asyncio.wait_for(
                cognee.search(user_message, user=wa_id),
                timeout=5.0
            )
            
            if not results:
                return None
                
            # Analyse de pertinence conservative
            confidence = min(len(results) / 5.0, 1.0)
            
            if confidence < 0.4:  # Seuil plus élevé
                return None
                
            # Formater la réponse (limiter la taille)
            main_result = str(results[0])[:400] + "..." if len(str(results[0])) > 400 else str(results[0])
                
            return {
                "response": main_result,
                "confidence": confidence,
                "results_count": len(results),
                "source": "cognee"
            }
            
        except asyncio.TimeoutError:
            logger.warning("⏱️ Timeout Cognee search")
            return None
        except Exception as e:
            logger.error(f"❌ Erreur Cognee search: {str(e)}")
            return None

# Instance globale
cognee_manager = OptimizedCogneeManager()

# Gestionnaire de mémoire optimisé
class OptimizedMemoryManager:
    """Gestionnaire de mémoire optimisé avec nettoyage automatique"""
    
    MAX_SESSIONS = 100  # Limite le nombre de sessions
    MAX_MESSAGES = 10   # Réduit la taille des conversations
    
    @staticmethod
    def get_or_create_memory(wa_id: str) -> ConversationBufferMemory:
        """Obtient ou crée une mémoire avec nettoyage automatique"""
        with memory_lock:
            # Nettoyage automatique si trop de sessions
            if len(memory_store) >= OptimizedMemoryManager.MAX_SESSIONS:
                OptimizedMemoryManager.cleanup_old_sessions()
            
            if wa_id not in memory_store:
                memory_store[wa_id] = ConversationBufferMemory(
                    memory_key="history",
                    return_messages=True
                )
            
            return memory_store[wa_id]
    
    @staticmethod
    def cleanup_old_sessions():
        """Nettoie les anciennes sessions"""
        if len(memory_store) > OptimizedMemoryManager.MAX_SESSIONS // 2:
            # Garder seulement la moitié des sessions
            sessions_to_keep = list(memory_store.keys())[:OptimizedMemoryManager.MAX_SESSIONS // 2]
            memory_store.clear()
            logger.info(f"🧹 Nettoyage mémoire: {len(sessions_to_keep)} sessions conservées")
    
    @staticmethod
    def trim_memory(memory: ConversationBufferMemory):
        """Réduit la taille de la mémoire"""
        messages = memory.chat_memory.messages
        if len(messages) > OptimizedMemoryManager.MAX_MESSAGES:
            memory.chat_memory.messages = messages[-OptimizedMemoryManager.MAX_MESSAGES:]
    
    @staticmethod
    def get_memory_summary(memory: ConversationBufferMemory) -> Dict[str, Any]:
        """Résumé de la mémoire"""
        messages = memory.chat_memory.messages
        return {
            "total_messages": len(messages),
            "memory_size_chars": sum(len(str(m.content)) for m in messages)
        }

# Classes métier conservées mais optimisées
class PaymentContextProcessor:
    """Processeur de contexte de paiement - optimisé"""
    
    # Patterns compilés pour de meilleures performances
    FINANCING_PATTERNS = {
        'CPF': re.compile(r'\b(cpf|compte personnel)\b', re.IGNORECASE),
        'OPCO': re.compile(r'\b(opco|operateur|opérateur)\b', re.IGNORECASE),
        'direct': re.compile(r'\b(direct|entreprise|particulier)\b', re.IGNORECASE)
    }
    
    DELAY_PATTERN = re.compile(r'(?:il y a|depuis|ça fait|ca fait)\s*(\d+)\s*(mois|semaines?)', re.IGNORECASE)
    
    @staticmethod
    def extract_financing_type(message: str) -> Optional[str]:
        """Extrait le type de financement (optimisé)"""
        for financing_type, pattern in PaymentContextProcessor.FINANCING_PATTERNS.items():
            if pattern.search(message):
                return financing_type
        return None
    
    @staticmethod
    def extract_time_delay(message: str) -> Optional[int]:
        """Extrait le délai (optimisé)"""
        match = PaymentContextProcessor.DELAY_PATTERN.search(message)
        if match:
            number = int(match.group(1))
            unit = match.group(2).lower()
            if 'semaine' in unit:
                return max(1, round(number / 4.33))
            return number
        return None

class OptimizedMessageProcessor:
    """Processeur de messages optimisé"""
    
    # Patterns compilés
    AGGRESSIVE_PATTERN = re.compile(r'\b(merde|nul|batard|enervez)\b', re.IGNORECASE)
    PAYMENT_PATTERN = re.compile(r'\b(pas été payé|rien reçu|virement|attends|paiement|argent)\b', re.IGNORECASE)
    
    @staticmethod
    async def detect_priority_rules_hybrid(user_message: str, matched_bloc_response: str,
                                         conversation_context: Dict[str, Any]) -> Dict[str, Any]:
        """Détection de règles prioritaires hybride optimisée"""
        
        # Essayer Cognee pour les cas complexes (seulement si activé)
        if COGNEE_ENABLED and not cognee_manager.fallback_mode:
            try:
                cognee_result = await cognee_manager.try_cognee_search(
                    user_message, 
                    conversation_context.get("wa_id", "unknown")
                )
                
                if cognee_result and cognee_result["confidence"] > 0.6:
                    logger.info(f"✅ Réponse Cognee (conf: {cognee_result['confidence']:.2f})")
                    return {
                        "use_matched_bloc": False,
                        "priority_detected": "COGNEE_RESPONSE",
                        "response": cognee_result["response"],
                        "confidence": cognee_result["confidence"],
                        "source": "cognee",
                        "context": conversation_context
                    }
            except Exception as e:
                logger.error(f"❌ Erreur Cognee: {e}")
        
        # Fallback vers système existant optimisé
        logger.info("📋 Fallback système existant")
        
        # Détection agressivité (optimisée)
        if OptimizedMessageProcessor.AGGRESSIVE_PATTERN.search(user_message):
            return {
                "use_matched_bloc": False,
                "priority_detected": "AGRESSIVITE",
                "response": "Être impoli ne fera pas avancer la situation plus vite. Bien au contraire. Souhaites-tu que je te propose un poème ou une chanson d'amour pour apaiser ton cœur ? 💌",
                "context": conversation_context,
                "source": "existing_system"
            }
        
        # Détection paiement (optimisée)
        if OptimizedMessageProcessor.PAYMENT_PATTERN.search(user_message):
            financing_type = PaymentContextProcessor.extract_financing_type(user_message)
            delay_months = PaymentContextProcessor.extract_time_delay(user_message)
            
            if financing_type == "CPF" and delay_months and delay_months >= 2:
                return {
                    "use_matched_bloc": False,
                    "priority_detected": "CPF_DELAI_DEPASSE_FILTRAGE",
                    "response": """Juste avant que je transmette ta demande 🙏

Est-ce que tu as déjà été informé par l'équipe que ton dossier CPF faisait partie des quelques cas bloqués par la Caisse des Dépôts ?

👉 Si oui, je te donne directement toutes les infos liées à ce blocage.
Sinon, je fais remonter ta demande à notre équipe pour vérification ✅""",
                    "context": conversation_context,
                    "awaiting_cpf_info": True,
                    "source": "existing_system"
                }
        
        # Utiliser bloc n8n si disponible
        if matched_bloc_response and matched_bloc_response.strip():
            return {
                "use_matched_bloc": True,
                "priority_detected": "N8N_BLOC_DETECTED",
                "response": matched_bloc_response,
                "context": conversation_context,
                "source": "existing_system"
            }
        
        # Fallback général
        return {
            "use_matched_bloc": False,
            "priority_detected": "FALLBACK_GENERAL",
            "context": conversation_context,
            "response": None,
            "use_ai": True,
            "source": "existing_system"
        }

# Gestionnaire de contexte pour l'application
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestionnaire de cycle de vie de l'application"""
    logger.info("🚀 Démarrage application optimisée")
    
    # Initialisation différée de Cognee
    if COGNEE_ENABLED and COGNEE_AVAILABLE:
        logger.info("📋 Cognee sera initialisé lors de la première utilisation")
    else:
        logger.info("📋 Mode système existant uniquement")
    
    yield
    
    # Nettoyage
    logger.info("🧹 Nettoyage application")
    memory_store.clear()
    gc.collect()

# Application FastAPI optimisée
app = FastAPI(
    title="JAK Company AI Agent API OPTIMISÉ",
    version="24.0",
    lifespan=lifespan
)

# Middleware CORS optimisé
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # Limité aux méthodes nécessaires
    allow_headers=["*"],
)

# Endpoint principal optimisé
@app.post("/")
async def process_message_optimized(request: Request):
    """Point d'entrée principal optimisé"""
    
    try:
        # Parse request avec timeout
        body = await asyncio.wait_for(request.json(), timeout=10.0)
        
        user_message = body.get("message_original", body.get("message", ""))
        matched_bloc_response = body.get("matched_bloc_response", "")
        wa_id = body.get("wa_id", "default_wa_id")
        
        if not user_message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        logger.info(f"[{wa_id}] Processing: '{user_message[:30]}...'")
        
        # Gestion mémoire optimisée
        memory = OptimizedMemoryManager.get_or_create_memory(wa_id)
        OptimizedMemoryManager.trim_memory(memory)
        
        # Contexte conversation
        conversation_context = {
            "message_count": len(memory.chat_memory.messages),
            "wa_id": wa_id,
            "is_follow_up": len(memory.chat_memory.messages) > 0,
            "timestamp": datetime.now().isoformat()
        }
        
        # Ajouter message utilisateur
        memory.chat_memory.add_user_message(user_message)
        
        # Traitement hybride optimisé
        priority_result = await OptimizedMessageProcessor.detect_priority_rules_hybrid(
            user_message, matched_bloc_response, conversation_context
        )
        
        # Construire réponse
        final_response = priority_result.get("response")
        response_source = priority_result.get("source", "unknown")
        
        if not final_response:
            final_response = matched_bloc_response or """Salut 👋

Je vais faire suivre ta demande à notre équipe ! 😊

🕐 Notre équipe est disponible du lundi au vendredi, de 9h à 17h.
On te tiendra informé dès que possible ✅"""
            response_source = "fallback"
        
        # Ajouter réponse à la mémoire
        memory.chat_memory.add_ai_message(final_response)
        OptimizedMemoryManager.trim_memory(memory)
        
        # Apprentissage Cognee différé (non-bloquant)
        if COGNEE_ENABLED and cognee_manager.cognee_initialized:
            asyncio.create_task(cognee_manager.try_cognee_search(
                f"Conversation {wa_id}: {user_message} -> {final_response}",
                wa_id
            ))
        
        # Nettoyage mémoire
        gc.collect()
        
        return {
            "matched_bloc_response": final_response,
            "confidence": priority_result.get("confidence", 0.7),
            "processing_type": priority_result.get("priority_detected", "hybrid"),
            "escalade_required": priority_result.get("escalade_required", False),
            "escalade_type": priority_result.get("escalade_type", "general"),
            "status": "optimized_success",
            "response_source": response_source,
            "cognee_available": COGNEE_AVAILABLE and COGNEE_ENABLED,
            "session_id": wa_id,
            "memory_summary": OptimizedMemoryManager.get_memory_summary(memory)
        }
        
    except asyncio.TimeoutError:
        logger.error("⏱️ Timeout processing request")
        return _error_response("Timeout")
    except Exception as e:
        logger.error(f"❌ Error processing: {str(e)}")
        return _error_response("Error")

def _error_response(error_type: str):
    """Réponse d'erreur standard"""
    return {
        "matched_bloc_response": """Salut 👋

Je rencontre un petit problème technique. Notre équipe va regarder ça ! 😊

🕐 Horaires : Lundi-Vendredi, 9h-17h""",
        "confidence": 0.1,
        "processing_type": f"error_{error_type.lower()}",
        "escalade_required": True,
        "status": "error",
        "response_source": "error_fallback"
    }

# Endpoints de monitoring
@app.get("/health")
async def health_check():
    """Health check optimisé"""
    return {
        "status": "healthy",
        "version": "24.0 OPTIMIZED",
        "timestamp": datetime.now().isoformat(),
        "cognee_available": COGNEE_AVAILABLE,
        "cognee_enabled": COGNEE_ENABLED,
        "cognee_initialized": cognee_manager.cognee_initialized if COGNEE_AVAILABLE else False,
        "fallback_mode": cognee_manager.fallback_mode if COGNEE_AVAILABLE else True,
        "active_sessions": len(memory_store),
        "memory_usage": f"{len(memory_store)}/{OptimizedMemoryManager.MAX_SESSIONS}"
    }

@app.post("/cognee/reset")
async def reset_cognee():
    """Reset Cognee"""
    if not COGNEE_AVAILABLE or not COGNEE_ENABLED:
        raise HTTPException(status_code=400, detail="Cognee not available")
    
    try:
        await cognee.reset()
        cognee_manager.cognee_initialized = False
        cognee_manager.knowledge_populated = False
        gc.collect()
        return {"status": "Cognee reset successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/memory/cleanup")
async def cleanup_memory():
    """Nettoyage manuel de la mémoire"""
    with memory_lock:
        session_count = len(memory_store)
        memory_store.clear()
        gc.collect()
        return {
            "status": "Memory cleaned",
            "sessions_cleared": session_count,
            "timestamp": datetime.now().isoformat()
        }

# Point d'entrée principal
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        workers=1,  # Un seul worker pour économiser la mémoire
        log_level="warning"  # Réduire les logs
    )