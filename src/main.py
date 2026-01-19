"""
Script principal d'orchestration de la validation JSON-LD
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict
from tqdm import tqdm

from .config import (
    OUTPUT_DIR, ACCEPTED_FILE, REJECTED_FILE, 
    REPORT_FILE, DETAILED_REPORT_FILE,
    LOG_FILE, LOG_LEVEL, CHECKPOINT_INTERVAL,
    ENABLE_PROGRESS_BAR
)
from .scraper import scrape_url
from .scorer import score_json_ld
from .reporter import save_reports


# Configuration du logging
def setup_logging():
    """Configure le système de logging"""
    # Créer le dossier output si nécessaire
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    # Configuration
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )


logger = logging.getLogger(__name__)


def load_urls(input_file: str) -> List[Dict]:
    """
    Charge les URLs depuis un fichier JSON
    
    Format attendu:
    [
        {"url": "https://example.com", "category": "ecommerce", "priority": 1},
        {"url": "https://example2.com"},
        ...
    ]
    
    ou simplement:
    ["https://example.com", "https://example2.com", ...]
    """
    logger.info(f"Chargement des URLs depuis {input_file}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Normaliser le format
    if isinstance(data, list):
        if len(data) == 0:
            raise ValueError("Le fichier d'entrée est vide")
        
        # Si liste de strings, convertir en liste de dicts
        if isinstance(data[0], str):
            urls = [{'url': url} for url in data]
        else:
            urls = data
    else:
        raise ValueError("Format d'entrée invalide. Attendu: liste de strings ou liste d'objets")
    
    logger.info(f"✅ {len(urls)} URLs chargées")
    return urls


def process_single_url(url_data: Dict) -> Dict:
    """
    Traite une URL complète: scraping + validation + scoring
    
    Returns:
        {
            'url': str,
            'passed': bool,
            'score': float,
            'schema_type': str,
            'json_ld': dict,
            'validation_details': dict,
            'breakdown': dict,
            'rejection_reason': str (si rejeté),
            'scrape_status': str,
            'timestamp': str
        }
    """
    url = url_data['url']
    result = {
        'url': url,
        'passed': False,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }
    
    # Métadonnées additionnelles si fournies
    if 'category' in url_data:
        result['category'] = url_data['category']
    if 'priority' in url_data:
        result['priority'] = url_data['priority']
    
    # 1. Scraping
    scrape_result = scrape_url(url)
    result['scrape_status'] = scrape_result['status']
    result['http_status'] = scrape_result['http_status']
    
    if scrape_result['status'] != 'success':
        result['rejection_reason'] = scrape_result['error_reason']
        return result
    
    # 2. Traiter chaque JSON-LD trouvé (on garde le meilleur score)
    json_lds = scrape_result['json_ld']
    
    best_score = 0
    best_result = None
    
    for json_ld in json_lds:
        try:
            score_result = score_json_ld(json_ld)
            
            if score_result['score'] > best_score:
                best_score = score_result['score']
                best_result = score_result
                best_result['json_ld'] = json_ld
        
        except Exception as e:
            logger.error(f"Erreur scoring JSON-LD pour {url}: {e}")
            continue
    
    if best_result is None:
        result['rejection_reason'] = 'scoring_failed'
        return result
    
    # 3. Mise à jour du résultat avec le meilleur JSON-LD
    result.update({
        'passed': best_result['passed'],
        'score': best_result['score'],
        'breakdown': best_result['breakdown'],
        'validation_details': best_result['validation_details'],
        'json_ld': best_result['json_ld'],
        'schema_type': best_result['validation_details'].get('schema_type', 'Unknown')
    })
    
    if not best_result['passed']:
        result['rejection_reason'] = best_result.get('rejection_reason', 'unknown')
    
    return result


def save_checkpoint(results: List[Dict], index: int):
    """Sauvegarde un checkpoint intermédiaire"""
    checkpoint_file = f"{OUTPUT_DIR}/checkpoint_{index}.json"
    with open(checkpoint_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    logger.info(f"💾 Checkpoint sauvegardé: {checkpoint_file}")


def save_results(results: List[Dict]):
    """
    Sauvegarde les résultats dans les fichiers de sortie
    """
    accepted = []
    rejected = []
    
    for result in results:
        if result.get('passed', False):
            accepted.append(result)
        else:
            rejected.append(result)
    
    # Sauvegarder acceptés
    logger.info(f"Sauvegarde de {len(accepted)} URLs acceptées...")
    with open(ACCEPTED_FILE, 'w', encoding='utf-8') as f:
        for item in accepted:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    # Sauvegarder rejetés
    logger.info(f"Sauvegarde de {len(rejected)} URLs rejetées...")
    with open(REJECTED_FILE, 'w', encoding='utf-8') as f:
        for item in rejected:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    logger.info(f"✅ Résultats sauvegardés:")
    logger.info(f"   - Acceptés: {ACCEPTED_FILE}")
    logger.info(f"   - Rejetés: {REJECTED_FILE}")


def main(input_file: str):
    """
    Point d'entrée principal
    """
    setup_logging()
    
    logger.info("=" * 60)
    logger.info("🚀 JSON-LD VALIDATOR - WORKFLOW 1: LOCAL VALIDATION")
    logger.info("=" * 60)
    
    start_time = datetime.utcnow()
    
    try:
        # 1. Charger les URLs
        url_data_list = load_urls(input_file)
        total_urls = len(url_data_list)
        
        logger.info(f"📊 Traitement de {total_urls} URLs...")
        
        # 2. Traiter chaque URL
        results = []
        
        iterator = enumerate(url_data_list, 1)
        if ENABLE_PROGRESS_BAR:
            iterator = tqdm(iterator, total=total_urls, desc="Processing URLs")
        
        for i, url_data in iterator:
            if ENABLE_PROGRESS_BAR:
                iterator.set_description(f"Processing {url_data['url'][:50]}...")
            
            result = process_single_url(url_data)
            results.append(result)
            
            # Checkpoint périodique
            if i % CHECKPOINT_INTERVAL == 0:
                save_checkpoint(results, i)
        
        # 3. Sauvegarder les résultats
        logger.info("\n" + "=" * 60)
        logger.info("💾 Sauvegarde des résultats...")
        save_results(results)
        
        # 4. Générer les rapports
        end_time = datetime.utcnow()
        logger.info("\n" + "=" * 60)
        logger.info("📊 Génération des rapports...")
        save_reports(results, total_urls, start_time, end_time, REPORT_FILE, DETAILED_REPORT_FILE)
        
        # 5. Résumé final
        accepted_count = len([r for r in results if r.get('passed', False)])
        rejected_count = len([r for r in results if not r.get('passed', False)])
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ TRAITEMENT TERMINÉ")
        logger.info("=" * 60)
        logger.info(f"📊 Résumé:")
        logger.info(f"   - Total URLs: {total_urls}")
        logger.info(f"   - ✅ Acceptées: {accepted_count} ({accepted_count/total_urls*100:.1f}%)")
        logger.info(f"   - ❌ Rejetées: {rejected_count} ({rejected_count/total_urls*100:.1f}%)")
        logger.info(f"   - ⏱️  Durée: {(end_time-start_time).total_seconds()/60:.1f} minutes")
        logger.info("")
        logger.info(f"📁 Fichiers générés:")
        logger.info(f"   - {ACCEPTED_FILE}")
        logger.info(f"   - {REJECTED_FILE}")
        logger.info(f"   - {REPORT_FILE}")
        logger.info(f"   - {DETAILED_REPORT_FILE}")
        logger.info("=" * 60)
        
        return 0
    
    except Exception as e:
        logger.error(f"❌ Erreur fatale: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python -m src.main <input_json_file>")
        print("Example: python -m src.main data/input_urls.json")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    if not os.path.exists(input_file):
        print(f"❌ Fichier introuvable: {input_file}")
        sys.exit(1)
    
    exit_code = main(input_file)
    sys.exit(exit_code)
