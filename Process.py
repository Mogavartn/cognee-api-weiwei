// Enhanced Fuzzy Matcher V8 - VERSION COMPLÈTE CORRIGÉE OPCO/DIRECT
const inputData = $('Input Validation').first().json;
const bdd = $('Load BDD').first().json;

console.log("=== ENHANCED FUZZY MATCHER V8 COMPLET CORRIGÉ ===");
console.log("Message original:", inputData.original_message);
console.log("Message clean:", inputData.clean_message);

if (inputData.error || inputData.skip_processing || inputData.media_escalade) {
  console.log("ARRÊT : Erreur détectée");
  return [{
    json: {
      matched_bloc_id: inputData.media_escalade ? "media_escalade" : "input_error",
      matched_bloc_response: inputData.response,
      confidence: 1.0,
      processing_type: "direct_response",
      escalade_required: inputData.escalade_required || false,
      original_message: inputData.original_message,
      use_ai_agent: false
    }
  }];
}

const userMessage = inputData.clean_message;
const originalMessage = inputData.original_message;

// 1. DÉTECTION CONTEXTUELLE - VERSION ULTRA RENFORCÉE
function detectContextualResponse(message, originalMessage) {
  const messageLower = message.toLowerCase();
  const originalLower = originalMessage.toLowerCase();
  const messageWords = messageLower.trim().split(/\s+/);

  // MAP DE FINANCEMENT ULTRA RENFORCÉE
  const financingMap = {
    // CPF
    "cpf": "CPF",
    "compte personnel": "CPF",
    "compte personnel formation": "CPF",
    
    // OPCO - PATTERNS ULTRA RENFORCÉS
    "opco": "OPCO",
    "operateur": "OPCO",
    "opérateur": "OPCO", 
    "opco entreprise": "OPCO",
    "organisme paritaire": "OPCO",
    "formation opco": "OPCO",
    "financé par opco": "OPCO",
    "finance par opco": "OPCO",
    "financement opco": "OPCO",
    "via opco": "OPCO",
    "avec opco": "OPCO",
    "par opco": "OPCO",
    "opco formation": "OPCO",
    "formation via opco": "OPCO",
    "formation avec opco": "OPCO",
    "formation par opco": "OPCO",
    "grâce opco": "OPCO",
    "grace opco": "OPCO",
    "opco paie": "OPCO",
    "opco paye": "OPCO",
    "opco a payé": "OPCO",
    "opco a paye": "OPCO",
    "pris en charge opco": "OPCO",
    "prise en charge opco": "OPCO",
    "remboursé opco": "OPCO",
    "rembourse opco": "OPCO",
    
    // FINANCEMENT DIRECT - PATTERNS ULTRA RENFORCÉS
    "en direct": "direct",
    "financé en direct": "direct",
    "finance en direct": "direct", 
    "financement direct": "direct",
    "direct": "direct",
    "entreprise": "direct",
    "particulier": "direct",
    "patron": "direct",
    "j'ai financé": "direct",
    "jai finance": "direct",
    "j ai finance": "direct",
    "financé moi": "direct",
    "finance moi": "direct",
    "payé moi": "direct",
    "paye moi": "direct",
    "moi même": "direct",
    "moi meme": "direct",
    "j'ai payé": "direct",
    "jai paye": "direct",
    "j ai paye": "direct",
    "payé par moi": "direct",
    "paye par moi": "direct",
    "financé par moi": "direct",
    "finance par moi": "direct",
    "sur mes fonds": "direct",
    "fonds propres": "direct",
    "personnellement": "direct",
    "directement": "direct",
    "par mon entreprise": "direct",
    "par la société": "direct",
    "par ma société": "direct",
    "financement personnel": "direct",
    "auto-financement": "direct",
    "auto financement": "direct",
    "tout seul": "direct",
    "payé tout seul": "direct",
    "paye tout seul": "direct",
    "financé seul": "direct",
    "finance seul": "direct",
    "de ma poche": "direct",
    "par moi même": "direct",
    "par moi meme": "direct",
    "avec mes deniers": "direct",
    "société directement": "direct",
    "entreprise directement": "direct",
    "payé directement": "direct",
    "paye directement": "direct",
    "financé directement": "direct",
    "finance directement": "direct",
    "moi qui ai payé": "direct",
    "moi qui ai paye": "direct",
    "c'est moi qui ai payé": "direct",
    "c'est moi qui ai paye": "direct",
    "payé de ma poche": "direct",
    "paye de ma poche": "direct",
    "sortie de ma poche": "direct",
    "mes propres fonds": "direct",
    "argent personnel": "direct",
    "personnel": "direct"
  };

  let financingType = null;
  
  // RECHERCHE EXACTE DANS LA MAP
  for (const [key, value] of Object.entries(financingMap)) {
    if (messageLower.includes(key)) {
      financingType = value;
      console.log(`✅ Financement détecté via pattern exact: "${key}" -> ${value}`);
      break;
    }
  }

  // DÉTECTION CONTEXTUELLE RENFORCÉE SI PAS TROUVÉ
  if (!financingType) {
    console.log("🔍 Recherche contextuelle approfondie...");
    
    // OPCO - Patterns contextuels
    if (messageLower.includes("opco")) {
      financingType = "OPCO";
      console.log("✅ OPCO détecté par pattern contextuel simple");
    }
    
    // FINANCEMENT DIRECT - Patterns contextuels élargis
    else if ((messageLower.includes("financé") || messageLower.includes("finance") || 
              messageLower.includes("payé") || messageLower.includes("paye")) && 
             (messageLower.includes("direct") || messageLower.includes("moi") || 
              messageLower.includes("personnel") || messageLower.includes("entreprise") ||
              messageLower.includes("seul") || messageLower.includes("même") || 
              messageLower.includes("meme") || messageLower.includes("poche") ||
              messageLower.includes("propre") || messageLower.includes("perso"))) {
      financingType = "direct";
      console.log("✅ Financement direct détecté par pattern contextuel");
    }
    
    // Pattern "j'ai" + action de paiement
    else if ((messageLower.includes("j'ai") || messageLower.includes("jai") || 
              messageLower.includes("j ai")) &&
             (messageLower.includes("payé") || messageLower.includes("paye") || 
              messageLower.includes("financé") || messageLower.includes("finance"))) {
      financingType = "direct";
      console.log("✅ Financement direct détecté par 'j'ai payé/financé'");
    }
    
    // Pattern entreprise/société paye
    else if ((messageLower.includes("entreprise") || messageLower.includes("société") || 
              messageLower.includes("societe") || messageLower.includes("boite")) &&
             (messageLower.includes("payé") || messageLower.includes("paye") || 
              messageLower.includes("financé") || messageLower.includes("finance"))) {
      financingType = "direct";
      console.log("✅ Financement direct détecté par 'entreprise paye'");
    }
  }

  // DÉTECTION DÉLAI ULTRA RENFORCÉE
  const delayPatterns = [
    /(?:il y a|depuis|ça fait|ca fait)\\s*(\\d+)\\s*mois/,
    /(?:il y a|depuis|ça fait|ca fait)\\s*(\\d+)\\s*semaines?/,
    /(?:il y a|depuis|ça fait|ca fait)\\s*(\\d+)\\s*jours?/,
    /terminé\\s+il y a\\s+(\\d+)\\s*(mois|semaines?|jours?)/,
    /fini\\s+il y a\\s+(\\d+)\\s*(mois|semaines?|jours?)/,
    /(\\d+)\\s*(mois|semaines?|jours?)\\s+que/,
    /(\\d+)\\s*(mois|semaines?|jours?)\\s*que/,
    /fait\\s+(\\d+)\\s*(mois|semaines?|jours?)/,
    /depuis\\s+(\\d+)\\s*(mois|semaines?|jours?)/,
    // NOUVEAUX PATTERNS PLUS FLEXIBLES
    /(\\d+)\\s*(mois|semaines?|jours?)$/,
    /\\b(\\d+)\\s*(mois|semaines?|jours?)\\b/,
    /\\s+(\\d+)\\s*(mois|semaines?|jours?)\\s/
  ];
  
  let delayMonths = null;
  let matchedUnit = "";
  
  for (const pattern of delayPatterns) {
    const match = messageLower.match(pattern);
    if (match) {
      const number = parseInt(match[1]);
      const unit = match[2] || "mois";
      
      // Conversion en mois
      if (unit.includes("semaine")) {
        delayMonths = Math.max(1, Math.round(number / 4.33));
        matchedUnit = "semaines";
      } else if (unit.includes("jour")) {
        delayMonths = Math.max(1, Math.round(number / 30));
        matchedUnit = "jours";
      } else {
        delayMonths = number;
        matchedUnit = "mois";
      }
      
      console.log(`✅ Délai détecté: ${number} ${matchedUnit} = ${delayMonths} mois`);
      break;
    }
  }

  // LOGIQUE DE RETOUR RENFORCÉE
  if (financingType && delayMonths !== null) {
    console.log(`🎯 DÉTECTION COMPLÈTE: ${financingType} + ${delayMonths} mois`);
    return {
      type: "financing_with_delay_response",
      financing_type: financingType,
      delay_months: delayMonths,
      confidence: 0.99,
      context_hint: "payment_flow_response",
      override_direct_match: true
    };
  }

  if (financingType && delayMonths === null && messageWords.length <= 4) {
    console.log(`✅ Détection financement seul : ${financingType}`);
    return {
      type: "financing_short_response",
      financing_type: financingType,
      confidence: 0.90,
      context_hint: "payment_flow_response"
    };
  }

  // FALLBACK pour délai sans financement explicite (supposer CPF)
  if (!financingType && delayMonths !== null && messageWords.length <= 5) {
    console.log(`⚠️ Fallback contexte implicite CPF : délai ${delayMonths} mois`);
    return {
      type: "financing_with_delay_response",
      financing_type: "CPF",
      delay_months: delayMonths,
      confidence: 0.95,
      context_hint: "payment_flow_response",
      override_direct_match: true
    };
  }

  // FORCE VERS API SI PATTERN LARGE DÉTECTÉ
  const hasFinancingWord = ["cpf", "opco", "direct", "financé", "finance", "financement", 
                           "payé", "paye", "entreprise", "personnel", "seul"].some(word => messageLower.includes(word));
  const hasDelayWord = ["il y a", "ça fait", "ca fait", "depuis", "terminé", "fini", "fait"].some(word => messageLower.includes(word));
  const hasTimeUnit = ["mois", "semaines", "jours", "semaine", "jour"].some(word => messageLower.includes(word));
  
  if (hasFinancingWord && hasDelayWord && hasTimeUnit && messageWords.length <= 12) {
    console.log("🎯 FINANCEMENT + DÉLAI DÉTECTÉ (pattern large) - Force vers API Python");
    return {
      type: "financing_with_delay_response",
      financing_type: "unknown",
      delay_months: 1,
      confidence: 0.99,
      context_hint: "payment_flow_response",
      override_direct_match: true
    };
  }

  // CONFIRMATIONS ET NÉGATIONS
  const confirmationWords = ["oui", "yes", "ok", "d'accord", "exact", "c'est ca", "c'est ça", "effectivement", "confirme"];
  const negationWords = ["non", "no", "pas", "jamais", "aucune", "pas du tout"];
  if (messageWords.length <= 3) {
    if (confirmationWords.some(word => messageLower.includes(word))) {
      return { type: "confirmation", confidence: 0.85 };
    }
    if (negationWords.some(word => messageLower.includes(word))) {
      return { type: "negation", confidence: 0.85 };
    }
  }

  // DÉTECTION CONTACTS AMBASSADEUR
  const contactPatterns = [
    /[a-zA-ZÀ-ÿ]+\\s+[a-zA-ZÀ-ÿ]+\\s+0[0-9]{9}/,
    /[a-zA-ZÀ-ÿ]+.*@.*\\.(com|fr|net|org)/,
    /0[0-9]{9}/,
    /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}/
  ];
  const isContactList = contactPatterns.some(p => p.test(originalMessage)) ||
                        (originalLower.includes("@") && originalLower.includes("."));
  if (isContactList) {
    return { type: "contacts_ambassadeur", confidence: 0.95 };
  }

  return null;
}

// 2. DÉTECTION DIRECTE - VERSION NETTOYÉE
function detectDirectMatch(message) {
  const messageLower = message.toLowerCase();
  const messageWords = messageLower.trim().split(/\\s+/);
  const isLongMessage = messageWords.length > 3;
  
  const isPaiementContext = messageLower.includes("payé") || messageLower.includes("paiement") || 
                           messageLower.includes("virement") || messageLower.includes("attends") ||
                           messageLower.includes("reçu") || messageLower.includes("argent");
  
  // AGRESSIVITÉ (priorité absolue)
  const aggressiveTerms = ["merde", "nul", "batard", "enervez", "chier", "putain"];
  if (aggressiveTerms.some(term => messageLower.includes(term))) {
    return { type: "agressivite", confidence: 1.0, bloc: "gestion_agressivite" };
  }
  
  if ((messageLower.includes(" con ") || messageLower.startsWith("con ") || messageLower.endsWith(" con")) 
      && !messageLower.includes("contact")) {
    return { type: "agressivite", confidence: 1.0, bloc: "gestion_agressivite" };
  }

  // AMBASSADEUR INSCRIPTION (priorité TRÈS haute)
  const ambassadeurInscriptionPatterns = [
    "comment devenir ambassadeur", "je veux devenir ambassadeur", 
    "devenir ambassadeur", "inscription ambassadeur", "programme ambassadeur",
    "comment m inscrire", "comment m'inscrire", "comment être ambassadeur",
    "comment etre ambassadeur", "rejoindre programme", "participer programme", 
    "devenir partenaire", "programme partenaire", "comment je deviens ambassadeur",
    "gagner argent avec vous", "faire de l'argent avec", "faire de l argent avec",
    "on m'a parle de votre programme", "on m'a parlé de votre programme",
    "toucher commission", "gagner commission", "être rémunéré", "etre remunere",
    "comment gagner de l argent", "comment gagner de l'argent", 
    "gagne de l argent dans cette histoire", "gagne de l'argent dans cette histoire",
    "comment je peux gagner", "comment faire de l argent", "comment faire de l'argent"
  ];

  const hasAmbassadeurInscription = ambassadeurInscriptionPatterns.some(pattern => messageLower.includes(pattern));

  if (hasAmbassadeurInscription && !isPaiementContext) {
    console.log("🤝 DÉTECTION AMBASSADEUR INSCRIPTION");
    return { type: "ambassadeur_inscription", confidence: 0.98, bloc: "bloc_ambassadeur_nouveau" };
  }

  // AMBASSADEUR EXPLICATION
  const ambassadeurExplicationPatterns = [
    "c'est quoi un ambassadeur", "qu'est-ce qu'un ambassadeur", "que fait un ambassadeur",
    "ambassadeur c'est quoi", "ambassadeur ça consiste en quoi", "role ambassadeur", "rôle ambassadeur",
    "définition ambassadeur", "expliquer ambassadeur", "ambassadeur kesako", "ambassadeur ?",
    "qu est ce qu un ambassadeur", "qu'est ce qu'un ambassadeur", "ambassadeur definition", "ambassadeur définition"
  ];

  const hasAmbassadeurExplication = ambassadeurExplicationPatterns.some(pattern => messageLower.includes(pattern));

  if (hasAmbassadeurExplication && !hasAmbassadeurInscription && !isPaiementContext) {
    console.log("❓ DÉTECTION AMBASSADEUR EXPLICATION");
    return { type: "ambassadeur_explication", confidence: 0.95, bloc: "bloc_ambassadeur_explication" };
  }

  // AFFILIATION QUESTION
  const affiliationQuestionPatterns = [
    "j'ai reçu un mail concernant l'affiliation", "j'ai recu un mail concernant l'affiliation",
    "mail affiliation", "email affiliation", "programme affiliation",
    "affiliation c'est quoi", "c'est quoi l'affiliation", "qu'est-ce que l'affiliation",
    "mail sur l'affiliation", "recu mail affiliation", "reçu mail affiliation",
    "j'ai un mail sur l'affiliation", "mail programme affiliation", "email programme affiliation",
    "info affiliation", "information affiliation", "renseignement affiliation",
    "question affiliation", "affiliation comment ça marche", "comment marche l'affiliation"
  ];

  if (affiliationQuestionPatterns.some(pattern => messageLower.includes(pattern))) {
    console.log("📧 DÉTECTION QUESTION AFFILIATION");
    return { type: "affiliation_question", confidence: 0.95, bloc: "bloc_affiliation_question" };
  }

  // FORMATIONS SPÉCIFIQUES (priorité HAUTE)
  const formationsSpecifiquesPatterns = [
    "formation en anglais", "formations en anglais", "cours d'anglais", "cours anglais",
    "apprendre anglais", "formation langue anglaise", "formation espagnol", "formation allemand",
    "formation italien", "formation français", "cours espagnol", "cours allemand", 
    "cours italien", "cours français", "formation langues", "formation langue", "cours de langue",
    "formation excel", "formation word", "formation powerpoint", "cours excel",
    "cours word", "cours powerpoint", "formation bureautique",
    "formation informatique", "formation développement web", "formation 3D",
    "cours informatique", "cours développement",
    "formation marketing", "formation vente", "formation développement personnel",
    "bilan de compétences", "formation écologie", "formation numérique responsable"
  ];

  const hasFormationSpecifique = formationsSpecifiquesPatterns.some(pattern => messageLower.includes(pattern));

  const isReallyGeneralQuestion = (messageLower.includes("faites vous") || messageLower.includes("proposez vous") ||
                                  messageLower.includes("quelles formations") || messageLower.includes("que proposez")) &&
                                 !hasFormationSpecifique;

  if (hasFormationSpecifique && !isReallyGeneralQuestion && !isPaiementContext) {
    console.log("🎯 DÉTECTION FORMATION SPÉCIFIQUE");
    return { type: "formation_specifique", confidence: 0.95, bloc: "bloc_formation_specifique" };
  }

  // FORMATIONS - QUESTIONS GÉNÉRALES
  const formationsQuestionsGenerales = [
    "faites vous des formations", "faites-vous des formations", "vous faites des formations",
    "proposez vous des formations", "proposez-vous des formations", "formations professionnelles",
    "formation professionnelle", "est ce que vous faites", "est-ce que vous faites"
  ];

  const hasQuestionGenerale = formationsQuestionsGenerales.some(pattern => messageLower.includes(pattern));
  const isShortQuestion = messageWords.length <= 6 && 
    (messageLower.includes("formation") && 
     (messageLower.includes("faites") || messageLower.includes("proposez") || messageLower.includes("pro")));

  const isCatalogueRequest = messageLower.includes("quelles") || messageLower.includes("liste") ||
                            messageLower.includes("catalogue") || messageLower.includes("disponible") ||
                            messageLower.includes("proposez quoi");

  if ((hasQuestionGenerale || isShortQuestion) && !isPaiementContext && !isCatalogueRequest && !hasFormationSpecifique) {
    console.log("❓ DÉTECTION QUESTION FORMATION GÉNÉRALE");
    return { type: "formations_question_generale", confidence: 0.95, bloc: "bloc_formations_question_generale" };
  }

  // FORMATIONS - CATALOGUE DÉTAILLÉ
  const formationCataloguePatterns = [
    "quelles formations proposez vous", "quelles formations proposez-vous",
    "vous proposez quoi comme formation", "vous avez quoi comme formation",
    "formations disponibles", "liste des formations", "catalogue formation",
    "vos formations", "formations que vous proposez", "formations que vous avez",
    "qu'est ce que vous proposez", "qu'est-ce que vous proposez",
    "je veux voir vos formations", "je veux connaitre vos formations",
    "je m'interesse aux formations", "je m'intéresse aux formations",
    "formations possibles", "types de formation", "domaines de formation"
  ];

  const hasFormationCatalogue = formationCataloguePatterns.some(pattern => messageLower.includes(pattern));

  if (hasFormationCatalogue && !isPaiementContext && !hasFormationSpecifique) {
    console.log("🎓 DÉTECTION CATALOGUE FORMATION");
    return { type: "formations_disponibles", confidence: 0.95, bloc: "bloc_formations_disponibles" };
  }

  // PAIEMENT FORMATION
  const paiementPatterns = [
    "je veux etre paye pour ma formation", "je veux être payé pour ma formation",
    "j'ai pas ete paye pour", "j'ai pas été payé pour",
    "comment etre paye pour", "comment être payé pour",
    "quand vais je recevoir mon paiement", "quand vais-je recevoir mon paiement",
    "ou en est mon paiement de formation", "où en est mon paiement de formation",
    "probleme avec mon paiement", "problème avec mon paiement",
    "retard de paiement formation", "paiement formation en retard"
  ];
  
  const hasPaiementKeyword = paiementPatterns.some(pattern => messageLower.includes(pattern));
  const hasFormationContext = messageLower.includes("formation") && messageLower.includes("paye");
  
  if ((hasPaiementKeyword || hasFormationContext) && isLongMessage && isPaiementContext) {
    console.log("💰 DÉTECTION PAIEMENT");
    return { type: "paiement", confidence: 0.98, bloc: "bloc_paiement_formation" };
  }

  // CPF FORMATION
  const cpfFormationPatterns = [
    "je veux une formation cpf", "inscription formation cpf",
    "comment faire une formation cpf", "formation financée par cpf",
    "vous faites encore du cpf", "formations cpf disponibles",
    "cpf encore possible", "utiliser mon cpf"
  ];

  const delayWords = ["il y a", "ça fait", "depuis", "mois", "semaines", "jours"];
  const isCpfWithDelay = messageLower.includes("cpf") && 
                         delayWords.some(word => messageLower.includes(word));

  const hasCpfKeyword = cpfFormationPatterns.some(pattern => messageLower.includes(pattern));
  const isPotentialCpfRequest = messageLower.includes("cpf") && 
                               (messageLower.includes("formation") || messageLower.includes("inscrire")) &&
                               isLongMessage && 
                               !isCpfWithDelay;

  if ((hasCpfKeyword || isPotentialCpfRequest) && !isPaiementContext && !isCpfWithDelay) {
    console.log("📚 DÉTECTION CPF FORMATION");
    return { type: "cpf", confidence: 0.98, bloc: "bloc_cpf_indisponible" };
  }

  if (isCpfWithDelay) {
    console.log("🎯 CPF + DÉLAI DÉTECTÉ - Vers API Python");
    return null;
  }
  
  // TRANSMISSION CONTACTS
  const contactsPatterns = [
    "comment envoyer des contacts", "ou envoyer ma liste", "où envoyer ma liste",
    "formulaire pour contacts", "transmettre des contacts"
  ];
  
  if (contactsPatterns.some(pattern => messageLower.includes(pattern))) {
    return { type: "contacts", confidence: 0.98, bloc: "bloc_transmission_contacts" };
  }
  
  // DEMANDE HUMAIN
  const humainPatterns = [
    "parler a un humain", "parler à un humain", "contact humain",
    "etre rappele", "être rappelé", "je veux un appel"
  ];
  
  if (humainPatterns.some(pattern => messageLower.includes(pattern))) {
    return { type: "humain", confidence: 0.98, bloc: "bloc_demande_humain" };
  }
  
  return null;
}

// 3. FUZZY MATCHING
function enhancedSimilarity(text1, text2) {
  const words1 = text1.toLowerCase().split(/\\W+/).filter(w => w.length > 2);
  const words2 = text2.toLowerCase().split(/\\W+/).filter(w => w.length > 2);
  
  if (words1.length === 0 || words2.length === 0) return 0;
  
  const intersection = words1.filter(w => words2.includes(w));
  const union = [...new Set([...words1, ...words2])];
  
  const jaccardScore = union.length > 0 ? intersection.length / union.length : 0;
  
  const importantWords = ['ambassadeur', 'paiement', 'formation', 'cpf', 'contacts', 'argent', 'commission', 'proposez', 'disponible', 'catalogue'];
  const importantBonus = intersection.filter(w => importantWords.includes(w)).length * 0.1;
  
  let sequenceBonus = 0;
  if (text1.toLowerCase().includes(text2.toLowerCase()) || text2.toLowerCase().includes(text1.toLowerCase())) {
    sequenceBonus = 0.2;
  }
  
  return Math.min(1.0, jaccardScore + importantBonus + sequenceBonus);
}

// EXÉCUTION PRINCIPALE
console.log("=== DÉBUT ANALYSE ===");

// 1. DÉTECTION CONTEXTUELLE EN PRIORITÉ
const contextualMatch = detectContextualResponse(userMessage, originalMessage);
if (contextualMatch) {
  console.log("CONTEXTE DÉTECTÉ:", contextualMatch);
  
  if (contextualMatch.override_direct_match || contextualMatch.confidence >= 0.99) {
    console.log("🎯 PRIORITÉ CONTEXTUELLE ACTIVÉE");
    return [{
      json: {
        matched_bloc_id: null,
        matched_bloc_response: null,
        confidence: contextualMatch.confidence,
        processing_type: "contextual_response_priority",
        escalade_required: false,
        original_message: originalMessage,
        use_ai_agent: true,
        ai_context: `PRIORITÉ CONTEXTE: ${contextualMatch.type} - ${contextualMatch.financing_type || ''} ${contextualMatch.delay_months || ''}`,
        contextual_info: contextualMatch
      }
    }];
  }
  
  return [{
    json: {
      matched_bloc_id: null,
      matched_bloc_response: null,
      confidence: contextualMatch.confidence,
      processing_type: "contextual_response_detected",
      escalade_required: false,
      original_message: originalMessage,
      use_ai_agent: true,
      ai_context: `Réponse contextuelle détectée: ${contextualMatch.type}`,
      contextual_info: contextualMatch
    }
  }];
}

// 2. DÉTECTION DIRECTE
const directMatch = detectDirectMatch(userMessage);
if (directMatch) {
  console.log(`✅ MATCH DIRECT TROUVÉ: ${directMatch.type} -> ${directMatch.bloc}`);
  
  if (directMatch.type === "agressivite") {
    return [{
      json: {
        matched_bloc_id: "gestion_agressivite",
        matched_bloc_response: bdd.regles_comportementales.gestion_agressivite.response,
        confidence: 1.0,
        processing_type: "agressivite_detected",
        escalade_required: false,
        original_message: originalMessage,
        use_ai_agent: false
      }
    }];
  } else {
    const bloc = bdd.blocs_reponses[directMatch.bloc];
    if (bloc) {
      return [{
        json: {
          matched_bloc_id: directMatch.bloc,
          matched_bloc_response: bloc.response,
          confidence: directMatch.confidence,
          processing_type: "direct_keyword_match",
          escalade_required: false,
          original_message: originalMessage,
          use_ai_agent: false
        }
      }];
    }
  }
}

console.log("Aucun match direct trouvé, passage au fuzzy matching");

// 3. FUZZY MATCHING
let bestMatch = null;
let highestScore = 0;

console.log("=== FUZZY MATCHING ===");
for (const [blocId, bloc] of Object.entries(bdd.blocs_reponses)) {
  if (!bloc.intentions) continue;
  
  for (const intention of bloc.intentions) {
    const score = enhancedSimilarity(userMessage, intention);
    
    let bonusScore = 0;
    if (blocId.includes("formation")) bonusScore = 0.25;
    if (blocId.includes("paiement")) bonusScore = 0.20;
    if (blocId.includes("ambassadeur")) bonusScore = 0.20;
    if (blocId.includes("cpf")) bonusScore = 0.15;
    if (blocId.includes("transmission")) bonusScore = 0.15;
    if (blocId.includes("humain")) bonusScore = 0.10;
    
    const finalScore = Math.min(1.0, score + bonusScore);
    
    if (finalScore > highestScore && finalScore >= 0.25) {
      highestScore = finalScore;
      bestMatch = {
        bloc_id: blocId,
        response: bloc.response,
        confidence: finalScore,
        matched_intention: intention
      };
    }
  }
}

// 4. DÉCISION FINALE
if (bestMatch && bestMatch.confidence >= 0.5) {
  console.log(`✅ BLOC HAUTE CONFIANCE: ${bestMatch.bloc_id} (${bestMatch.confidence.toFixed(2)})`);
  return [{
    json: {
      matched_bloc_id: bestMatch.bloc_id,
      matched_bloc_response: bestMatch.response,
      confidence: bestMatch.confidence,
      processing_type: "bloc_matched_high_confidence",
      matched_intention: bestMatch.matched_intention,
      escalade_required: false,
      original_message: originalMessage,
      use_ai_agent: false
    }
  }];
} else if (bestMatch && bestMatch.confidence >= 0.3) {
  console.log(`✅ BLOC CONFIANCE MOYENNE: ${bestMatch.bloc_id} (${bestMatch.confidence.toFixed(2)})`);
  return [{
    json: {
      matched_bloc_id: bestMatch.bloc_id,
      matched_bloc_response: bestMatch.response,
      confidence: bestMatch.confidence,
      processing_type: "bloc_matched_medium_confidence",
      matched_intention: bestMatch.matched_intention,
      escalade_required: false,
      original_message: originalMessage,
      use_ai_agent: true,
      ai_context: `Bloc trouvé: ${bestMatch.bloc_id} avec confiance ${bestMatch.confidence.toFixed(2)}`
    }
  }];
} else {
  console.log("❌ AUCUN BLOC TROUVÉ - Analyse catégorie");
  
  // ANALYSE DE CATÉGORIE POUR FALLBACK
  const categoryKeywords = {
    "formation": ["formation", "cours", "apprendre", "enseigner", "stage", "proposez", "catalogue", "disponible"],
    "paiement": ["paye", "virement", "argent", "attente", "retard", "finance", "euro", "commission"],
    "ambassadeur": ["ambassadeur", "commission", "contacts", "partenaire", "affiliation", "recommander"],
    "cpf": ["cpf", "compte personnel", "formation"],
    "technique": ["bug", "erreur", "probleme", "problème", "marche", "fonctionne", "ne marche pas"]
  };

  let categoryType = "general";
  let categoryScore = 0;
  
  for (const [category, keywords] of Object.entries(categoryKeywords)) {
    const matchCount = keywords.filter(keyword => userMessage.includes(keyword)).length;
    if (matchCount > categoryScore) {
      categoryScore = matchCount;
      categoryType = category;
    }
  }

  // PATCH SPÉCIAL POUR CPF + DÉLAI (Bypass API si problème)
  if (contextualMatch && contextualMatch.type === "financing_with_delay_response") {
    const financing = contextualMatch.financing_type;
    const delay = contextualMatch.delay_months;
    
    if (financing === "CPF" && delay >= 2) {
      console.log("🔧 PATCH CPF: Bypass activé - API retourne fallback");
      return [{
        json: {
          matched_bloc_id: "cpf_delai_filtrage_patch",
          matched_bloc_response: `Juste avant que je transmette ta demande 🙏

Est-ce que tu as déjà été informé par l'équipe que ton dossier CPF faisait partie des quelques cas bloqués par la Caisse des Dépôts ?

👉 Si oui, je te donne directement toutes les infos liées à ce blocage.
Sinon, je fais remonter ta demande à notre équipe pour vérification ✅`,
          confidence: 0.99,
          processing_type: "cpf_bypass_api_fallback",
          escalade_required: false,
          original_message: originalMessage,
          use_ai_agent: false
        }
      }];
    }
  }

  console.log(`📊 FALLBACK: Catégorie ${categoryType} (score: ${categoryScore})`);
  return [{
    json: {
      matched_bloc_id: null,
      matched_bloc_response: null,
      confidence: 0.1,
      processing_type: "no_match_use_ai",
      escalade_required: true,
      escalade_type: categoryType,
      original_message: originalMessage,
      use_ai_agent: true,
      ai_context: `Catégorie détectée: ${categoryType} (score: ${categoryScore}), pas de bloc correspondant trouvé`
    }
  }];
}