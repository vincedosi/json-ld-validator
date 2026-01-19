# 🔍 JSON-LD Validator - Complete Dataset Creation Pipeline

Outil automatisé en 2 workflows pour créer un dataset de haute qualité de JSON-LD optimisés pour le fine-tuning de LLMs.

## 🎯 Objectif

Créer un dataset de **1500-2000 exemples de JSON-LD de qualité exceptionnelle** (score ≥ 80/100) optimisés pour l'indexation par les IA (ChatGPT, Perplexity, Gemini, etc.).

## 🔄 Pipeline en 2 Workflows

### **Workflow 0 : Discovery** 🔍
Analyse 240 domaines et découvre 3500-4000 URLs prometteuses via sitemap.xml

### **Workflow 1 : Validation** ✅  
Scrape, valide et score les URLs découvertes pour créer le dataset final

## 📋 Workflow 0 : Discovery (URL Discovery)

### Objectif
Analyser 240 domaines de qualité et découvrir **3500-4000 URLs** prometteuses contenant potentiellement du JSON-LD de qualité.

### Fonctionnement
1. **Parse sitemap.xml** de chaque domaine
2. **Filtre** selon patterns prioritaires (FAQ, HowTo, Article, etc.)
3. **Score** chaque URL (0-100) selon :
   - Match avec patterns prioritaires (40%)
   - Profondeur optimale dans le site (20%)
   - Propreté de l'URL (15%)
   - Priorité sitemap (15%)
   - Type de contenu détecté (10%)
4. **Sélectionne** les N meilleures URLs par domaine :
   - Sites GOLD : 100 URLs max
   - Sites HIGH : 50 URLs max  
   - Sites STANDARD : 30 URLs max

### Input
`data/domains_master.json` - 240 domaines classés par tier et catégorie

### Output
- `data/discovered_urls.json` - 3500-4000 URLs scorées et prêtes
- `output/discovery_report.md` - Rapport détaillé
- `output/discovery.log` - Logs complets

### Exécution

**Local:**
```bash
python -m src.discovery data/domains_master.json
```

**GitHub Actions:**
1. Aller dans l'onglet "Actions"
2. Sélectionner "Workflow 0 - URL Discovery"
3. Cliquer "Run workflow"

**Durée:** ~30-60 minutes pour 240 domaines

---

## 📊 Scoring Criteria (Total: 100 points + bonus)

| Critère | Poids | Description |
|---------|-------|-------------|
| **Validation syntaxique** | 15% | JSON valide + structure JSON-LD correcte |
| **Complétude** | 30% | % de propriétés remplies (requises + recommandées) |
| **Conformité Google** | 25% | Propriétés requises selon Google présentes |
| **Richesse sémantique** | 20% | @id, sameAs, entités imbriquées |
| **Spécificité du type** | 10% | Utilisation du type le plus spécifique |
| **Bonus IA** | +10 | Types prioritaires (FAQPage, HowTo, Article, etc.) |

**Seuil d'acceptation:** ≥ 80/100

## 🚀 Installation

### Prérequis
- Python 3.9+
- Git

### Setup local

```bash
# Cloner le repo
git clone <votre-repo>
cd json-ld-validator

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt
```

## 📝 Configuration

### Fichier d'entrée: `data/input_urls.json`

Deux formats supportés:

**Format simple (liste d'URLs):**
```json
[
  "https://example.com/page1",
  "https://example.com/page2"
]
```

**Format enrichi (recommandé):**
```json
[
  {
    "url": "https://example.com/page1",
    "category": "ecommerce",
    "priority": 1,
    "note": "Product page example"
  }
]
```

### Paramètres: `src/config.py`

Personnalisable:
- `MIN_SCORE_THRESHOLD`: Seuil minimum (défaut: 80)
- `RATE_LIMIT_DELAY`: Délai entre requêtes (défaut: 2s)
- `REQUEST_TIMEOUT`: Timeout par URL (défaut: 15s)
- `RESPECT_ROBOTS_TXT`: Respecter robots.txt (défaut: True)

## 🔧 Utilisation

### Exécution locale

```bash
# Avec le fichier par défaut
python -m src.main data/input_urls.json

# Avec un fichier custom
python -m src.main path/to/your/urls.json
```

### Exécution via GitHub Actions

1. **Push votre fichier d'URLs** dans `data/input_urls.json`
2. **Aller dans l'onglet "Actions"** du repo GitHub
3. **Sélectionner "JSON-LD Local Validation"**
4. **Cliquer "Run workflow"**
5. **Optionnel:** Spécifier un fichier d'entrée différent

Les résultats seront disponibles dans les artifacts (~90 jours de rétention).

## 📁 Outputs

Tous les fichiers sont générés dans le dossier `output/`:

### 1. `accepted_local.jsonl` ✅
Dataset final des URLs acceptées (score ≥ 80).

**Format:**
```json
{
  "url": "https://example.com/page",
  "passed": true,
  "score": 87.5,
  "schema_type": "Article",
  "json_ld": {...},
  "breakdown": {
    "syntax": 15.0,
    "completeness": 26.0,
    "google_conformity": 22.5,
    "semantic_richness": 15.0,
    "type_specificity": 7.0,
    "ai_priority_bonus": 10.0
  },
  "validation_details": {...},
  "timestamp": "2024-01-16T10:30:00Z"
}
```

### 2. `rejected_local.jsonl` ❌
URLs rejetées avec raison.

**Format:**
```json
{
  "url": "https://bad-example.com",
  "passed": false,
  "rejection_reason": "score_too_low (72.3/80)",
  "score": 72.3,
  "timestamp": "2024-01-16T10:35:00Z"
}
```

### 3. `validation_report.md` 📊
Rapport Markdown détaillé avec:
- Résumé exécutif
- Breakdown par score, type de schema
- Raisons de rejet
- Top 10 des meilleures URLs
- Distribution des scores
- Recommandations

### 4. `detailed_report.json` 📈
Rapport JSON complet avec toutes les métriques pour analyse programmatique.

### 5. `scraping.log` 📝
Logs détaillés de l'exécution.

## 🏆 Sites "Gold Standard" Inclus

Le fichier `data/input_urls.json` contient 10 URLs de référence:

| Site | Type Schema | Performance Documentée |
|------|-------------|------------------------|
| Amazon | Product | Rich results standards |
| Food Network | Recipe | +35% traffic |
| The Guardian | NewsArticle | Author attribution gold standard |
| Eventbrite | Event | +100% growth |
| Nestlé | Organization | +82% CTR |
| StyleCraze | HowTo | +20% CTR |
| GOV.UK | Government | Public implementation docs |
| The Verge | Article | Clean implementation |
| Brainly | QAPage | Early adopter |
| Jobrapido | JobPosting | -15% bounce rate |

**Ajoutez vos propres URLs** en complétant ce fichier.

## 🔍 Détails Techniques

### Respect des bonnes pratiques

✅ **Robots.txt:** Vérifié avant chaque scraping  
✅ **Rate limiting:** 2 secondes entre requêtes (configurable)  
✅ **User-Agent:** Identifiable (`AIDatasetBot/1.0`)  
✅ **Timeout:** 15s max par URL avec retry (2x)  
✅ **Checkpoints:** Sauvegarde tous les 100 URLs  

### Validation en 5 couches

1. **Syntaxe JSON:** JSON valide + structure de base
2. **Structure JSON-LD:** @context + @type + schema.org
3. **Propriétés Schema.org:** Requises + recommandées par type
4. **Richesse sémantique:** @id, sameAs, imbrication
5. **Spécificité:** Type le plus précis de la hiérarchie

### Types Schema.org Supportés

50+ types incluant:
- Articles: Article, NewsArticle, BlogPosting
- Commerce: Product, Offer, Review, AggregateRating
- Food: Recipe, NutritionInformation
- QA: FAQPage, QAPage, Question, Answer, HowTo
- Events: Event, Place
- Jobs: JobPosting
- Organizations: Organization, LocalBusiness, Person
- Media: VideoObject, Book, SoftwareApplication
- Et plus...

## 📊 Exemples de Rapports

### Résumé typique

```
Total URLs scanned: 5000
✅ Accepted: 3421 (68.4%)
❌ Rejected: 1579 (31.6%)
⏱️ Duration: 3h 42m

Top rejection reasons:
- no_jsonld_found: 876 (55.5%)
- score_too_low: 432 (27.4%)
- invalid_json: 198 (12.5%)
```

### Score distribution

```
90-95: ████████████████████ 842
85-89: ████████████████████████████ 1234
80-84: ████████████ 1345
```

## 🔄 Workflow 2 (À venir)

Une fois les URLs acceptées, vous pourrez exécuter le **Workflow 2** qui:
- Lit `accepted_local.jsonl`
- Valide via l'API Google Rich Results Test
- Traite 200 URLs/jour (quota gratuit)
- Génère le dataset final ultra-qualité

## 🐛 Troubleshooting

### Problème: Trop de rejets (>70%)

**Solutions:**
- Vérifier que les URLs ont bien du JSON-LD
- Baisser le seuil dans `config.py` (ex: 70 au lieu de 80)
- Améliorer la qualité des URLs sources

### Problème: "Blocked by robots.txt"

**Solutions:**
- Vérifier le fichier robots.txt du site
- Désactiver temporairement: `RESPECT_ROBOTS_TXT = False` (déconseillé)

### Problème: Timeouts fréquents

**Solutions:**
- Augmenter `REQUEST_TIMEOUT` dans config.py
- Augmenter `MAX_RETRIES`

### Problème: Rate limited par les sites

**Solutions:**
- Augmenter `RATE_LIMIT_DELAY` (ex: 5 secondes)
- Traiter en plusieurs batches

## 📚 Ressources

- [Schema.org Vocabulary](https://schema.org)
- [Google Structured Data Guidelines](https://developers.google.com/search/docs/appearance/structured-data)
- [JSON-LD Specification](https://json-ld.org)

## 🤝 Contribution

Les PRs sont les bienvenues ! Notamment pour:
- Ajouter des types Schema.org
- Améliorer les règles de scoring
- Optimiser les performances
- Ajouter des tests

## 📄 License

MIT License - Libre d'utilisation pour vos projets de fine-tuning LLM.

## 🙏 Acknowledgments

Basé sur les guidelines officielles de:
- Schema.org
- Google Search Console
- Études de cas documentées (Eventbrite, Food Network, etc.)

---

**Prêt à créer votre dataset de qualité ? 🚀**

```bash
python -m src.main data/input_urls.json
```
