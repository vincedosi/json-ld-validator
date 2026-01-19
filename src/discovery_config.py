"""
Configuration pour le Workflow 0 - Discovery
"""

# === DISCOVERY TARGETS ===
TARGET_TOTAL_URLS = 3500  # Objectif total d'URLs à découvrir
MAX_URLS_PER_TIER = {
    'gold': 100,      # Sites GOLD : jusqu'à 100 URLs chacun
    'high': 50,       # Sites HIGH : jusqu'à 50 URLs chacun
    'standard': 30    # Sites STANDARD : jusqu'à 30 URLs chacun
}

# === SITEMAP DISCOVERY ===
SITEMAP_TIMEOUT = 10  # secondes max pour récupérer un sitemap
SITEMAP_COMMON_PATHS = [
    '/sitemap.xml',
    '/sitemap_index.xml',
    '/sitemap-index.xml',
    '/post-sitemap.xml',
    '/page-sitemap.xml',
    '/product-sitemap.xml',
    '/recipe-sitemap.xml',
    '/article-sitemap.xml',
    '/news-sitemap.xml',
    '/robots.txt'  # Pour trouver le sitemap mentionné dans robots.txt
]

# Taille max d'un sitemap à parser (éviter les sitemaps géants)
MAX_SITEMAP_SIZE_MB = 50

# === URL PRE-SCORING ===
# Patterns universels prioritaires (tous sites)
UNIVERSAL_PRIORITY_PATTERNS = [
    '/faq', '/foire-aux-questions', '/questions-frequentes',
    '/aide', '/help', '/support',
    '/how-to', '/guide', '/tutoriel', '/tutorial'
]

# Patterns par type de contenu
CONTENT_TYPE_PATTERNS = {
    'faq': ['/faq', '/questions', '/q-a', '/aide', '/help'],
    'howto': ['/how-to', '/guide', '/tutorial', '/tutoriel', '/tuto'],
    'article': ['/article', '/blog', '/post', '/news', '/actualites'],
    'product': ['/product', '/p/', '/dp/', '/item/', '/produit'],
    'recipe': ['/recipe', '/recette', '/recipes', '/cooking'],
    'job': ['/job', '/jobs', '/emploi', '/career', '/careers'],
    'event': ['/event', '/events', '/evenement', '/salon'],
}

# === URL FILTERING ===
# Patterns à ÉVITER (URLs de mauvaise qualité)
EXCLUDE_PATTERNS = [
    '/tag/', '/tags/',
    '/author/', '/authors/', '/auteur/',
    '/category/', '/categories/', '/categorie/',
    '/page/', '/p/',
    '/search', '/recherche',
    '/login', '/signin', '/register',
    '/cart', '/checkout', '/panier',
    '/wp-content/', '/wp-admin/',
    '/feed/', '/rss/',
    '.pdf', '.jpg', '.png', '.gif', '.zip',
    '/cdn-cgi/',
    '/api/',
]

# Extensions de fichiers à ignorer
IGNORE_EXTENSIONS = [
    '.pdf', '.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp',
    '.zip', '.tar', '.gz', '.rar',
    '.mp3', '.mp4', '.avi', '.mov',
    '.css', '.js', '.xml', '.json'
]

# === URL DEPTH ===
# Profondeur optimale dans l'arborescence du site
OPTIMAL_DEPTH_MIN = 1  # Ex: /article (pas la homepage)
OPTIMAL_DEPTH_MAX = 4  # Ex: /category/subcategory/article

# === RATE LIMITING ===
DISCOVERY_RATE_LIMIT = 1  # secondes entre requêtes (plus rapide que le scraping)
DISCOVERY_TIMEOUT = 10    # secondes max par requête

# === OUTPUT ===
DISCOVERED_URLS_FILE = 'data/discovered_urls.json'
DISCOVERY_REPORT_FILE = 'output/discovery_report.md'
DISCOVERY_LOG_FILE = 'output/discovery.log'

# === CHECKPOINTING ===
DISCOVERY_CHECKPOINT_INTERVAL = 20  # Sauvegarder tous les 20 domaines
DISCOVERY_CHECKPOINT_FILE = 'output/discovery_checkpoint.json'

# === PRE-SCORING WEIGHTS ===
# Score de 0-100 pour prioriser les URLs avant scraping
PRE_SCORE_WEIGHTS = {
    'pattern_match': 40,      # Match avec patterns prioritaires
    'depth_optimal': 20,      # Profondeur optimale
    'url_cleanliness': 15,    # URL propre (pas de params complexes)
    'sitemap_priority': 15,   # Priorité indiquée dans sitemap
    'content_type_bonus': 10  # Type de contenu détecté
}

# Score minimum pour garder une URL
MIN_PRE_SCORE = 40  # Sur 100

# === LOGGING ===
DISCOVERY_LOG_LEVEL = 'INFO'
ENABLE_DISCOVERY_PROGRESS = True
