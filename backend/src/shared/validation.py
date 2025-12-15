"""
Validation utilities for the regulatory jobs application.
"""
from datetime import datetime
from typing import Union
from dateutil import parser as date_parser


# Comprehensive list of cities in the Île-de-France region
# This includes all communes in the 8 departments of Île-de-France
ILE_DE_FRANCE_CITIES = {
    # Paris (75)
    "paris",
    
    # Seine-et-Marne (77) - Major cities
    "meaux", "melun", "fontainebleau", "provins", "montereau-fault-yonne",
    "chelles", "pontault-combault", "savigny-le-temple", "champs-sur-marne",
    "torcy", "roissy-en-brie", "combs-la-ville", "ozoir-la-ferrière",
    "lagny-sur-marne", "bussy-saint-georges", "mitry-mory", "dammarie-les-lys",
    "le-mée-sur-seine", "villeparisis", "bailly-romainvilliers",
    
    # Yvelines (78) - Major cities
    "versailles", "sartrouville", "mantes-la-jolie", "saint-germain-en-laye",
    "poissy", "conflans-sainte-honorine", "les-mureaux", "plaisir",
    "trappes", "houilles", "chatou", "le-chesnay-rocquencourt",
    "montigny-le-bretonneux", "vélizy-villacoublay", "rambouillet",
    "maisons-laffitte", "élancourt", "guyancourt", "limay", "meulan-en-yvelines",
    
    # Essonne (91) - Major cities
    "évry-courcouronnes", "corbeil-essonnes", "massy", "savigny-sur-orge",
    "sainte-geneviève-des-bois", "palaiseau", "draveil", "viry-châtillon",
    "brunoy", "yerres", "montgeron", "longjumeau", "étampes", "ris-orangis",
    "grigny", "athis-mons", "juvisy-sur-orge", "vigneux-sur-seine",
    "fleury-mérogis", "gif-sur-yvette", "orsay", "les-ulis", "marcoussis",
    
    # Hauts-de-Seine (92) - Major cities
    "boulogne-billancourt", "nanterre", "courbevoie", "colombes", "asnières-sur-seine",
    "rueil-malmaison", "aubervilliers", "saint-denis", "argenteuil", "montreuil",
    "créteil", "vitry-sur-seine", "champigny-sur-marne", "saint-maur-des-fossés",
    "noisy-le-grand", "rosny-sous-bois", "pantin", "drancy", "aulnay-sous-bois",
    "blanc-mesnil", "épinay-sur-seine", "bobigny", "bondy", "livry-gargan",
    "sevran", "villemomble", "gagny", "neuilly-plaisance", "clichy-sous-bois",
    "montfermeil", "coubron", "vaujours", "courtry", "fresnes", "antony",
    "clamart", "issy-les-moulineaux", "vanves", "malakoff", "montrouge",
    "châtillon", "bagneux", "fontenay-aux-roses", "sceaux", "le-plessis-robinson",
    "châtenay-malabry", "bourg-la-reine", "cachan", "arcueil", "gentilly",
    "kremlin-bicêtre", "villejuif", "l'haÿ-les-roses", "chevilly-larue",
    "thiais", "choisy-le-roi", "orly", "villeneuve-le-roi", "ablon-sur-seine",
    "ivry-sur-seine", "charenton-le-pont", "saint-maurice", "joinville-le-pont",
    "saint-mandé", "vincennes", "fontenay-sous-bois", "nogent-sur-marne",
    "perreux-sur-marne", "bry-sur-marne", "villiers-sur-marne", "neuilly-sur-marne",
    "gournay-sur-marne", "champs-sur-marne", "noisiel", "lognes", "emerainville",
    "pontault-combault", "roissy-en-brie", "ozoir-la-ferrière", "lesigny",
    "brie-comte-robert", "gretz-armainvilliers", "tournan-en-brie", "presles-en-brie",
    
    # Seine-Saint-Denis (93) - Major cities
    "saint-denis", "montreuil", "aubervilliers", "aulnay-sous-bois", "drancy",
    "noisy-le-grand", "pantin", "bondy", "épinay-sur-seine", "rosny-sous-bois",
    "bagnolet", "bobigny", "livry-gargan", "sevran", "villemomble", "gagny",
    "neuilly-plaisance", "clichy-sous-bois", "montfermeil", "coubron",
    "vaujours", "courtry", "dugny", "le-bourget", "la-courneuve", "stains",
    "pierrefitte-sur-seine", "villetaneuse", "saint-ouen-sur-seine", "l'île-saint-denis",
    "romainville", "les-lilas", "le-pré-saint-gervais", "noisy-le-sec",
    "villepinte", "tremblay-en-france", "villevaude", "mitry-mory",
    
    # Val-de-Marne (94) - Major cities
    "créteil", "vitry-sur-seine", "champigny-sur-marne", "saint-maur-des-fossés",
    "ivry-sur-seine", "maisons-alfort", "fontenay-sous-bois", "vincennes",
    "nogent-sur-marne", "perreux-sur-marne", "bry-sur-marne", "villiers-sur-marne",
    "neuilly-sur-marne", "gournay-sur-marne", "joinville-le-pont", "saint-mandé",
    "charenton-le-pont", "saint-maurice", "alfortville", "choisy-le-roi",
    "thiais", "chevilly-larue", "l'haÿ-les-roses", "villejuif", "cachan",
    "arcueil", "gentilly", "kremlin-bicêtre", "fresnes", "rungis", "orly",
    "villeneuve-le-roi", "ablon-sur-seine", "valenton", "limeil-brévannes",
    "boissy-saint-léger", "sucy-en-brie", "la-queue-en-brie", "ormesson-sur-marne",
    "noiseau", "chennevières-sur-marne", "villecresnes", "mandres-les-roses",
    "périgny-sur-yerres", "varennes-jarcy", "brunoy", "épinay-sous-sénart",
    
    # Val-d'Oise (95) - Major cities
    "argenteuil", "sarcelles", "cergy", "garges-lès-gonesse", "franconville",
    "goussainville", "pontoise", "bezons", "ermont", "villiers-le-bel",
    "gonesse", "taverny", "herblay-sur-seine", "saint-gratien", "enghien-les-bains",
    "montmorency", "soisy-sous-montmorency", "eaubonne", "saint-leu-la-forêt",
    "margency", "andilly", "montlignon", "bouffémont", "domont", "ezanville",
    "saint-brice-sous-forêt", "sannois", "cormeilles-en-parisis", "la-frette-sur-seine",
    "montigny-lès-cormeilles", "saint-ouen-l'aumône", "neuville-sur-oise",
    "jouy-le-moutier", "vauréal", "osny", "éragny", "courdimanche", "puiseux-en-france",
    "roissy-en-france", "le-mesnil-amelot", "mitry-mory", "compans", "othis",
    "saint-soupplets", "le-plessis-belleville", "nantouillet", "messy",
    "rouvres", "saint-pathus", "oissery", "congis-sur-thérouanne", "barcy",
    "chambry", "etrepilly", "acy-en-multien", "crouy-sur-ourcq", "lizy-sur-ourcq",
    "mary-sur-marne", "isles-lès-villenoy", "poincy", "trilbardou", "annet-sur-marne",
    "fresnes-sur-marne", "carnetin", "dampmart", "thorigny-sur-marne", "lagny-sur-marne",
    "pomponne", "bussy-saint-martin", "saint-thibault-des-vignes", "gouvernes",
    "guermantes", "collégien", "bussy-saint-georges", "ferrières-en-brie",
    "pontcarré", "faremoutiers", "coulommiers", "mouroux", "saint-augustin",
    "pommeuse", "la-celle-sur-morin", "guérard", "tigeaux", "hautefeuille",
    "saint-germain-sur-morin", "crécy-la-chapelle", "voulangis", "montry",
    "condé-sainte-libiaire", "esbly", "coupvray", "magny-le-hongre", "chessy",
    "bailly-romainvilliers", "serris", "montévrain", "val-d'europe"
}

# Normalize city names for comparison (lowercase, handle accents, etc.)
NORMALIZED_CITIES = {city.lower().replace("'", "-").replace("'", "-") for city in ILE_DE_FRANCE_CITIES}


def validate_ile_de_france_city(city: str) -> bool:
    """
    Validate that a city is within the Île-de-France region.
    
    Args:
        city: The city name to validate
        
    Returns:
        True if the city is in Île-de-France, False otherwise
        
    Requirements: 4.2 - Geographic validation for Île-de-France cities
    """
    if not city or not isinstance(city, str):
        return False
    
    # Normalize the input city name for comparison
    normalized_city = city.lower().strip().replace("'", "-").replace("'", "-")
    
    # Remove common prefixes/suffixes that might vary
    normalized_city = normalized_city.replace("saint-", "st-").replace("sainte-", "ste-")
    
    return normalized_city in NORMALIZED_CITIES


def normalize_date(date_input: Union[str, datetime]) -> str:
    """
    Normalize various date formats to ISO 8601 format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS).
    
    Args:
        date_input: Date string in various formats or datetime object
        
    Returns:
        ISO 8601 formatted date string
        
    Raises:
        ValueError: If the date cannot be parsed or is invalid
        
    Requirements: 4.5 - Date normalization to ISO 8601 format
    """
    if isinstance(date_input, datetime):
        return date_input.isoformat()
    
    if not isinstance(date_input, str) or not date_input.strip():
        raise ValueError("Date input must be a non-empty string or datetime object")
    
    try:
        # Use dateutil parser which handles many different date formats
        parsed_date = date_parser.parse(date_input.strip())
        
        # Return ISO format
        # If time is midnight (00:00:00), return just the date part
        if parsed_date.time() == parsed_date.time().replace(hour=0, minute=0, second=0, microsecond=0):
            return parsed_date.date().isoformat()
        else:
            return parsed_date.isoformat()
            
    except (ValueError, TypeError, OverflowError) as e:
        raise ValueError(f"Unable to parse date '{date_input}': {str(e)}")


def validate_job_record_completeness(job_data: dict) -> bool:
    """
    Validate that a job record contains all required fields.
    
    Args:
        job_data: Dictionary containing job record data
        
    Returns:
        True if all required fields are present and non-empty, False otherwise
        
    Requirements: 4.1 - Job storage completeness validation
    """
    required_fields = {
        'job_title', 'company_name', 'city', 'year_of_experience', 
        'published_date', 'link'
    }
    
    if not isinstance(job_data, dict):
        return False
    
    # Check that all required fields are present and non-empty
    for field in required_fields:
        if field not in job_data:
            return False
        
        value = job_data[field]
        
        # Check for None or empty string
        if value is None or (isinstance(value, str) and not value.strip()):
            return False
        
        # Check for negative experience years
        if field == 'year_of_experience' and (not isinstance(value, int) or value < 0):
            return False
    
    return True


def generate_job_id(job_url: str) -> str:
    """
    Generate a unique job ID from the job URL using a hash.
    
    Args:
        job_url: The original job posting URL
        
    Returns:
        A unique job ID string
        
    Requirements: 4.3 - Duplicate prevention using URL hashing
    """
    import hashlib
    
    if not job_url or not isinstance(job_url, str):
        raise ValueError("Job URL must be a non-empty string")
    
    # Normalize URL for consistent hashing
    normalized_url = job_url.strip().lower()
    
    # Create SHA-256 hash of the URL
    hash_object = hashlib.sha256(normalized_url.encode('utf-8'))
    return hash_object.hexdigest()[:16]  # Use first 16 characters for shorter ID