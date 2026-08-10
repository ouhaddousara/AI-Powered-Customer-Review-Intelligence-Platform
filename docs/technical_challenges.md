# Technical Challenges & Solutions

Ce document trace les problèmes techniques réels rencontrés pendant la
construction du pipeline, et comment ils ont été diagnostiqués et résolus —
pas juste "ce qui a été fait", mais comment les blocages ont été débloqués.

## Layer 1 — Ingestion

### Dataset Hugging Face cassé par un changement de politique de sécurité
La lib `datasets` a désactivé le support des scripts de chargement Python
personnalisés (risque d'exécution de code arbitraire), cassant le
chargement standard du dataset Amazon Reviews 2023.
**Résolution** : accès direct au fichier JSON Lines brut via son URL HTTP,
en contournant la lib — plus robuste, indépendant des changements internes
de `datasets`.

### Choix légal de la cible de scraping
Etsy et eBay écartés après vérification de leurs Conditions d'Utilisation
(interdiction explicite du scraping, malgré un `robots.txt` parfois
permissif) — précédent juridique notable pour eBay (*eBay v. Bidder's
Edge*, 2000). Jumia.ma retenu après vérification : `robots.txt` autorise
explicitement le scraping identifié sous 200 req/min.
**Compétence démontrée** : vérification légale systématique avant tout
scraping, pas seulement `robots.txt`.

### Contournement de la protection Cloudflare
Jumia bloque les requêtes HTTP simples (`curl`, downloader Scrapy par
défaut) via un challenge JavaScript Cloudflare.
**Résolution** : bascule vers Selenium (navigateur réel, résout le
challenge nativement), avec configuration anti-détection.

### Pagination des reviews introuvable
Trois hypothèses testées méthodiquement et éliminées : scroll infini,
paramètre d'URL (`?page=`), appel API caché (vérifié via les logs de
performance natifs de Chrome DevTools Protocol, sans dépendance tierce
après l'échec de `selenium-wire`).
**Décision** : la page n'expose que les 10 reviews les plus récentes par
produit — stratégie adaptée en conséquence (couverture par volume de
produits plutôt que profondeur par produit).

## Layer 3 — OCR

### Bug confirmé de `paddlepaddle` sur CPU
`PaddleOCR` plantait avec une erreur interne (`ConvertPirAttribute2Run
timeAttribute not support`) — bug connu de la version 3.3.x sur
l'exécution CPU avec accélération oneDNN, documenté sur plusieurs issues
GitHub officielles du projet PaddlePaddle.
**Résolution** : contournement testé (`enable_mkldnn=False`), mais le
résultat obtenu (score et temps d'exécution aberrants) a révélé un mode
d'exécution dégradé plutôt qu'un vrai fix — PaddleOCR exclu du benchmark
final sur cette base, documentée et chiffrée, pas par abandon.

## Principe transversal

Chaque blocage a été traité avec la même méthode : diagnostiquer avant
d'agir, tester une hypothèse à la fois, accepter une limite documentée
plutôt que de s'acharner indéfiniment quand le coût de la résolution
dépasse la valeur récupérable (pagination Jumia, PaddleOCR).

## Layer 5 — OCR

### Seuil de pertinence — calibration empirique et bug de couplage

Ajout d'un garde-fou pour éviter que le LLM ne génère une réponse à
partir de contexte hors-sujet quand aucune review pertinente n'existe.

**Calibration** : la première approche envisagée (seuil sur la distance
minimale du meilleur résultat) a été testée avant d'être codée — et
rejetée sur preuve, pas sur intuition. Une question hors-sujet
("What is the capital of France?") produisait parfois un match isolé
trompeur avec une distance plus basse qu'une vraie question pertinente,
faussant un seuil basé sur le minimum seul. La moyenne des distances
sur les k résultats s'est révélée un signal fiable : ~0.66 pour une
question pertinente, ~0.71 pour une question hors-sujet — seuil fixé
à 0.69 sur cette base observée.

**Bug découvert en testant, pas en théorisant** : une fois le seuil
implémenté, une question réellement pertinente ("What do customers
complain about most?") était incorrectement rejetée. Cause : la
vérification de pertinence utilisait la recherche **filtrée** par
sentiment (Layer 4), un sous-ensemble de résultats différent de celui
utilisé pour calibrer le seuil — comparaison biaisée entre deux mesures
non comparables. Corrigé en découplant totalement les deux logiques :
`check_relevance()` interroge toujours l'index **sans filtre**, le
filtre sentiment n'intervenant que dans la recherche réelle utilisée
pour construire le contexte, une fois la pertinence confirmée.

**Leçon** : deux fonctionnalités ajoutées à des moments différents du
projet (filtre sentiment en premier, seuil de pertinence ensuite)
peuvent interagir silencieusement si elles partagent le même chemin de
code sans qu'on y pense explicitement — d'où l'importance de tester
chaque ajout contre des cas concrets (question pertinente ET hors-sujet)
avant de le considérer terminé.