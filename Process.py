# Process.py V26 COMPLET - Logique Langchain Intégrale + Cognee + Corrections Render
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

# Configuration du logging pour Render (réduite mais pas supprimée)
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
    # Ne pas sys.exit() pour éviter les erreurs Render
    COGNEE_ENABLED = False

# Configuration environnement
if OPENAI_API_KEY:
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
if LLM_API_KEY:
    os.environ["LLM_API_KEY"] = LLM_API_KEY

# Store mémoire optimisé avec TTL (logique originale préservée)
memory_store: Dict[str, ConversationBufferMemory] = {}
memory_lock = threading.Lock()
MAX_SESSIONS = 100  # Augmenté pour préserver la logique originale
MAX_MESSAGES = 15   # Logique originale
MEMORY_TTL_HOURS = 24

class MemoryManager:
    """Gestionnaire de mémoire optimisé - LOGIQUE ORIGINALE PRÉSERVÉE"""
    
    @staticmethod
    def trim_memory(memory: ConversationBufferMemory, max_messages: int = 15):
        """Limite la mémoire aux N derniers messages pour économiser les tokens"""
        messages = memory.chat_memory.messages
        
        if len(messages) > max_messages:
            # Garder seulement les max_messages derniers
            memory.chat_memory.messages = messages[-max_messages:]
            logger.info(f"Memory trimmed to {max_messages} messages")
    
    @staticmethod
    def get_memory_summary(memory: ConversationBufferMemory) -> Dict[str, Any]:
        """Retourne un résumé de la mémoire"""
        messages = memory.chat_memory.messages
        return {
            "total_messages": len(messages),
            "user_messages": len([m for m in messages if hasattr(m, 'type') and m.type == 'human']),
            "ai_messages": len([m for m in messages if hasattr(m, 'type') and m.type == 'ai']),
            "memory_size_chars": sum(len(str(m.content)) for m in messages)
        }
    
    @staticmethod
    def cleanup_expired_sessions():
        """Nettoie les sessions expirées"""
        current_time = datetime.now()
        expired_keys = []
        
        with memory_lock:
            for session_id, memory in memory_store.items():
                # Vérifier l'âge de la session (logique simple mais efficace)
                if hasattr(memory, 'last_accessed'):
                    if current_time - memory.last_accessed > timedelta(hours=MEMORY_TTL_HOURS):
                        expired_keys.append(session_id)
            
            for key in expired_keys:
                del memory_store[key]
                
        if expired_keys:
            logger.info(f"🧹 Nettoyé {len(expired_keys)} sessions expirées")
    
    @staticmethod
    def get_or_create_memory(wa_id: str) -> ConversationBufferMemory:
        """Obtient ou crée une mémoire pour une session"""
        with memory_lock:
            # Cleanup préventif
            if len(memory_store) >= MAX_SESSIONS:
                MemoryManager.cleanup_expired_sessions()
            
            if wa_id not in memory_store:
                memory_store[wa_id] = ConversationBufferMemory(
                    memory_key="history",
                    return_messages=True
                )
            
            memory = memory_store[wa_id]
            if not hasattr(memory, 'last_accessed'):
                setattr(memory, 'last_accessed', datetime.now())
            else:
                memory.last_accessed = datetime.now()
            
            # Trim automatique
            MemoryManager.trim_memory(memory, MAX_MESSAGES)
            
            return memory

class CogneeManager:
    """Gestionnaire Cognee avec base de connaissances complète"""
    
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
        try:
            if hasattr(cognee, 'priming'):
                await cognee.priming()
            else:
                logger.info("🧠 Cognee initialisé sans priming")
        except Exception as e:
                logger.warning(f"⚠️ Cognee init: {e}")
        
        # Peupler la base de connaissances JAK Company
        if not self.knowledge_base_populated:
            await self._populate_knowledge_base()
            self.knowledge_base_populated = True
    
    async def _populate_knowledge_base(self):
        """Peuple la base de connaissances avec les informations JAK Company COMPLÈTES"""
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
                - Formations sur mesure pour entreprises
                
                Modalités : 
                - E-learning (100% en ligne)
                - Présentiel (selon localisation)
                - Formations sur mesure pour entreprises
                
                Financement : 
                - Entreprises & professionnels
                - OPCO (Organismes de formation)
                - Financement direct
                
                Note importante : formations CPF suspendues temporairement."""
            },
            {
                "topic": "programme_ambassadeur_complet",
                "content": """Programme Ambassadeur JAK Company - PROCESSUS COMPLET :
                
                ÉTAPE 1 : Abonnement aux réseaux sociaux
                - Instagram : https://hi.switchy.io/InstagramWeiWei
                - Snapchat : https://hi.switchy.io/SnapChatWeiWei
                
                ÉTAPE 2 : Création du code d'affiliation
                - Lien : https://swiy.co/jakpro
                - Ressources : vidéos et conseils disponibles
                
                ÉTAPE 3 : Transmission des contacts
                - Formulaire : https://mrqz.to/AffiliationPromotion
                - Informations requises : nom, prénom, téléphone ou email
                - Bonus entreprise : SIRET si disponible
                
                ÉTAPE 4 : Commissions
                - Jusqu'à 60% par dossier validé
                - Paiement compte personnel : max 3000€/an, 3 virements
                - Au-delà : création micro-entreprise nécessaire
                
                SCRIPTS DE VENTE :
                - Prospect : "Je travaille avec un organisme de formation super sérieux..."
                - Entreprise : "Je vous parle d'un organisme de formation qui s'occupe de tout..."
                - Argumentaire : "C'est une opportunité hyper simple pour gagner de l'argent..."
                
                DÉLAIS MOYENS : 3 à 6 mois pour toucher les commissions"""
            },
            {
                "topic": "delais_paiement_detailles",
                "content": """Délais de paiement JAK Company - SYSTÈME COMPLET :
                
                PAIEMENT DIRECT :
                - Délai : 7 jours après fin formation + dossier complet
                - Condition : réception de tous les documents
                
                CPF (PROBLÈME ACTUEL) :
                - Délai minimum officiel : 45 jours après feuilles émargement signées
                - Problème réforme février 2025 : moins de 50 dossiers sur 2500 bloqués
                - Cause : demandes répétées de documents par Caisse des Dépôts
                - Délais imprévisibles : parfois 2 mois entre chaque demande
                - Impact : aucun paiement perçu par JAK Company pour ces dossiers
                
                OPCO :
                - Délai moyen : 2 mois après fin formation
                - Délai maximum : 6 mois selon organisme
                - Note : JAK Company n'a pas la main sur ces délais
                
                GESTION DES CAS BLOQUÉS CPF :
                - Éléments transmis à l'organisme de contrôle
                - Accompagnement centre de formation
                - Engagement de retour vers chaque personne concernée
                - Pas de relance utile entre-temps"""
            },
            {
                "topic": "conditions_remuneration",
                "content": """Conditions de rémunération JAK Company :
                
                COMPTE PERSONNEL :
                - Limite montant : 3000€/an
                - Limite virements : 3 virements maximum
                - Déclaration fiscale : BNC occasionnels (cases 1OA ou 1OB)
                
                MICRO-ENTREPRISE :
                - Obligatoire si dépassement des limites
                - Aide à la création proposée
                - Accompagnement étape par étape
                
                FORMATION ET LÉGALITÉ :
                - Interdiction d'inscrire quelqu'un uniquement pour être rémunéré
                - Formation sérieuse requise avant participation programme
                - Participation affiliation possible après formation"""
            },
            {
                "topic": "gestion_escalade_complete",
                "content": """Système d'escalade JAK Company :
                
                TYPES D'ESCALADE :
                - ESCALADE AGENT ADMIN : paiements, vérifications dossiers
                - ESCALADE ÉQUIPE FORMATION : formations pros/particuliers
                - ESCALADE ÉQUIPE ENTREPRISE : demandes B2B, formations collectives
                
                HORAIRES ÉQUIPE :
                - Lundi-Vendredi : 9h-17h (hors pause déjeuner)
                - Traitement des demandes selon ordre d'arrivée
                
                RÉSEAUX SOCIAUX :
                - Instagram : https://hi.switchy.io/InstagramWeiWei
                - Snapchat : https://hi.switchy.io/SnapChatWeiWei
                
                GESTION AGRESSIVITÉ :
                - Réponse standard : "Être impoli ne fera pas avancer la situation plus vite..."
                - Proposition détente : poème ou chanson d'amour
                
                RELANCES :
                - Délai normal avant relance équipe
                - Respect des processus internes
                - Information transparente sur les délais"""
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
                if len(response) > 800:
                    response = response[:800] + "..."
                return response
                
        except asyncio.TimeoutError:
            logger.warning("⏱️ Timeout recherche Cognee")
        except Exception as e:
            logger.warning(f"❌ Erreur recherche Cognee: {e}")
            
        return None

class ConversationContextManager:
    """Gestionnaire du contexte conversationnel - LOGIQUE ORIGINALE COMPLÈTE"""
    
    @staticmethod
    def analyze_conversation_context(user_message: str, memory: ConversationBufferMemory) -> Dict[str, Any]:
        """Analyse le contexte de la conversation pour adapter la réponse"""
        
        # Récupérer l'historique
        history = memory.chat_memory.messages
        message_count = len(history)
        
        # Analyser si c'est un message de suivi
        follow_up_indicators = [
            "comment", "pourquoi", "vous pouvez", "tu peux", "aide", "démarrer",
            "oui", "ok", "d'accord", "et après", "ensuite", "comment faire",
            "vous pouvez m'aider", "tu peux m'aider", "comment ça marche",
            "ça marche comment", "pour les contacts", "les étapes"
        ]
        
        is_follow_up = any(indicator in user_message.lower() for indicator in follow_up_indicators)
        
        # Analyser le sujet précédent dans l'historique
        previous_topic = None
        last_bot_message = ""
        awaiting_cpf_info = False
        awaiting_financing_info = False
        
        # LOGIQUE DÉTECTION DU CONTEXTE PAIEMENT FORMATION
        payment_context_detected = False
        financing_question_asked = False
        timing_question_asked = False
        
        # LOGIQUE DÉTECTION DU CONTEXTE AFFILIATION
        affiliation_context_detected = False
        awaiting_steps_info = False
        
        if message_count > 0:
            # Chercher dans les derniers messages
            for msg in reversed(history[-6:]):  # Regarder les 6 derniers messages
                content = str(msg.content).lower()
                
                # DÉTECTION AMÉLIORÉE : Chercher les patterns du bloc paiement formation
                payment_patterns = [
                    "comment la formation a été financée",
                    "comment la formation a-t-elle été financée",
                    "cpf, opco, ou paiement direct",
                    "et environ quand la formation s'est-elle terminée",
                    "pour t'aider au mieux, peux-tu me dire comment"
                ]
                
                if any(pattern in content for pattern in payment_patterns):
                    payment_context_detected = True
                    financing_question_asked = True
                    last_bot_message = str(msg.content)
                
                if "environ quand la formation s'est terminée" in content or "environ quand la formation s'est-elle terminée" in content:
                    payment_context_detected = True
                    timing_question_asked = True
                    last_bot_message = str(msg.content)
                
                # Détecter si on attend des infos spécifiques
                if "comment la formation a été financée" in content:
                    awaiting_financing_info = True
                    last_bot_message = str(msg.content)
                
                if "environ quand la formation s'est terminée" in content:
                    awaiting_financing_info = True
                    last_bot_message = str(msg.content)
                
                # Détecter le contexte CPF bloqué
                if "dossier cpf faisait partie des quelques cas bloqués" in content:
                    awaiting_cpf_info = True
                    last_bot_message = str(msg.content)
                
                # DÉTECTION CONTEXTE AFFILIATION
                if "ancien apprenant" in content or "programme d'affiliation privilégié" in content:
                    affiliation_context_detected = True
                
                if "tu as déjà des contacts en tête ou tu veux d'abord voir comment ça marche" in content:
                    awaiting_steps_info = True
                    last_bot_message = str(msg.content)
                
                # Détecter les sujets principaux
                if "ambassadeur" in content or "commission" in content:
                    previous_topic = "ambassadeur"
                    break
                elif "paiement" in content or "formation" in content:
                    previous_topic = "paiement"
                    break
                elif "cpf" in content:
                    previous_topic = "cpf"
                    break
        
        return {
            "message_count": message_count,
            "is_follow_up": is_follow_up,
            "previous_topic": previous_topic,
            "needs_greeting": message_count == 0,
            "conversation_flow": "continuing" if message_count > 0 else "starting",
            "awaiting_cpf_info": awaiting_cpf_info,
            "awaiting_financing_info": awaiting_financing_info,
            "last_bot_message": last_bot_message,
            # NOUVELLES CLÉS CRITIQUES
            "affiliation_context_detected": affiliation_context_detected,
            "awaiting_steps_info": awaiting_steps_info,
            "payment_context_detected": payment_context_detected,
            "financing_question_asked": financing_question_asked,
            "timing_question_asked": timing_question_asked,
            "last_messages": [str(msg.content) for msg in history[-3:]] if history else []
        }

class PaymentContextProcessor:
    """Processeur spécialisé pour le contexte paiement formation - LOGIQUE ORIGINALE COMPLÈTE"""
    
    @staticmethod
    def extract_financing_type(message: str) -> Optional[str]:
        """Extrait le type de financement du message - VERSION ULTRA RENFORCÉE"""
        message_lower = message.lower()
        
        logger.info(f"🔍 ANALYSE FINANCEMENT: '{message}'")
        
        # MAP ULTRA RENFORCÉE COMPLÈTE
        financing_patterns = {
            # CPF
            'CPF': [
                'cpf', 'compte personnel', 'compte personnel formation'
            ],
            # OPCO - PATTERNS ULTRA RENFORCÉS
            'OPCO': [
                'opco', 'operateur', 'opérateur', 'opco entreprise',
                'organisme paritaire', 'formation opco', 'financé par opco',
                'finance par opco', 'financement opco', 'via opco',
                'avec opco', 'par opco', 'opco formation', 'formation via opco',
                'formation avec opco', 'formation par opco', 'grâce opco',
                'grace opco', 'opco paie', 'opco paye', 'opco a payé',
                'opco a paye', 'pris en charge opco', 'prise en charge opco',
                'remboursé opco', 'rembourse opco'
            ],
            # FINANCEMENT DIRECT - PATTERNS ULTRA RENFORCÉS
            'direct': [
    'en direct', 'financé en direct', 'finance en direct',
    'financement direct', 'direct', 'entreprise', 'particulier',
    'patron', "j'ai financé", 'jai finance', 'j ai finance',
    'financé moi', 'finance moi', 'payé moi', 'paye moi',
    'moi même', 'moi meme', "j'ai payé", 'jai paye', 'j ai paye',
    'payé par moi', 'paye par moi', 'financé par moi',
    'finance par moi', 'sur mes fonds', 'fonds propres',
    'personnellement', 'directement', 'par mon entreprise',
    'par la société', 'par ma société', 'financement personnel',
    'auto-financement', 'auto financement', 'tout seul',
    'payé tout seul', 'paye tout seul', 'financé seul',
    'finance seul', 'de ma poche', 'par moi même',
    'par moi meme', 'avec mes deniers', 'société directement',
    'entreprise directement', 'payé directement',
    'paye directement', 'financé directement',
    'finance directement', 'moi qui ai payé',
    'moi qui ai paye', "c'est moi qui ai payé",
    "c'est moi qui ai paye", 'payé de ma poche',
    'paye de ma poche', 'sortie de ma poche',
    'mes propres fonds', 'argent personnel', 'personnel',
    
    # === NOUVEAUX PATTERNS CRITIQUES (BIEN DANS LA LISTE) ===
    
    # Formulations "c'est moi"
    "c'est moi", "c est moi", "cest moi",
    "c'est moi qui", "c est moi qui", "cest moi qui",
    "c'est moi qui ai", "c est moi qui ai", "cest moi qui ai",
    "c'est moi qui a", "c est moi qui a", "cest moi qui a",
    "c'est moi qui ai financé", "c'est moi qui ai finance",
    "c est moi qui ai financé", "c est moi qui ai finance",
    "cest moi qui ai financé", "cest moi qui ai finance",
    
    # Formulations "toute seule" / "tout seul"
    "toute seule", "toute seule qui", "tout seul qui",
    "tout seul qui ai", "toute seule qui ai", "toute seule qui a",
    "moi toute seule", "moi tout seul",
    
    # Variations féminines
    "j'ai payée", "jai payée", "j ai payée",
    "j'ai financée", "jai financée", "j ai financée", 
    "financée par moi", "payée par moi",
    "financée toute seule", "payée toute seule",
    
    # Formulations courantes
    "c'est moi qui l'ai", "c est moi qui l'ai", "cest moi qui l'ai",
    "c'est moi qui l ai", "c est moi qui l ai", "cest moi qui l ai",
    "moi qui l'ai", "moi qui l ai",
    "c'est bien moi", "c est bien moi", "cest bien moi",
    
    # Autres formulations naturelles
    "j'ai fait le paiement", "jai fait le paiement", "j ai fait le paiement",
    "j'ai réglé", "jai regle", "j ai regle",
    "j'ai soldé", "jai solde", "j ai solde",
    "c'était moi", "c etait moi", "cetait moi",
    "ça vient de moi", "ca vient de moi",
    "de mes deniers", "avec mes sous",
    
    # Formulations avec contexte formation
    "la formation c'est moi", "la formation c est moi",
    "la formation cest moi", "pour la formation c'est moi",
    
    # Contexte entreprise personnelle
    "ma boite", "ma boîte", "mon entreprise",
    "ma société", "ma structure",
    "mon compte pro", "compte professionnel"
]
        }
        
        # Recherche par patterns
        for financing_type, patterns in financing_patterns.items():
            for pattern in patterns:
                if pattern in message_lower:
                    logger.info(f"✅ Financement détecté: '{pattern}' -> {financing_type}")
                    return financing_type
        
        # DÉTECTION CONTEXTUELLE RENFORCÉE
        logger.info("🔍 Recherche contextuelle financement...")
        
        # NOUVEAU : Détection combinée "j'ai" + action + contexte
        jai_patterns = ["j'ai", "jai", "j ai", "je ai"]
        payment_actions = ["payé", "paye", "payée", "financé", "finance", "financée", "réglé", "regle", "réglée"]
        direct_indicators = ["formation", "moi", "seul", "seule", "direct", "personnel", "entreprise", "poche", "fonds"]
    
        has_jai = any(pattern in message_lower for pattern in jai_patterns)
        has_payment_action = any(action in message_lower for action in payment_actions)
        has_direct_indicator = any(indicator in message_lower for indicator in direct_indicators)
    
        if has_jai and has_payment_action and has_direct_indicator:
            logger.info("✅ Financement direct détecté par combinaison contextuelle j'ai + action + contexte")
            return 'direct'
    
        # NOUVEAU : Détection "c'est moi" + contexte
        cest_moi_patterns = ["c'est moi", "c est moi", "cest moi"]
        has_cest_moi = any(pattern in message_lower for pattern in cest_moi_patterns)
    
        if has_cest_moi and (has_payment_action or has_direct_indicator):
            logger.info("✅ Financement direct détecté par 'c'est moi' + contexte")
            return 'direct'
    
        # DÉTECTION "toute seule" / "tout seul"
        if "toute seule" in message_lower or "tout seul" in message_lower:
            logger.info("✅ Financement direct détecté par 'toute seule/tout seul'")
            return 'direct'
    
        # OPCO simple
        if 'opco' in message_lower:
            logger.info("✅ OPCO détecté par mot-clé simple")
            return 'OPCO'
        
        # Financement direct contextuel
        if any(word in message_lower for word in ['financé', 'finance', 'payé', 'paye']) and \
           any(word in message_lower for word in ['direct', 'moi', 'personnel', 'entreprise', 'seul', 'même', 'meme', 'poche', 'propre']):
            logger.info("✅ Financement direct détecté par contexte")
            return 'direct'
        
        # Pattern "j'ai" + action
        if any(word in message_lower for word in ["j'ai", 'jai', 'j ai']) and \
           any(word in message_lower for word in ['payé', 'paye', 'financé', 'finance']):
            logger.info("✅ Financement direct détecté par 'j'ai payé/financé'")
            return 'direct'
        
        logger.warning(f"❌ Aucun financement détecté dans: '{message}'")
        return None
    
    @staticmethod
    def extract_time_delay(message: str) -> Optional[int]:
        """Extrait le délai en jours du message - LOGIQUE ORIGINALE COMPLÈTE"""
        message_lower = message.lower()
        
        logger.info(f"🕐 ANALYSE DÉLAI: '{message}'")
        
        # PATTERNS ULTRA RENFORCÉS COMPLETS
        delay_patterns = [
            # Patterns avec préfixes
            r'(?:il y a|depuis|ça fait|ca fait)\s*(\d+)\s*mois',
            r'(?:il y a|depuis|ça fait|ca fait)\s*(\d+)\s*semaines?',
            r'(?:il y a|depuis|ça fait|ca fait)\s*(\d+)\s*jours?',
            
            # Patterns terminaison
            r'terminé\s+il y a\s+(\d+)\s*(mois|semaines?|jours?)',
            r'fini\s+il y a\s+(\d+)\s*(mois|semaines?|jours?)',
            
            # Patterns avec "que"
            r'(\d+)\s*(mois|semaines?|jours?)\s+que',
            r'(\d+)\s*(mois|semaines?|jours?)\s*que',
            
            # Patterns simples
            r'fait\s+(\d+)\s*(mois|semaines?|jours?)',
            r'depuis\s+(\d+)\s*(mois|semaines?|jours?)',
            
            # NOUVEAUX PATTERNS PLUS FLEXIBLES
            r'(\d+)\s*(mois|semaines?|jours?)$',
            r'\b(\d+)\s*(mois|semaines?|jours?)\b',
            r'\s+(\d+)\s*(mois|semaines?|jours?)\s',
            
            # PATTERNS SANS UNITÉ (assume mois par défaut)
            r'il y a\s+(\d+)(?!\s*(?:mois|semaines?|jours?))',
            r'ça fait\s+(\d+)(?!\s*(?:mois|semaines?|jours?))',
            r'depuis\s+(\d+)(?!\s*(?:mois|semaines?|jours?))'
        ]
        
        for pattern in delay_patterns:
            match = re.search(pattern, message_lower)
            if match:
                number = int(match.group(1))
                
                # Déterminer l'unité
                unit = "mois"  # défaut
                if len(match.groups()) > 1 and match.group(2):
                    unit = match.group(2)
                
                # Conversion en jours - LOGIQUE PRÉCISE
                if 'semaine' in unit:
                    delay_days = number * 7
                    logger.info(f"✅ Délai détecté: {number} semaines = {delay_days} jours")
                elif 'jour' in unit:
                    delay_days = number
                    logger.info(f"✅ Délai détecté: {number} jours")
                else:
                    delay_days = number * 30
                    logger.info(f"✅ Délai détecté: {number} mois = {delay_days} jours")
                
                return delay_days
        
        logger.warning(f"❌ Aucun délai détecté dans: '{message}'")
        return None
    
    @staticmethod
    def handle_cpf_delay_context(delay_days: int, user_message: str, conversation_context: Dict[str, Any]) -> Dict[str, Any]:
        """Gère le contexte spécifique CPF avec délai - LOGIQUE ORIGINALE COMPLÈTE"""
        
        if delay_days >= 45:  # CPF délai dépassé (45 jours = seuil officiel)
            # Vérifier si c'est une réponse à la question de blocage CPF
            if conversation_context.get("awaiting_cpf_info"):
                user_lower = user_message.lower()
                
                # Si l'utilisateur confirme qu'il était informé du blocage
                if any(word in user_lower for word in ['oui', 'yes', 'informé', 'dit', 'déjà', 'je sais']):
                    return {
                        "use_matched_bloc": False,
                        "priority_detected": "CPF_BLOQUE_CONFIRME",
                        "response": """On comprend parfaitement ta frustration. Ce dossier fait partie des quelques cas (moins de 50 sur plus de 2500) bloqués depuis la réforme CPF de février 2025. Même nous n'avons pas été payés. Le blocage est purement administratif, et les délais sont impossibles à prévoir. On te tiendra informé dès qu'on a du nouveau. Inutile de relancer entre-temps 🙏

Tous les éléments nécessaires ont bien été transmis à l'organisme de contrôle 📋🔍
Mais le problème, c'est que la Caisse des Dépôts demande des documents que le centre de formation envoie sous une semaine...
Et ensuite, ils prennent parfois jusqu'à 2 mois pour demander un nouveau document, sans donner de réponse entre-temps.

✅ On accompagne au maximum le centre de formation pour que tout rentre dans l'ordre.
⚠️ On est aussi impactés financièrement : chaque formation a un coût pour nous.
🤞 On garde confiance et on espère une issue favorable.
🗣️ Et surtout, on s'engage à revenir vers chaque personne concernée dès qu'on a du nouveau.""",
                        "context": conversation_context,
                        "escalade_type": "admin"
                    }
            else:
                # Première fois qu'on détecte un délai CPF dépassé
                return {
                    "use_matched_bloc": False,
                    "priority_detected": "CPF_DELAI_DEPASSE_FILTRAGE",
                    "response": """Juste avant que je transmette ta demande 🙏

Est-ce que tu as déjà été informé par l'équipe que ton dossier CPF faisait partie des quelques cas bloqués par la Caisse des Dépôts ?

👉 Si oui, je te donne directement toutes les infos liées à ce blocage.
Sinon, je fais remonter ta demande à notre équipe pour vérification ✅""",
                    "context": conversation_context,
                    "awaiting_cpf_info": True
                }
        else:
            # Délai CPF normal
            return {
                "use_matched_bloc": False,
                "priority_detected": "CPF_DELAI_NORMAL",
                "response": f"""Pour un financement CPF, le délai minimum est de 45 jours après réception des feuilles d'émargement signées 📋

Ton dossier est encore dans les délais normaux ⏰ (tu en es à environ {delay_days} jours)

Si tu as des questions spécifiques sur ton dossier, je peux faire suivre à notre équipe pour vérification ✅

Tu veux que je transmette ta demande ? 🙏""",
                "context": conversation_context,
                "escalade_type": "admin"
            }

class ResponseValidator:
    """Classe pour valider et nettoyer les réponses - LOGIQUE ORIGINALE"""
    
    @staticmethod
    def clean_response(response: str) -> str:
        """Nettoie et formate la réponse"""
        if not response:
            return ""
        
        # Supprimer les caractères de contrôle
        response = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', response)
        
        # Nettoyer les espaces multiples
        response = re.sub(r'\s+', ' ', response.strip())
        
        return response
    
    @staticmethod
    def validate_escalade_keywords(message: str) -> Optional[str]:
        """Détecte si le message nécessite une escalade"""
        escalade_keywords = [
            "retard anormal", "paiement bloqué", "problème grave",
            "urgence", "plainte", "avocat", "tribunal"
        ]
        
        message_lower = message.lower()
        for keyword in escalade_keywords:
            if keyword in message_lower:
                return "admin"
        
        return None

class MessageProcessor:
    """Classe principale pour traiter les messages avec contexte - LOGIQUE ORIGINALE COMPLÈTE"""
    
    @staticmethod
    def is_aggressive(message: str) -> bool:
        """Détecte l'agressivité en évitant les faux positifs"""
        
        message_lower = message.lower()
        
        # Liste des mots agressifs avec leurs contextes d'exclusion
        aggressive_patterns = [
            ("merde", []),  # Pas d'exclusion
            ("nul", ["nul part", "nulle part"]),  # Exclure "nul part"
            ("énervez", []),
            ("batards", []),
            ("putain", []),
            ("chier", [])
        ]
        
        # Vérification spéciale pour "con" - doit être un mot isolé
        if " con " in f" {message_lower} " or message_lower.startswith("con ") or message_lower.endswith(" con"):
            # Exclure les mots contenant "con" comme "contacts", "conseil", "condition", etc.
            exclusions = [
                "contacts", "contact", "conseil", "conseils", "condition", "conditions",
                "concernant", "concerne", "construction", "consultation", "considère",
                "consommation", "consommer", "constitue", "contenu", "contexte",
                "contrôle", "contraire", "confiance", "confirmation", "conformité"
            ]
            
            # Vérifier qu'il n'y a pas ces mots dans le message
            if not any(exclusion in message_lower for exclusion in exclusions):
                return True
        
        # Vérifier les autres mots agressifs
        for aggressive_word, exclusions in aggressive_patterns:
            if aggressive_word in message_lower:
                # Vérifier que ce n'est pas dans un contexte d'exclusion
                if not any(exclusion in message_lower for exclusion in exclusions):
                    return True
        
        return False
    
    @staticmethod
    def detect_priority_rules(user_message: str, matched_bloc_response: str, conversation_context: Dict[str, Any]) -> Dict[str, Any]:
        """Applique les règles de priorité avec prise en compte du contexte - LOGIQUE ORIGINALE COMPLÈTE"""
        
        message_lower = user_message.lower()
        
        logger.info(f"🔍 PRIORITY DETECTION COMPLET: user_message='{user_message}', has_bloc_response={bool(matched_bloc_response)}")
        
        # ÉTAPE 0.1: DÉTECTION PRIORITAIRE FINANCEMENT + DÉLAI (TOUS TYPES)
        financing_indicators = ["cpf", "opco", "direct", "financé", "finance", "financement", "payé", "paye", "entreprise", "personnel", "seul"]
        delay_indicators = ["mois", "semaines", "jours", "il y a", "ça fait", "ca fait", "depuis", "terminé", "fini", "fait"]
        
        has_financing = any(word in message_lower for word in financing_indicators)
        has_delay = any(word in message_lower for word in delay_indicators)
        
        if has_financing and has_delay:
            financing_type = PaymentContextProcessor.extract_financing_type(user_message)
            delay_days = PaymentContextProcessor.extract_time_delay(user_message)
            
            logger.info(f"💰 FINANCEMENT + DÉLAI DÉTECTÉ: {financing_type} / {delay_days} jours")
            
            if financing_type and delay_days is not None:
                # CPF avec délai
                if financing_type == "CPF":
                    logger.info(f"🔍 CPF SEUIL CHECK: {delay_days} jours vs 45 jours")
                    
                    cpf_result = PaymentContextProcessor.handle_cpf_delay_context(
                        delay_days, user_message, conversation_context
                    )
                    if cpf_result:
                        return cpf_result
                
                # OPCO avec délai
                elif financing_type == "OPCO":
                    delay_days_threshold = 60  # 2 mois = 60 jours
                    
                    logger.info(f"🏢 CALCUL OPCO: {delay_days} jours (seuil: {delay_days_threshold} jours)")
                    
                    if delay_days >= delay_days_threshold:
                        return {
                            "use_matched_bloc": False,
                            "priority_detected": "OPCO_DELAI_DEPASSE",
                            "response": """Merci pour ta réponse 🙏

Pour un financement via un OPCO, le délai moyen est de 2 mois. Certains dossiers peuvent aller jusqu'à 6 mois ⏳

Mais vu que cela fait plus de 2 mois, on préfère ne pas te faire attendre plus longtemps sans retour.

👉 Je vais transmettre ta demande à notre équipe pour qu'on vérifie ton dossier dès maintenant 📋

🔄 ESCALADE AGENT ADMIN

🕐 Notre équipe traite les demandes du lundi au vendredi, de 9h à 17h (hors pause déjeuner).
On te tiendra informé dès qu'on a une réponse ✅""",
                            "context": conversation_context,
                            "escalade_type": "admin"
                        }
                    else:
                        return {
                            "use_matched_bloc": False,
                            "priority_detected": "OPCO_DELAI_NORMAL",
                            "response": f"""Pour un financement OPCO, le délai moyen est de 2 mois après la fin de formation 📋

Ton dossier est encore dans les délais normaux ⏰ (environ {delay_days} jours)

Certains dossiers peuvent prendre jusqu'à 6 mois selon l'organisme.

Si tu as des questions spécifiques, je peux faire suivre à notre équipe ✅

Tu veux que je transmette ta demande pour vérification ? 🙏""",
                            "context": conversation_context,
                            "escalade_type": "admin"
                        }
                
                # Financement direct avec délai
                elif financing_type == "direct":
                    logger.info(f"🏦 CALCUL DIRECT: {delay_days} jours (seuil: 7 jours)")
                    
                    if delay_days > 7:
                        return {
                            "use_matched_bloc": False,
                            "priority_detected": "DIRECT_DELAI_DEPASSE",
                            "response": """Merci pour ta réponse 🙏

Pour un financement direct, le délai normal est de 7 jours après fin de formation + réception du dossier complet 📋

Vu que cela fait plus que le délai habituel, je vais faire suivre ta demande à notre équipe pour vérification immédiate.

👉 Je transmets ton dossier dès maintenant 📋

🔄 ESCALADE AGENT ADMIN

🕐 Notre équipe traite les demandes du lundi au vendredi, de 9h à 17h (hors pause déjeuner).
On te tiendra informé rapidement ✅""",
                            "context": conversation_context,
                            "escalade_type": "admin"
                        }
                    else:
                        return {
                            "use_matched_bloc": False,
                            "priority_detected": "DIRECT_DELAI_NORMAL",
                            "response": f"""Pour un financement direct, le délai normal est de 7 jours après la fin de formation et réception du dossier complet 📋

Ton dossier est encore dans les délais normaux ⏰ (environ {delay_days} jours)

Si tu as des questions spécifiques sur ton dossier, je peux faire suivre à notre équipe ✅

Tu veux que je transmette ta demande ? 🙏""",
                            "context": conversation_context,
                            "escalade_type": "admin"
                        }
        
        # ÉTAPE 0.2: DÉTECTION DES DEMANDES D'ÉTAPES AMBASSADEUR
        if conversation_context.get("awaiting_steps_info") or conversation_context.get("affiliation_context_detected"):
            how_it_works_patterns = [
                "comment ça marche", "comment ca marche", "comment faire", "les étapes",
                "comment démarrer", "comment commencer", "comment s'y prendre",
                "voir comment ça marche", "voir comment ca marche", "étapes à suivre"
            ]
            
            if any(pattern in message_lower for pattern in how_it_works_patterns):
                return {
                    "use_matched_bloc": False,
                    "priority_detected": "AFFILIATION_STEPS_REQUEST",
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
                    "context": conversation_context,
                    "escalade_type": None
                }
        
        # ÉTAPE 1: PRIORITÉ ABSOLUE - Contexte paiement formation
        if conversation_context.get("payment_context_detected"):
            logger.info("💰 CONTEXTE PAIEMENT DÉTECTÉ - Analyse des réponses contextuelles")
            
            # Extraire le type de financement et délai
            financing_type = PaymentContextProcessor.extract_financing_type(user_message)
            delay_days = PaymentContextProcessor.extract_time_delay(user_message)
            
            # CAS 1: Réponse "CPF" seule dans le contexte paiement
            if financing_type == "CPF" and not delay_days:
                if conversation_context.get("financing_question_asked") and not conversation_context.get("timing_question_asked"):
                    return {
                        "use_matched_bloc": False,
                        "priority_detected": "PAIEMENT_CPF_DEMANDE_TIMING",
                        "response": "Et environ quand la formation s'est-elle terminée ? 📅",
                        "context": conversation_context,
                        "awaiting_financing_info": True
                    }
            
            # CAS 2: Réponse avec financement + délai
            if financing_type and delay_days:
                if financing_type == "CPF":
                    cpf_result = PaymentContextProcessor.handle_cpf_delay_context(
                        delay_days, user_message, conversation_context
                    )
                    if cpf_result:
                        return cpf_result
                
                elif financing_type == "OPCO" and delay_days >= 60:  # 2 mois
                    return {
                        "use_matched_bloc": False,
                        "priority_detected": "OPCO_DELAI_DEPASSE",
                        "response": """Merci pour ta réponse 🙏

Pour un financement via un OPCO, le délai moyen est de 2 mois. Certains dossiers peuvent aller jusqu'à 6 mois ⏳

Mais vu que cela fait plus de 2 mois, on préfère ne pas te faire attendre plus longtemps sans retour.

👉 Je vais transmettre ta demande à notre équipe pour qu'on vérifie ton dossier dès maintenant 📋

🔄 ESCALADE AGENT ADMIN

🕐 Notre équipe traite les demandes du lundi au vendredi, de 9h à 17h (hors pause déjeuner).
On te tiendra informé dès qu'on a une réponse ✅""",
                        "context": conversation_context,
                        "escalade_type": "admin"
                    }
        
        # ÉTAPE 2: Si n8n a matché un bloc ET qu'on n'est pas dans un contexte spécial, l'utiliser
        if matched_bloc_response and matched_bloc_response.strip():
            # Vérifier si c'est un vrai bloc (pas un fallback générique)
            fallback_indicators = [
                "je vais faire suivre ta demande à notre équipe",
                "notre équipe est disponible du lundi au vendredi",
                "on te tiendra informé dès que possible"
            ]
            
            is_fallback = any(indicator in matched_bloc_response.lower() for indicator in fallback_indicators)
            
            if not is_fallback and not conversation_context.get("payment_context_detected") and not conversation_context.get("awaiting_steps_info"):
                logger.info("✅ UTILISATION BLOC N8N - Bloc valide détecté par n8n")
                return {
                    "use_matched_bloc": True,
                    "priority_detected": "N8N_BLOC_DETECTED",
                    "response": matched_bloc_response,
                    "context": conversation_context
                }
        
        # ÉTAPE 3: Traitement des réponses aux questions spécifiques en cours
        if conversation_context.get("awaiting_financing_info"):
            financing_type = PaymentContextProcessor.extract_financing_type(user_message)
            delay_days = PaymentContextProcessor.extract_time_delay(user_message)
            
            if financing_type == "CPF" and delay_days:
                cpf_result = PaymentContextProcessor.handle_cpf_delay_context(
                    delay_days, user_message, conversation_context
                )
                if cpf_result:
                    return cpf_result
            
            elif financing_type == "OPCO" and delay_days and delay_days >= 60:
                return {
                    "use_matched_bloc": False,
                    "priority_detected": "OPCO_DELAI_DEPASSE",
                    "response": """Merci pour ta réponse 🙏

Pour un financement via un OPCO, le délai moyen est de 2 mois. Certains dossiers peuvent aller jusqu'à 6 mois ⏳

Mais vu que cela fait plus de 2 mois, on préfère ne pas te faire attendre plus longtemps sans retour.

👉 Je vais transmettre ta demande à notre équipe pour qu'on vérifie ton dossier dès maintenant 📋

🔄 ESCALADE AGENT ADMIN

🕐 Notre équipe traite les demandes du lundi au vendredi, de 9h à 17h (hors pause déjeuner).
On te tiendra informé dès qu'on a une réponse ✅""",
                    "context": conversation_context,
                    "escalade_type": "admin"
                }
            
            elif financing_type and not delay_days:
                return {
                    "use_matched_bloc": False,
                    "priority_detected": "DEMANDE_DATE_FORMATION",
                    "response": "Et environ quand la formation s'est-elle terminée ? 📅",
                    "context": conversation_context,
                    "awaiting_financing_info": True
                }
        
        # ÉTAPE 4: Traitement du contexte CPF bloqué
        if conversation_context.get("awaiting_cpf_info"):
            return PaymentContextProcessor.handle_cpf_delay_context(0, user_message, conversation_context)
        
        # ÉTAPE 5: Agressivité (priorité haute pour couper court)
        if MessageProcessor.is_aggressive(user_message):
            return {
                "use_matched_bloc": False,
                "priority_detected": "AGRESSIVITE",
                "response": "Être impoli ne fera pas avancer la situation plus vite. Bien au contraire. Souhaites-tu que je te propose un poème ou une chanson d'amour pour apaiser ton cœur ? 💌",
                "context": conversation_context
            }
        
        # ÉTAPE 6: Détection problème paiement formation (si pas déjà dans le contexte)
        if not conversation_context.get("payment_context_detected"):
            payment_keywords = [
                "pas été payé", "rien reçu", "virement", "attends",
                "paiement", "argent", "retard", "promesse", "veux être payé",
                "payé pour ma formation", "être payé pour"
            ]
            
            if any(keyword in message_lower for keyword in payment_keywords):
                # Si c'est un message de suivi sur le paiement
                if conversation_context["message_count"] > 0 and conversation_context["is_follow_up"]:
                    return {
                        "use_matched_bloc": False,
                        "priority_detected": "PAIEMENT_SUIVI",
                        "response": None,  # Laisser l'IA gérer avec contexte
                        "context": conversation_context,
                        "use_ai": True
                    }
                # Si un bloc est matché pour le paiement, l'utiliser
                elif matched_bloc_response and ("paiement" in matched_bloc_response.lower() or "délai" in matched_bloc_response.lower()):
                    return {
                        "use_matched_bloc": True,
                        "priority_detected": "PAIEMENT_FORMATION_BLOC",
                        "response": matched_bloc_response,
                        "context": conversation_context
                    }
                # Sinon, fallback paiement
                else:
                    return {
                        "use_matched_bloc": False,
                        "priority_detected": "PAIEMENT_SANS_BLOC",
                        "response": """Salut 👋

Je comprends que tu aies des questions sur le paiement 💰

Je vais faire suivre ta demande à notre équipe spécialisée qui te recontactera rapidement ✅

🕐 Horaires : Lundi-Vendredi, 9h-17h""",
                        "context": conversation_context,
                        "escalade_type": "admin"
                    }
        
        # ÉTAPE 7: Messages de suivi généraux
        if conversation_context["is_follow_up"] and conversation_context["message_count"] > 0:
            return {
                "use_matched_bloc": False,
                "priority_detected": "FOLLOW_UP_CONVERSATION",
                "response": None,  # Laisser l'IA gérer
                "context": conversation_context,
                "use_ai": True
            }
        
        # ÉTAPE 8: Escalade automatique
        escalade_type = ResponseValidator.validate_escalade_keywords(user_message)
        if escalade_type:
            return {
                "use_matched_bloc": False,
                "priority_detected": "ESCALADE_AUTO",
                "escalade_type": escalade_type,
                "response": """🔄 ESCALADE AGENT ADMIN

🕐 Notre équipe traite les demandes du lundi au vendredi, de 9h à 17h (hors pause déjeuner).
📋 On te tiendra informé dès qu'on a du nouveau ✅""",
                "context": conversation_context
            }
        
        # ÉTAPE 9: Si on arrive ici, utiliser le bloc n8n s'il existe (même si générique)
        if matched_bloc_response and matched_bloc_response.strip():
            logger.info("✅ UTILISATION BLOC N8N - Fallback sur bloc n8n")
            return {
                "use_matched_bloc": True,
                "priority_detected": "N8N_BLOC_FALLBACK",
                "response": matched_bloc_response,
                "context": conversation_context
            }
        
        # ÉTAPE 10: Fallback général
        return {
            "use_matched_bloc": False,
            "priority_detected": "FALLBACK_GENERAL",
            "context": conversation_context,
            "response": None,
            "use_ai": True
        }

# Instance globale Cognee
cognee_manager = CogneeManager()

# Processeur principal unifié - LOGIQUE ORIGINALE COMPLÈTE
async def process_message_unified(
    message: str, 
    wa_id: str, 
    matched_bloc: str = "", 
    processing_type: str = "",
    contextual_info: Dict = None
) -> Dict[str, Any]:
    """Processeur unifié combinant Cognee, Langchain et logique métier COMPLÈTE"""
    
    logger.info(f"🔍 TRAITEMENT MESSAGE COMPLET: '{message[:50]}...', wa_id: {wa_id}")
    
    # Validation des entrées
    if not message or not message.strip():
        return {
            "response": "Message vide reçu",
            "source": "validation_error",
            "priority": "ERROR"
        }
    
    # Nettoyage des données
    message = ResponseValidator.clean_response(message)
    matched_bloc = ResponseValidator.clean_response(matched_bloc)
    
    # 1. Gestion de la mémoire
    memory = MemoryManager.get_or_create_memory(wa_id)
    
    # Optimiser la mémoire en limitant la taille
    MemoryManager.trim_memory(memory, max_messages=15)
    
    # 2. Analyser le contexte de conversation
    conversation_context = ConversationContextManager.analyze_conversation_context(message, memory)
    
    # Résumé mémoire pour logs
    memory_summary = MemoryManager.get_memory_summary(memory)
    
    logger.info(f"🧠 CONTEXTE CONVERSATION: {conversation_context}")
    logger.info(f"📊 MÉMOIRE RÉSUMÉ: {memory_summary}")
    
    # 3. Ajouter le message utilisateur à la mémoire
    memory.chat_memory.add_user_message(message)
    
    # 4. Application des règles de priorité avec contexte
    priority_result = MessageProcessor.detect_priority_rules(
        message,
        matched_bloc,
        conversation_context
    )
    
    # 5. Traitement selon les règles de priorité
    final_response = None
    response_type = "unknown"
    escalade_required = False
    
    if priority_result.get("use_matched_bloc") and priority_result.get("response"):
        final_response = priority_result["response"]
        response_type = "exact_match_enforced"
        escalade_required = False
    
    elif priority_result.get("priority_detected") == "N8N_BLOC_DETECTED":
        final_response = priority_result["response"]
        response_type = "n8n_bloc_used"
        escalade_required = False
    
    elif priority_result.get("priority_detected") == "N8N_BLOC_FALLBACK":
        final_response = priority_result["response"]
        response_type = "n8n_bloc_fallback"
        escalade_required = False
    
    elif priority_result.get("priority_detected") == "CPF_DELAI_DEPASSE_FILTRAGE":
        final_response = priority_result["response"]
        response_type = "cpf_delay_filtering"
        escalade_required = False
    
    elif priority_result.get("priority_detected") == "CPF_DELAI_NORMAL":
        final_response = priority_result["response"]
        response_type = "cpf_delay_normal"
        escalade_required = False
    
    elif priority_result.get("priority_detected") == "OPCO_DELAI_DEPASSE":
        final_response = priority_result["response"]
        response_type = "opco_delay_exceeded"
        escalade_required = True
    
    elif priority_result.get("priority_detected") == "OPCO_DELAI_NORMAL":
        final_response = priority_result["response"]
        response_type = "opco_delay_normal"
        escalade_required = False
    
    elif priority_result.get("priority_detected") == "DIRECT_DELAI_DEPASSE":
        final_response = priority_result["response"]
        response_type = "direct_delay_exceeded"
        escalade_required = True
    
    elif priority_result.get("priority_detected") == "DIRECT_DELAI_NORMAL":
        final_response = priority_result["response"]
        response_type = "direct_delay_normal"
        escalade_required = False
    
    elif priority_result.get("priority_detected") == "AFFILIATION_STEPS_REQUEST":
        final_response = priority_result["response"]
        response_type = "affiliation_steps_provided"
        escalade_required = False
    
    elif priority_result.get("priority_detected") == "PAIEMENT_CPF_DEMANDE_TIMING":
        final_response = priority_result["response"]
        response_type = "cpf_timing_request"
        escalade_required = False
    
    elif priority_result.get("priority_detected") == "CPF_BLOQUE_CONFIRME":
        final_response = priority_result["response"]
        response_type = "cpf_blocked_confirmed"
        escalade_required = False
    
    elif priority_result.get("priority_detected") == "DEMANDE_DATE_FORMATION":
        final_response = priority_result["response"]
        response_type = "asking_formation_date"
        escalade_required = False
    
    elif priority_result.get("priority_detected") == "AGRESSIVITE":
        final_response = priority_result["response"]
        response_type = "agressivite_detected"
        escalade_required = False
    
    elif priority_result.get("priority_detected") == "FOLLOW_UP_CONVERSATION":
        final_response = None  # Sera géré par l'IA ou Cognee
        response_type = "follow_up_ai_handled"
        escalade_required = False
    
    elif priority_result.get("priority_detected") == "PAIEMENT_SUIVI":
        final_response = None  # Sera géré par l'IA ou Cognee
        response_type = "paiement_suivi_ai_handled"
        escalade_required = False
    
    elif priority_result.get("priority_detected") == "ESCALADE_AUTO":
        final_response = priority_result["response"]
        response_type = "auto_escalade"
        escalade_required = True
    
    elif priority_result.get("priority_detected") == "PAIEMENT_SANS_BLOC":
        final_response = priority_result["response"]
        response_type = "paiement_fallback"
        escalade_required = True
    
    else:
        # Utiliser l'IA pour une réponse contextuelle ou fallback
        final_response = None
        response_type = "ai_contextual_response"
        escalade_required = priority_result.get("use_ai", False)
    
    # 6. Si pas de réponse finale, essayer Cognee puis fallback
    if final_response is None:
        # Essayer Cognee d'abord
        if cognee_manager.enabled:
            # Initialisation paresseuse
            if not cognee_manager.ready and not cognee_manager.initialization_attempted:
                asyncio.create_task(cognee_manager.initialize())
            
            if cognee_manager.ready:
                try:
                    cognee_response = await cognee_manager.search_knowledge(message, wa_id)
                    if cognee_response:
                        final_response = cognee_response
                        response_type = "cognee_knowledge_response"
                        logger.info("✅ RÉPONSE COGNEE UTILISÉE")
                except Exception as e:
                    logger.warning(f"⚠️ Erreur recherche Cognee: {e}")
        
        # Si toujours pas de réponse, fallback contextuel
        if final_response is None:
            # Adapter le fallback selon le contexte
            if conversation_context["needs_greeting"]:
                final_response = """Salut 👋

Je vais analyser ta demande et te répondre au mieux ! 😊

🕐 Notre équipe est disponible du lundi au vendredi, de 9h à 17h (hors pause déjeuner).
En attendant, peux-tu me préciser un peu plus ce que tu recherches ?"""
            else:
                final_response = """Parfait, je vais faire suivre ta demande à notre équipe ! 🙏

🕐 Notre équipe est disponible du lundi au vendredi, de 9h à 17h.
On te tiendra informé dès que possible ✅"""
            
            response_type = "fallback_with_context"
            escalade_required = True
    
    # 7. Ajout à la mémoire seulement si on a une réponse finale
    if final_response:
        memory.chat_memory.add_ai_message(final_response)
    
    # 8. Optimiser la mémoire après ajout
    MemoryManager.trim_memory(memory, max_messages=15)
    
    # 9. Construction du résultat final
    result = {
        "response": final_response,
        "source": response_type,
        "priority": priority_result.get("priority_detected", "NONE"),
        "escalade_required": escalade_required,
        "escalade_type": priority_result.get("escalade_type", "admin"),
        "conversation_context": conversation_context,
        "memory_summary": memory_summary,
        "processing_chain": "unified_complete"
    }
    
    logger.info(f"✅ TRAITEMENT TERMINÉ: source={response_type}, escalade={escalade_required}")
    
    return result

# Application FastAPI avec gestion du cycle de vie sécurisée
app = FastAPI(
    title="JAK Company API V26 - Complet Unifié",
    version="26.0",
    description="API complète combinant Cognee et Langchain avec toute la logique originale",
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

# Gestion du cycle de vie sans contextmanager pour éviter les erreurs Render
@app.on_event("startup")
async def startup_event():
    """Initialisation au démarrage"""
    logger.info("🚀 Démarrage serveur JAK Company API V26 - Version Complète")
    
    # Initialisation Cognee en arrière-plan si activé
    if COGNEE_ENABLED:
        asyncio.create_task(cognee_manager.initialize())
    
    # Tâche de nettoyage périodique
    async def periodic_cleanup():
        while True:
            try:
                await asyncio.sleep(3600)  # Toutes les heures
                MemoryManager.cleanup_expired_sessions()
                gc.collect()
            except Exception as e:
                logger.error(f"Erreur cleanup périodique: {e}")
    
    asyncio.create_task(periodic_cleanup())

@app.on_event("shutdown")
async def shutdown_event():
    """Arrêt propre"""
    logger.info("🛑 Arrêt serveur")
    with memory_lock:
        memory_store.clear()
    gc.collect()

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
        
        # Traitement unifié complet
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
            "confidence": 0.95 if result["source"] in ["cognee_knowledge_response", "exact_match_enforced"] else 0.8,
            "processing_type": result["priority"],
            "escalade_required": result.get("escalade_required", False),
            "escalade_type": result.get("escalade_type", "admin") if result.get("escalade_required") else None,
            "status": "success",
            "source": result["source"],
            "session_id": wa_id,
            "cognee_enabled": cognee_manager.enabled,
            "cognee_ready": cognee_manager.ready,
            "memory_info": result.get("memory_summary", {}),
            "conversation_context": result.get("conversation_context", {}),
            "processing_chain": result.get("processing_chain", "unified_complete")
        }
        
        logger.info(f"✅ RÉPONSE GÉNÉRÉE: source={result['source']}, priority={result['priority']}")
        
        # Cleanup périodique
        if len(memory_store) > MAX_SESSIONS:
            MemoryManager.cleanup_expired_sessions()
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

# ENDPOINTS DE MONITORING ET GESTION COMPLETS
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
            "debug_mode": DEBUG_MODE,
            "openai_configured": bool(OPENAI_API_KEY)
        },
        "memory": memory_stats,
        "improvements": [
            "VERSION 26: Unification complète Cognee + Langchain",
            "LOGIQUE ORIGINALE: Tous les patterns de paiement préservés",
            "CONTEXTE AVANCÉ: Analyse conversationnelle complète", 
            "ESCALADES: Système complet admin/formation/entreprise",
            "DÉLAIS: Calculs précis CPF/OPCO/Direct avec seuils corrects",
            "AMBASSADEUR: Processus complet avec scripts de vente",
            "MÉMOIRE: Gestion optimisée avec TTL et cleanup",
            "COGNEE: Base de connaissances JAK Company intégrée",
            "FALLBACKS: Contextuels et intelligents",
            "MONITORING: Endpoints complets pour surveillance"
        ]
    })

@app.get("/memory/status")
async def memory_status():
    """Statut détaillé de la mémoire"""
    
    total_messages = 0
    session_details = {}
    
    with memory_lock:
        for session_id, memory in memory_store.items():
            summary = MemoryManager.get_memory_summary(memory)
            total_messages += summary["total_messages"]
            
            session_details[session_id] = {
                **summary,
                "last_activity": getattr(memory, 'last_accessed', datetime.now()).isoformat(),
                "age_hours": (datetime.now() - getattr(memory, 'last_accessed', datetime.now())).total_seconds() / 3600
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
    MemoryManager.cleanup_expired_sessions()
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
        "message": "JAK Company API V26 - Agent IA WhatsApp Complet Unifié",
        "version": "26.0",
        "features": [
            "Cognee Knowledge Base",
            "Langchain Memory Management", 
            "Complete Payment Logic",
            "Advanced Context Analysis",
            "Ambassador Process",
            "Escalation System",
            "Memory TTL & Cleanup"
        ],
        "endpoints": {
            "main": "POST /",
            "health": "GET /health",
            "memory": "GET /memory/status",
            "cleanup": "POST /memory/cleanup",
            "cognee": "POST /cognee/reinitialize",
            "docs": "GET /docs" if DEBUG_MODE else "disabled"
        }
    })

# Point d'entrée
if __name__ == "__main__":
    import uvicorn
    
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    workers = int(os.environ.get("WORKERS", 1))
    
    # Configuration optimisée pour Render
    uvicorn_config = {
        "host": host,
        "port": port,
        "workers": workers,
        "log_level": "info" if DEBUG_MODE else "warning",
        "access_log": DEBUG_MODE,
        "timeout_keep_alive": 60,
        "timeout_graceful_shutdown": 30
    }
    
    logger.info(f"🚀 Démarrage serveur complet sur {host}:{port}")
    logger.info(f"🔧 Configuration: workers={workers}, debug={DEBUG_MODE}")
    logger.info(f"🧠 Cognee: disponible={COGNEE_AVAILABLE}, activé={COGNEE_ENABLED}")
    logger.info(f"🔑 OpenAI: configuré={bool(OPENAI_API_KEY)}")
    
    uvicorn.run(app, **uvicorn_config)