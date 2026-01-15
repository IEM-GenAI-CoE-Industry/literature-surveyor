"""
Mock data provider for Academic Venue Discovery.
Falls back to this when external APIs fail or return no results.
"""

MOCK_VENUES = {
    "default": {
        "conferences": ["NeurIPS", "ICML", "AAAI", "CVPR", "ICLR"],
        "journals": ["Journal of Machine Learning Research", "IEEE TPAMI", "Nature Machine Intelligence"]
    },
    "healthcare": {
        "conferences": ["AMIA Annual Symposium", "CHIL", "MICCAI", "IEEE BIBM"],
        "journals": ["JAMIA", "Lancet Digital Health", "IEEE Journal of Biomedical and Health Informatics"]
    },
    "finance": {
        "conferences": ["ICAIF (ACM International Conference on AI in Finance)", "IEEE CIFEr"],
        "journals": ["Journal of Finance", "Journal of Financial Data Science", "Quantitative Finance"]
    },
    "education": {
        "conferences": ["AIED", "LAK (Learning Analytics and Knowledge)", "EDM"],
        "journals": ["International Journal of Artificial Intelligence in Education", "Computers & Education"]
    }
}

def get_mock_venues(domain: str):
    """Returns venues based on simple keyword matching."""
    domain_lower = domain.lower()
    
    if "health" in domain_lower or "medic" in domain_lower or "clinic" in domain_lower:
        return MOCK_VENUES["healthcare"]
    if "financ" in domain_lower or "econ" in domain_lower:
        return MOCK_VENUES["finance"]
    if "educa" in domain_lower or "learn" in domain_lower and "machine" not in domain_lower:
        return MOCK_VENUES["education"]
    
    return MOCK_VENUES["default"]