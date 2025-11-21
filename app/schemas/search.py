from typing import List, Any, Optional, Dict
from pydantic import BaseModel, Field

# ==========================
# REQUEST / RESPONSE MODELS
# ========================= 

class SearchRequest(BaseModel):
    search_key: str = Field(..., description="API access key")
    query: str = Field(..., description="Natural language query, e.g. 'sporty mens t-shirts under 800'")
    limit: int = Field(20, ge=1, le=100, description="Max number of rows to return")

class ProductOut(BaseModel):
    id: int
    title: str
    average_rating: Optional[float] = None
    rating_number: Optional[int] = None
    price: Optional[float] = None
    store: Optional[str] = None
    image_url: Optional[str] = None 


class SearchResponse(BaseModel):
    filters: Dict
    results: List[ProductOut]
