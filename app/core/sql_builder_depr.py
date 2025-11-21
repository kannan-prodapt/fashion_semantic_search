from typing import Dict, Any, List


def build_sql_from_filters(filters: Dict[str, Any], limit: int):
    base_select = "SELECT DISTINCT p.id, p.title FROM products p"
    joins = []
    where_clauses = []
    params: List[Any] = []

    label_map = {
        "vibe":      ("product_vibe_labels",      "pv"),
        "occasion":  ("product_occasion_labels",  "po"),
        "gender":    ("product_gender_labels",    "pg"),
        "category":  ("product_category_labels",  "pc"),
        "age":       ("product_age_labels",       "pa"),
        "style":     ("product_style_labels",     "ps"),
    }

    for dim, (table, alias) in label_map.items():
        values = filters.get(dim)
        if isinstance(values, list) and values:
            joins.append(f"LEFT JOIN {table} {alias} ON {alias}.product_id = p.id")
            placeholders = ", ".join(["%s"] * len(values))
            where_clauses.append(f"{alias}.label IN ({placeholders})")
            params.extend(values)

    price_min = filters.get("price_min")
    price_max = filters.get("price_max")
    rating_min = filters.get("rating_min")

    if price_min is not None:
        where_clauses.append("p.price >= %s")
        params.append(float(price_min))

    if price_max is not None:
        where_clauses.append("p.price <= %s")
        params.append(float(price_max))

    if rating_min is not None:
        where_clauses.append("p.average_rating >= %s")
        params.append(float(rating_min))

    store = filters.get("store")
    if isinstance(store, str) and store.strip():
        where_clauses.append("p.store = %s")
        params.append(store.strip())

    main_category = filters.get("main_category")
    if isinstance(main_category, str) and main_category.strip():
        where_clauses.append("p.main_category = %s")
        params.append(main_category.strip())

    sql_parts = [base_select]

    if joins:
        seen = set()
        uniq_joins = []
        for j in joins:
            if j not in seen:
                uniq_joins.append(j)
                seen.add(j)
        sql_parts.extend(uniq_joins)

    if where_clauses:
        sql_parts.append("WHERE " + " AND ".join(where_clauses))

    sql_parts.append("LIMIT %s")
    params.append(limit)

    full_sql = " ".join(sql_parts)
    return full_sql, params
