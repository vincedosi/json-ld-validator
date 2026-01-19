"""
Module de parsing de sitemaps XML
"""

import requests
import xml.etree.ElementTree as ET
import gzip
import logging
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Optional, Set
from io import BytesIO

from .discovery_config import (
    SITEMAP_TIMEOUT, SITEMAP_COMMON_PATHS,
    MAX_SITEMAP_SIZE_MB, DISCOVERY_RATE_LIMIT
)

logger = logging.getLogger(__name__)


class SitemapParser:
    """Parser de sitemaps XML avec support des sitemaps imbriqués"""
    
    def __init__(self, base_url: str, user_agent: str):
        self.base_url = base_url.rstrip('/')
        self.user_agent = user_agent
        self.parsed_sitemaps = set()  # Éviter les boucles infinies
        
    def find_sitemap_url(self) -> Optional[str]:
        """
        Trouve l'URL du sitemap principal
        Essaie plusieurs chemins communs + robots.txt
        """
        # 1. Vérifier robots.txt
        try:
            robots_url = urljoin(self.base_url, '/robots.txt')
            response = requests.get(
                robots_url,
                headers={'User-Agent': self.user_agent},
                timeout=SITEMAP_TIMEOUT
            )
            
            if response.status_code == 200:
                for line in response.text.split('\n'):
                    if line.lower().startswith('sitemap:'):
                        sitemap_url = line.split(':', 1)[1].strip()
                        logger.info(f"  Sitemap trouvé dans robots.txt: {sitemap_url}")
                        return sitemap_url
        except Exception as e:
            logger.debug(f"  Erreur lecture robots.txt: {e}")
        
        # 2. Essayer les chemins communs
        for path in SITEMAP_COMMON_PATHS:
            if path == '/robots.txt':
                continue
                
            sitemap_url = urljoin(self.base_url, path)
            try:
                response = requests.head(
                    sitemap_url,
                    headers={'User-Agent': self.user_agent},
                    timeout=SITEMAP_TIMEOUT,
                    allow_redirects=True
                )
                
                if response.status_code == 200:
                    logger.info(f"  Sitemap trouvé: {sitemap_url}")
                    return sitemap_url
            except:
                continue
        
        logger.warning(f"  Aucun sitemap trouvé pour {self.base_url}")
        return None
    
    def fetch_sitemap(self, sitemap_url: str) -> Optional[bytes]:
        """Récupère le contenu d'un sitemap"""
        try:
            response = requests.get(
                sitemap_url,
                headers={'User-Agent': self.user_agent},
                timeout=SITEMAP_TIMEOUT,
                stream=True
            )
            
            if response.status_code != 200:
                logger.warning(f"  Sitemap {sitemap_url} retourne {response.status_code}")
                return None
            
            # Vérifier la taille
            content_length = response.headers.get('content-length')
            if content_length and int(content_length) > MAX_SITEMAP_SIZE_MB * 1024 * 1024:
                logger.warning(f"  Sitemap trop gros: {content_length} bytes")
                return None
            
            content = response.content
            
            # Décompresser si gzip
            if sitemap_url.endswith('.gz') or response.headers.get('content-encoding') == 'gzip':
                try:
                    content = gzip.decompress(content)
                except:
                    pass
            
            return content
            
        except Exception as e:
            logger.error(f"  Erreur fetch sitemap {sitemap_url}: {e}")
            return None
    
    def parse_sitemap_xml(self, xml_content: bytes) -> Dict[str, List]:
        """
        Parse le XML d'un sitemap
        Retourne {'urls': [...], 'sitemaps': [...]}
        """
        result = {'urls': [], 'sitemaps': []}
        
        try:
            root = ET.fromstring(xml_content)
            
            # Détecter le namespace
            namespace = ''
            if root.tag.startswith('{'):
                namespace = root.tag.split('}')[0] + '}'
            
            # Parser sitemap index (contient d'autres sitemaps)
            for sitemap in root.findall(f'.//{namespace}sitemap'):
                loc_elem = sitemap.find(f'{namespace}loc')
                if loc_elem is not None and loc_elem.text:
                    result['sitemaps'].append(loc_elem.text.strip())
            
            # Parser URL set (contient des URLs)
            for url_elem in root.findall(f'.//{namespace}url'):
                loc_elem = url_elem.find(f'{namespace}loc')
                if loc_elem is not None and loc_elem.text:
                    url_data = {'loc': loc_elem.text.strip()}
                    
                    # Extraire lastmod si présent
                    lastmod_elem = url_elem.find(f'{namespace}lastmod')
                    if lastmod_elem is not None and lastmod_elem.text:
                        url_data['lastmod'] = lastmod_elem.text.strip()
                    
                    # Extraire priority si présent
                    priority_elem = url_elem.find(f'{namespace}priority')
                    if priority_elem is not None and priority_elem.text:
                        try:
                            url_data['priority'] = float(priority_elem.text.strip())
                        except:
                            url_data['priority'] = 0.5
                    else:
                        url_data['priority'] = 0.5
                    
                    result['urls'].append(url_data)
            
            return result
            
        except ET.ParseError as e:
            logger.error(f"  Erreur parsing XML: {e}")
            return result
        except Exception as e:
            logger.error(f"  Erreur inattendue parsing sitemap: {e}")
            return result
    
    def discover_all_urls(self, max_depth: int = 3) -> List[Dict]:
        """
        Découvre toutes les URLs depuis le sitemap principal
        Suit les sitemaps imbriqués jusqu'à max_depth
        
        Returns:
            List[{'url': str, 'priority': float, 'lastmod': str}]
        """
        all_urls = []
        
        # Trouver le sitemap principal
        main_sitemap = self.find_sitemap_url()
        if not main_sitemap:
            return all_urls
        
        # Parser récursivement
        to_parse = [(main_sitemap, 0)]  # (url, depth)
        
        while to_parse:
            sitemap_url, depth = to_parse.pop(0)
            
            # Éviter les boucles
            if sitemap_url in self.parsed_sitemaps:
                continue
            
            if depth > max_depth:
                logger.debug(f"  Max depth atteint pour {sitemap_url}")
                continue
            
            self.parsed_sitemaps.add(sitemap_url)
            logger.debug(f"  Parsing sitemap (depth {depth}): {sitemap_url}")
            
            # Fetch et parse
            xml_content = self.fetch_sitemap(sitemap_url)
            if not xml_content:
                continue
            
            parsed = self.parse_sitemap_xml(xml_content)
            
            # Ajouter les URLs trouvées
            for url_data in parsed['urls']:
                all_urls.append({
                    'url': url_data['loc'],
                    'priority': url_data.get('priority', 0.5),
                    'lastmod': url_data.get('lastmod', ''),
                    'source': 'sitemap'
                })
            
            # Ajouter les sous-sitemaps à parser
            for sub_sitemap in parsed['sitemaps']:
                to_parse.append((sub_sitemap, depth + 1))
        
        logger.info(f"  ✅ {len(all_urls)} URLs découvertes depuis sitemaps")
        return all_urls


def discover_urls_from_sitemap(
    domain_url: str,
    user_agent: str,
    max_urls: int = 1000
) -> List[Dict]:
    """
    Point d'entrée principal pour découvrir les URLs d'un domaine
    
    Args:
        domain_url: URL du domaine (ex: https://example.com)
        user_agent: User-Agent à utiliser
        max_urls: Nombre max d'URLs à retourner
    
    Returns:
        List[{'url': str, 'priority': float, 'lastmod': str, 'source': str}]
    """
    parser = SitemapParser(domain_url, user_agent)
    urls = parser.discover_all_urls()
    
    # Limiter si nécessaire
    if len(urls) > max_urls:
        # Trier par priorité décroissante
        urls.sort(key=lambda x: x.get('priority', 0.5), reverse=True)
        urls = urls[:max_urls]
        logger.info(f"  Limité à {max_urls} URLs (trié par priorité)")
    
    return urls
