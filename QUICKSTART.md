# 📁 Project Structure & Quick Start

## 🗂️ Architecture Complète

```
json-ld-validator/
│
├── 📂 src/                          # Code source
│   ├── __init__.py
│   │
│   ├── 🔍 WORKFLOW 0 - DISCOVERY
│   ├── discovery.py                 # Orchestrateur principal discovery
│   ├── discovery_config.py          # Config discovery
│   ├── sitemap_parser.py            # Parser de sitemaps XML
│   ├── url_prescorer.py             # Pre-scoring des URLs (0-100)
│   │
│   ├── ✅ WORKFLOW 1 - VALIDATION
│   ├── main.py                      # Orchestrateur principal validation
│   ├── config.py                    # Config validation
│   ├── scraper.py                   # Extraction JSON-LD depuis URLs
│   ├── validator.py                 # Validation JSON-LD
│   ├── scorer.py                    # Scoring final (0-100)
│   ├── schema_rules.py              # Règles Schema.org (50+ types)
│   └── reporter.py                  # Génération rapports
│
├── 📂 data/                         # Données d'entrée
│   ├── domains_master.json          # 240 domaines classés ⭐
│   ├── discovered_urls.json         # Output Workflow 0 → Input Workflow 1
│   ├── input_urls.json              # (legacy) 10 sites gold standard
│   └── URL_PREPARATION_GUIDE.md     # Guide préparation URLs
│
├── 📂 output/                       # Résultats (créé automatiquement)
│   │
│   ├── 🔍 WORKFLOW 0 OUTPUTS
│   ├── discovery_report.md          # Rapport discovery
│   ├── discovery.log                # Logs discovery
│   ├── discovery_checkpoint.json    # Checkpoints
│   │
│   ├── ✅ WORKFLOW 1 OUTPUTS
│   ├── accepted_local.jsonl         # 🎯 DATASET FINAL
│   ├── rejected_local.jsonl         # URLs rejetées
│   ├── validation_report.md         # Rapport validation
│   ├── detailed_report.json         # Métriques JSON
│   └── scraping.log                 # Logs scraping
│
├── 📂 .github/workflows/            # GitHub Actions
│   ├── discovery.yml                # Workflow 0 automation
│   └── local-validation.yml         # Workflow 1 automation
│
├── 📂 scripts/                      # Scripts utilitaires
│   └── url_manager.py               # Gestion URLs (merge, stats, etc.)
│
├── 📂 docs/                         # Documentation
│   └── WORKFLOW_0_DISCOVERY.md      # Doc détaillée Workflow 0
│
├── 📄 test_discovery.py             # Tests Workflow 0
├── 📄 test_quick.py                 # Tests Workflow 1
├── 📄 requirements.txt              # Dépendances Python
├── 📄 README.md                     # Documentation principale
└── 📄 .gitignore
```

## 🚀 Quick Start Guide

### 1️⃣ Installation

```bash
# Cloner le repo
git clone <votre-repo>
cd json-ld-validator

# Installer les dépendances
pip install -r requirements.txt
```

### 2️⃣ Workflow 0 : Discovery (Découverte d'URLs)

**🎯 Objectif :** Analyser 240 domaines → Découvrir 3500-4000 URLs

```bash
# Option A : Exécution complète (30-60 min)
python -m src.discovery data/domains_master.json

# Option B : Test rapide (quelques domaines)
python test_discovery.py

# Résultat :
# ✅ data/discovered_urls.json (3500-4000 URLs scorées)
# ✅ output/discovery_report.md (rapport complet)
```

### 3️⃣ Workflow 1 : Validation (Scraping + Scoring)

**🎯 Objectif :** Scraper les URLs découvertes → Créer dataset final

```bash
# Lancer sur les URLs découvertes
python -m src.main data/discovered_urls.json

# Durée : 2-4 heures pour 3500 URLs
# Rate limit : 2 secondes entre URLs

# Résultat :
# 🎯 output/accepted_local.jsonl (1500-2000 exemples)
# ✅ output/validation_report.md (rapport complet)
```

### 4️⃣ Via GitHub Actions

**Workflow 0 :**
1. Actions → "Workflow 0 - URL Discovery" → Run workflow
2. Télécharger `discovered_urls.json` depuis artifacts

**Workflow 1 :**
1. Actions → "JSON-LD Local Validation" → Run workflow
2. Télécharger `accepted_local.jsonl` depuis artifacts

## 📊 Pipeline Complet Visualisé

```
┌─────────────────────────────────────────────────────────────┐
│                    domains_master.json                      │
│                    240 domaines classés                     │
│              (20 GOLD, 40 HIGH, 180 STANDARD)              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                 🔍 WORKFLOW 0 : DISCOVERY                   │
│                                                             │
│  1. Parse sitemap.xml de chaque domaine                    │
│  2. Filtre par patterns (FAQ, HowTo, Article...)           │
│  3. Pre-score (0-100) chaque URL                          │
│  4. Sélectionne top N par domaine                         │
│                                                             │
│  Durée : 30-60 minutes                                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                 discovered_urls.json                        │
│                  3500-4000 URLs scorées                    │
│              (avg pre-score ~65/100)                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                ✅ WORKFLOW 1 : VALIDATION                   │
│                                                             │
│  1. Scrape HTML de chaque URL                             │
│  2. Extrait JSON-LD                                        │
│  3. Valide syntaxe + structure                            │
│  4. Score final (0-110)                                    │
│  5. Accepte si score ≥ 80                                 │
│                                                             │
│  Durée : 2-4 heures (rate limit 2s)                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              🎯 accepted_local.jsonl                        │
│                                                             │
│           DATASET FINAL : 1500-2000 exemples               │
│            JSON-LD de qualité exceptionnelle               │
│                  (score ≥ 80/100)                          │
│                                                             │
│         ✅ Prêt pour fine-tuning LLM                       │
└─────────────────────────────────────────────────────────────┘
```

## 🎯 Données Clés

### Input Principal
- **domains_master.json** : 240 domaines
  - 20 GOLD ⭐ (Amazon, Google, Guardian, etc.)
  - 40 HIGH (sites reconnus)
  - 180 STANDARD (sites de qualité)
  - Ratio : 60% EN / 40% FR

### Outputs Principaux

1. **discovered_urls.json** (Workflow 0)
   - 3500-4000 URLs
   - Pre-scorées (0-100)
   - Prêtes pour validation

2. **accepted_local.jsonl** (Workflow 1)
   - 1500-2000 exemples
   - JSON-LD score ≥ 80
   - Format : 1 JSON par ligne

## 🔧 Configuration Rapide

### Workflow 0 : `src/discovery_config.py`

```python
TARGET_TOTAL_URLS = 3500
MIN_PRE_SCORE = 40
DISCOVERY_RATE_LIMIT = 1  # secondes
```

### Workflow 1 : `src/config.py`

```python
MIN_SCORE_THRESHOLD = 80
RATE_LIMIT_DELAY = 2  # secondes
REQUEST_TIMEOUT = 15
```

## 📈 Performances Attendues

| Metric | Workflow 0 | Workflow 1 |
|--------|-----------|-----------|
| **Input** | 240 domaines | 3500 URLs |
| **Durée** | 30-60 min | 2-4 heures |
| **Output** | 3500-4000 URLs | 1500-2000 exemples |
| **Taux succès** | ~100% | ~60% |
| **Rate limit** | 1s/domaine | 2s/URL |

## 🐛 Troubleshooting Rapide

### Workflow 0

**Problème :** Peu d'URLs trouvées
```bash
# Vérifier les sitemaps manuellement
curl https://example.com/sitemap.xml

# Baisser le seuil minimum
MIN_PRE_SCORE = 30  # au lieu de 40
```

**Problème :** Timeouts
```bash
# Augmenter le timeout
DISCOVERY_TIMEOUT = 20  # au lieu de 10
```

### Workflow 1

**Problème :** Trop de rejets (>70%)
```bash
# Vérifier le rapport
cat output/validation_report.md

# Baisser le seuil si nécessaire
MIN_SCORE_THRESHOLD = 70  # au lieu de 80
```

**Problème :** Bloqué par robots.txt
```bash
# Désactiver temporairement (déconseillé)
RESPECT_ROBOTS_TXT = False
```

## 📚 Documentation Complète

- **README.md** : Vue d'ensemble
- **docs/WORKFLOW_0_DISCOVERY.md** : Discovery détaillé
- **data/URL_PREPARATION_GUIDE.md** : Préparer vos URLs
- **Logs** : `output/*.log` pour debugging

## ✅ Checklist de Production

- [ ] `pip install -r requirements.txt`
- [ ] Vérifier `data/domains_master.json` existe
- [ ] Lancer Workflow 0 : `python -m src.discovery data/domains_master.json`
- [ ] Vérifier output : `data/discovered_urls.json`
- [ ] Lancer Workflow 1 : `python -m src.main data/discovered_urls.json`
- [ ] Vérifier dataset : `output/accepted_local.jsonl`
- [ ] Consulter rapports : `output/*_report.md`
- [ ] 🎉 Fine-tuner votre LLM !

---

**Prêt à créer votre dataset de qualité ! 🚀**
