"""
Règles de validation Schema.org par type
Basé sur la documentation Google et Schema.org officielle
"""

# Structure: {
#   "SchemaType": {
#       "required": [...],          # Propriétés requises par Google
#       "recommended": [...],        # Propriétés recommandées
#       "expected_types": {...},    # Types attendus pour propriétés imbriquées
#       "parent_types": [...]       # Hiérarchie schema.org
#   }
# }

SCHEMA_RULES = {
    # === ARTICLES & NEWS ===
    "Article": {
        "required": ["headline", "image", "datePublished", "author"],
        "recommended": ["dateModified", "publisher", "description", "mainEntityOfPage"],
        "expected_types": {
            "author": ["Person", "Organization"],
            "publisher": ["Organization"],
            "image": ["ImageObject", "URL"],
        },
        "parent_types": ["CreativeWork", "Thing"]
    },
    
    "NewsArticle": {
        "required": ["headline", "image", "datePublished", "author"],
        "recommended": ["dateModified", "publisher", "description", "mainEntityOfPage"],
        "expected_types": {
            "author": ["Person", "Organization"],
            "publisher": ["Organization"],
            "image": ["ImageObject", "URL"],
        },
        "parent_types": ["Article", "CreativeWork", "Thing"]
    },
    
    "BlogPosting": {
        "required": ["headline", "image", "datePublished", "author"],
        "recommended": ["dateModified", "publisher", "description"],
        "expected_types": {
            "author": ["Person", "Organization"],
            "publisher": ["Organization"],
        },
        "parent_types": ["Article", "CreativeWork", "Thing"]
    },

    # === PRODUCTS & COMMERCE ===
    "Product": {
        "required": ["name"],
        "recommended": ["image", "description", "brand", "offers", "aggregateRating", "review", "sku", "gtin"],
        "expected_types": {
            "brand": ["Brand", "Organization"],
            "offers": ["Offer", "AggregateOffer"],
            "aggregateRating": ["AggregateRating"],
            "review": ["Review"],
        },
        "parent_types": ["Thing"]
    },
    
    "Offer": {
        "required": ["price", "priceCurrency"],
        "recommended": ["availability", "url", "priceValidUntil", "itemCondition"],
        "expected_types": {
            "seller": ["Organization", "Person"],
        },
        "parent_types": ["Intangible", "Thing"]
    },
    
    "AggregateRating": {
        "required": ["ratingValue", "ratingCount"],
        "recommended": ["bestRating", "worstRating"],
        "expected_types": {},
        "parent_types": ["Rating", "Intangible", "Thing"]
    },
    
    "Review": {
        "required": ["reviewRating", "author"],
        "recommended": ["datePublished", "reviewBody"],
        "expected_types": {
            "author": ["Person", "Organization"],
            "reviewRating": ["Rating"],
        },
        "parent_types": ["CreativeWork", "Thing"]
    },

    # === RECIPES & FOOD ===
    "Recipe": {
        "required": ["name", "image"],
        "recommended": [
            "author", "datePublished", "description", 
            "recipeIngredient", "recipeInstructions",
            "totalTime", "recipeCuisine", "recipeYield",
            "nutrition", "aggregateRating"
        ],
        "expected_types": {
            "author": ["Person", "Organization"],
            "nutrition": ["NutritionInformation"],
            "recipeInstructions": ["HowToStep", "HowToSection"],
            "aggregateRating": ["AggregateRating"],
        },
        "parent_types": ["HowTo", "CreativeWork", "Thing"]
    },
    
    "NutritionInformation": {
        "required": [],
        "recommended": ["calories", "fatContent", "proteinContent", "carbohydrateContent"],
        "expected_types": {},
        "parent_types": ["StructuredValue", "Intangible", "Thing"]
    },

    # === HOW-TO & FAQ ===
    "HowTo": {
        "required": ["name", "step"],
        "recommended": ["image", "totalTime", "estimatedCost", "supply", "tool"],
        "expected_types": {
            "step": ["HowToStep", "HowToSection"],
            "supply": ["HowToSupply", "Text"],
            "tool": ["HowToTool", "Text"],
        },
        "parent_types": ["CreativeWork", "Thing"]
    },
    
    "HowToStep": {
        "required": ["text"],
        "recommended": ["image", "name", "url"],
        "expected_types": {
            "image": ["ImageObject", "URL"],
        },
        "parent_types": ["CreativeWork", "Thing"]
    },
    
    "FAQPage": {
        "required": ["mainEntity"],
        "recommended": [],
        "expected_types": {
            "mainEntity": ["Question"],
        },
        "parent_types": ["WebPage", "CreativeWork", "Thing"]
    },
    
    "Question": {
        "required": ["name", "acceptedAnswer"],
        "recommended": ["author", "dateCreated"],
        "expected_types": {
            "acceptedAnswer": ["Answer"],
            "author": ["Person", "Organization"],
        },
        "parent_types": ["CreativeWork", "Thing"]
    },
    
    "Answer": {
        "required": ["text"],
        "recommended": ["author", "dateCreated", "upvoteCount"],
        "expected_types": {
            "author": ["Person", "Organization"],
        },
        "parent_types": ["CreativeWork", "Thing"]
    },
    
    "QAPage": {
        "required": ["mainEntity"],
        "recommended": [],
        "expected_types": {
            "mainEntity": ["Question"],
        },
        "parent_types": ["WebPage", "CreativeWork", "Thing"]
    },

    # === ORGANIZATIONS & PEOPLE ===
    "Organization": {
        "required": ["name"],
        "recommended": ["url", "logo", "contactPoint", "sameAs", "address"],
        "expected_types": {
            "logo": ["ImageObject", "URL"],
            "contactPoint": ["ContactPoint"],
            "address": ["PostalAddress"],
        },
        "parent_types": ["Thing"]
    },
    
    "LocalBusiness": {
        "required": ["name", "address"],
        "recommended": ["telephone", "openingHours", "geo", "priceRange", "image"],
        "expected_types": {
            "address": ["PostalAddress"],
            "geo": ["GeoCoordinates"],
        },
        "parent_types": ["Organization", "Thing"]
    },
    
    "Person": {
        "required": ["name"],
        "recommended": ["url", "image", "jobTitle", "worksFor", "sameAs", "email"],
        "expected_types": {
            "worksFor": ["Organization"],
            "image": ["ImageObject", "URL"],
        },
        "parent_types": ["Thing"]
    },

    # === EVENTS ===
    "Event": {
        "required": ["name", "startDate", "location"],
        "recommended": ["endDate", "image", "description", "offers", "performer", "organizer"],
        "expected_types": {
            "location": ["Place", "VirtualLocation"],
            "offers": ["Offer"],
            "performer": ["Person", "Organization"],
            "organizer": ["Person", "Organization"],
        },
        "parent_types": ["Thing"]
    },
    
    "Place": {
        "required": ["name"],
        "recommended": ["address", "geo"],
        "expected_types": {
            "address": ["PostalAddress"],
            "geo": ["GeoCoordinates"],
        },
        "parent_types": ["Thing"]
    },

    # === JOBS ===
    "JobPosting": {
        "required": ["title", "description", "datePosted", "hiringOrganization"],
        "recommended": [
            "baseSalary", "employmentType", "jobLocation",
            "validThrough", "qualifications", "responsibilities"
        ],
        "expected_types": {
            "hiringOrganization": ["Organization"],
            "jobLocation": ["Place"],
            "baseSalary": ["MonetaryAmount"],
        },
        "parent_types": ["Intangible", "Thing"]
    },

    # === COURSES & EDUCATION ===
    "Course": {
        "required": ["name", "description"],
        "recommended": ["provider", "offers", "hasCourseInstance"],
        "expected_types": {
            "provider": ["Organization"],
            "offers": ["Offer"],
        },
        "parent_types": ["CreativeWork", "Thing"]
    },

    # === VIDEO ===
    "VideoObject": {
        "required": ["name", "description", "thumbnailUrl", "uploadDate"],
        "recommended": ["duration", "contentUrl", "embedUrl", "interactionStatistic"],
        "expected_types": {
            "thumbnailUrl": ["ImageObject", "URL"],
        },
        "parent_types": ["MediaObject", "CreativeWork", "Thing"]
    },

    # === WEB PAGES ===
    "WebPage": {
        "required": ["name"],
        "recommended": ["url", "description", "breadcrumb"],
        "expected_types": {
            "breadcrumb": ["BreadcrumbList"],
        },
        "parent_types": ["CreativeWork", "Thing"]
    },
    
    "BreadcrumbList": {
        "required": ["itemListElement"],
        "recommended": [],
        "expected_types": {
            "itemListElement": ["ListItem"],
        },
        "parent_types": ["ItemList", "Intangible", "Thing"]
    },

    # === BOOKS ===
    "Book": {
        "required": ["name", "author"],
        "recommended": ["isbn", "bookFormat", "publisher", "datePublished", "aggregateRating"],
        "expected_types": {
            "author": ["Person", "Organization"],
            "publisher": ["Organization"],
        },
        "parent_types": ["CreativeWork", "Thing"]
    },

    # === SOFTWARE ===
    "SoftwareApplication": {
        "required": ["name"],
        "recommended": [
            "offers", "aggregateRating", "operatingSystem",
            "applicationCategory", "description"
        ],
        "expected_types": {
            "offers": ["Offer"],
            "aggregateRating": ["AggregateRating"],
        },
        "parent_types": ["CreativeWork", "Thing"]
    },

    # === GENERIC FALLBACK ===
    "Thing": {
        "required": [],
        "recommended": ["name", "description", "url", "image"],
        "expected_types": {},
        "parent_types": []
    },
    
    "CreativeWork": {
        "required": ["name"],
        "recommended": ["author", "datePublished", "description"],
        "expected_types": {
            "author": ["Person", "Organization"],
        },
        "parent_types": ["Thing"]
    },
}


def get_schema_rules(schema_type):
    """
    Récupère les règles pour un type donné, avec fallback sur les parents
    """
    if schema_type in SCHEMA_RULES:
        return SCHEMA_RULES[schema_type]
    
    # Fallback sur CreativeWork si le type hérite de CreativeWork
    creative_work_types = [
        "Article", "BlogPosting", "NewsArticle", "Recipe", 
        "HowTo", "Question", "Answer", "VideoObject", "Book"
    ]
    if any(parent in creative_work_types for parent in SCHEMA_RULES.get(schema_type, {}).get("parent_types", [])):
        return SCHEMA_RULES["CreativeWork"]
    
    # Fallback sur Thing
    return SCHEMA_RULES["Thing"]


def get_all_schema_types():
    """Retourne tous les types supportés"""
    return list(SCHEMA_RULES.keys())


def is_ai_priority_type(schema_type):
    """Vérifie si le type est prioritaire pour les IA"""
    from .config import AI_PRIORITY_TYPES
    return schema_type in AI_PRIORITY_TYPES
