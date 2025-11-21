# app/api/v1/search_routes.py
from fastapi import APIRouter
from app.schemas.search import SearchRequest, SearchResponse
from app.services.search_service import (
    search_sql_only,
    search_with_vector,
)

router = APIRouter(tags=["search"])


@router.post("/search_sql", response_model=SearchResponse)
def search_products_sql_only_endpoint(req: SearchRequest):
    return search_sql_only(req)


@router.post("/search", response_model=SearchResponse)
def search_products_vector_endpoint(req: SearchRequest):
    return search_with_vector(req)
