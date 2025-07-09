# Process.py V26 UNIFIÉ - Cognee + Langchain optimisé pour WhatsApp Agent IA
import os
import logging
import asyncio
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from langchain.memory import ConversationBufferMemory
from langchain.schema import BaseMessage, HumanMessage, AIMessage
import json
import re
import gc
import threading
from datetime import datetime, timedelta
import signal
import sys

# Configuration du logging optimisée
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# COGNEE: Import avec gestion d'erreur robuste
COGNEE_AVAILABLE = False
COGNEE_READY = False

try:
    import cognee
    COGNEE_AVAILABLE = True
    logger.info("✅ Cognee importé avec succès")
except ImportError as e:
    logger.warning(f"⚠️ Cognee non disponible: {e}")
except Exception as e:
    logger.error(f"❌ Erreur import Cognee: {e}")

# Variables d'environnement sécurisées
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LLM_API_KEY = os.getenv("LLM_API_KEY") or OPENAI_API_KEY
COGNEE_ENABLED = os.getenv("COGNEE_ENABLED", "true").lower() == "true"
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"

if not OPENAI_API_KEY:
    logger.error("❌ OPENAI_API_KEY manquant")
    sys.exit(1)

# Configuration environnement
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
if LLM_API_KEY:
    os.environ["LLM_API_KEY"] = LLM_API_KEY

# Store mémoire optimisé avec TTL
memory_store: Dict[str, Dict[str, Any]] = {}
memory_lock = threading.Lock()
MAX_SESSIONS = 100
MAX_MESSAGES = 15
MEMORY_TTL_HOURS = 24

class OptimizedMemoryManager:
    """Gestionnaire de mémoire avec TTL et cleanup automatique"""
    
    @staticmethod
    def cleanup_expired_sessions():
        """Nettoie les sessions expirées"""
        current_time = datetime.now()
        expired_keys = []
        
        with memory_lock:
            for session_id, session_data in memory_store.items():
                if 'last_activity' in session_data:
                    last_activity = session_data['last_activity']
                    if current_time - last_activity > timedelta(hours=MEMORY_TTL_HOURS):
                        expired_keys.append(session_id)
            
            for key in expired_keys:
                del memory_store[key]
                
        if expired_keys:
            logger.info(f"🧹 Nettoyé {len(expired_keys)} sessions expirées")
    
    @staticmethod
    def get_memory(wa_id: str) -> ConversationBufferMemory:
        """Obtient mémoire avec gestion TTL"""
        current_time = datetime.now()
        
        with memory_lock:
            # Cleanup préventif
            if len(memory_store) >= MAX_SESSIONS:
                OptimizedMemoryManager.cleanup_expired_sessions()
            
            if wa_id not in memory_store:
                memory = ConversationBufferMemory(
                    memory_key="history",
                    return_messages=True
                )
                memory_store[wa_id] = {
                    'memory': memory,
                    'last_activity': current_time,
                    'message_count': 0
                }
            else:
                memory_store[wa_id]['last_activity'] = current_time
            
            session_data = memory_store[wa_id]
            memory = session_data['memory']
            
            # Trim messages si nécessaire
            messages = memory.chat_memory.messages
            if len(messages) > MAX_MESSAGES:
                memory.chat_memory.messages = messages[-MAX_MESSAGES:]
                session_data['message_count'] = len(memory.chat_memory.messages)
            
            return memory
    
    @staticmethod
    def get_memory_summary(memory: ConversationBufferMemory) -> Dict[str, Any]:
        """Retourne un résumé de la mémoire"""
        messages = memory.chat_memory.messages
        return {
            "total_messages": len(messages),
            "user_messages": len([m for m in messages if isinstance(m, HumanMessage)]),
            "ai_messages": len([m for m in messages if isinstance(m, AIMessage)]),
            "memory_size_chars": sum(len(str(m.content)) for m in messages)
        }

class CogneeManager:
    """Gestionnaire Cognee optimisé avec fallback"""
    
    def __init__(self):
        self.enabled = COGNEE_AVAILABLE and COGNEE_ENABLED
        self.ready = False
        self.initialization_attempted = False
        self.knowledge_base_populated = False
        
    async def initialize(self):
        """Initialisation complète de Cognee"""
        if not self.enabled or self.initialization_attempted:
            return
            
        self.initialization_attempted = True
        
        try:
            logger.info("🔄 Initialisation Cognee...")
            await asyncio.wait_for(self._full_init(), timeout=30.0)
            self.ready = True
            logger.info("✅ Cognee initialisé avec succès")
        except asyncio.TimeoutError:
            logger.warning("⏱️ Timeout init Cognee - Mode fallback activé")
            self.enabled = False
        except Exception as e:
            logger.error(f"❌ Échec initialisation Cognee: {e}")
            self.enabled = False
    
    async def _full_init(self):
        """Initialisation complète avec base de connaissances"""
        if not COGNEE_AVAILABLE:
            return
            
        # Configuration Cognee
        await cognee.priming()
        
        # Peupler la base de connaissances JAK Company
        if not self.knowledge_base_populated:
            await self._populate_knowledge_base()
            self.knowledge_base_populated = True
    
    async def _populate_knowledge_base(self):
        """Peuple la base de connaissances avec les informations JAK Company"""
        knowledge_data = [
            {
                "topic": "formations_jak_company",
                "content": """JAK Company propose plus de 100 formations dans plusieurs domaines :
                - Bureautique (Word, Excel, PowerPoint)
                - Informatique & Développement Web/3D
                - Langues étrangères
                - Vente & Marketing digital
                - Développement personnel
                - Écologie & Numérique responsable
                - Bilan de compétences
                
                Modalités : e-learning (100% en ligne) et présentiel selon localisation.
                Financement : entreprises, professionnels, OPCO.
                Note importante : formations CPF suspendues temporairement."""
            },
            {
                "topic": "programme_ambassadeur",
                "content": """Programme Ambassadeur JAK Company :
                1. S'abonner aux réseaux sociaux (Instagram, Snapchat)
                2. Créer son code d'affiliation sur https://swiy.co/jakpro
                3. Envoyer des contacts via https://mrqz.to/AffiliationPromotion
                4. Toucher une commission jusqu'à 60% par dossier validé
                
                Paiement possible sur compte personnel (max 3000€/an, 3 virements).
                Au-delà, création micro-entreprise nécessaire."""
            },
            {
                "topic": "delais_paiement",
                "content": """Délais de paiement JAK Company :
                - Paiement direct : 7 jours après fin formation + dossier complet
                - CPF : minimum 45 jours après feuilles émargement signées
                - OPCO : délai moyen 2 mois, peut aller jusqu'à 6 mois
                
                Problème actuel CPF : moins de 50 dossiers sur 2500 bloqués depuis réforme février 2025.
                Délais imprévisibles dus aux demandes répétées de la Caisse des Dépôts."""
            },
            {
                "topic": "contact_escalade",
                "content": """Informations de contact et escalade :
                - Horaires équipe : Lundi-Vendredi, 9h-17h (hors pause déjeuner)
                - Types d'escalade : AGENT ADMIN, ÉQUIPE FORMATION, ÉQUIPE ENTREPRISE
                - Réseaux sociaux : Instagram (https://hi.switchy.io/InstagramWeiWei), Snapchat (https://hi.switchy.io/SnapChatWeiWei)"""
            }
        ]
        
        for item in knowledge_data:
            try:
                await cognee.add(item["content"], dataset_name=item["topic"])
                logger.info(f"📚 Ajouté à la base de connaissances: {item['topic']}")
            except Exception as e:
                logger.warning(f"⚠️ Erreur ajout {item['topic']}: {e}")
    
    async def search_knowledge(self, query: str, user_id: str) -> Optional[str]:
        """Recherche dans la base de connaissances"""
        if not self.enabled or not self.ready:
            return None
            
        try:
            results = await asyncio.wait_for(
                cognee.search(query, user=user_id), 
                timeout=5.0
            )
            
            if results and len(results) > 0:
                # Formater la réponse
                response = str(results[0])
                if len(response) > 500:
                    response = response[:500] + "..."
                return response
                
        except asyncio.TimeoutError:
            logger.warning("⏱️ Timeout recherche Cognee")
        except Exception as e:
            logger.warning(f"❌ Erreur recherche Cognee: {e}")
            
        return None

class ConversationContextManager:
    """Gestionnaire du contexte conversationnel avancé"""
    
    @staticmethod
    def analyze_conversation_context(user_message: str, memory: ConversationBufferMemory) -> Dict[str, Any]:
        """Analyse complète du contexte conversationnel"""
        
        history = memory.chat_memory.messages
        message_count = len(history)
        
        # Analyse des indicateurs de suivi
        follow_up_indicators = [
            "comment", "pourquoi", "vous pouvez", "tu peux", "aide", "démarrer",
            "oui", "ok", "d'accord", "et après", "ensuite", "comment faire",
            "comment ça marche", "les étapes", "ça marche comment"
        ]
        
        is_follow_up = any(indicator in user_message.lower() for indicator in follow_up_indicators)
        
        # Analyse du contexte récent
        context_analysis = {
            "message_count": message_count,
            "is_follow_up": is_follow_up,
            "needs_greeting": message_count == 0,
            "conversation_flow": "continuing" if message_count > 0 else "starting",
            "last_messages": [],
            "topics_discussed": [],
            "awaiting_specific_info": False,
            "payment_context_detected": False,
            "affiliation_context_detected": False,
            "formation_context_detected": False
        }
        
        if message_count > 0:
            # Analyser les derniers messages pour détecter les contextes
            recent_messages = history[-6:] if len(history) >= 6 else history
            
            for msg in recent_messages:
                content = str(msg.content).lower()
                context_analysis["last_messages"].append(content)
                
                # Détection des contextes
                if any(word in content for word in ["paiement", "payé", "virement", "formation", "cpf", "opco"]):
                    context_analysis["payment_context_detected"] = True
                    context_analysis["topics_discussed"].append("paiement")
                
                if any(word in content for word in ["ambassadeur", "affiliation", "commission", "contacts"]):
                    context_analysis["affiliation_context_detected"] = True
                    context_analysis["topics_discussed"].append("ambassadeur")
                
                if any(word in content for word in ["formation", "cours", "apprentissage", "financement"]):
                    context_analysis["formation_context_detected"] = True
                    context_analysis["topics_discussed"].append("formation")
                
                # Détection d'attente d'informations spécifiques
                if any(phrase in content for phrase in [
                    "comment la formation a été financée",
                    "environ quand la formation s'est terminée",
                    "tu as déjà été informé"
                ]):
                    context_analysis["awaiting_specific_info"] = True
        
        return context_analysis

class EnhancedPatternDetector:
    """Détecteur de patterns avancé avec logique contextuelle"""
    
    @staticmethod
    def detect_payment_context(message: str, conversation_context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Détecte le contexte de paiement avec analyse des délais"""
        
        message_lower = message.lower()
        
        # Patterns de financement
        financing_patterns = {
            'CPF': ['cpf', 'compte personnel', 'compte personnel formation'],
            'OPCO': ['opco', 'operateur', 'opérateur', 'organisme paritaire'],
            'direct': ['direct', 'entreprise', 'particulier', 'j\'ai payé', 'financé moi']
        }
        
        # Patterns de délai
        delay_pattern = re.compile(r'(\d+)\s*(mois|semaines?|jours?)', re.IGNORECASE)
        
        financing_type = None
        for fin_type, patterns in financing_patterns.items():
            if any(pattern in message_lower for pattern in patterns):
                financing_type = fin_type
                break
        
        delay_match = delay_pattern.search(message_lower)
        delay_info = None
        
        if delay_match:
            number = int(delay_match.group(1))
            unit = delay_match.group(2).lower()
            
            # Conversion en jours pour calcul précis
            if 'semaine' in unit:
                delay_days = number * 7
            elif 'jour' in unit:
                delay_days = number
            else:  # mois
                delay_days = number * 30
            
            delay_info = {
                "original_number": number,
                "original_unit": unit,
                "delay_days": delay_days,
                "delay_months": delay_days / 30
            }
        
        if financing_type or delay_info:
            return {
                "financing_type": financing_type,
                "delay_info": delay_info,
                "requires_specialized_handling": True
            }
        
        return None
    
    @staticmethod
    def detect_priority_patterns(message: str, conversation_context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Détecte les patterns prioritaires nécessitant un traitement spécialisé"""
        
        message_lower = message.lower()
        
        # 1. Agressivité (priorité absolue)
        aggressive_terms = ['merde', 'nul', 'batard', 'énervez', 'chier', 'putain']
        if any(term in message_lower for term in aggressive_terms):
            return {
                "priority": "AGRESSIVITE",
                "response": "Être impoli ne fera pas avancer la situation plus vite. Bien au contraire. Souhaites-tu que je te propose un poème ou une chanson d'amour pour apaiser ton cœur ? 💌",
                "final": True
            }
        
        # 2. Contexte de paiement
        payment_context = EnhancedPatternDetector.detect_payment_context(message, conversation_context)
        if payment_context:
            return {
                "priority": "PAYMENT_CONTEXT",
                "context_data": payment_context,
                "requires_specialized_processing": True
            }
        
        # 3. Demandes d'étapes ambassadeur
        if conversation_context.get("affiliation_context_detected") and any(
            phrase in message_lower for phrase in ["comment ça marche", "les étapes", "comment faire"]
        ):
            return {
                "priority": "AMBASSADEUR_STEPS",
                "requires_specialized_processing": True
            }
        
        return None

# Instance globale Cognee
cognee_manager = CogneeManager()

# Processeur principal unifié
async def process_message_unified(
    message: str, 
    wa_id: str, 
    matched_bloc: str = "", 
    processing_type: str = "",
    contextual_info: Dict = None
) -> Dict[str, Any]:
    """Processeur unifié combinant Cognee, Langchain et logique métier"""
    
    logger.info(f"🔍 TRAITEMENT MESSAGE: '{message[:50]}...', wa_id: {wa_id}")
    
    # 1. Gestion de la mémoire
    memory = OptimizedMemoryManager.get_memory(wa_id)
    conversation_context = ConversationContextManager.analyze_conversation_context(message, memory)
    
    # 2. Détection de patterns prioritaires
    priority_pattern = EnhancedPatternDetector.detect_priority_patterns(message, conversation_context)
    
    if priority_pattern and priority_pattern.get("final"):
        logger.info(f"🎯 PATTERN PRIORITAIRE FINAL: {priority_pattern['priority']}")
        return {
            "response": priority_pattern["response"],
            "source": "priority_pattern",
            "priority": priority_pattern["priority"],
            "escalade_required": False
        }
    
    # 3. Traitement spécialisé si nécessaire
    if priority_pattern and priority_pattern.get("requires_specialized_processing"):
        logger.info(f"🔧 TRAITEMENT SPÉCIALISÉ: {priority_pattern['priority']}")
        specialized_response = await handle_specialized_processing(
            message, wa_id, priority_pattern, conversation_context
        )
        if specialized_response:
            return specialized_response
    
    # 4. Recherche Cognee (si disponible et initialisé)
    cognee_response = None
    if cognee_manager.enabled:
        # Initialisation paresseuse
        if not cognee_manager.ready:
            await cognee_manager.initialize()
        
        if cognee_manager.ready:
            cognee_response = await cognee_manager.search_knowledge(message, wa_id)
    
    if cognee_response:
        logger.info("✅ RÉPONSE COGNEE UTILISÉE")
        memory.chat_memory.add_user_message(message)
        memory.chat_memory.add_ai_message(cognee_response)
        return {
            "response": cognee_response,
            "source": "cognee_knowledge_base",
            "priority": "COGNEE_KNOWLEDGE"
        }
    
    # 5. Utilisation du bloc n8n si pertinent
    if matched_bloc and matched_bloc.strip() and not _is_generic_fallback(matched_bloc):
        logger.info("📋 UTILISATION BLOC N8N SPÉCIALISÉ")
        memory.chat_memory.add_user_message(message)
        memory.chat_memory.add_ai_message(matched_bloc)
        return {
            "response": matched_bloc,
            "source": "n8n_specialized_bloc",
            "priority": "N8N_BLOC"
        }
    
    # 6. Génération de réponse contextuelle avec mémoire
    contextual_response = await generate_contextual_response(
        message, memory, conversation_context
    )
    
    if contextual_response:
        logger.info("🧠 RÉPONSE CONTEXTUELLE GÉNÉRÉE")
        memory.chat_memory.add_user_message(message)
        memory.chat_memory.add_ai_message(contextual_response)
        return {
            "response": contextual_response,
            "source": "contextual_generation",
            "priority": "CONTEXTUAL"
        }
    
    # 7. Fallback final optimisé
    logger.info("🔄 FALLBACK FINAL")
    fallback_response = generate_smart_fallback(conversation_context)
    memory.chat_memory.add_user_message(message)
    memory.chat_memory.add_ai_message(fallback_response)
    
    return {
        "response": fallback_response,
        "source": "smart_fallback",
        "priority": "FALLBACK"
    }

def _is_generic_fallback(response: str) -> bool:
    """Détermine si une réponse est un fallback générique"""
    generic_indicators = [
        "Salut 👋",
        "Je vais faire suivre ta demande",
        "Notre équipe est disponible",
        "On te tiendra informé"
    ]
    return any(indicator in response for indicator in generic_indicators)

async def handle_specialized_processing(
    message: str, 
    wa_id: str, 
    priority_pattern: Dict[str, Any], 
    conversation_context: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Gère le traitement spécialisé pour les cas complexes"""
    
    priority = priority_pattern["priority"]
    
    if priority == "PAYMENT_CONTEXT":
        return await handle_payment_context(
            message, priority_pattern["context_data"], conversation_context
        )
    elif priority == "AMBASSADEUR_STEPS":
        return handle_ambassadeur_steps()
    
    return None

async def handle_payment_context(
    message: str, 
    payment_data: Dict[str, Any], 
    conversation_context: Dict[str, Any]
) -> Dict[str, Any]:
    """Gère les contextes de paiement avec logique métier spécialisée"""
    
    financing_type = payment_data.get("financing_type")
    delay_info = payment_data.get("delay_info")
    
    if not financing_type or not delay_info:
        # Demander les informations manquantes
        if not financing_type:
            return {
                "response": "Comment la formation a-t-elle été financée ? (CPF, OPCO, ou paiement direct)",
                "source": "payment_info_request",
                "priority": "PAYMENT_INFO_REQUEST"
            }
        elif not delay_info:
            return {
                "response": "Et environ quand la formation s'est-elle terminée ? 📅",
                "source": "delay_info_request", 
                "priority": "DELAY_INFO_REQUEST"
            }
    
    # Logique selon le type de financement et délai
    delay_days = delay_info["delay_days"]
    
    if financing_type == "CPF" and delay_days >= 45:
        return {
            "response": """Juste avant que je transmette ta demande 🙏

Est-ce que tu as déjà été informé par l'équipe que ton dossier CPF faisait partie des quelques cas bloqués par la Caisse des Dépôts ?

👉 Si oui, je te donne directement toutes les infos liées à ce blocage.
Sinon, je fais remonter ta demande à notre équipe pour vérification ✅""",
            "source": "cpf_delay_filter",
            "priority": "CPF_DELAY_EXCEEDED",
            "escalade_required": False
        }
    
    elif financing_type == "OPCO" and delay_days > 60:
        return {
            "response": f"""Merci pour ta réponse 🙏

Pour un financement via un OPCO, le délai moyen est de 2 mois. Certains dossiers peuvent aller jusqu'à 6 mois ⏳

Mais vu que cela fait plus de 2 mois, on préfère ne pas te faire attendre plus longtemps sans retour.

👉 Je vais transmettre ta demande à notre équipe pour qu'on vérifie ton dossier dès maintenant 📋

🔄 ESCALADE AGENT ADMIN

🕐 Notre équipe traite les demandes du lundi au vendredi, de 9h à 17h (hors pause déjeuner).
On te tiendra informé dès qu'on a une réponse ✅""",
            "source": "opco_delay_exceeded",
            "priority": "OPCO_DELAY_EXCEEDED",
            "escalade_required": True
        }
    
    elif financing_type == "direct" and delay_days > 7:
        return {
            "response": f"""Merci pour ta réponse 🙏

Pour un financement direct, le délai normal est de 7 jours après fin de formation + réception du dossier complet 📋

Vu que cela fait plus que le délai habituel, je vais faire suivre ta demande à notre équipe pour vérification immédiate.

👉 Je transmets ton dossier dès maintenant 📋

🔄 ESCALADE AGENT ADMIN

🕐 Notre équipe traite les demandes du lundi au vendredi, de 9h à 17h (hors pause déjeuner).
On te tiendra informé rapidement ✅""",
            "source": "direct_delay_exceeded",
            "priority": "DIRECT_DELAY_EXCEEDED",
            "escalade_required": True
        }
    
    # Délais normaux
    return {
        "response": f"""Pour un financement {financing_type}, ton dossier est encore dans les délais normaux ⏰

Si tu as des questions spécifiques sur ton dossier, je peux faire suivre à notre équipe pour vérification ✅

Tu veux que je transmette ta demande ? 🙏""",
        "source": "payment_delay_normal",
        "priority": "PAYMENT_DELAY_NORMAL",
        "escalade_required": False
    }

def handle_ambassadeur_steps() -> Dict[str, Any]:
    """Gère les demandes d'étapes pour devenir ambassadeur"""
    
    return {
        "response": """Parfait ! 😊

Tu veux devenir ambassadeur et commencer à gagner de l'argent avec nous ? C'est super simple 👇

✅ Étape 1 : Tu t'abonnes à nos réseaux
📱 Insta : https://hi.switchy.io/InstagramWeiWei
📱 Snap : https://hi.switchy.io/SnapChatWeiWei

✅ Étape 2 : Tu créé ton code d'affiliation via le lien suivant (tout en bas) :
🔗 https://swiy.co/jakpro
⬆️ Retrouve plein de vidéos 📹 et de conseils sur ce lien 💡

✅ Étape 3 : Tu nous envoies une liste de contacts intéressés (nom, prénom, téléphone ou email).
➕ Si c'est une entreprise ou un pro, le SIRET est un petit bonus 😊
🔗 Formulaire ici : https://mrqz.to/AffiliationPromotion

✅ Étape 4 : Si un dossier est validé, tu touches une commission jusqu'à 60 % 💰
Et tu peux même être payé sur ton compte perso (jusqu'à 3000 €/an et 3 virements)

Tu veux qu'on t'aide à démarrer ou tu envoies ta première liste ? 📝""",
        "source": "ambassadeur_steps",
        "priority": "AMBASSADEUR_STEPS_PROVIDED",
        "escalade_required": False
    }

async def generate_contextual_response(
    message: str, 
    memory: ConversationBufferMemory, 
    conversation_context: Dict[str, Any]
) -> Optional[str]:
    """Génère une réponse contextuelle basée sur l'historique et le contexte"""
    
    # Ici, vous pourriez intégrer un appel à un LLM pour générer une réponse contextuelle
    # Pour l'instant, on utilise une logique simplifiée
    
    topics = conversation_context.get("topics_discussed", [])
    is_follow_up = conversation_context.get("is_follow_up", False)
    
    if is_follow_up and "paiement" in topics:
        return """D'accord, je comprends ta préoccupation concernant le paiement 💰

Je vais faire suivre ta demande à notre équipe spécialisée qui pourra t'aider au mieux ✅

🕐 Horaires : Lundi-Vendredi, 9h-17h"""
    
    elif is_follow_up and "ambassadeur" in topics:
        return """Parfait ! Si tu as d'autres questions sur le programme ambassadeur, n'hésite pas 😊

Ou tu veux qu'on t'aide à démarrer tout de suite ? 🚀"""
    
    elif is_follow_up and "formation" in topics:
        return """Excellente question sur nos formations ! 🎓

Je peux te mettre en relation avec notre équipe pédagogique qui te donnera tous les détails ✅"""
    
    return None

def generate_smart_fallback(conversation_context: Dict[str, Any]) -> str:
    """Génère un fallback intelligent basé sur le contexte"""
    
    needs_greeting = conversation_context.get("needs_greeting", True)
    topics = conversation_context.get("topics_discussed", [])
    
    if needs_greeting:
        return """Salut 👋

Je vais analyser ta demande et te répondre au mieux ! 😊

🕐 Notre équipe est disponible du lundi au vendredi, de 9h à 17h.
En attendant, peux-tu me préciser un peu plus ce que tu recherches ?"""
    
    elif topics:
        return f"""Je vois que tu t'intéresses à nos {"".join(f" {topic}" for topic in topics)} 😊

Je vais faire suivre ta demande à notre équipe spécialisée qui pourra t'aider au mieux ✅

🕐 Horaires : Lundi-Vendredi, 9h-17h"""
    
    else:
        return """Parfait, je vais faire suivre ta demande à notre équipe ! 🙏

🕐 Notre équipe est disponible du lundi au vendredi, de 9h à 17h.
On te tiendra informé dès que possible ✅"""

# Gestionnaire d'arrêt propre
def signal_handler(signum, frame):
    """Gestionnaire d'arrêt propre"""
    logger.info("🛑 Arrêt du serveur en cours...")
    
    # Cleanup mémoire
    with memory_lock:
        memory_store.clear()
    
    gc.collect()
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

# Application FastAPI optimisée
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Cycle de vie avec initialisation Cognee"""
    logger.info("🚀 Démarrage serveur JAK Company API V26")
    
    # Initialisation Cognee en arrière-plan
    if COGNEE_ENABLED:
        asyncio.create_task(cognee_manager.initialize())
    
    # Tâche de nettoyage périodique
    async def periodic_cleanup():
        while True:
            await asyncio.sleep(3600)  # Toutes les heures
            OptimizedMemoryManager.cleanup_expired_sessions()
    
    cleanup_task = asyncio.create_task(periodic_cleanup())
    
    yield
    
    # Arrêt propre
    cleanup_task.cancel()
    logger.info("🛑 Arrêt serveur")
    with memory_lock:
        memory_store.clear()
    gc.collect()

app = FastAPI(
    title="JAK Company API V26 - Unifié Cognee + Langchain",
    version="26.0",
    description="API unifiée combinant Cognee et Langchain pour l'agent WhatsApp IA",
    lifespan=lifespan,
    docs_url="/docs" if DEBUG_MODE else None,
    redoc_url="/redoc" if DEBUG_MODE else None
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# ENDPOINT PRINCIPAL
@app.post("/")
async def main_endpoint(request: Request):
    """Endpoint principal unifié pour le traitement des messages"""
    
    try:
        # Parse du body avec timeout
        body = await asyncio.wait_for(request.json(), timeout=10.0)
        
        # Extraction des données
        message = body.get("message_original", body.get("message", ""))
        matched_bloc = body.get("matched_bloc_response", "")
        wa_id = body.get("wa_id", "default_session")
        processing_type = body.get("processing_type", "")
        contextual_info = body.get("contextual_info", {})
        clean_message = body.get("clean_message", message)
        
        if not message:
            raise HTTPException(status_code=400, detail="Message requis")
        
        logger.info(f"📨 MESSAGE REÇU: wa_id={wa_id}, message='{message[:100]}...'")
        
        # Traitement unifié
        result = await asyncio.wait_for(
            process_message_unified(
                message=clean_message or message,
                wa_id=wa_id,
                matched_bloc=matched_bloc,
                processing_type=processing_type,
                contextual_info=contextual_info
            ),
            timeout=25.0
        )
        
        # Construction de la réponse
        response_data = {
            "matched_bloc_response": result["response"],
            "confidence": 0.95 if result["source"] in ["cognee_knowledge_base", "priority_pattern"] else 0.8,
            "processing_type": result["priority"],
            "escalade_required": result.get("escalade_required", False),
            "escalade_type": "admin" if result.get("escalade_required") else None,
            "status": "success",
            "source": result["source"],
            "session_id": wa_id,
            "cognee_enabled": cognee_manager.enabled,
            "cognee_ready": cognee_manager.ready,
            "memory_info": OptimizedMemoryManager.get_memory_summary(
                OptimizedMemoryManager.get_memory(wa_id)
            )
        }
        
        logger.info(f"✅ RÉPONSE GÉNÉRÉE: source={result['source']}, priority={result['priority']}")
        
        # Cleanup périodique
        if len(memory_store) > MAX_SESSIONS:
            OptimizedMemoryManager.cleanup_expired_sessions()
            gc.collect()
        
        return JSONResponse(response_data)
        
    except asyncio.TimeoutError:
        logger.error("⏱️ Timeout traitement message")
        return JSONResponse({
            "matched_bloc_response": """Salut 👋

Je rencontre un petit délai de traitement. Notre équipe va regarder ça ! 😊

🕐 Horaires : Lundi-Vendredi, 9h-17h""",
            "confidence": 0.1,
            "processing_type": "timeout_error",
            "escalade_required": True,
            "status": "timeout_fallback"
        })
        
    except HTTPException:
        raise
        
    except Exception as e:
        logger.error(f"❌ Erreur traitement: {str(e)}")
        return JSONResponse({
            "matched_bloc_response": """Salut 👋

Je rencontre un petit problème technique. Notre équipe va regarder ça ! 😊

🕐 Horaires : Lundi-Vendredi, 9h-17h""",
            "confidence": 0.1,
            "processing_type": "error_fallback",
            "escalade_required": True,
            "status": "error"
        })

# ENDPOINTS DE MONITORING ET GESTION
@app.get("/health")
async def health_check():
    """Endpoint de santé complet"""
    
    memory_stats = {
        "active_sessions": len(memory_store),
        "max_sessions": MAX_SESSIONS,
        "max_messages_per_session": MAX_MESSAGES,
        "memory_ttl_hours": MEMORY_TTL_HOURS
    }
    
    return JSONResponse({
        "status": "healthy",
        "version": "26.0",
        "timestamp": datetime.now().isoformat(),
        "features": {
            "cognee_available": COGNEE_AVAILABLE,
            "cognee_enabled": COGNEE_ENABLED,
            "cognee_ready": cognee_manager.ready,
            "cognee_knowledge_populated": cognee_manager.knowledge_base_populated,
            "debug_mode": DEBUG_MODE
        },
        "memory": memory_stats,
        "improvements": [
            "VERSION 26: Unification Cognee + Langchain",
            "Gestion mémoire optimisée avec TTL",
            "Base de connaissances JAK Company intégrée",
            "Contexte conversationnel avancé",
            "Patterns de détection améliorés",
            "Traitement spécialisé paiements/formations",
            "Fallbacks intelligents contextuels",
            "Cleanup automatique et monitoring"
        ]
    })

@app.get("/memory/status")
async def memory_status():
    """Statut détaillé de la mémoire"""
    
    total_messages = 0
    session_details = {}
    
    with memory_lock:
        for session_id, session_data in memory_store.items():
            memory = session_data["memory"]
            summary = OptimizedMemoryManager.get_memory_summary(memory)
            total_messages += summary["total_messages"]
            
            session_details[session_id] = {
                **summary,
                "last_activity": session_data["last_activity"].isoformat(),
                "age_hours": (datetime.now() - session_data["last_activity"]).total_seconds() / 3600
            }
    
    return JSONResponse({
        "active_sessions": len(memory_store),
        "total_messages": total_messages,
        "memory_ttl_hours": MEMORY_TTL_HOURS,
        "sessions": session_details
    })

@app.post("/memory/cleanup")
async def cleanup_memory():
    """Nettoyage manuel de la mémoire"""
    
    before_count = len(memory_store)
    OptimizedMemoryManager.cleanup_expired_sessions()
    after_count = len(memory_store)
    
    gc.collect()
    
    return JSONResponse({
        "status": "success",
        "sessions_before": before_count,
        "sessions_after": after_count,
        "sessions_cleaned": before_count - after_count
    })

@app.delete("/memory/{session_id}")
async def delete_session(session_id: str):
    """Supprime une session spécifique"""
    
    with memory_lock:
        if session_id in memory_store:
            del memory_store[session_id]
            return JSONResponse({"status": "success", "message": f"Session {session_id} supprimée"})
        else:
            raise HTTPException(status_code=404, detail="Session non trouvée")

@app.post("/cognee/reinitialize")
async def reinitialize_cognee():
    """Réinitialise Cognee (pour debug)"""
    
    if not COGNEE_AVAILABLE:
        raise HTTPException(status_code=400, detail="Cognee non disponible")
    
    cognee_manager.ready = False
    cognee_manager.initialization_attempted = False
    cognee_manager.knowledge_base_populated = False
    
    await cognee_manager.initialize()
    
    return JSONResponse({
        "status": "success",
        "cognee_ready": cognee_manager.ready,
        "knowledge_populated": cognee_manager.knowledge_base_populated
    })

@app.get("/")
async def root():
    """Endpoint racine avec informations de base"""
    
    return JSONResponse({
        "message": "JAK Company API V26 - Agent IA WhatsApp Unifié",
        "version": "26.0",
        "features": ["Cognee", "Langchain", "Memory Management", "Context Analysis"],
        "endpoints": {
            "main": "POST /",
            "health": "GET /health",
            "memory": "GET /memory/status",
            "docs": "GET /docs" if DEBUG_MODE else "disabled"
        }
    })

# Point d'entrée
if __name__ == "__main__":
    import uvicorn
    
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    workers = int(os.environ.get("WORKERS", 1))
    
    # Configuration optimisée
    uvicorn_config = {
        "host": host,
        "port": port,
        "workers": workers,
        "log_level": "info" if DEBUG_MODE else "warning",
        "access_log": DEBUG_MODE,
        "timeout_keep_alive": 60,
        "timeout_graceful_shutdown": 30
    }
    
    logger.info(f"🚀 Démarrage serveur sur {host}:{port}")
    logger.info(f"🔧 Configuration: workers={workers}, debug={DEBUG_MODE}")
    logger.info(f"🧠 Cognee: disponible={COGNEE_AVAILABLE}, activé={COGNEE_ENABLED}")
    
    uvicorn.run(app, **uvicorn_config)