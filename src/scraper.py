"""
Module de scraping pour extraire les JSON-LD depuis les URLs
"""

import requests
import json
import time
import logging
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from .config import (
    REQUEST_TIMEOUT, RATE_LIMIT_DELAY, MAX_RETRIES,
    REQUEST_HEADERS, RESPECT_ROBOTS_TXT, ROBOTS_CACHE_DURATION
)

logger = logging.getLogger(__name__)


class RobotsCache:
    """Cache pour les fichiers robots.txt"""
    def __init__(self):
        self.cache = {}
        self.timestamps = {}
    
    def get_parser(self, base_url: str) -> Optional[RobotFileParser]:
        """Récupère ou crée un parser robots.txt"""
        if base_url in self.cache:
            # Vérifier si le cache est encore valide
            if time.time() - self.timestamps[base_url] < ROBOTS_CACHE_DURATION:
                return self.cache[base_url]
        
        # Créer un nouveau parser
        try:
            rp = RobotFileParser()
            rp.set_url(urljoin(base_url, '/robots.txt'))
            rp.read()
            self.cache[base_url] = rp
            self.timestamps[base_url] = time.time()
            return rp
        except Exception as e:
            logger.warning(f"Impossible de lire robots.txt pour {base_url}: {e}")
            return None


# Instance globale du cache robots
robots_cache = RobotsCache()


def can_fetch_url(url: str, user_agent: str) -> Tuple[bool, str]:
    """
    Vérifie si l'URL peut être scrapée selon robots.txt
    
    Returns:
        (can_fetch, reason)
    """
    if not RESPECT_ROBOTS_TXT:
        return True, "robots.txt check disabled"
    
    try:
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        
        rp = robots_cache.get_parser(base_url)
        if rp is None:
            return True, "robots.txt not found or accessible"
        
        can_fetch = rp.can_fetch(user_agent, url)
        if not can_fetch:
            return False, "blocked by robots.txt"
        
        # Vérifier le Crawl-delay si présent
        crawl_delay = rp.crawl_delay(user_agent)
        if crawl_delay and crawl_delay > RATE_LIMIT_DELAY:
            logger.info(f"Crawl-delay for {base_url}: {crawl_delay}s")
        
        return True, "allowed by robots.txt"
        
    except Exception as e:
        logger.warning(f"Erreur vérification robots.txt pour {url}: {e}")
        return True, f"robots.txt check failed: {str(e)}"


def fetch_html(url: str, retry_count: int = 0) -> Tuple[Optional[str], str, int]:
    """
    Récupère le HTML d'une URL
    
    Returns:
        (html_content, status_message, http_status_code)
    """
    try:
        response = requests.get(
            url,
            headers=REQUEST_HEADERS,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True
        )
        
        if response.status_code == 200:
            return response.text, "success", 200
        else:
            return None, f"HTTP {response.status_code}", response.status_code
            
    except requests.Timeout:
        if retry_count < MAX_RETRIES:
            logger.warning(f"Timeout pour {url}, retry {retry_count + 1}/{MAX_RETRIES}")
            time.sleep(2)
            return fetch_html(url, retry_count + 1)
        return None, "timeout", 0
        
    except requests.RequestException as e:
        if retry_count < MAX_RETRIES:
            logger.warning(f"Erreur pour {url}, retry {retry_count + 1}/{MAX_RETRIES}: {e}")
            time.sleep(2)
            return fetch_html(url, retry_count + 1)
        return None, f"request_error: {str(e)}", 0
        
    except Exception as e:
        return None, f"unexpected_error: {str(e)}", 0


def extract_jsonld(html: str) -> List[Dict]:
    """
    Extrait tous les blocs JSON-LD d'une page HTML
    
    Returns:
        Liste des objets JSON-LD trouvés
    """
    jsonld_blocks = []
    
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Chercher tous les scripts de type application/ld+json
        scripts = soup.find_all('script', type='application/ld+json')
        
        for script in scripts:
            try:
                content = script.string
                if content:
                    # Parser le JSON
                    data = json.loads(content)
                    
                    # Gérer le cas d'un tableau de JSON-LD
                    if isinstance(data, list):
                        jsonld_blocks.extend(data)
                    else:
                        jsonld_blocks.append(data)
                        
            except json.JSONDecodeError as e:
                logger.warning(f"JSON invalide trouvé: {str(e)[:100]}")
                continue
                
    except Exception as e:
        logger.error(f"Erreur extraction JSON-LD: {e}")
    
    return jsonld_blocks


def scrape_url(url: str, enforce_rate_limit: bool = True) -> Dict:
    """
    Scrape une URL et extrait les JSON-LD
    
    Returns:
        {
            'url': str,
            'status': 'success'|'error',
            'error_reason': str (si erreur),
            'json_ld': List[Dict],
            'json_ld_count': int,
            'timestamp': str,
            'http_status': int
        }
    """
    result = {
        'url': url,
        'status': 'error',
        'error_reason': None,
        'json_ld': [],
        'json_ld_count': 0,
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'http_status': 0
    }
    
    # Vérifier robots.txt
    can_fetch, robots_reason = can_fetch_url(url, REQUEST_HEADERS['User-Agent'])
    if not can_fetch:
        result['error_reason'] = robots_reason
        logger.info(f"❌ {url} - {robots_reason}")
        return result
    
    # Respecter le rate limit
    if enforce_rate_limit:
        time.sleep(RATE_LIMIT_DELAY)
    
    # Fetch HTML
    html, status_msg, http_status = fetch_html(url)
    result['http_status'] = http_status
    
    if html is None:
        result['error_reason'] = status_msg
        logger.warning(f"❌ {url} - {status_msg}")
        return result
    
    # Extraire JSON-LD
    jsonld_blocks = extract_jsonld(html)
    
    if not jsonld_blocks:
        result['error_reason'] = 'no_jsonld_found'
        logger.info(f"⚠️  {url} - Pas de JSON-LD trouvé")
        return result
    
    # Succès
    result['status'] = 'success'
    result['json_ld'] = jsonld_blocks
    result['json_ld_count'] = len(jsonld_blocks)
    logger.info(f"✅ {url} - {len(jsonld_blocks)} JSON-LD trouvé(s)")
    
    return result


def scrape_urls_batch(urls: List[str], start_index: int = 0) -> List[Dict]:
    """
    Scrape un batch d'URLs avec gestion du rate limiting
    
    Args:
        urls: Liste des URLs à scraper
        start_index: Index de départ (pour reprendre après interruption)
    
    Returns:
        Liste des résultats
    """
    results = []
    total = len(urls)
    
    for i, url in enumerate(urls[start_index:], start=start_index):
        logger.info(f"[{i+1}/{total}] Scraping {url}")
        
        result = scrape_url(url)
        results.append(result)
    
    return results
