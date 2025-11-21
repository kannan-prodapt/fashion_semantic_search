import streamlit as st
import streamlit.components.v1 as components
import requests

# Page configuration
st.set_page_config(
    page_title="VogueVista",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session state
if 'products' not in st.session_state:
    st.session_state.products = []
if 'search_query' not in st.session_state:
    st.session_state.search_query = ""
if 'results_from_sql' not in st.session_state:
    st.session_state.results_from_sql = False
if 'filters' not in st.session_state:
    st.session_state.filters = None

# API Configuration
API_BASE_URL_1 = "http://ec2-13-234-76-80.ap-south-1.compute.amazonaws.com:8000/v1/search"
API_BASE_URL_2 = "http://ec2-13-234-76-80.ap-south-1.compute.amazonaws.com:8000/v1/search_sql"
SEARCH_KEY = "ai04product29key#"

# Custom CSS
st.markdown("""
<style>
    /* Hide Streamlit elements */
    #MainMenu, footer, header {visibility: hidden;}
    .stDeployButton {display: none;}
    
    .main {
        padding: 0 !important;
        margin: 0 !important;
        max-width: 100% !important;
    }
    
    .block-container {
        padding: 0 !important;
        margin: 0 !important;
        max-width: 100% !important;
    }
    
    /* Remove all Streamlit containers */
    .element-container {
        margin: 0 !important;
        padding: 0 !important;
        background: transparent !important;
    }
    
    div[data-testid="column"] {
        padding: 0 !important;
        background: transparent !important;
    }
    
    div[data-testid="stVerticalBlock"] {
        gap: 0 !important;
        padding: 0 !important;
    }
    
    div[data-testid="stHorizontalBlock"] {
        background: transparent !important;
        gap: 0 !important;
    }
    
    [data-testid="stAppViewContainer"] {
        background: white !important;
    }
    
    [data-testid="stHeader"] {
        background: transparent !important;
    }
    
    .stForm {
        border: none !important;
    }
    
    /* Search input */
    .stTextInput > div > div > input {
        background-color: white !important;
        border: 3px solid #ff9900 !important;
        border-right: none !important;
        border-radius: 4px 0 0 4px !important;
        padding: 10px 15px !important;
        font-size: 16px !important;
        height: 44px !important;
        color: #111 !important;
        caret-color: #111 !important;
        cursor: text !important;
    }
    
    .stTextInput > div > div > input:focus {
        outline: none !important;
        border: 3px solid #ff9900 !important;
        box-shadow: 0 0 0 3px rgba(255, 153, 0, 0.2) !important;
        caret-color: #111 !important;
    }
    
    .stTextInput {
        cursor: text !important;
    }
    
    .stTextInput > div {
        cursor: text !important;
    }
    
    /* Search button */
    .stButton > button {
        background-color: #febd69 !important;
        border: none !important;
        border-radius: 0 4px 4px 0 !important;
        padding: 0 !important;
        height: 44px !important;
        width: 50px !important;
        color: #111 !important;
        font-size: 20px !important;
        cursor: pointer !important;
        margin: 0 !important;
        transition: background-color 0.2s !important;
    }
    
    .stButton > button:hover {
        background-color: #f3a847 !important;
    }
    
    /* Amazon Header */
    .amazon-header {
        background-color: #131921;
        padding: 15px 30px;
        display: flex;
        align-items: center;
        gap: 30px;
    }
    
    .amazon-logo {
        color: white;
        font-size: 32px;
        font-weight: bold;
        font-family: Arial, sans-serif;
        cursor: pointer;
        padding: 5px 10px;
        border: 1px solid transparent;
        border-radius: 2px;
        flex-shrink: 0;
    }
    
    .amazon-logo:hover {
        border-color: white;
    }
    
    .logo-in {
        font-size: 16px;
    }
    
    .search-section {
        flex: 1;
        max-width: 900px;
    }
    
    /* Sidebar */
    .sidebar {
        width: 260px;
        background-color: white;
        padding: 20px;
        border-right: 1px solid #ddd;
        flex-shrink: 0;
        min-height: calc(100vh - 80px);
    }
    
    .filter-section {
        margin-bottom: 20px;
        padding-bottom: 15px;
        border-bottom: 1px solid #e3e6e6;
    }
    
    .filter-section:last-child {
        border-bottom: none;
    }
    
    .filter-title {
        font-size: 16px;
        font-weight: bold;
        color: #0f1111;
        margin-bottom: 12px;
    }
    
    .filter-badge {
        display: inline-block;
        background-color: #e7f3f8;
        color: #007185;
        padding: 6px 12px;
        border-radius: 12px;
        font-size: 13px;
        margin: 4px 4px 4px 0;
        border: 1px solid #c7e6f5;
    }
    
    .filter-badge-exclude {
        background-color: #fce8e8;
        color: #c45500;
        border: 1px solid #f5c7c7;
    }
    
    .main-with-sidebar {
        display: flex;
        background-color: white;
    }
</style>
""", unsafe_allow_html=True)

def call_search_api(query):
    """Call the first search API"""
    print("Calling Search API")
    try:
        payload = {"search_key": SEARCH_KEY, "query": query, "limit": 50}
        response = requests.post(API_BASE_URL_1, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

def call_search_sql_api(query):
    """Call the second SQL search API"""
    print("Calling Vector Search API")
    try:
        payload = {"search_key": SEARCH_KEY, "query": query, "limit": 50}
        response = requests.post(API_BASE_URL_2, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

def parse_products(data):
    """Parse API response"""
    if not data:
        return [], None
    
    # Extract filters
    filters = data.get('filters', {})
    
    # Extract products
    if 'results' not in data:
        return [], filters
    
    products = []
    for item in data.get('results', []):
        products.append({
            'id': item.get('id'),
            'title': item.get('title', ''),
            'price': item.get('price'),
            'rating': item.get('average_rating', 0),
            'reviews': item.get('rating_number', 0),
            'image_url': item.get('image_url', ''),
            'store': item.get('store', ''),
            'best_seller': item.get('average_rating', 0) >= 4.5
        })
    return products, filters

def render_product(p):
    """Render product card"""
    rating = p['rating']
    full = int(rating)
    half = 1 if rating - full >= 0.5 else 0
    empty = 5 - full - half
    
    stars = "★" * full + ("⯨" if half else "") + "☆" * empty
    
    badge = '<div class="best-seller">High Rated</div>' if p['best_seller'] else ''
    price_html = f'<div class="product-price"><span class="rupee">₹</span>{p["price"]}</div>' if p['price'] else ''
    
    return f'''
    <div class="product-card">
        {badge}
        <div class="product-image-box">
            <img src="{p['image_url']}" class="product-img" alt="{p['title']}" loading="lazy">
        </div>
        <div class="product-title">{p['title']}</div>
        <div class="rating-box">
            <span class="stars">{stars}</span>
            <span class="review-count">({p['reviews']})</span>
        </div>
        {price_html}
        <div class="store-info">by {p['store']}</div>
        <div class="prime-delivery">Get it by Tomorrow</div>
    </div>
    '''

# ==================== INITIAL DEFAULT LOAD ====================
# On first page load, show some products by default
if not st.session_state.products and not st.session_state.search_query:
    DEFAULT_QUERY = "casual outfits for women"  # <- change this to whatever you like

    # You can choose either API; here I use the SQL one:
    result = call_search_sql_api(DEFAULT_QUERY)
    if result:
        products, filters = parse_products(result)
        st.session_state.products = products
        st.session_state.filters = filters
        st.session_state.search_query = DEFAULT_QUERY


# ==================== HEADER ====================
st.markdown("""
<div class="amazon-header">
    <div class="amazon-logo">
        VogueVista<span class="logo-in"></span>
    </div>
    <div class="search-section">
""", unsafe_allow_html=True)

# Search bar with form to enable Enter key
with st.form(key='search_form', clear_on_submit=False):
    col1, col2 = st.columns([20, 1])
    with col1:
        search_val = st.text_input("Search", value=st.session_state.search_query, 
                                   placeholder="Search VogueVista", label_visibility="collapsed",
                                   key="search_input")
    with col2:
        search_btn = st.form_submit_button("🔍")

st.markdown("""
    </div>
</div>
""", unsafe_allow_html=True)

# ==================== HANDLE SEARCH ====================
if search_btn and search_val.strip():
    st.session_state.search_query = search_val.strip()
    
    # Loading state
    loading_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {
                margin: 0;
                padding: 0;
                font-family: Arial, sans-serif;
                background-color: white;
            }
            .loading-state {
                text-align: center;
                padding: 100px 20px;
            }
            .spinner {
                font-size: 50px;
                animation: spin 1s linear infinite;
            }
            @keyframes spin {
                from { transform: rotate(0deg); }
                to { transform: rotate(360deg); }
            }
            .loading-msg {
                font-size: 18px;
                color: #565959;
                margin-top: 20px;
            }
        </style>
    </head>
    <body>
        <div class="loading-state">
            <div class="spinner">⏳</div>
            <div class="loading-msg">Searching for products...</div>
        </div>
    </body>
    </html>
    """
    components.html(loading_html, height=400)
    
    # Call first API
    result1 = call_search_sql_api(st.session_state.search_query)
    print("received results")
    if result1:
        products, filters = parse_products(result1)
        st.session_state.products = products
        st.session_state.filters = filters
        st.session_state.results_from_sql = False
        st.experimental_rerun()
    
    # Call second API
    result2 = call_search_api(st.session_state.search_query)
    print("received vector results")
    if result2:
        products, filters = parse_products(result2)
        st.session_state.products = products
        st.session_state.filters = filters
        st.session_state.results_from_sql = True
        st.experimental_rerun()

# ==================== MAIN CONTENT ====================

if st.session_state.products:
    # Layout with sidebar
    col_sidebar, col_products = st.columns([1, 4])
    
    with col_sidebar:
        # Render sidebar
        sidebar_html = '<div class="sidebar">'
        
        if st.session_state.filters:
            filters = st.session_state.filters
            
            # Occasions filter
            if 'occasion_in' in filters and filters['occasion_in']:
                sidebar_html += '<div class="filter-section"><div class="filter-title">Occasions</div>'
                for occasion in filters['occasion_in']:
                    sidebar_html += f'<div class="filter-badge">{occasion.title()}</div>'
                sidebar_html += '</div>'
            
            # Categories excluded
            if 'category_not_in' in filters and filters['category_not_in']:
                sidebar_html += '<div class="filter-section"><div class="filter-title">Excluded Categories</div>'
                for category in filters['category_not_in']:
                    sidebar_html += f'<div class="filter-badge filter-badge-exclude">{category.title()}</div>'
                sidebar_html += '</div>'
            
            # Other filters
            for key, value in filters.items():
                if key not in ['occasion_in', 'category_not_in'] and value:
                    filter_name = key.replace('_', ' ').title()
                    sidebar_html += f'<div class="filter-section"><div class="filter-title">{filter_name}</div>'
                    if isinstance(value, list):
                        for item in value:
                            sidebar_html += f'<div class="filter-badge">{str(item).title()}</div>'
                    else:
                        sidebar_html += f'<div class="filter-badge">{str(value)}</div>'
                    sidebar_html += '</div>'
        
        sidebar_html += '</div>'
        st.markdown(sidebar_html, unsafe_allow_html=True)
    
    with col_products:
        # Build products HTML
        count = len(st.session_state.products)
        products_html = ""
        for product in st.session_state.products:
            products_html += render_product(product)
        
        # Render products
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    margin: 0;
                    padding: 0;
                    font-family: Arial, sans-serif;
                    background-color: white;
                }}
                
                .product-area {{
                    background-color: white;
                    padding: 20px 30px;
                }}
                
                .results-bar {{
                    padding: 15px 0;
                    margin-bottom: 30px;
                    border-bottom: 1px solid #e7e7e7;
                }}
                
                .results-text {{
                    font-size: 16px;
                    color: #565959;
                }}
                
                .keyword {{
                    color: #c45500;
                    font-weight: 600;
                }}
                
                .products-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
                    gap: 25px;
                }}
                
                .product-card {{
                    background: white;
                    cursor: pointer;
                    position: relative;
                    padding: 15px;
                    border-radius: 4px;
                }}
                
                .product-card:hover {{
                    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
                }}
                
                .best-seller {{
                    position: absolute;
                    top: 10px;
                    left: 10px;
                    background-color: #c45500;
                    color: white;
                    padding: 5px 10px;
                    font-size: 12px;
                    font-weight: 600;
                    border-radius: 2px;
                    z-index: 1;
                }}
                
                .product-image-box {{
                    width: 100%;
                    height: 260px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin-bottom: 15px;
                    background-color: #fafafa;
                    border-radius: 4px;
                }}
                
                .product-img {{
                    max-width: 100%;
                    max-height: 100%;
                    object-fit: contain;
                }}
                
                .product-title {{
                    color: #007185;
                    font-size: 14px;
                    line-height: 1.4;
                    margin-bottom: 10px;
                    min-height: 40px;
                    overflow: hidden;
                    display: -webkit-box;
                    -webkit-line-clamp: 2;
                    -webkit-box-orient: vertical;
                }}
                
                .product-title:hover {{
                    color: #c7511f;
                }}
                
                .rating-box {{
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    margin-bottom: 10px;
                }}
                
                .stars {{
                    color: #ff9900;
                    font-size: 13px;
                }}
                
                .review-count {{
                    color: #007185;
                    font-size: 13px;
                }}
                
                .product-price {{
                    font-size: 24px;
                    color: #0f1111;
                    font-weight: 500;
                    margin-bottom: 8px;
                }}
                
                .rupee {{
                    font-size: 14px;
                    vertical-align: top;
                }}
                
                .store-info {{
                    color: #565959;
                    font-size: 12px;
                    margin-top: 8px;
                }}
                
                .prime-delivery {{
                    color: #007185;
                    font-size: 12px;
                    margin-top: 5px;
                    font-weight: 500;
                }}
            </style>
        </head>
        <body>
            <div class="product-area">
                <div class="results-bar">
                    <span class="results-text">1-{count} of {count} results for <span class="keyword">"{st.session_state.search_query}"</span></span>
                </div>
                <div class="products-grid">
                    {products_html}
                </div>
            </div>
        </body>
        </html>
        """
        
        components.html(full_html, height=2000, scrolling=True)

else:
    # Empty state
    empty_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {
                margin: 0;
                padding: 0;
                font-family: Arial, sans-serif;
                background-color: white;
            }
            .empty-state {
                text-align: center;
                padding: 100px 20px;
            }
            .empty-icon {
                font-size: 100px;
                margin-bottom: 30px;
                opacity: 0.3;
            }
            .empty-title {
                font-size: 28px;
                color: #0f1111;
                margin-bottom: 15px;
            }
            .empty-desc {
                font-size: 16px;
                color: #565959;
            }
        </style>
    </head>
    <body>
        <div class="empty-state">
            <div class="empty-icon">🔍</div>
            <div class="empty-title">Search for products</div>
            <div class="empty-desc">Enter a search query above to find products</div>
        </div>
    </body>
    </html>
    """
    components.html(empty_html, height=400)
