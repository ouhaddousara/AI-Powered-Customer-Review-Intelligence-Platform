# OCR Engine Benchmark — Layer 3

## Méthodologie

15 images générées à partir de vraies reviews Amazon (Amazon Reviews 2023),
avec dégradation réaliste volontaire (rotation ±2°, flou gaussien, bruit,
compression JPEG qualité 70) — pour que le benchmark différencie réellement
les moteurs, plutôt que du texte parfaitement rendu où tous scoreraient ~100%.

Métrique : distance de Levenshtein normalisée (distance d'édition / longueur
du texte de référence). 0 = parfait, plus haut = pire.

Script : `scripts/benchmark_ocr_engines.py`

## Résultats

| Moteur     | Score moyen | Temps total (15 images) |
|------------|-------------|--------------------------|
| Tesseract  | 0.126       | 3.9s                     |
| EasyOCR    | 0.193       | 14.9s                    |
| PaddleOCR  | 1.116       | 95.2s                    |

## Décision

**Tesseract retenu** pour `src/ocr/ocr_loader.py` — meilleur score ET
le plus rapide, sur les deux critères à la fois.

## Limitation connue — PaddleOCR

`paddlepaddle 3.3.1` a un bug confirmé sur l'exécution CPU avec
accélération oneDNN (`NotImplementedError:
ConvertPirAttribute2RuntimeAttribute not support`), documenté sur
plusieurs issues du repo officiel PaddlePaddle/Paddle. Contourné via
`enable_mkldnn=False`, mais ce mode dégradé produit un score aberrant
(>1.0, pire que ne rien extraire) et un temps d'exécution 25x supérieur
à Tesseract — signe d'un chemin d'exécution cassé, pas d'une vraie
comparaison de qualité OCR. Exclu de la décision finale pour cette
raison, pas par manque de test.
