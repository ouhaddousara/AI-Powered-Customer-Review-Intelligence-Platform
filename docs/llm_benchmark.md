# LLM Benchmark — Layer 5 RAG

## Méthodologie

5 questions test envoyées à 3 LLM, en réutilisant le même contexte
ChromaDB pour chaque question (retrieval identique) — isole la
comparaison à la qualité de génération, pas à la recherche.

Script : `scripts/benchmark_llm_engines.py`

## Substitution notée — Gemini remplacé par Qwen

Gemini (prévu dans la proposal initiale) a été exclu : la clé API en
tier gratuit retournait systématiquement `429 RESOURCE_EXHAUSTED`
(limite bloquée à 0 requêtes, un problème connu sur les comptes
Gemini non facturés depuis fin 2025/2026). Plutôt que de lier un
compte de facturation pour un usage 100% gratuit, Qwen 3.6 27B a été
utilisé à la place — servi directement par Groq (déjà en place),
sans nouvelle inscription ni risque de blocage supplémentaire.

## Résultats

| Moteur | Temps moyen | Temps total (5 questions) |
|--------|-------------|----------------------------|
| Groq / LLaMA 3.3 70B | 0.95s | 4.8s |
| Qwen 3.6 27B (via Groq) | 1.17s | 5.8s |
| Mistral Small | 1.91s | 9.5s |

## Observations qualité

- **Groq/LLaMA 3** : réponses correctes et rapides, formulation parfois
  générique.
- **Qwen** : réponses bien structurées, la plus fine sur les nuances
  multilingues (a détecté "precio accesible" en espagnol comme signal
  de valeur, manqué par les deux autres moteurs).
- **Mistral** : concis, correct, mais le plus lent — parfois des
  réponses tronquées avant la fin de la phrase.

## Décision

**Qwen 3.6 27B retenu** comme moteur de production, remplaçant
LLaMA 3.3 70B dans `src/rag/qa.py` — meilleure qualité observée
(nuances multilingues) pour un coût de vitesse minime (+0.22s de
moyenne), et évite la dépréciation annoncée de `llama-3.3-70b-versatile`
par Groq (17 juin 2026).

## Limitation connue — bug de raisonnement Qwen

Qwen 3.6 27B est un modèle à raisonnement — sans le paramètre
`reasoning_effort="none"`, il expose son raisonnement interne
(`<think>...</think>`) directement dans la réponse, la rendant
inutilisable telle quelle et ralentissant l'inférence de ~3x. Corrigé
en désactivant explicitement le mode raisonnement, adapté à notre cas
d'usage (QA factuel, pas de calcul complexe).
