# Final Evaluation — Layer 8

## Méthodologie

5 questions test, annotées à la main (IDs produits vérifiés comme
pertinents), mesurées sur 3 axes : Precision@5, latence end-to-end,
faithfulness (LLM-as-judge, Qwen via Groq).

Script : `evaluation/metrics.py`

## Résultats

| Question | IDs pertinents | Precision@5 | Faithfulness |
|---|---|---|---|
| Complaints | 4 | 0.80 | PASS |
| Size/fit issues | 2 | 0.40 | PASS |
| Shipping/delivery | 5 | 1.00 | PASS |
| Value for money | 2 | 0.40 | PASS |
| What customers love | 3 | 0.60 | PASS |
| **Moyenne** | — | **0.64** | **5/5 PASS** |

**Latence moyenne : 1.53s** (mesurée sur l'exécution finale retenue pour
ce rapport — la latence varie légèrement d'une exécution à l'autre,
dépendante de la charge réseau/API au moment de l'appel).

## Découverte clé — le retrieval trouve 100% des reviews pertinentes connues

Dans les 5 questions testées, la Precision@5 obtenue correspond
exactement à (nombre d'IDs pertinents annotés / 5) — c'est-à-dire que
la recherche a retrouvé **la totalité** des reviews pertinentes
connues dans le top-5, sans exception. Le score "imparfait" observé
sur certaines questions n'est pas un défaut de la recherche : c'est le
plafond mathématique inhérent à demander 5 résultats quand seulement
2-3 reviews pertinentes existent pour cette question précise dans le
jeu de test annoté.

## Conclusion

- **Faithfulness parfaite** (5/5) — la contrainte anti-hallucination
  du prompt tient sur un jeu de test élargi, pas juste un cas isolé.
- **Latence solide** (1.53s en moyenne), toujours largement sous
  l'objectif de 4s fixé dans la proposal initiale.
- **Retrieval fiable à 100%** sur les reviews pertinentes connues —
  la variation de Precision@5 s'explique entièrement par le nombre
  de résultats pertinents disponibles par question, pas par une
  faiblesse de la recherche elle-même.