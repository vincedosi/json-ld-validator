# 📝 Guide pour préparer vos 5000 URLs

Ce fichier explique comment structurer votre liste d'URLs pour le scraping.

## Format du fichier: `data/input_urls.json`

### Option 1: Format simple (liste d'URLs)
```json
[
  "https://example.com/page1",
  "https://example.com/page2",
  "https://example.com/page3"
]
```

### Option 2: Format enrichi (RECOMMANDÉ)
```json
[
  {
    "url": "https://example.com/page1",
    "category": "ecommerce",
    "priority": 1,
    "note": "Product page with reviews"
  },
  {
    "url": "https://example.com/page2",
    "category": "blog",
    "priority": 2
  }
]
```

## 🎯 Sites Recommandés Déjà Inclus (10 URLs)

Le fichier `data/input_urls.json` contient déjà 10 URLs "gold standard":
1. Amazon - Product
2. Food Network - Recipe
3. The Guardian - NewsArticle
4. Eventbrite - Event
5. Nestlé - Organization
6. StyleCraze - HowTo
7. GOV.UK - Government
8. The Verge - Article
9. Brainly - QAPage
10. Jobrapido - JobPosting

## ➕ Comment ajouter vos URLs

### Méthode 1: Édition manuelle du JSON

Ouvrez `data/input_urls.json` et ajoutez vos URLs à la liste:

```json
[
  {
    "url": "https://www.amazon.com/dp/B08N5WRWNW",
    "category": "ecommerce",
    "priority": 1
  },
  {
    "url": "VOTRE_URL_ICI",
    "category": "VOTRE_CATEGORIE",
    "priority": 1
  }
]
```

### Méthode 2: Script Python pour générer depuis CSV/TXT

Si vous avez vos URLs dans un autre format, utilisez ce script:

```python
# convert_urls.py
import json
import csv

# Depuis un fichier TXT (une URL par ligne)
def from_txt(input_file, output_file):
    with open(input_file, 'r') as f:
        urls = [line.strip() for line in f if line.strip()]
    
    url_objects = [{"url": url} for url in urls]
    
    with open(output_file, 'w') as f:
        json.dump(url_objects, f, indent=2)
    
    print(f"✅ {len(urls)} URLs converties vers {output_file}")

# Depuis un fichier CSV
def from_csv(input_file, output_file):
    urls = []
    with open(input_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            urls.append({
                "url": row['url'],
                "category": row.get('category', 'uncategorized'),
                "priority": int(row.get('priority', 2))
            })
    
    with open(output_file, 'w') as f:
        json.dump(urls, f, indent=2)
    
    print(f"✅ {len(urls)} URLs converties vers {output_file}")

# Usage
# from_txt('mes_urls.txt', 'data/input_urls.json')
# from_csv('mes_urls.csv', 'data/input_urls.json')
```

### Méthode 3: Merge avec les URLs existantes

Pour ajouter vos URLs aux 10 déjà présentes:

```python
# merge_urls.py
import json

# Charger les URLs existantes
with open('data/input_urls.json', 'r') as f:
    existing_urls = json.load(f)

# Vos nouvelles URLs
new_urls = [
    {"url": "https://your-site.com/page1"},
    {"url": "https://your-site.com/page2"},
    # ... ajoutez vos 5000 URLs ici
]

# Merger
all_urls = existing_urls + new_urls

# Sauvegarder
with open('data/input_urls.json', 'w') as f:
    json.dump(all_urls, f, indent=2)

print(f"✅ Total: {len(all_urls)} URLs")
```

## 💡 Conseils pour sélectionner vos URLs

### ✅ Bonnes sources d'URLs

1. **Sites e-commerce bien établis**
   - Pages produits avec reviews
   - Exemple: Amazon, eBay, Shopify stores

2. **Médias et actualités**
   - Articles avec auteurs identifiés
   - Exemple: CNN, BBC, New York Times

3. **Sites de recettes**
   - Recettes détaillées
   - Exemple: AllRecipes, BBC Good Food

4. **Sites éducatifs**
   - Tutoriels, HowTo
   - Exemple: Khan Academy, WikiHow

5. **Sites d'événements**
   - Pages événements avec dates
   - Exemple: Meetup, Ticketmaster

6. **Sites gouvernementaux**
   - Souvent excellent schema
   - Exemple: .gov, .gouv.fr

### ❌ URLs à éviter

- Sites spam ou low-quality
- Pages d'erreur (404)
- Redirections infinies
- Sites bloquant les bots (robots.txt)
- Pages générées dynamiquement sans SSR
- Sites adult/gambling

## 🔍 Où trouver des URLs de qualité?

### 1. Google Search Console (si vous avez accès)
Exportez les URLs avec rich results

### 2. Sitemap XML
Récupérez le sitemap.xml des sites de référence

### 3. CommonCrawl
Dataset public d'URLs crawlées

### 4. Schema.org Examples
https://schema.org - exemples officiels

### 5. Google Structured Data Gallery
https://developers.google.com/search/docs/appearance/structured-data/search-gallery

## 📊 Stratégie de Priorisation

Ajoutez un champ `priority` pour traiter les meilleures URLs en premier:

- **Priority 1**: Sites gold standard, haute confiance
- **Priority 2**: Sites connus mais incertains
- **Priority 3**: Sites à tester

Le script peut ensuite trier par priorité.

## 🚀 Template Complet

Copiez ce template dans `data/input_urls.json`:

```json
[
  {
    "url": "https://www.amazon.com/dp/B08N5WRWNW",
    "category": "ecommerce",
    "priority": 1,
    "note": "Gold standard - Product"
  },
  {
    "url": "VOS_URLS_ICI",
    "category": "CATEGORIE",
    "priority": 1
  }
]
```

## ⚙️ Validation de votre fichier

Avant de lancer le scraping, validez votre JSON:

```bash
# Tester la syntaxe JSON
python -c "import json; json.load(open('data/input_urls.json'))"

# Compter les URLs
python -c "import json; print(f'{len(json.load(open(\"data/input_urls.json\")))} URLs')"
```

## 🎯 Prêt?

Une fois vos URLs ajoutées:

```bash
python -m src.main data/input_urls.json
```

---

**Questions? Problèmes?** Consultez le README.md
