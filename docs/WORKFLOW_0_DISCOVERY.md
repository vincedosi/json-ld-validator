# 🔍 Workflow 0 : URL Discovery - Documentation Complète

## Vue d'ensemble

Le Workflow 0 est la **première étape** du pipeline de création de dataset JSON-LD. Il analyse 240 domaines de qualité pour découvrir et scorer 3500-4000 URLs prometteuses.

## 🎯 Objectifs

1. **Découvrir** les meilleures pages de chaque domaine via sitemap.xml
2. **Filtrer** selon des patterns intelligents (FAQ, HowTo, Article, Product, etc.)
3. **Scorer** chaque URL (0-100) selon sa probabilité de contenir du JSON-LD de qualité
4. **Sélectionner** les N meilleures URLs par domaine selon le tier

## 📊 Input : domains_master.json

### Structure

```json
{
  "meta": {
    "total_domains": 240,
    "target_urls": "3500-4000",
    "language_ratio": {"english": "60%", "french": "40%"}
  },
  "categories": {
    "Sante_Pharmacie_Medical": {
      "priority": 1,
      "expected_schema_types": ["MedicalWebPage", "Article", "FAQPage"],
      "discovery_config": {
        "max_urls_per_gold": 100,
        "max_urls_per_high": 50,
        "max_urls_per_standard": 30,
        "priority_patterns": ["/faq", "/diseases", "/health"],
        "use_sitemap": true
      },
      "domains": [
        {
          "url": "https://www.mayoclinic.org",
          "tier": "gold",
          "language": "en",
          "notes": "⭐ GOLD - Medical authority"
        }
      ]
    }
  }
}
```

### Tiers de Qualité

| Tier | Nombre | URLs Max | Taux Acceptation Estimé |
|------|--------|----------|-------------------------|
| **GOLD** | 20 domaines | 100 URLs | ~85% |
| **HIGH** | 40 domaines | 50 URLs | ~65% |
| **STANDARD** | 180 domaines | 30 URLs | ~45% |

## 🔧 Fonctionnement Détaillé

### Étape 1 : Discovery depuis Sitemap

Pour chaque domaine, le workflow :

1. **Cherche le sitemap principal**
   - Vérifie `/robots.txt`
   - Teste `/sitemap.xml`, `/sitemap_index.xml`, etc.
   
2. **Parse récursivement** tous les sitemaps trouvés
   - Suit les sitemap index
   - Extrait toutes les URLs
   - Récupère `priority` et `lastmod` si disponibles

3. **Limite par domaine**
   - GOLD : Max 300 URLs brutes
   - HIGH : Max 150 URLs brutes
   - STANDARD : Max 90 URLs brutes

### Étape 2 : Pre-Scoring (0-100 points)

Chaque URL est scorée selon 5 critères :

#### 1. Pattern Match (0-40 points)

**Patterns Universels Prioritaires** (+30 points max)
```
/faq, /help, /support, /how-to, /guide, /tutorial
```

**Patterns de Type de Contenu** (+10 points)
- FAQ: `/faq`, `/questions`, `/q-a`
- HowTo: `/how-to`, `/guide`, `/tutoriel`
- Article: `/article`, `/blog`, `/news`
- Product: `/product`, `/p/`, `/dp/`
- Recipe: `/recipe`, `/recette`
- Job: `/job`, `/emploi`, `/career`
- Event: `/event`, `/evenement`

**Patterns Spécifiques à la Catégorie** (+15 points max)
- Définis dans `discovery_config.priority_patterns`

#### 2. Profondeur Optimale (0-20 points)

| Profondeur | Score | Exemple |
|------------|-------|---------|
| 0 (homepage) | 5 | `example.com/` |
| 1 | 10 | `example.com/about` |
| **2-4 (optimal)** | **20** | `example.com/blog/article-title` |
| 5+ | Décroissant | Pénalité -3 par niveau |

#### 3. Propreté URL (0-15 points)

- **Sans paramètres** : 15 points
- **1-2 paramètres** : 12 points
- **3+ paramètres** : 7 points
- **Pénalités** :
  - Session ID / tracking : -5
  - URL > 150 chars : -3
  - Fragments (#) : -2

#### 4. Priorité Sitemap (0-15 points)

- Basé sur la balise `<priority>` du sitemap (0.0-1.0)
- Score = priority × 15

#### 5. Bonus Type de Contenu (0-10 points)

- **Types prioritaires IA** (FAQ, HowTo, Article, Recipe) : +10
- **Autres types détectés** : +5
- **Type inconnu** : 0

### Étape 3 : Filtrage

#### Exclusions Automatiques

**Patterns à Éviter**
```
/tag/, /author/, /category/, /page/,
/search, /login, /cart, /checkout,
/wp-content/, /feed/, /cdn-cgi/, /api/
```

**Extensions Ignorées**
```
.pdf, .jpg, .png, .zip, .mp3, .mp4, .css, .js
```

#### Seuil Minimum

- **Score minimum** : 40/100
- URLs en dessous → rejetées

### Étape 4 : Sélection Finale

1. **Trier** par score décroissant
2. **Limiter** au max_urls selon tier :
   - GOLD : 100 URLs
   - HIGH : 50 URLs
   - STANDARD : 30 URLs

## 📁 Outputs

### 1. discovered_urls.json

Format de chaque entrée :
```json
{
  "url": "https://www.mayoclinic.org/diseases-conditions/diabetes/faq",
  "pre_score": 87.5,
  "breakdown": {
    "pattern_match": 35.0,
    "depth_optimal": 20.0,
    "url_cleanliness": 15.0,
    "sitemap_priority": 12.5,
    "content_type_bonus": 10.0
  },
  "content_type": "faq",
  "should_exclude": false,
  "domain": "https://www.mayoclinic.org",
  "tier": "gold",
  "language": "en",
  "category": "Sante_Pharmacie_Medical",
  "expected_schema_types": ["MedicalWebPage", "FAQPage"],
  "lastmod": "2024-01-15",
  "source": "sitemap"
}
```

### 2. discovery_report.md

Contient :
- Résumé exécutif (total URLs, avg score)
- Stats par tier, langue, catégorie
- Distribution des scores
- Top 20 URLs par score
- Prochaines étapes

### 3. discovery.log

Logs détaillés de toute l'exécution

## ⚙️ Configuration

### Fichier : src/discovery_config.py

```python
# Objectifs
TARGET_TOTAL_URLS = 3500

# Limites par tier
MAX_URLS_PER_TIER = {
    'gold': 100,
    'high': 50,
    'standard': 30
}

# Scoring
MIN_PRE_SCORE = 40  # Score minimum pour garder une URL

# Rate limiting
DISCOVERY_RATE_LIMIT = 1  # secondes entre domaines
DISCOVERY_TIMEOUT = 10     # timeout par requête
```

## 🚀 Exécution

### Local

```bash
# Installation
pip install -r requirements.txt

# Exécution complète
python -m src.discovery data/domains_master.json

# Durée : 30-60 minutes
```

### GitHub Actions

```bash
# 1. Aller dans Actions tab
# 2. Sélectionner "Workflow 0 - URL Discovery"
# 3. Click "Run workflow"
# 4. Télécharger artifacts après completion
```

### Test Rapide

```bash
# Tester sur quelques domaines GOLD
python test_discovery.py

# Tester un domaine spécifique
python test_discovery.py https://www.mayoclinic.org
```

## 📊 Résultats Attendus

```
Input:  240 domaines
        ├─ 20 GOLD × 100 = 2000 URLs potentielles
        ├─ 40 HIGH × 50 = 2000 URLs potentielles
        └─ 180 STANDARD × 30 = 5400 URLs potentielles

Filter: Score minimum 40/100
        
Output: ~3500-4000 URLs sélectionnées
        ├─ ~1700 URLs de domaines GOLD (avg score ~75)
        ├─ ~1300 URLs de domaines HIGH (avg score ~65)
        └─ ~500 URLs de domaines STANDARD (avg score ~55)
```

## 🔗 Enchaînement avec Workflow 1

Une fois le Workflow 0 terminé :

```bash
# Lancer Workflow 1 sur les URLs découvertes
python -m src.main data/discovered_urls.json

# Résultat final attendu :
# ~2000-2500 URLs acceptées (score Workflow 1 ≥ 80)
```

## 🐛 Troubleshooting

### Problème : Peu d'URLs découvertes

**Solutions :**
- Vérifier que les domaines ont un sitemap.xml accessible
- Baisser `MIN_PRE_SCORE` temporairement
- Augmenter `MAX_URLS_PER_TIER`

### Problème : Trop d'URLs de mauvaise qualité

**Solutions :**
- Augmenter `MIN_PRE_SCORE` (ex: 50 au lieu de 40)
- Ajouter plus de patterns d'exclusion
- Affiner les `priority_patterns` par catégorie

### Problème : Timeouts fréquents

**Solutions :**
- Augmenter `DISCOVERY_TIMEOUT`
- Vérifier la connexion réseau
- Certains domaines peuvent bloquer les bots

## 📈 Optimisations Futures

- [ ] Fallback sur patterns si sitemap absent
- [ ] Cache des sitemaps pour reruns
- [ ] Parallélisation (multiprocessing)
- [ ] Support des sitemaps .gz compressés (déjà implémenté)
- [ ] Detection de duplicate content (même contenu, URLs différentes)

## 📞 Support

Questions ou problèmes ? Consultez :
- Le README principal
- Les logs dans `output/discovery.log`
- Le rapport `output/discovery_report.md`

---

**Prêt à découvrir des milliers d'URLs de qualité ! 🚀**
