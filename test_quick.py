#!/usr/bin/env python
"""
Script de test rapide pour valider l'installation et le fonctionnement
"""

import sys
import json
from pathlib import Path

# Ajouter le dossier src au path
sys.path.insert(0, str(Path(__file__).parent))

from src.validator import validate_full
from src.scorer import score_json_ld


def test_validation():
    """Test de validation avec des exemples"""
    
    print("🧪 TEST 1: JSON-LD valide minimal")
    print("-" * 50)
    
    valid_minimal = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": "Test Article",
        "author": {
            "@type": "Person",
            "name": "John Doe"
        }
    }
    
    is_valid, details = validate_full(valid_minimal)
    print(f"✅ Validation: {is_valid}")
    print(f"Schema Type: {details.get('schema_type')}")
    print()
    
    print("🧪 TEST 2: Scoring d'un JSON-LD")
    print("-" * 50)
    
    score_result = score_json_ld(valid_minimal)
    print(f"Score: {score_result['score']}/100")
    print(f"Passed (≥80): {score_result['passed']}")
    print(f"Breakdown:")
    for key, value in score_result['breakdown'].items():
        print(f"  - {key}: {value}")
    print()
    
    print("🧪 TEST 3: JSON-LD riche avec bonus IA")
    print("-" * 50)
    
    rich_jsonld = {
        "@context": "https://schema.org",
        "@type": "FAQPage",  # Type prioritaire IA
        "@id": "https://example.com/faq#faqpage",
        "name": "FAQ About Our Service",
        "sameAs": [
            "https://www.wikidata.org/wiki/Q12345",
            "https://en.wikipedia.org/wiki/Example"
        ],
        "mainEntity": [
            {
                "@type": "Question",
                "name": "What is this?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "This is an example."
                }
            }
        ]
    }
    
    score_result = score_json_ld(rich_jsonld)
    print(f"Score: {score_result['score']}/100")
    print(f"Passed (≥80): {score_result['passed']}")
    print(f"AI Priority Bonus: {score_result['breakdown'].get('ai_priority_bonus', 0)}")
    print()
    
    print("🧪 TEST 4: JSON-LD invalide")
    print("-" * 50)
    
    invalid_jsonld = {
        "name": "Missing required fields"
        # Pas de @context ni @type
    }
    
    is_valid, details = validate_full(invalid_jsonld)
    print(f"❌ Validation: {is_valid}")
    if details.get('structure'):
        print(f"Errors: {details['structure'].get('errors', [])}")
    print()
    
    print("=" * 50)
    print("✅ Tous les tests passés avec succès!")
    print("=" * 50)
    print()
    print("📝 Prochaines étapes:")
    print("1. Ajouter vos URLs dans data/input_urls.json")
    print("2. Lancer: python -m src.main data/input_urls.json")
    print("3. Consulter les résultats dans output/")


if __name__ == '__main__':
    try:
        test_validation()
    except Exception as e:
        print(f"❌ Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
