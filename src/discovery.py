"""
Workflow 0 : Discovery - Script principal
Découvre et score les meilleures URLs depuis le fichier domains_master.json
"""

import json
import logging
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from tqdm import tqdm
from collections import defaultdict

from .discovery_config import (
    TARGET_TOTAL_URLS,
    MAX_URLS_PER_TIER,
    DISCOVERED_URLS_FILE,
    DISCOVERY_REPORT_FILE,
    DISCOVERY_LOG_FILE,
    DISCOVERY_CHECKPOINT_FILE,
    DISCOVERY_CHECKPOINT_INTERVAL,
    DISCOVERY_LOG_LEVEL,
    ENABLE_DISCOVERY_PROGRESS,
    DISCOVERY_RATE_LIMIT,
    MIN_PRE_SCORE
)
from .config import REQUEST_HEADERS
from .sitemap_parser import discover_urls_from_sitemap
from .url_prescorer import score_and_filter_urls


# Configuration logging
def setup_discovery_logging():
    """Configure le système de logging pour discovery"""
    Path('output').mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, DISCOVERY_LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(DISCOVERY_LOG_FILE, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )


logger = logging.getLogger(__name__)


def load_domains_master(filepath: str) -> Dict:
    """Charge le fichier domains_master.json"""
    logger.info(f"Chargement de {filepath}...")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Compter les domaines par tier
    tier_counts = defaultdict(int)
    total_domains = 0
    
    for category_name, category_data in data.get('categories', {}).items():
        for domain in category_data.get('domains', []):
            tier = domain.get('tier', 'standard')
            tier_counts[tier] += 1
            total_domains += 1
    
    logger.info(f"✅ {total_domains} domaines chargés")
    logger.info(f"   - GOLD: {tier_counts['gold']}")
    logger.info(f"   - HIGH: {tier_counts['high']}")
    logger.info(f"   - STANDARD: {tier_counts['standard']}")
    
    return data


def process_single_domain(
    domain_data: Dict,
    category_config: Dict,
    category_name: str
) -> List[Dict]:
    """
    Traite un domaine : découvre et score les URLs
    
    Returns:
        Liste des URLs découvertes et scorées
    """
    domain_url = domain_data['url']
    tier = domain_data.get('tier', 'standard')
    language = domain_data.get('language', 'en')
    
    logger.info(f"\n{'='*70}")
    logger.info(f"🔍 Analyse de: {domain_url}")
    logger.info(f"   Tier: {tier.upper()} | Langue: {language} | Catégorie: {category_name}")
    logger.info('='*70)
    
    # Déterminer le nombre max d'URLs pour ce tier
    max_urls_for_tier = category_config.get('discovery_config', {}).get(
        f'max_urls_per_{tier}',
        MAX_URLS_PER_TIER.get(tier, 30)
    )
    
    logger.info(f"📊 Target: {max_urls_for_tier} URLs max")
    
    # 1. Découvrir les URLs depuis le sitemap
    logger.info("📡 Discovery depuis sitemap...")
    discovered_urls = discover_urls_from_sitemap(
        domain_url,
        REQUEST_HEADERS['User-Agent'],
        max_urls=max_urls_for_tier * 3  # Découvrir plus, filtrer ensuite
    )
    
    if not discovered_urls:
        logger.warning(f"❌ Aucune URL découverte pour {domain_url}")
        return []
    
    logger.info(f"✅ {len(discovered_urls)} URLs brutes découvertes")
    
    # 2. Récupérer les patterns spécifiques à la catégorie
    category_patterns = category_config.get('discovery_config', {}).get('priority_patterns', [])
    
    # 3. Scorer et filtrer les URLs
    logger.info("🎯 Scoring et filtrage...")
    scored_urls = score_and_filter_urls(
        discovered_urls,
        category_patterns=category_patterns,
        min_score=MIN_PRE_SCORE,
        max_urls=max_urls_for_tier
    )
    
    if not scored_urls:
        logger.warning(f"⚠️  Aucune URL n'a passé le filtrage (min_score={MIN_PRE_SCORE})")
        return []
    
    # 4. Enrichir avec les métadonnées du domaine
    for url_data in scored_urls:
        url_data.update({
            'domain': domain_url,
            'tier': tier,
            'language': language,
            'category': category_name,
            'expected_schema_types': category_config.get('expected_schema_types', [])
        })
    
    # Afficher quelques stats
    avg_score = sum(u['pre_score'] for u in scored_urls) / len(scored_urls)
    content_types = defaultdict(int)
    for u in scored_urls:
        content_types[u['content_type']] += 1
    
    logger.info(f"✅ {len(scored_urls)} URLs sélectionnées")
    logger.info(f"   Score moyen: {avg_score:.1f}/100")
    logger.info(f"   Types détectés: {dict(content_types)}")
    
    # Respect rate limit
    time.sleep(DISCOVERY_RATE_LIMIT)
    
    return scored_urls


def save_checkpoint(all_discovered_urls: List[Dict], processed_count: int):
    """Sauvegarde un checkpoint"""
    checkpoint_data = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'processed_domains': processed_count,
        'total_urls': len(all_discovered_urls),
        'urls': all_discovered_urls
    }
    
    with open(DISCOVERY_CHECKPOINT_FILE, 'w', encoding='utf-8') as f:
        json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"💾 Checkpoint sauvegardé: {processed_count} domaines, {len(all_discovered_urls)} URLs")


def generate_discovery_report(
    all_discovered_urls: List[Dict],
    total_domains: int,
    start_time: datetime,
    end_time: datetime
):
    """Génère le rapport Markdown de discovery"""
    
    duration = end_time - start_time
    
    # Stats par tier
    tier_stats = defaultdict(lambda: {'domains': 0, 'urls': 0, 'avg_score': []})
    for url_data in all_discovered_urls:
        tier = url_data.get('tier', 'standard')
        tier_stats[tier]['urls'] += 1
        tier_stats[tier]['avg_score'].append(url_data.get('pre_score', 0))
    
    # Stats par catégorie
    category_stats = defaultdict(lambda: {'urls': 0, 'domains': set()})
    for url_data in all_discovered_urls:
        cat = url_data.get('category', 'unknown')
        category_stats[cat]['urls'] += 1
        category_stats[cat]['domains'].add(url_data.get('domain', ''))
    
    # Stats par langue
    lang_stats = defaultdict(int)
    for url_data in all_discovered_urls:
        lang = url_data.get('language', 'en')
        lang_stats[lang] += 1
    
    # Stats par type de contenu
    content_type_stats = defaultdict(int)
    for url_data in all_discovered_urls:
        ctype = url_data.get('content_type', 'unknown')
        content_type_stats[ctype] += 1
    
    # Génération rapport
    report = f"""# 🔍 Discovery Report - Workflow 0

**Generated:** {end_time.strftime('%Y-%m-%d %H:%M:%S UTC')}  
**Duration:** {duration.total_seconds() / 60:.1f} minutes

---

## 🎯 Executive Summary

| Metric | Value |
|--------|-------|
| **Total Domains Processed** | {total_domains} |
| **Total URLs Discovered** | {len(all_discovered_urls)} |
| **Average Pre-Score** | {sum(u['pre_score'] for u in all_discovered_urls) / len(all_discovered_urls):.1f}/100 |
| **Target Met** | {'✅ YES' if len(all_discovered_urls) >= TARGET_TOTAL_URLS * 0.9 else '⚠️ PARTIAL'} |

---

## 📊 URLs by Quality Tier

| Tier | URLs | Avg Score | Domains |
|------|------|-----------|---------|
"""
    
    for tier in ['gold', 'high', 'standard']:
        stats = tier_stats[tier]
        if stats['urls'] > 0:
            avg = sum(stats['avg_score']) / len(stats['avg_score'])
            # Compter domaines uniques
            unique_domains = len(set(u['domain'] for u in all_discovered_urls if u.get('tier') == tier))
            report += f"| {tier.upper()} | {stats['urls']} | {avg:.1f}/100 | {unique_domains} |\n"
    
    report += f"""
---

## 🌍 URLs by Language

| Language | URLs | Percentage |
|----------|------|------------|
"""
    
    total_urls = len(all_discovered_urls)
    for lang, count in sorted(lang_stats.items(), key=lambda x: x[1], reverse=True):
        pct = count / total_urls * 100
        report += f"| {lang.upper()} | {count} | {pct:.1f}% |\n"
    
    report += f"""
---

## 📂 URLs by Category (Top 10)

| Category | URLs | Domains |
|----------|------|---------|
"""
    
    sorted_cats = sorted(category_stats.items(), key=lambda x: x[1]['urls'], reverse=True)[:10]
    for cat, stats in sorted_cats:
        report += f"| {cat} | {stats['urls']} | {len(stats['domains'])} |\n"
    
    report += f"""
---

## 🎨 URLs by Content Type

| Content Type | Count | Percentage |
|--------------|-------|------------|
"""
    
    for ctype, count in sorted(content_type_stats.items(), key=lambda x: x[1], reverse=True):
        pct = count / total_urls * 100
        report += f"| {ctype} | {count} | {pct:.1f}% |\n"
    
    report += f"""
---

## 🏆 Top 20 Highest Scoring URLs

| Rank | Score | Content Type | URL |
|------|-------|--------------|-----|
"""
    
    top_urls = sorted(all_discovered_urls, key=lambda x: x['pre_score'], reverse=True)[:20]
    for i, url_data in enumerate(top_urls, 1):
        url = url_data['url']
        display_url = url[:60] + '...' if len(url) > 60 else url
        report += f"| {i} | {url_data['pre_score']:.1f} | {url_data['content_type']} | {display_url} |\n"
    
    report += f"""
---

## 📁 Output Files

- ✅ **Discovered URLs:** `{DISCOVERED_URLS_FILE}` ({len(all_discovered_urls)} entries)
- 📊 **This Report:** `{DISCOVERY_REPORT_FILE}`
- 📝 **Discovery Log:** `{DISCOVERY_LOG_FILE}`

---

## 📈 Score Distribution

"""
    
    # Distribution des scores
    score_buckets = defaultdict(int)
    for u in all_discovered_urls:
        score = u['pre_score']
        bucket = int(score // 10) * 10
        score_buckets[bucket] += 1
    
    for bucket in sorted(score_buckets.keys(), reverse=True):
        count = score_buckets[bucket]
        bar = '█' * int(count / max(score_buckets.values()) * 50)
        report += f"{bucket}-{bucket+9} | {bar} {count}\n"
    
    report += f"""
---

## 🚀 Next Steps

1. **Review** the discovered URLs in `{DISCOVERED_URLS_FILE}`
2. **Run Workflow 1** (Validation) on these URLs:
   ```bash
   python -m src.main {DISCOVERED_URLS_FILE}
   ```
3. **Expected output:** ~{int(len(all_discovered_urls) * 0.6)}-{int(len(all_discovered_urls) * 0.7)} URLs accepted (score ≥80)

---

*Report generated by Discovery Workflow v1.0*
"""
    
    # Sauvegarder
    with open(DISCOVERY_REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write(report)
    
    logger.info(f"✅ Rapport sauvegardé: {DISCOVERY_REPORT_FILE}")


def main_discovery(domains_file: str):
    """
    Point d'entrée principal du Workflow 0
    """
    setup_discovery_logging()
    
    logger.info("=" * 70)
    logger.info("🚀 WORKFLOW 0: URL DISCOVERY")
    logger.info("=" * 70)
    
    start_time = datetime.utcnow()
    
    # 1. Charger les domaines
    domains_data = load_domains_master(domains_file)
    
    # 2. Préparer le traitement
    all_discovered_urls = []
    categories = domains_data.get('categories', {})
    
    total_domains = sum(len(cat.get('domains', [])) for cat in categories.values())
    processed_count = 0
    
    logger.info(f"\n🎯 Objectif: {TARGET_TOTAL_URLS} URLs à découvrir depuis {total_domains} domaines")
    logger.info("")
    
    # 3. Traiter chaque catégorie
    for category_name, category_data in categories.items():
        category_priority = category_data.get('priority', 2)
        domains = category_data.get('domains', [])
        
        if not domains:
            continue
        
        logger.info(f"\n{'#'*70}")
        logger.info(f"📂 CATÉGORIE: {category_name} (Priority {category_priority})")
        logger.info(f"   {len(domains)} domaines à traiter")
        logger.info('#'*70)
        
        # Iterator avec ou sans barre de progression
        domain_iter = enumerate(domains, 1)
        if ENABLE_DISCOVERY_PROGRESS:
            domain_iter = tqdm(domain_iter, total=len(domains), desc=f"{category_name}")
        
        # Traiter chaque domaine
        for i, domain_data in domain_iter:
            try:
                urls = process_single_domain(domain_data, category_data, category_name)
                all_discovered_urls.extend(urls)
                processed_count += 1
                
                # Checkpoint périodique
                if processed_count % DISCOVERY_CHECKPOINT_INTERVAL == 0:
                    save_checkpoint(all_discovered_urls, processed_count)
                
                # Vérifier si on a atteint l'objectif
                if len(all_discovered_urls) >= TARGET_TOTAL_URLS:
                    logger.info(f"\n🎯 Objectif atteint: {len(all_discovered_urls)} URLs !")
                    break
                
            except Exception as e:
                logger.error(f"❌ Erreur traitement {domain_data.get('url', 'unknown')}: {e}")
                continue
        
        if len(all_discovered_urls) >= TARGET_TOTAL_URLS:
            break
    
    # 4. Sauvegarder les résultats
    logger.info(f"\n{'='*70}")
    logger.info("💾 Sauvegarde des résultats...")
    
    # Sauvegarder le fichier final
    Path(DISCOVERED_URLS_FILE).parent.mkdir(parents=True, exist_ok=True)
    
    with open(DISCOVERED_URLS_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_discovered_urls, f, indent=2, ensure_ascii=False)
    
    logger.info(f"✅ {len(all_discovered_urls)} URLs sauvegardées: {DISCOVERED_URLS_FILE}")
    
    # 5. Générer le rapport
    end_time = datetime.utcnow()
    logger.info("\n📊 Génération du rapport...")
    generate_discovery_report(all_discovered_urls, processed_count, start_time, end_time)
    
    # 6. Résumé final
    duration = (end_time - start_time).total_seconds()
    
    logger.info(f"\n{'='*70}")
    logger.info("✅ DISCOVERY TERMINÉ")
    logger.info('='*70)
    logger.info(f"📊 Résumé:")
    logger.info(f"   - Domaines traités: {processed_count}/{total_domains}")
    logger.info(f"   - URLs découvertes: {len(all_discovered_urls)}")
    logger.info(f"   - Durée: {duration/60:.1f} minutes")
    logger.info(f"   - Vitesse: {len(all_discovered_urls)/(duration/60):.0f} URLs/minute")
    logger.info("")
    logger.info(f"📁 Fichiers générés:")
    logger.info(f"   - {DISCOVERED_URLS_FILE}")
    logger.info(f"   - {DISCOVERY_REPORT_FILE}")
    logger.info(f"   - {DISCOVERY_LOG_FILE}")
    logger.info("")
    logger.info(f"🚀 Prochaine étape: Workflow 1 (Validation)")
    logger.info(f"   python -m src.main {DISCOVERED_URLS_FILE}")
    logger.info('='*70)
    
    return 0


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python -m src.discovery data/domains_master.json")
        sys.exit(1)
    
    domains_file = sys.argv[1]
    
    if not Path(domains_file).exists():
        print(f"❌ Fichier introuvable: {domains_file}")
        sys.exit(1)
    
    exit_code = main_discovery(domains_file)
    sys.exit(exit_code)
