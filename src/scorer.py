"""
Module de scoring pour évaluer la qualité des JSON-LD
"""

import logging
from typing import Dict
from .config import WEIGHTS, AI_PRIORITY_TYPES_BONUS
from .schema_rules import is_ai_priority_type

logger = logging.getLogger(__name__)


def calculate_syntax_score(validation_details: Dict) -> float:
    """
    Score de validation syntaxique (0-15 points)
    Pass/Fail critique
    """
    syntax = validation_details.get('syntax', {})
    
    if not syntax.get('is_valid', False):
        return 0.0
    
    # JSON valide = 15 points
    score = 15.0
    
    # Pénalité pour warnings
    warnings = syntax.get('warnings', [])
    score -= len(warnings) * 2
    
    return max(0, score)


def calculate_completeness_score(validation_details: Dict) -> float:
    """
    Score de complétude (0-30 points)
    Basé sur le % de propriétés remplies (requises + recommandées)
    """
    structure = validation_details.get('structure', {})
    properties = validation_details.get('properties', {})
    
    if not structure.get('is_valid', False):
        return 0.0
    
    info = properties.get('info', {})
    
    # Calculer le total de propriétés applicables
    required_count = info.get('required_count', 0)
    recommended_count = info.get('recommended_count', 0)
    total_applicable = required_count + recommended_count
    
    if total_applicable == 0:
        # Pas de règles spécifiques, utiliser le nombre de propriétés
        property_count = structure.get('info', {}).get('property_count', 0)
        # Score basé sur le nombre absolu
        score = min(property_count * 3, 30)
        return score
    
    # Calculer le % de propriétés remplies
    required_present = info.get('required_present', 0)
    recommended_present = info.get('recommended_present', 0)
    total_present = required_present + recommended_present
    
    completion_ratio = total_present / total_applicable
    
    # Score de 0 à 30 basé sur le ratio
    score = completion_ratio * 30
    
    return score


def calculate_google_conformity_score(validation_details: Dict) -> float:
    """
    Score de conformité Google (0-25 points)
    Basé sur les propriétés requises par Google
    """
    properties = validation_details.get('properties', {})
    
    if not properties.get('is_valid', False):
        return 0.0
    
    info = properties.get('info', {})
    
    required_count = info.get('required_count', 0)
    required_present = info.get('required_present', 0)
    
    if required_count == 0:
        # Pas de propriétés requises spécifiques
        return 15.0  # Score de base
    
    # Score basé sur le % de propriétés requises présentes
    conformity_ratio = required_present / required_count
    score = conformity_ratio * 25
    
    # Bonus si toutes les propriétés requises sont présentes
    if conformity_ratio == 1.0:
        score = 25.0
    
    return score


def calculate_semantic_richness_score(validation_details: Dict) -> float:
    """
    Score de richesse sémantique (0-20 points)
    - @id: +5 points
    - sameAs: +5 points
    - sameAs avec liens qualité: +5 points
    - Entités imbriquées: jusqu'à +5 points
    """
    richness = validation_details.get('richness', {})
    score = 0.0
    
    # @id présent
    if richness.get('has_id', False):
        score += 5
    
    # sameAs présent
    if richness.get('has_same_as', False):
        score += 5
        
        # Bonus pour liens de qualité
        if richness.get('has_quality_links', False):
            score += 5
    
    # Entités imbriquées
    nested_count = richness.get('nested_entities_count', 0)
    if nested_count > 1:
        # +1 point par entité imbriquée, max 5 points
        score += min(nested_count - 1, 5)
    
    return min(score, 20)


def calculate_type_specificity_score(validation_details: Dict) -> float:
    """
    Score de spécificité du type (0-10 points)
    Plus le type est spécifique dans la hiérarchie Schema.org, plus le score est élevé
    """
    specificity = validation_details.get('specificity_score', 0)
    return float(specificity)


def calculate_ai_priority_bonus(validation_details: Dict) -> float:
    """
    Bonus pour types prioritaires IA (+10 points max)
    """
    schema_type = validation_details.get('schema_type')
    
    if schema_type and is_ai_priority_type(schema_type):
        return AI_PRIORITY_TYPES_BONUS
    
    return 0.0


def calculate_final_score(validation_details: Dict) -> Dict:
    """
    Calcule le score final avec détails des composantes
    
    Returns:
        {
            'total_score': float (0-100+),
            'breakdown': {
                'syntax': float,
                'completeness': float,
                'google_conformity': float,
                'semantic_richness': float,
                'type_specificity': float,
                'ai_priority_bonus': float
            },
            'passed': bool (score >= threshold)
        }
    """
    breakdown = {
        'syntax': calculate_syntax_score(validation_details),
        'completeness': calculate_completeness_score(validation_details),
        'google_conformity': calculate_google_conformity_score(validation_details),
        'semantic_richness': calculate_semantic_richness_score(validation_details),
        'type_specificity': calculate_type_specificity_score(validation_details),
        'ai_priority_bonus': calculate_ai_priority_bonus(validation_details)
    }
    
    total_score = sum(breakdown.values())
    
    # Vérifier le seuil d'acceptation
    from .config import MIN_SCORE_THRESHOLD
    passed = total_score >= MIN_SCORE_THRESHOLD
    
    return {
        'total_score': round(total_score, 2),
        'breakdown': {k: round(v, 2) for k, v in breakdown.items()},
        'passed': passed
    }


def score_json_ld(json_ld: Dict) -> Dict:
    """
    Score complet d'un JSON-LD
    
    Returns:
        {
            'score': float,
            'breakdown': dict,
            'passed': bool,
            'validation_details': dict
        }
    """
    from .validator import validate_full
    
    # Validation complète
    is_valid, validation_details = validate_full(json_ld)
    
    if not is_valid:
        return {
            'score': 0.0,
            'breakdown': {},
            'passed': False,
            'validation_details': validation_details,
            'rejection_reason': 'validation_failed'
        }
    
    # Calcul du score
    score_result = calculate_final_score(validation_details)
    
    result = {
        'score': score_result['total_score'],
        'breakdown': score_result['breakdown'],
        'passed': score_result['passed'],
        'validation_details': validation_details
    }
    
    if not score_result['passed']:
        result['rejection_reason'] = f"score_too_low ({score_result['total_score']}/{MIN_SCORE_THRESHOLD})"
    
    return result
