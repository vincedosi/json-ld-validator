"""
JSON-LD Validator Package
Workflow 1: Local Validation
"""

__version__ = '1.0.0'
__author__ = 'AI Dataset Bot'

from .main import main
from .scraper import scrape_url
from .validator import validate_full
from .scorer import score_json_ld

__all__ = ['main', 'scrape_url', 'validate_full', 'score_json_ld']
