#!/usr/bin/env python
"""
Script de test rapide pour Workflow 0 - Discovery
Teste sur quelques domaines seulement
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.sitemap_parser import discover_urls_from_sitemap
from src.url_prescorer import score_and_filter_urls
from src.config import REQUEST_HEADERS


def test_single_domain(domain_url: str, max_urls: int = 20):
    """Test discovery sur un seul domaine"""
    print(f"\n{'='*70}")
    print(f"🧪 TEST DISCOVERY: {domain_url}")
    print('='*70)
    
    # 1. Discovery
    print("\n1️⃣ Discovery depuis sitemap...")
    discovered = discover_urls_from_sitemap(
        domain_url,
        REQUEST_HEADERS['User-Agent'],
        max_urls=max_urls * 2
    )
    
    print(f"   ✅ {len(discovered)} URLs brutes trouvées")
    
    if not discovered:
        print("   ❌ Aucune URL trouvée")
        return
    
    # Afficher quelques exemples
    print(f"\n   Exemples d'URLs découvertes:")
    for url_data in discovered[:5]:
        print(f"   - {url_data['url'][:80]}")
        print(f"     Priority: {url_data['priority']}")
    
    # 2. Scoring
    print(f"\n2️⃣ Scoring et filtrage...")
    scored = score_and_filter_urls(
        discovered,
        category_patterns=['/faq', '/help', '/guide'],
        min_score=40,
        max_urls=max_urls
    )
    
    print(f"   ✅ {len(scored)} URLs après filtrage")
    
    if not scored:
        print("   ⚠️  Aucune URL n'a passé le seuil minimum")
        return
    
    # 3. Stats
    print(f"\n3️⃣ Statistiques:")
    avg_score = sum(u['pre_score'] for u in scored) / len(scored)
    print(f"   - Score moyen: {avg_score:.1f}/100")
    print(f"   - Score max: {max(u['pre_score'] for u in scored):.1f}")
    print(f"   - Score min: {min(u['pre_score'] for u in scored):.1f}")
    
    # Types de contenu
    content_types = {}
    for u in scored:
        ct = u['content_type']
        content_types[ct] = content_types.get(ct, 0) + 1
    
    print(f"   - Types détectés: {content_types}")
    
    # 4. Top URLs
    print(f"\n4️⃣ Top 5 URLs par score:")
    for i, url_data in enumerate(scored[:5], 1):
        print(f"   {i}. Score {url_data['pre_score']:.1f} - {url_data['content_type']}")
        print(f"      {url_data['url'][:70]}...")


def test_multiple_domains():
    """Test sur plusieurs domaines de différents tiers"""
    
    test_domains = [
        ("https://www.mayoclinic.org", "GOLD - Medical"),
        ("https://www.gov.uk", "GOLD - Government"),
        ("https://stackoverflow.com", "GOLD - QA"),
        ("https://www.foodnetwork.com", "GOLD - Recipe"),
        ("https://www.amazon.com", "GOLD - Product"),
    ]
    
    print("\n" + "="*70)
    print("🧪 TEST DISCOVERY SUR DOMAINES GOLD")
    print("="*70)
    
    results = {}
    
    for domain_url, description in test_domains:
        print(f"\n\n{'#'*70}")
        print(f"Testing: {description}")
        print('#'*70)
        
        try:
            test_single_domain(domain_url, max_urls=15)
            results[domain_url] = "✅ Success"
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            results[domain_url] = f"❌ Error: {str(e)[:50]}"
    
    # Résumé
    print(f"\n\n{'='*70}")
    print("📊 RÉSUMÉ DES TESTS")
    print('='*70)
    
    for domain, status in results.items():
        print(f"{status} - {domain}")
    
    print("\n✅ Tests terminés!")


if __name__ == '__main__':
    if len(sys.argv) > 1:
        # Test un domaine spécifique
        domain = sys.argv[1]
        test_single_domain(domain)
    else:
        # Test sur plusieurs domaines
        test_multiple_domains()
