"""
Configuration centralisée pour le validateur JSON-LD
"""

# === VALIDATION PARAMETERS ===
MIN_SCORE_THRESHOLD = 80  # Score minimum pour acceptation (0-100)

# === SCORING WEIGHTS (total = 100%) ===
WEIGHTS = {
    'syntax_validation': 15,      # JSON valide + structure base
    'completeness': 30,            # % propriétés remplies
    'google_conformity': 25,       # Propriétés requises Google
    'semantic_richness': 20,       # sameAs, @id, imbrication
    'type_specificity': 10,        # Spécificité du type schema
}

# Bonus pour types prioritaires IA
AI_PRIORITY_TYPES_BONUS = 10

# Types de schema prioritaires pour les IA (bonus +10 points)
AI_PRIORITY_TYPES = [
    'FAQPage',
    'HowTo',
    'Article',
    'NewsArticle',
    'Product',
    'Organization',
    'QAPage',
]

# === SCRAPING PARAMETERS ===
REQUEST_TIMEOUT = 15  # secondes max par URL
RATE_LIMIT_DELAY = 2  # secondes entre chaque requête
MAX_RETRIES = 2       # nombre de tentatives si échec

USER_AGENT = 'AIDatasetBot/1.0 (JSON-LD Quality Dataset; +https://github.com/yourname/json-ld-validator)'

# Headers pour les requêtes
REQUEST_HEADERS = {
    'User-Agent': USER_AGENT,
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

# === VALIDATION RULES ===
# Propriétés minimum requises pour tout JSON-LD valide
REQUIRED_BASE_PROPERTIES = ['@context', '@type']

# Nombre minimum de propriétés au-delà de @context et @type
MIN_PROPERTIES_COUNT = 3

# Sources considérées comme "haute qualité" pour sameAs
QUALITY_SAME_AS_SOURCES = [
    'wikidata.org',
    'wikipedia.org',
    'linkedin.com',
    'facebook.com',
    'twitter.com',
    'instagram.com',
    'youtube.com',
]

# === OUTPUT SETTINGS ===
OUTPUT_DIR = 'output'
ACCEPTED_FILE = f'{OUTPUT_DIR}/accepted_local.jsonl'
REJECTED_FILE = f'{OUTPUT_DIR}/rejected_local.jsonl'
REPORT_FILE = f'{OUTPUT_DIR}/validation_report.md'
DETAILED_REPORT_FILE = f'{OUTPUT_DIR}/detailed_report.json'

# === ROBOTS.TXT ===
RESPECT_ROBOTS_TXT = True
ROBOTS_CACHE_DURATION = 3600  # 1 heure en cache

# === LOGGING ===
LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR
LOG_FILE = f'{OUTPUT_DIR}/scraping.log'

# === PROGRESS TRACKING ===
CHECKPOINT_INTERVAL = 100  # Sauvegarde tous les 100 URLs
ENABLE_PROGRESS_BAR = True
