#!/usr/bin/env python
"""
Script utilitaire pour gérer les URLs
Usage:
  python scripts/url_manager.py merge <file1> <file2> -o output.json
  python scripts/url_manager.py validate <file>
  python scripts/url_manager.py stats <file>
  python scripts/url_manager.py deduplicate <file> -o output.json
"""

import json
import sys
from pathlib import Path
from urllib.parse import urlparse
from collections import Counter


def load_urls(filepath):
    """Charge les URLs depuis différents formats"""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Normaliser en liste d'objets
    if isinstance(data, list):
        if not data:
            return []
        if isinstance(data[0], str):
            return [{"url": url} for url in data]
        return data
    else:
        raise ValueError("Format non supporté")


def merge_urls(file1, file2, output):
    """Merge deux fichiers d'URLs"""
    urls1 = load_urls(file1)
    urls2 = load_urls(file2)
    
    merged = urls1 + urls2
    
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Merge réussi:")
    print(f"   - Fichier 1: {len(urls1)} URLs")
    print(f"   - Fichier 2: {len(urls2)} URLs")
    print(f"   - Total: {len(merged)} URLs")
    print(f"   - Sauvegardé: {output}")


def validate_urls(filepath):
    """Valide un fichier d'URLs"""
    print(f"🔍 Validation de {filepath}...")
    print()
    
    try:
        urls = load_urls(filepath)
        print(f"✅ JSON valide: {len(urls)} URLs chargées")
        print()
        
        # Vérifications
        issues = []
        
        # URLs vides
        empty_urls = [i for i, u in enumerate(urls) if not u.get('url')]
        if empty_urls:
            issues.append(f"⚠️ {len(empty_urls)} entrées sans URL")
        
        # URLs invalides
        invalid_urls = []
        for i, url_obj in enumerate(urls):
            url = url_obj.get('url', '')
            try:
                parsed = urlparse(url)
                if not parsed.scheme or not parsed.netloc:
                    invalid_urls.append((i, url))
            except:
                invalid_urls.append((i, url))
        
        if invalid_urls:
            issues.append(f"⚠️ {len(invalid_urls)} URLs malformées")
            for i, url in invalid_urls[:5]:  # Montrer les 5 premières
                print(f"   Ligne {i+1}: {url}")
        
        # Duplicatas
        url_list = [u.get('url') for u in urls if u.get('url')]
        duplicates = [url for url, count in Counter(url_list).items() if count > 1]
        if duplicates:
            issues.append(f"⚠️ {len(duplicates)} URLs dupliquées")
        
        # Résumé
        print()
        if not issues:
            print("✅ Aucun problème détecté!")
        else:
            print("⚠️ Problèmes détectés:")
            for issue in issues:
                print(f"   {issue}")
        
        return len(issues) == 0
        
    except json.JSONDecodeError as e:
        print(f"❌ Erreur JSON: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


def show_stats(filepath):
    """Affiche des statistiques sur les URLs"""
    urls = load_urls(filepath)
    
    print(f"📊 Statistiques pour {filepath}")
    print("=" * 50)
    print(f"Total URLs: {len(urls)}")
    print()
    
    # Par catégorie
    categories = Counter([u.get('category', 'uncategorized') for u in urls])
    if categories:
        print("Par catégorie:")
        for cat, count in categories.most_common():
            print(f"  - {cat}: {count} ({count/len(urls)*100:.1f}%)")
        print()
    
    # Par priorité
    priorities = Counter([u.get('priority', 'N/A') for u in urls])
    if priorities:
        print("Par priorité:")
        for pri, count in sorted(priorities.items()):
            print(f"  - Priority {pri}: {count}")
        print()
    
    # Par domaine
    domains = []
    for u in urls:
        try:
            parsed = urlparse(u.get('url', ''))
            domains.append(parsed.netloc)
        except:
            pass
    
    domain_counts = Counter(domains)
    print(f"Domaines uniques: {len(domain_counts)}")
    print("Top 10 domaines:")
    for domain, count in domain_counts.most_common(10):
        print(f"  - {domain}: {count}")


def deduplicate_urls(filepath, output):
    """Supprime les URLs dupliquées"""
    urls = load_urls(filepath)
    
    seen = set()
    unique = []
    duplicates = 0
    
    for url_obj in urls:
        url = url_obj.get('url')
        if url not in seen:
            seen.add(url)
            unique.append(url_obj)
        else:
            duplicates += 1
    
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(unique, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Déduplication réussie:")
    print(f"   - URLs originales: {len(urls)}")
    print(f"   - Duplicatas supprimés: {duplicates}")
    print(f"   - URLs uniques: {len(unique)}")
    print(f"   - Sauvegardé: {output}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'merge':
        if len(sys.argv) < 5 or sys.argv[4] != '-o':
            print("Usage: python url_manager.py merge <file1> <file2> -o <output>")
            sys.exit(1)
        merge_urls(sys.argv[2], sys.argv[3], sys.argv[5])
    
    elif command == 'validate':
        if len(sys.argv) < 3:
            print("Usage: python url_manager.py validate <file>")
            sys.exit(1)
        success = validate_urls(sys.argv[2])
        sys.exit(0 if success else 1)
    
    elif command == 'stats':
        if len(sys.argv) < 3:
            print("Usage: python url_manager.py stats <file>")
            sys.exit(1)
        show_stats(sys.argv[2])
    
    elif command == 'deduplicate':
        if len(sys.argv) < 5 or sys.argv[3] != '-o':
            print("Usage: python url_manager.py deduplicate <file> -o <output>")
            sys.exit(1)
        deduplicate_urls(sys.argv[2], sys.argv[4])
    
    else:
        print(f"Commande inconnue: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == '__main__':
    main()
