"""
Module de pré-scoring des URLs découvertes
Score de 0-100 pour prioriser les URLs avant le scraping complet
"""

import logging
from urllib.parse import urlparse, parse_qs
from typing import Dict, List

from .discovery_config import (
    UNIVERSAL_PRIORITY_PATTERNS,
    CONTENT_TYPE_PATTERNS,
    EXCLUDE_PATTERNS,
    IGNORE_EXTENSIONS,
    OPTIMAL_DEPTH_MIN,
    OPTIMAL_DEPTH_MAX,
    PRE_SCORE_WEIGHTS
)

logger = logging.getLogger(__name__)


def calculate_pattern_match_score(url: str, category_patterns: List[str] = None) -> float:
    """
    Score basé sur le match avec les patterns prioritaires
    Returns: 0-40 points
    """
    url_lower = url.lower()
    score = 0.0
    
    # Patterns universels (haute priorité)
    universal_matches = sum(1 for pattern in UNIVERSAL_PRIORITY_PATTERNS if pattern in url_lower)
    if universal_matches > 0:
        score += min(universal_matches * 15, 30)  # Max 30 points
    
    # Patterns de contenu (bonus)
    for content_type, patterns in CONTENT_TYPE_PATTERNS.items():
        if any(pattern in url_lower for pattern in patterns):
            score += 10  # +10 pour chaque type de contenu détecté
            break  # Une seule fois
    
    # Patterns spécifiques à la catégorie (si fournis)
    if category_patterns:
        category_matches = sum(1 for pattern in category_patterns if pattern.lower() in url_lower)
        if category_matches > 0:
            score += min(category_matches * 5, 15)
    
    return min(score, 40)  # Max 40 points


def calculate_depth_score(url: str) -> float:
    """
    Score basé sur la profondeur de l'URL dans l'arborescence
    Returns: 0-20 points
    """
    try:
        parsed = urlparse(url)
        path = parsed.path.strip('/')
        
        if not path:
            # Homepage
            return 5  # Peut avoir Organization schema, mais pas optimal
        
        depth = path.count('/') + 1
        
        if OPTIMAL_DEPTH_MIN <= depth <= OPTIMAL_DEPTH_MAX:
            # Profondeur optimale
            return 20
        elif depth < OPTIMAL_DEPTH_MIN:
            # Trop peu profond (mais mieux que homepage)
            return 10
        else:
            # Trop profond (pénalité croissante)
            penalty = (depth - OPTIMAL_DEPTH_MAX) * 3
            return max(0, 15 - penalty)
    
    except Exception as e:
        logger.debug(f"Erreur calcul depth pour {url}: {e}")
        return 5


def calculate_cleanliness_score(url: str) -> float:
    """
    Score basé sur la propreté de l'URL
    Returns: 0-15 points
    """
    score = 15.0
    
    try:
        parsed = urlparse(url)
        
        # Pénalité pour paramètres de requête
        query_params = parse_qs(parsed.query)
        if len(query_params) == 0:
            # Pas de params = parfait
            pass
        elif len(query_params) <= 2:
            # Peu de params = OK
            score -= 3
        else:
            # Beaucoup de params = mauvais signe
            score -= 8
        
        # Pénalité pour fragments
        if parsed.fragment:
            score -= 2
        
        # Pénalité pour URLs très longues
        if len(url) > 150:
            score -= 3
        elif len(url) > 200:
            score -= 5
        
        # Vérifier la présence de session IDs ou tracking params
        tracking_indicators = ['sessionid', 'sid', 'utm_', 'fbclid', 'gclid']
        if any(indicator in url.lower() for indicator in tracking_indicators):
            score -= 5
        
        return max(0, score)
        
    except Exception as e:
        logger.debug(f"Erreur calcul cleanliness pour {url}: {e}")
        return 5


def calculate_sitemap_priority_score(priority: float) -> float:
    """
    Score basé sur la priorité indiquée dans le sitemap
    Returns: 0-15 points
    """
    # priority va de 0.0 à 1.0
    return priority * 15


def detect_content_type(url: str) -> str:
    """
    Détecte le type de contenu probable depuis l'URL
    Returns: 'faq', 'howto', 'article', 'product', 'recipe', 'job', 'event', 'unknown'
    """
    url_lower = url.lower()
    
    for content_type, patterns in CONTENT_TYPE_PATTERNS.items():
        if any(pattern in url_lower for pattern in patterns):
            return content_type
    
    return 'unknown'


def calculate_content_type_bonus(url: str) -> float:
    """
    Bonus basé sur le type de contenu détecté
    Returns: 0-10 points
    """
    content_type = detect_content_type(url)
    
    # Types prioritaires pour les IA
    priority_types = ['faq', 'howto', 'article', 'recipe']
    
    if content_type in priority_types:
        return 10
    elif content_type != 'unknown':
        return 5
    else:
        return 0


def should_exclude_url(url: str) -> bool:
    """
    Vérifie si l'URL doit être exclue
    """
    url_lower = url.lower()
    
    # Vérifier les patterns d'exclusion
    if any(pattern in url_lower for pattern in EXCLUDE_PATTERNS):
        return True
    
    # Vérifier les extensions à ignorer
    if any(url_lower.endswith(ext) for ext in IGNORE_EXTENSIONS):
        return True
    
    return False


def pre_score_url(
    url: str,
    sitemap_priority: float = 0.5,
    category_patterns: List[str] = None
) -> Dict:
    """
    Calcule le score complet d'une URL
    
    Returns:
        {
            'url': str,
            'pre_score': float (0-100),
            'breakdown': {
                'pattern_match': float,
                'depth_optimal': float,
                'url_cleanliness': float,
                'sitemap_priority': float,
                'content_type_bonus': float
            },
            'content_type': str,
            'should_exclude': bool
        }
    """
    # Vérifier exclusion
    if should_exclude_url(url):
        return {
            'url': url,
            'pre_score': 0,
            'breakdown': {},
            'content_type': 'excluded',
            'should_exclude': True
        }
    
    # Calculer les composantes du score
    breakdown = {
        'pattern_match': calculate_pattern_match_score(url, category_patterns),
        'depth_optimal': calculate_depth_score(url),
        'url_cleanliness': calculate_cleanliness_score(url),
        'sitemap_priority': calculate_sitemap_priority_score(sitemap_priority),
        'content_type_bonus': calculate_content_type_bonus(url)
    }
    
    # Score total pondéré
    total_score = sum(breakdown.values())
    
    return {
        'url': url,
        'pre_score': round(total_score, 2),
        'breakdown': {k: round(v, 2) for k, v in breakdown.items()},
        'content_type': detect_content_type(url),
        'should_exclude': False
    }


def score_and_filter_urls(
    discovered_urls: List[Dict],
    category_patterns: List[str] = None,
    min_score: float = 40,
    max_urls: int = 100
) -> List[Dict]:
    """
    Score et filtre une liste d'URLs découvertes
    
    Args:
        discovered_urls: Liste de {'url': str, 'priority': float, ...}
        category_patterns: Patterns spécifiques à la catégorie
        min_score: Score minimum pour garder une URL
        max_urls: Nombre maximum d'URLs à retourner
    
    Returns:
        Liste des URLs scorées et filtrées, triées par score décroissant
    """
    scored_urls = []
    
    for url_data in discovered_urls:
        url = url_data['url']
        sitemap_priority = url_data.get('priority', 0.5)
        
        # Scorer l'URL
        score_result = pre_score_url(url, sitemap_priority, category_patterns)
        
        # Ignorer si exclu ou score trop bas
        if score_result['should_exclude']:
            continue
        
        if score_result['pre_score'] < min_score:
            continue
        
        # Ajouter les métadonnées du sitemap
        score_result.update({
            'lastmod': url_data.get('lastmod', ''),
            'source': url_data.get('source', 'sitemap')
        })
        
        scored_urls.append(score_result)
    
    # Trier par score décroissant
    scored_urls.sort(key=lambda x: x['pre_score'], reverse=True)
    
    # Limiter au nombre max
    if len(scored_urls) > max_urls:
        scored_urls = scored_urls[:max_urls]
    
    logger.info(f"  {len(scored_urls)} URLs après scoring et filtrage (min_score={min_score})")
    
    return scored_urls
