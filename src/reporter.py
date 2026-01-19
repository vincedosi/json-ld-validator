"""
Module de génération de rapports
"""

import json
import logging
from datetime import datetime
from typing import Dict, List
from collections import Counter, defaultdict

logger = logging.getLogger(__name__)


def generate_markdown_report(
    results: List[Dict],
    total_urls: int,
    start_time: datetime,
    end_time: datetime
) -> str:
    """
    Génère un rapport Markdown détaillé
    """
    duration = end_time - start_time
    
    # Séparer acceptés et rejetés
    accepted = [r for r in results if r.get('passed', False)]
    rejected = [r for r in results if not r.get('passed', False)]
    
    # Statistiques par raison de rejet
    rejection_reasons = Counter([r.get('rejection_reason', 'unknown') for r in rejected])
    
    # Statistiques par type de schema (acceptés)
    schema_types = Counter([r.get('schema_type', 'unknown') for r in accepted])
    
    # Statistiques par plage de score
    score_ranges = {
        '90-100': len([r for r in accepted if r.get('score', 0) >= 90]),
        '80-89': len([r for r in accepted if 80 <= r.get('score', 0) < 90]),
    }
    
    # Top 10 des URLs avec le meilleur score
    top_urls = sorted(
        [r for r in accepted if 'url' in r],
        key=lambda x: x.get('score', 0),
        reverse=True
    )[:10]
    
    # Génération du rapport
    report = f"""# 📊 JSON-LD Dataset Extraction Report

**Generated:** {end_time.strftime('%Y-%m-%d %H:%M:%S UTC')}  
**Duration:** {duration.total_seconds() / 3600:.2f} hours ({duration.total_seconds() / 60:.1f} minutes)

---

## 🎯 Executive Summary

| Metric | Value | Percentage |
|--------|-------|------------|
| **Total URLs Scanned** | {total_urls} | 100% |
| **✅ Accepted** | {len(accepted)} | {len(accepted)/total_urls*100:.1f}% |
| **❌ Rejected** | {len(rejected)} | {len(rejected)/total_urls*100:.1f}% |

### Quality Metrics
- **Average Score (Accepted):** {sum(r.get('score', 0) for r in accepted) / len(accepted):.2f}/100 (if accepted else 0)
- **Median Score (Accepted):** {sorted([r.get('score', 0) for r in accepted])[len(accepted)//2] if accepted else 0:.2f}/100

---

## 📈 Acceptance Breakdown

### By Score Range
| Range | Count | Percentage |
|-------|-------|------------|
| 90-100 (Excellent) | {score_ranges['90-100']} | {score_ranges['90-100']/len(accepted)*100 if accepted else 0:.1f}% |
| 80-89 (Good) | {score_ranges['80-89']} | {score_ranges['80-89']/len(accepted)*100 if accepted else 0:.1f}% |

### By Schema Type (Top 10)
| Schema Type | Count | Percentage |
|-------------|-------|------------|
"""
    
    for schema_type, count in schema_types.most_common(10):
        percentage = count / len(accepted) * 100 if accepted else 0
        report += f"| {schema_type} | {count} | {percentage:.1f}% |\n"
    
    report += f"""
---

## ❌ Rejection Breakdown

### By Reason
| Reason | Count | Percentage |
|--------|-------|------------|
"""
    
    for reason, count in rejection_reasons.most_common():
        percentage = count / len(rejected) * 100 if rejected else 0
        report += f"| {reason} | {count} | {percentage:.1f}% |\n"
    
    report += f"""
### Common Issues
"""
    
    # Analyse des warnings communs
    all_warnings = []
    for r in rejected:
        validation_details = r.get('validation_details', {})
        structure = validation_details.get('structure', {})
        all_warnings.extend(structure.get('warnings', []))
    
    warning_counter = Counter(all_warnings)
    for warning, count in warning_counter.most_common(5):
        percentage = count / len(rejected) * 100 if rejected else 0
        report += f"- **{warning}:** {count} occurrences ({percentage:.1f}%)\n"
    
    report += f"""
---

## 🏆 Top 10 Highest Scoring URLs

| Rank | Score | Schema Type | URL |
|------|-------|-------------|-----|
"""
    
    for i, url_data in enumerate(top_urls, 1):
        score = url_data.get('score', 0)
        schema_type = url_data.get('schema_type', 'Unknown')
        url = url_data.get('url', 'N/A')
        # Tronquer l'URL si trop longue
        display_url = url[:60] + '...' if len(url) > 60 else url
        report += f"| {i} | {score:.1f} | {schema_type} | {display_url} |\n"
    
    report += f"""
---

## 📁 Output Files

- ✅ **Accepted Dataset:** `output/accepted_local.jsonl` ({len(accepted)} entries)
- ❌ **Rejected URLs:** `output/rejected_local.jsonl` ({len(rejected)} entries)
- 📊 **Detailed Report:** `output/detailed_report.json` (full metrics)
- 📝 **This Report:** `output/validation_report.md`

---

## 📊 Score Distribution

### Accepted URLs Score Distribution
"""
    
    # Histogramme des scores
    score_buckets = defaultdict(int)
    for r in accepted:
        score = r.get('score', 0)
        bucket = int(score // 5) * 5  # Buckets de 5 points
        score_buckets[bucket] += 1
    
    for bucket in sorted(score_buckets.keys(), reverse=True):
        count = score_buckets[bucket]
        bar = '█' * int(count / max(score_buckets.values()) * 50)
        report += f"| {bucket}-{bucket+4} | {bar} {count}\n"
    
    report += f"""
---

## 🔍 Validation Statistics

### Syntax Validation
- **Valid JSON-LD:** {len([r for r in results if r.get('validation_details', {}).get('syntax', {}).get('is_valid', False)])}
- **Invalid JSON-LD:** {len([r for r in results if not r.get('validation_details', {}).get('syntax', {}).get('is_valid', False)])}

### Structure Validation
- **Valid Structure:** {len([r for r in results if r.get('validation_details', {}).get('structure', {}).get('is_valid', False)])}
- **Missing @context:** {len([r for r in results if '@context' in str(r.get('validation_details', {}).get('structure', {}).get('errors', []))])}
- **Missing @type:** {len([r for r in results if '@type' in str(r.get('validation_details', {}).get('structure', {}).get('errors', []))])}

### Semantic Richness (Accepted URLs)
- **With @id:** {len([r for r in accepted if r.get('validation_details', {}).get('richness', {}).get('has_id', False)])} ({len([r for r in accepted if r.get('validation_details', {}).get('richness', {}).get('has_id', False)]) / len(accepted) * 100 if accepted else 0:.1f}%)
- **With sameAs:** {len([r for r in accepted if r.get('validation_details', {}).get('richness', {}).get('has_same_as', False)])} ({len([r for r in accepted if r.get('validation_details', {}).get('richness', {}).get('has_same_as', False)]) / len(accepted) * 100 if accepted else 0:.1f}%)
- **With Quality Links:** {len([r for r in accepted if r.get('validation_details', {}).get('richness', {}).get('has_quality_links', False)])} ({len([r for r in accepted if r.get('validation_details', {}).get('richness', {}).get('has_quality_links', False)]) / len(accepted) * 100 if accepted else 0:.1f}%)

---

## 💡 Recommendations

"""
    
    # Recommandations basées sur les résultats
    if len(rejected) / total_urls > 0.5:
        report += "⚠️ **High rejection rate:** Consider adjusting the minimum score threshold or improving URL sources.\n\n"
    
    if rejection_reasons.get('no_jsonld_found', 0) > total_urls * 0.2:
        report += "⚠️ **Many URLs without JSON-LD:** Consider filtering URLs before scraping to ensure they have structured data.\n\n"
    
    if len(accepted) > 0:
        avg_score = sum(r.get('score', 0) for r in accepted) / len(accepted)
        if avg_score < 85:
            report += "💡 **Average score could be improved:** Focus on URLs with more complete Schema.org implementations.\n\n"
    
    report += f"""
---

## 📈 Next Steps

1. **Review** the accepted dataset in `accepted_local.jsonl`
2. **Analyze** rejected URLs to understand common issues
3. **Consider** running Workflow 2 (Google API validation) on accepted URLs for final quality check
4. **Fine-tune** your LLM with the high-quality dataset

---

*Report generated by JSON-LD Validator v1.0*
"""
    
    return report


def generate_detailed_json_report(
    results: List[Dict],
    total_urls: int,
    start_time: datetime,
    end_time: datetime
) -> Dict:
    """
    Génère un rapport JSON détaillé avec toutes les métriques
    """
    duration = (end_time - start_time).total_seconds()
    
    accepted = [r for r in results if r.get('passed', False)]
    rejected = [r for r in results if not r.get('passed', False)]
    
    return {
        'metadata': {
            'generated_at': end_time.isoformat() + 'Z',
            'start_time': start_time.isoformat() + 'Z',
            'end_time': end_time.isoformat() + 'Z',
            'duration_seconds': duration,
            'duration_hours': duration / 3600
        },
        'summary': {
            'total_urls': total_urls,
            'accepted_count': len(accepted),
            'rejected_count': len(rejected),
            'acceptance_rate': len(accepted) / total_urls if total_urls > 0 else 0,
            'rejection_rate': len(rejected) / total_urls if total_urls > 0 else 0
        },
        'scores': {
            'average': sum(r.get('score', 0) for r in accepted) / len(accepted) if accepted else 0,
            'median': sorted([r.get('score', 0) for r in accepted])[len(accepted)//2] if accepted else 0,
            'min': min([r.get('score', 0) for r in accepted]) if accepted else 0,
            'max': max([r.get('score', 0) for r in accepted]) if accepted else 0,
        },
        'schema_types': dict(Counter([r.get('schema_type', 'unknown') for r in accepted])),
        'rejection_reasons': dict(Counter([r.get('rejection_reason', 'unknown') for r in rejected])),
        'top_urls': [
            {
                'url': r.get('url'),
                'score': r.get('score'),
                'schema_type': r.get('schema_type')
            }
            for r in sorted(accepted, key=lambda x: x.get('score', 0), reverse=True)[:20]
        ]
    }


def save_reports(
    results: List[Dict],
    total_urls: int,
    start_time: datetime,
    end_time: datetime,
    markdown_path: str,
    json_path: str
):
    """
    Sauvegarde les rapports Markdown et JSON
    """
    # Génération Markdown
    logger.info("Génération du rapport Markdown...")
    markdown_report = generate_markdown_report(results, total_urls, start_time, end_time)
    
    with open(markdown_path, 'w', encoding='utf-8') as f:
        f.write(markdown_report)
    
    logger.info(f"✅ Rapport Markdown sauvegardé: {markdown_path}")
    
    # Génération JSON
    logger.info("Génération du rapport JSON détaillé...")
    json_report = generate_detailed_json_report(results, total_urls, start_time, end_time)
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_report, f, indent=2, ensure_ascii=False)
    
    logger.info(f"✅ Rapport JSON sauvegardé: {json_path}")
