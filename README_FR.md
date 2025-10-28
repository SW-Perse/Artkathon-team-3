# 🎨 Générateur d'Art Flow Field à partir d'un corpus de poèmes

Ce projet est une pipeline algorithmique légère qui transforme des textes de poèmes en œuvres d'art abstraites basées sur des champs de flux (flow field). Les poèmes sont convertis en vecteurs 14D basés sur leurs caractéristiques linguistiques, qui contrôlent ensuite les paramètres visuels comme la couleur, la turbulence, la densité et les motifs de flux.

Le choix du flow field comme méthode de rendu est inspiré des oeuvres de Tyler Hobbs : 
https://www.tylerxhobbs.com/words/flow-fields

Une grande partie des poèmes du corpus peuvent être consultés sur le site Poetry Foundation
https://www.poetryfoundation.org/

---

## L'équipe

### M1 IA
Mame Yacine NDIAYE
Imrane TITAOU LATIF

### M1 Data Engineer
Sophie CAPRON
Valentin FALQUET
Yves Malick Jordan MAO
Mama Aïssata SAKHO

---

## Concept principal

### Pipeline: Texte → Vecteur → Image

1. **Analyse textuelle** → Le poème est analysé pour ses caractéristiques linguistiques (rime, rythme, allitération, etc.)
2. **Vecteur 14D** → Les caractéristiques sont encodées en 14 valeurs numériques normalisées
3. **Mapping des paramètres** → Les valeurs du vecteur contrôlent les paramètres du champ de flux
4. **Rendu** → L'algorithme de champ de flux génère une œuvre d'art abstraite

---

## Le vecteur d'embedding 14D 

### Structure du vecteur

Chaque poème est vectorisé en 14 dimensions qui capturent sa structure poétique:

| Dimension |        Caractéristique       |    Normalisation   |          Effet Visuel         |
|-----------|------------------------------|--------------------|-------------------------------|
| **v[0]**  |       Longueur du titre      |       / 10.0       | Jitter des traits (aléatoire) |
| **v[1]**  | Complexité lexicale du titre |    diversité mots  |        Fidélité au flux       |
| **v[2]**  |        Nombre de vers        |       / 20.0       |        Nombre de traits       |
| **v[3]**  |     Mots moyens par vers     |       / 10.0       |      Résolution de grille     |
| **v[4]**  |   Variabilité longueur vers  |       / 5.0        |     Turbulence/complexité     |
| **v[5]**  |      Diversité des rimes     |  fréquence unique  |    Quantification angulaire   |
| **v[6]**  |         Rime dominante       |    fréquence max   |       Distorsion spirale      |
| **v[7]**  |     Score d'allitération     |  bigrammes répétés |        Couches de détail      |
| **v[8]**  |     Dominance vocalique      | voyelle principale |       Lissage des traits      |
| **v[9]**  |      Entropie vocalique      |       / 3.0        |        Graine aléatoire       |
| **v[10]** |          Rythme brut         |      mots/vers     |      Longueur des traits      |
| **v[11]** |      Longueur nom poète      |       / 5.0        |      Épaisseur des traits     |
| **v[12]** |      Diversité nom poète     |   lettres uniques  |           (réservé)           |
| **v[13]** |         Genre/Émotion        |       0.0-1.0      |    **Palette de couleurs**    |

### Mapping Genre → Couleur

La dimension **v[13]** détermine la palette de couleurs selon le genre émotionnel:

| Genre               | Valeur v[13]              | Colormap | Style Visuel                 |
|---------------------|---------------------------|----------|------------------------------|
| **Peur** (Fear)     | 0.0 - 0.2 (centre: 0.1)   | bone     | Niveaux de gris, inquiétant  |
| **Colère** (Anger)  | 0.2 - 0.3 (centre: 0.25)  | hot      | Couleurs feu (rouge/jaune)   |
| **Tristesse** (Sadness) | 0.3 - 0.4 (centre: 0.35) | PuBu     | Dégradés violet-bleu         |
| **Amour** (Love)    | 0.4 - 0.5 (centre: 0.45)  | RdPu     | Rouge-rose-violet            |
| **Joie** (Joy)      | 0.5 - 0.6 (centre: 0.55)  | rainbow  | Spectre complet              |
| **Surprise**        | 0.6 - 0.7 (centre: 0.65)  | cividis  | Bleu-jaune                   |

### Processus de rendu

1. **Construction de la grille**: Créer une grille d'angles basée sur la taille d'image et cell_size
2. **Génération des flux**: Générer un champ de bruit de Perlin avec plusieurs octaves
3. **Placement des points**: Disposer les points de départ sur le canvas (paramètre density)
4. **Tracé des traits**: Suivre les angles du champ de flux et dessiner des lignes colorées
   - La couleur varie selon la position ou l'angle de flux
   - La largeur s'amincit de épais à fin
   - La longueur est déterminée par le paramètre de rythme

### Paramètres du Champ de Flux

| Paramètre         | Formule             | Plage     | Contrôle                             |
|-------------------|---------------------|-----------|--------------------------------------|
| `cell_size`       | 4 + v[3] × 8        | 4-20 px   | Résolution grille (petit = détaillé) |
| `noise_scale`     | max(2, v[4] × 8)    | 2-16      | Complexité du flux                   |
| `octaves`         | 3 + v[7] × 4        | 3-7       | Couches de bruit Perlin              |
| `seed`            | v[9] × 1000         | 0-1000    | Graine déterministe                  |
| `quantize_steps`  | v[5] × 12           | 0-12      | Angles nets (rimes)                  |
| `swirl`           | v[6] × 0.3          | 0.0-0.3   | Distorsion spirale                   |

### Paramètres des traits

| Paramètre      | Formule                                 | Plage         | Contrôle                |
|----------------|-----------------------------------------|---------------|-------------------------|
| `density`      | max(0.001, min(0.006, v[2] × 0.002))    | 0.001-0.006   | Nombre de traits        |
| `max_length`   | 400 + v[10] × 20                        | 400-1400 px   | Longueur maximale       |
| `step_size`    | 2 + v[8] × 4                            | 2-6 px        | Lissage du trait        |
| `angle_gain`   | 0.6 + v[1] × 0.3                        | 0.6-0.9       | Fidélité au flux        |
| `jitter`       | v[0] × 0.15                             | 0.0-0.3       | Variation aléatoire     |
| `width_start`  | 6 + v[11] × 0.3                         | 6.0-6.3       | Épaisseur initiale      |
| `width_end`    | 0.8                                     | fixe          | Épaisseur finale        |

---

## Schémas de colorisation

### Expressive (Défaut)
- **Axe palette**: Vertical (haut vers bas)
- **Variation intra-trait**: Élevée (0.5)
- **Effet**: Changements de couleur audacieux, dégradés dramatiques
- **Idéal pour**: Compositions émotionnelles, dynamiques

### Very Smooth
- **Axe palette**: Horizontal (gauche vers droite)
- **Variation intra-trait**: Faible (0.2)
- **Effet**: Transitions subtiles, palette cohésive
- **Idéal pour**: Œuvres calmes, harmonieuses

### Wild
- **Axe palette**: Piloté par le champ de flux
- **Variation intra-trait**: Extrême (0.7)
- **Effet**: Chaos arc-en-ciel suivant les angles de flux
- **Idéal pour**: Pièces expérimentales, vibrantes

---

## Performance

- **Résolution**: 3000×3000 pixels
- **Temps de rendu**: ~10-15 secondes par image
- **Mémoire**: ~2GB RAM pour lots importants
- **Recommandé**: Traiter 50-100 poèmes maximum à la fois

---

## Installation rapide

### Cloner le repo Github
```powershell
git clone https://github.com/SW-Perse/Artkathon-team-3
cd Artkathon
```

### Installation
```powershell
# Créer et activer un environnement virtuel
python -m venv venv
venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt
```

### Génération d'image
```powershell
# Rendu de tous les poèmes du dataset
python pipeline.py

# Test avec 5 poèmes
python pipeline.py --limit 5

# Test avec un schéma de colorisation différent
python pipeline.py --color-scheme wild --limit 10
```

**Output**: `out/` dossier contenant les images générées

---

## Outils

### Pipeline principal (Traitement par lots)

```powershell
# Utilisation basique
python pipeline.py

# Dataset personnalisé
python pipeline.py --dataset chemin/vers/poemes.csv

# Schémas de couleur
python pipeline.py --color-scheme expressive   # Dégradés verticaux marqués (défaut)
python pipeline.py --color-scheme very_smooth  # Dégradés horizontaux subtils
python pipeline.py --color-scheme wild         # Chaos piloté par le flux

# Variations de style
python pipeline.py --style sharp               # Haut contraste, turbulent
python pipeline.py --style natural             # Rendu par défaut

# Contrôle de sortie
python pipeline.py --output galerie --limit 20
python pipeline.py --organize-by-genre         # Structure par dossiers de genre
```

### Outils individuels

#### Rendu d'un poème spécifique
```powershell
python tools/render_specific_poems.py "The Raven" "Fire and Ice"
python tools/render_specific_poems.py "Annabel Lee" --style sharp
```

#### Rendu d'un échantillon aléatoire
```powershell
python tools/render_random_samples.py --n 10
python tools/render_random_samples.py --n 5 --seed 42 --color-scheme wild
```

---

## Utilisation avancée

### Traiter par lots plusieurs schémas
```powershell
# Générer des galeries complètes avec chaque schéma de couleur
python pipeline.py --color-scheme expressive --output galerie_expressive
python pipeline.py --color-scheme very_smooth --output galerie_smooth
python pipeline.py --color-scheme wild --output galerie_wild
```

### Création de vecteur personnalisé
```python
from tools.simple_text_to_vectors import simple_text_to_vectors
from tools.render_embedding import map_embedding_to_params
from tools.flow_field import render

# Créer un vecteur personnalisé
vector = simple_text_to_vectors(
    title="Mon Poème",
    poem_text="Les roses sont rouges...",
    poet="Anonyme",
    genre="love"
)

# Rendu
params = map_embedding_to_params(vector, color_scheme='expressive')
img = render(params)
img.save('mon_oeuvre.png')
```

---

## 📁 Structure du projet

```
Artkathon/
├── pipeline.py                       # Script principal 
├── requirements.txt                  # Dépendances
│
├── tools/                            # Modules et utilitaires
│   ├── color_schemes.py              # Configurations de styles de rendus
│   ├── flow_field.py                 # Moteur de rendu
│   ├── perlin.py                     # Générateur de bruit
│   ├── render_embedding.py           # Mapping vecteur → paramètres
│   ├── render_random_samples.py      # Sélection aléatoire
│   ├── render_specific_poems.py      # Rendu par titre
│   └── simple_text_to_vectors.py     # Conversion texte → vecteur 14D
│
├── data/                             # Datasets
│   ├── PoemsDataset_cleaned.csv      # Corpus complet de poèmes bruts
│   └── poem_vectors_simple.csv       # Vecteurs pré-calculés (principal)
│
└── out/                              # Images générées (créé automatiquement)

```

---

## Format du dataset

### Option 1: Vecteurs pré-calculés (Recommandé)
CSV avec colonnes: `title`, `vector_14d`

```csv
title,vector_14d
"The Raven","[0.2, 1.0, 0.9, 0.85, 0.4, 0.3, 0.7, 0.6, 0.5, 0.7, 8.5, 0.4, 0.8, 0.1]"
"Fire and Ice","[0.3, 0.9, 0.3, 0.6, 0.2, 0.5, 0.4, 0.3, 0.6, 0.8, 6.0, 0.4, 0.75, 0.25]"
```

### Option 2: Poèmes bruts (vectorisés avant le rendu)
CSV/Excel avec colonnes: `Title`, `Poem`, `Poet`, `Genre`

```csv
Title,Poem,Poet,Genre
"The Raven","Once upon a midnight dreary...","Edgar Allan Poe","fear"
"Fire and Ice","Some say the world will end...","Robert Frost","anger"
```

**Genres supportés**: `fear`, `anger`, `sadness`, `love`, `joy`, `surprise`

---

## Dépannage

### "Dataset not found"
- Vérifier que le chemin du fichier est correct
- Utiliser un chemin absolu si le relatif ne fonctionne pas
- S'assurer que le fichier est `.csv`, `.xlsx`, ou `.xls`

### Erreurs d'import
```powershell
# S'assurer d'être dans le répertoire Artkathon
cd Artkathon

# Activer l'environnement virtuel
venv\Scripts\activate

# Réinstaller les dépendances
pip install -r requirements.txt
```

### Rendu lent
- Utiliser `--limit 10` pour les tests
- Envisager de réduire la résolution dans `flow_field.py` (changer width/height à 1500)
- Exécuter d'abord sur un sous-ensemble