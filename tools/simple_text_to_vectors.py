"""
Script pour transformer le texte en vecteurs 14D pour la génération d'images flow-field
"""
import numpy as np
import pandas as pd
import re
import os
import colorsys
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from collections import Counter

def count_syllables(word):
    """
    Compte approximativement le nombre de syllabes dans un mot
    Basé sur le nombre de voyelles consécutives
    """
    word = word.lower()
    # Supprimer les caractères non-alphabétiques
    word = re.sub(r'[^a-z]', '', word)
    
    if len(word) == 0:
        return 0
    
    # Compter les groupes de voyelles
    vowels = 'aeiouy'
    syllable_count = 0
    previous_was_vowel = False
    
    for char in word:
        is_vowel = char in vowels
        if is_vowel and not previous_was_vowel:
            syllable_count += 1
        previous_was_vowel = is_vowel
    
    # Un mot a au moins une syllabe
    return max(1, syllable_count)

def simple_text_to_vectors(title, poem_text, poet, genre):
    """
    Transformation du poème complet en vecteurs numériques (14 dimensions)
    
    STRUCTURE EXACTE DU VECTEUR (utilisée par render_embedding.py):
    
    v[0]: Title length / 10.0          → jitter (stroke randomness)
    v[1]: Title lexical complexity     → angle_gain (flow following strength)
    v[2]: Verse count / 20.0           → density (number of strokes)
    v[3]: Avg words per verse / 10.0   → cell_size (grid resolution)
    v[4]: Verse length variability     → noise_scale (flow complexity)
    v[5]: Rhyme diversity              → quantize_steps (angular snapping)
    v[6]: Dominant rhyme frequency     → swirl (spiral distortion)
    v[7]: Alliteration score           → octaves (detail layers)
    v[8]: Vowel dominance              → step_size (stroke smoothness)
    v[9]: Vowel entropy / 3.0          → seed (deterministic randomness)
    v[10]: Raw rhythm (words/verse)    → max_length (stroke length)
    v[11]: Poet name length / 5.0      → width_start (stroke thickness)
    v[12]: Poet name diversity         → (currently unused)
    v[13]: Genre ID (0.0-1.0)          → color_palette selection
    
    Args:
        title: Titre du poème
        poem_text: Texte complet du poème
        poet: Nom du poète
        genre: Genre émotionnel (fear/anger/sadness/love/joy/surprise)
    
    Returns:
        np.array de 14 dimensions prêt pour render_embedding.py
    """
    print(f"=== ANALYSE POÈME {title[:30]}... ===")
    # print(f"Titre: {title}")
    # print(f"Poète: {poet}")
    # print(f"Genre: {genre}")
    
    # Combiner toutes les informations
    combined_text = f"{title} {poem_text} {poet}".lower().strip()
    words = combined_text.replace(',', ' ').replace('.', ' ').split()
    
    # print(f"Mots extraits (total): {len(words)}")
    # print(f"Premiers mots: {words[:10]}...")
    
    # Analyser chaque composant séparément
    title_words = title.lower().strip().split()
    poem_words = poem_text.lower().strip().replace(',', ' ').replace('.', ' ').split()
    poet_words = poet.lower().strip().split()
    
    # Caractéristiques rythmiques globales
    total_syllables = sum(count_syllables(word) for word in words)
    
    # Métriques par section
    title_syllables = sum(count_syllables(word) for word in title_words)
    poem_syllables = sum(count_syllables(word) for word in poem_words)
    poet_syllables = sum(count_syllables(word) for word in poet_words)
    
    # Génération des vecteurs (14 dimensions exactement)
    vectors = []
    
    # 1-2: Caractéristiques du TITRE (2 vecteurs)
    title_complexity = len(set(title_words)) / max(len(title_words), 1)  # Diversité lexicale
    vectors.extend([
        len(title_words) / 10.0,                    # Longueur du titre
        title_complexity,                           # Complexité lexicale du titre
    ])
    
    # 3-11: Caractéristiques du POÈME (9 vecteurs avec analyse poétique)
    
    # Séparer le poème en vers (lignes)
    # Méthode 1: Saut de ligne traditionnel
    verses = [line.strip() for line in poem_text.split('\n') if line.strip()]
    
    # Méthode 2: Si pas de sauts de ligne, essayer de détecter les vers par espaces multiples
    if len(verses) <= 1:
        # Essayer de diviser par espaces multiples (3+ espaces)
        verses = [verse.strip() for verse in re.split(r'   +', poem_text) if verse.strip()]
    
    # Méthode 3: Si toujours pas de vers, essayer par ponctuation forte + espaces
    if len(verses) <= 1:
        # Diviser par point/virgule suivi d'espaces
        verses = [verse.strip() for verse in re.split(r'[.;]\s+', poem_text) if verse.strip()]
    
    verse_count = len(verses)

    # Longueur et structure
    if verse_count > 0:
        words_per_verse = [len(verse.split()) for verse in verses]
        chars_per_verse = [len(verse) for verse in verses]
        avg_words_per_verse = sum(words_per_verse) / verse_count
        avg_chars_per_verse = sum(chars_per_verse) / verse_count
        
        # Écart-type des longueurs de vers
        if verse_count > 1:
            variance_words = sum((x - avg_words_per_verse)**2 for x in words_per_verse) / verse_count
            std_words_per_verse = variance_words**0.5
        else:
            std_words_per_verse = 0
    else:
        avg_words_per_verse = 0
        avg_chars_per_verse = 0
        std_words_per_verse = 0
    
    # Analyse des rimes (fins de vers)
    verse_endings = []
    for verse in verses:
        words = verse.strip().split()
        if words:
            # Prendre les 2-3 dernières lettres du dernier mot
            last_word = words[-1].lower()
            # Nettoyer la ponctuation
            last_word = re.sub(r'[^a-z]', '', last_word)
            if len(last_word) >= 2:
                ending = last_word[-2:]  # 2 dernières lettres
                verse_endings.append(ending)
    
    # Diversité des rimes
    unique_endings = len(set(verse_endings))
    rime_diversity = unique_endings / max(len(verse_endings), 1)
    
    # Rime la plus fréquente
    if verse_endings:
        ending_counts = Counter(verse_endings)
        most_common_freq = ending_counts.most_common(1)[0][1] / len(verse_endings)
    else:
        most_common_freq = 0
    
    # Allitération (bigrammes consonantiques)
    consonants = 'bcdfghjklmnpqrstvwxz'
    consonant_bigrams = []
    for word in poem_words:
        clean_word = re.sub(r'[^a-z]', '', word.lower())
        if len(clean_word) >= 2 and clean_word[0] in consonants:
            for i in range(len(clean_word) - 1):
                if clean_word[i] in consonants and clean_word[i+1] in consonants:
                    consonant_bigrams.append(clean_word[i:i+2])
    
    alliteration_score = 0
    if consonant_bigrams:
        bigram_counts = Counter(consonant_bigrams)
        repeated_bigrams = sum(1 for count in bigram_counts.values() if count > 1)
        alliteration_score = repeated_bigrams / len(consonant_bigrams)
    
    # Assonance (fréquence des voyelles)
    vowels = 'aeiouy'
    vowel_counts = {v: 0 for v in vowels}
    total_vowels = 0
    
    for verse in verses:
        clean_verse = re.sub(r'[^a-z]', '', verse.lower())
        for char in clean_verse:
            if char in vowels:
                vowel_counts[char] += 1
                total_vowels += 1
    
    # Dominance de la voyelle principale
    if total_vowels > 0:
        dominant_vowel_freq = max(vowel_counts.values()) / total_vowels
        vowel_entropy = sum(-(count/total_vowels) * np.log2(count/total_vowels + 1e-10) 
                          for count in vowel_counts.values() if count > 0)
    else:
        dominant_vowel_freq = 0
        vowel_entropy = 0
    

    vectors.extend([
        verse_count / 20.0,                        # Nombre de vers normalisé
        avg_words_per_verse / 10.0,               # Mots moyens par vers (RYTHME)
        std_words_per_verse / 5.0,                # Variabilité des vers
        rime_diversity,                           # Diversité des rimes
        most_common_freq,                         # Fréquence de la rime dominante
        alliteration_score,                       # Score d'allitération
        dominant_vowel_freq,                      # Dominance vocalique
        vowel_entropy / 3.0,                      # Entropie vocalique normalisée
        avg_words_per_verse,                      # Rythme brut (mots/vers non normalisé)
    ])
    
    # 12-13: Caractéristiques du POÈTE (2 vecteurs)
    poet_name_diversity = len(set(''.join(poet_words).lower())) / max(len(''.join(poet_words)), 1)  # Diversité des lettres
    vectors.extend([
        len(poet_words) / 5.0,                     # Longueur du nom du poète
        poet_name_diversity,                       # Complexité du nom du poète
    ])
    
    # 14: Caractéristique du GENRE (1 vecteur) - ID colormap
    def genre_to_colormap_id(genre_name):
        """
        Convertit un genre en ID de colormap (valeur numérique unique)
        
        Mapping exact des seuils utilisés par render_embedding.py:
        - < 0.2: Fear → bone (greyscale ominous)
        - < 0.3: Anger → hot (fire colors)
        - < 0.4: Sadness → PuBu (purple-blue)
        - < 0.5: Love → RdPu (red-purple)
        - < 0.6: Joy → rainbow (vibrant spectrum)
        - < 0.7: Surprise → cividis (yellow-blue)
        - >= 0.7: Default → grey (neutral)
        """
        genre_lower = genre_name.lower()
        
        # Mapping des genres vers des IDs numériques (centrés dans chaque plage)
        genre_id_mapping = {
            'fear': 0.1,        # Centre de [0.0, 0.2) → bone colormap
            'anger': 0.25,      # Centre de [0.2, 0.3) → hot colormap  
            'sadness': 0.35,    # Centre de [0.3, 0.4) → PuBu colormap
            'love': 0.45,       # Centre de [0.4, 0.5) → RdPu colormap
            'joy': 0.55,        # Centre de [0.5, 0.6) → rainbow colormap
            'surprise': 0.65,   # Centre de [0.6, 0.7) → cividis colormap
        }
        
        return genre_id_mapping.get(genre_lower, 0.75)  # 0.75 pour neutre/défaut → grey
    
    vectors.append(genre_to_colormap_id(genre))
    
    return np.array(vectors)

def load_and_process_file(file_path):
    """
    Charge un fichier CSV de poèmes et transforme TOUS les poèmes en vecteurs
    """
    
    try:
        # Charger le CSV avec le bon séparateur et encodage
        df = pd.read_csv(file_path, delimiter=';', encoding='latin-1')
        
        print(f"📚 Fichier chargé: {len(df)} poèmes trouvés")
        
        all_vectors = []
        all_metadata = []
        
        for i in range(len(df)):
            try:
                poem = df.iloc[i]
                title = poem['Title']
                poem_text = poem['Poem']
                poet = poem['Poet']
                genre = poem['Genre']
                
                print(f"\n📖 Poème {i+1}/{len(df)}: '{title}' par {poet}")
                
                # Transformer le poème en vecteurs
                vectors = simple_text_to_vectors(title, poem_text, poet, genre)
                
                # Stocker les résultats
                all_vectors.append(vectors)
                all_metadata.append({
                    'index': i,
                    'title': title,
                    'poet': poet,
                    'genre': genre,
                    'poem_length': len(poem_text)
                })
                
                if (i + 1) % 10 == 0:
                    print(f"✅ Progression: {i+1}/{len(df)} poèmes traités")
                    
            except Exception as e:
                print(f"❌ Erreur avec le poème {i+1}: {e}")
                continue
        
        print(f"\n🎉 Traitement terminé: {len(all_vectors)} poèmes transformés avec succès")
        
        # Sauvegarder les vecteurs en .npy
        vectors_array = np.array(all_vectors)
        
        return vectors_array, all_metadata
        
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier: {e}")
        return None, None

def save_vectors_to_csv(vectors_array, metadata_list):
    """
    Sauvegarde les vecteurs dans un fichier CSV simple avec titre et 14 dimensions
    """
    
    print(f"\n📊 Création du CSV simple avec titre et vecteurs...")
    
    # Créer le DataFrame avec seulement titre et vecteurs
    data_rows = []
    
    for i, (vectors, metadata) in enumerate(zip(vectors_array, metadata_list)):
        # Convertir le vecteur en liste formatée entre crochets
        vector_str = str(vectors.tolist())
        
        row = {
            'title': metadata['title'],
            'vector_14d': vector_str
        }
        
        data_rows.append(row)
    
    # Créer le DataFrame
    df = pd.DataFrame(data_rows)
    
    # Sauvegarder le CSV
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    os.makedirs(output_dir, exist_ok=True)
    csv_output_path = os.path.join(output_dir, "poem_vectors_simple.csv")
    df.to_csv(csv_output_path, index=False, encoding='utf-8')
    
    print(f"📄 CSV simple sauvegardé dans: {csv_output_path}")
    print(f"📊 Colonnes: {list(df.columns)}")
    print(f"📈 Nombre de lignes: {len(df)}")
    
    # Afficher un échantillon
    print(f"\n🎯 ÉCHANTILLON DU CSV (3 premières lignes):")
    for i, row in df.head(3).iterrows():
        print(f"   Titre: {row['title']}")
        print(f"   Vecteur: {row['vector_14d'][:100]}...")
    
    return csv_output_path

if __name__ == "__main__":
    import sys
    
    # Default path relative to project root
    default_csv = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'PoemsDataset_cleaned.csv')
    
    # Accept path as command line argument
    csv_path = sys.argv[1] if len(sys.argv) > 1 else default_csv
    
    if not os.path.exists(csv_path):
        print(f"❌ File not found: {csv_path}")
        print(f"Usage: python {sys.argv[0]} [path/to/poems.csv]")
        sys.exit(1)
    
    vectors, metadata = load_and_process_file(csv_path)
    
    if vectors is not None:
        output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        print(f"\n✅ Traitement complet terminé!")
        print(f"📐 Forme des vecteurs: {vectors.shape}")
        print(f"📁 Fichiers générés:")
        print(f"   - {os.path.join(output_dir, 'all_poem_vectors.npy')}")
        print(f"   - {os.path.join(output_dir, 'poem_vectors_simple.csv')}")
    else:
        print(f"❌ Échec du traitement")
