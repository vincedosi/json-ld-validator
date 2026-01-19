"""
Module de validation JSON-LD
"""

import json
import logging
from typing import Dict, List, Tuple, Any
from .config import REQUIRED_BASE_PROPERTIES, MIN_PROPERTIES_COUNT
from .schema_rules import get_schema_rules, get_all_schema_types

logger = logging.getLogger(__name__)


class ValidationResult:
    """Résultat de validation avec détails"""
    def __init__(self):
        self.is_valid = False
        self.errors = []
        self.warnings = []
        self.info = {}
    
    def add_error(self, message: str):
        self.errors.append(message)
        self.is_valid = False
    
    def add_warning(self, message: str):
        self.warnings.append(message)
    
    def to_dict(self):
        return {
            'is_valid': self.is_valid,
            'errors': self.errors,
            'warnings': self.warnings,
            'info': self.info
        }


def validate_json_syntax(json_ld: Any) -> ValidationResult:
    """
    Valide la syntaxe JSON de base
    """
    result = ValidationResult()
    
    # Vérifier que c'est bien un dict (ou list de dicts)
    if not isinstance(json_ld, (dict, list)):
        result.add_error(f"JSON-LD doit être un objet ou un tableau, pas {type(json_ld).__name__}")
        return result
    
    # Si c'est une liste, valider chaque élément
    if isinstance(json_ld, list):
        if len(json_ld) == 0:
            result.add_error("Tableau JSON-LD vide")
            return result
        
        # Pour l'instant, on valide juste le premier élément
        # On pourrait valider tous les éléments mais ça complexifie
        json_ld = json_ld[0]
        result.add_warning("JSON-LD est un tableau, validation du premier élément uniquement")
    
    result.is_valid = True
    result.info['type'] = 'object'
    return result


def validate_jsonld_structure(json_ld: Dict) -> ValidationResult:
    """
    Valide la structure de base JSON-LD
    - Présence de @context
    - Présence de @type
    - Référence à schema.org
    """
    result = ValidationResult()
    
    # Vérifier @context
    if '@context' not in json_ld:
        result.add_error("Propriété '@context' manquante")
    else:
        context = json_ld['@context']
        # Vérifier que schema.org est référencé
        if 'schema.org' not in str(context).lower():
            result.add_warning("@context ne référence pas schema.org explicitement")
        result.info['context'] = context
    
    # Vérifier @type
    if '@type' not in json_ld:
        result.add_error("Propriété '@type' manquante")
    else:
        schema_type = json_ld['@type']
        result.info['schema_type'] = schema_type
        
        # Vérifier si le type est connu
        known_types = get_all_schema_types()
        if schema_type not in known_types:
            result.add_warning(f"Type '{schema_type}' non reconnu dans nos règles (peut être valide)")
    
    # Vérifier le nombre minimum de propriétés
    prop_count = len([k for k in json_ld.keys() if not k.startswith('@')])
    result.info['property_count'] = prop_count
    
    if prop_count < MIN_PROPERTIES_COUNT:
        result.add_warning(
            f"Seulement {prop_count} propriétés (minimum recommandé: {MIN_PROPERTIES_COUNT})"
        )
    
    # Si pas d'erreurs, marquer comme valide
    if len(result.errors) == 0:
        result.is_valid = True
    
    return result


def validate_schema_properties(json_ld: Dict, schema_type: str) -> ValidationResult:
    """
    Valide les propriétés selon les règles Schema.org/Google
    """
    result = ValidationResult()
    
    rules = get_schema_rules(schema_type)
    
    # Vérifier les propriétés requises
    missing_required = []
    for prop in rules.get('required', []):
        if prop not in json_ld:
            missing_required.append(prop)
    
    if missing_required:
        result.add_warning(f"Propriétés requises manquantes: {', '.join(missing_required)}")
    
    result.info['missing_required'] = missing_required
    result.info['required_count'] = len(rules.get('required', []))
    result.info['required_present'] = len(rules.get('required', [])) - len(missing_required)
    
    # Vérifier les propriétés recommandées
    missing_recommended = []
    for prop in rules.get('recommended', []):
        if prop not in json_ld:
            missing_recommended.append(prop)
    
    result.info['missing_recommended'] = missing_recommended
    result.info['recommended_count'] = len(rules.get('recommended', []))
    result.info['recommended_present'] = len(rules.get('recommended', [])) - len(missing_recommended)
    
    # Vérifier les types des propriétés imbriquées
    type_mismatches = []
    for prop, expected_types in rules.get('expected_types', {}).items():
        if prop in json_ld:
            value = json_ld[prop]
            if isinstance(value, dict) and '@type' in value:
                actual_type = value['@type']
                if actual_type not in expected_types:
                    type_mismatches.append({
                        'property': prop,
                        'expected': expected_types,
                        'actual': actual_type
                    })
    
    if type_mismatches:
        for mismatch in type_mismatches:
            result.add_warning(
                f"Propriété '{mismatch['property']}': type '{mismatch['actual']}' "
                f"(attendu: {', '.join(mismatch['expected'])})"
            )
    
    result.info['type_mismatches'] = type_mismatches
    result.is_valid = True
    
    return result


def check_semantic_richness(json_ld: Dict) -> Dict:
    """
    Évalue la richesse sémantique du JSON-LD
    
    Returns:
        {
            'has_id': bool,
            'has_same_as': bool,
            'same_as_count': int,
            'has_quality_links': bool,
            'nested_depth': int,
            'nested_entities_count': int
        }
    """
    from .config import QUALITY_SAME_AS_SOURCES
    
    richness = {
        'has_id': '@id' in json_ld,
        'has_same_as': 'sameAs' in json_ld,
        'same_as_count': 0,
        'has_quality_links': False,
        'nested_depth': 0,
        'nested_entities_count': 0
    }
    
    # Analyser sameAs
    if 'sameAs' in json_ld:
        same_as = json_ld['sameAs']
        if isinstance(same_as, list):
            richness['same_as_count'] = len(same_as)
            # Vérifier si des liens de qualité sont présents
            for link in same_as:
                if any(source in str(link).lower() for source in QUALITY_SAME_AS_SOURCES):
                    richness['has_quality_links'] = True
                    break
        elif isinstance(same_as, str):
            richness['same_as_count'] = 1
            if any(source in same_as.lower() for source in QUALITY_SAME_AS_SOURCES):
                richness['has_quality_links'] = True
    
    # Compter les entités imbriquées et la profondeur
    def analyze_nesting(obj, depth=0):
        max_depth = depth
        entity_count = 0
        
        if isinstance(obj, dict):
            if '@type' in obj:
                entity_count = 1
            
            for value in obj.values():
                sub_depth, sub_count = analyze_nesting(value, depth + 1)
                max_depth = max(max_depth, sub_depth)
                entity_count += sub_count
                
        elif isinstance(obj, list):
            for item in obj:
                sub_depth, sub_count = analyze_nesting(item, depth)
                max_depth = max(max_depth, sub_depth)
                entity_count += sub_count
        
        return max_depth, entity_count
    
    richness['nested_depth'], richness['nested_entities_count'] = analyze_nesting(json_ld)
    
    return richness


def get_type_specificity_score(schema_type: str) -> int:
    """
    Calcule un score de spécificité pour un type
    Plus le type est spécifique, plus le score est élevé
    
    Returns:
        Score de 0 à 10
    """
    rules = get_schema_rules(schema_type)
    parent_count = len(rules.get('parent_types', []))
    
    # Plus il y a de parents, plus le type est spécifique
    if parent_count >= 3:
        return 10
    elif parent_count == 2:
        return 7
    elif parent_count == 1:
        return 4
    else:
        return 1


def validate_full(json_ld: Dict) -> Tuple[bool, Dict]:
    """
    Validation complète d'un JSON-LD
    
    Returns:
        (is_valid, validation_details)
    """
    details = {
        'syntax': None,
        'structure': None,
        'properties': None,
        'richness': None,
        'schema_type': None,
        'specificity_score': 0
    }
    
    # 1. Validation syntaxique
    syntax_result = validate_json_syntax(json_ld)
    details['syntax'] = syntax_result.to_dict()
    
    if not syntax_result.is_valid:
        return False, details
    
    # Si c'était une liste, on prend le premier élément
    if isinstance(json_ld, list):
        json_ld = json_ld[0]
    
    # 2. Validation structure JSON-LD
    structure_result = validate_jsonld_structure(json_ld)
    details['structure'] = structure_result.to_dict()
    
    if not structure_result.is_valid:
        return False, details
    
    schema_type = structure_result.info.get('schema_type', 'Thing')
    details['schema_type'] = schema_type
    
    # 3. Validation propriétés Schema.org
    properties_result = validate_schema_properties(json_ld, schema_type)
    details['properties'] = properties_result.to_dict()
    
    # 4. Analyse richesse sémantique
    richness = check_semantic_richness(json_ld)
    details['richness'] = richness
    
    # 5. Score de spécificité
    details['specificity_score'] = get_type_specificity_score(schema_type)
    
    return True, details
