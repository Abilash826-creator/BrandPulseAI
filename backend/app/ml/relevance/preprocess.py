import re
from typing import List, Optional

def clean_relevance_text(text: str, brand: Optional[str] = None) -> str:
    """
    Cleans conversation text and augments with brand context token for contextual relevance modeling.
    """
    if not text:
        return ""
    text_clean = re.sub(r'[\r\n\t]+', ' ', str(text))
    text_clean = re.sub(r'\s+', ' ', text_clean).strip()
    
    brand_prefix = f"__brand_{brand.lower().replace(' ', '')}__ " if brand else "__brand_none__ "
    return brand_prefix + text_clean
