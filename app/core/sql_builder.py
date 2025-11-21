from typing import Dict, Any, List


def build_sql_from_filters(filters: Dict[str, Any], limit: int):
    base_select = "SELECT DISTINCT p.id, p.title FROM products p"
    joins: List[str] = []
    where_clauses: List[str] = []
    params: List[Any] = []
    print(filters)
    # Map logical dimensions to label tables + aliases
    label_map = {
        "vibe":     ("product_vibe_labels",     "pv"),
        "occasion": ("product_occasion_labels", "po"),
        "gender":   ("product_gender_labels",   "pg"),
        "category": ("product_category_labels", "pc"),
        "age":      ("product_age_labels",      "pa"),
        "style":    ("product_style_labels",    "ps"),
    }

    # Handle label dimensions with *_in / *_not_in (plus backward compatibility for old keys)
    for dim, (table, alias) in label_map.items():
        in_key = f"{dim}_in"
        not_in_key = f"{dim}_not_in"

        # IN values (or legacy key without suffix)
        values_in = filters.get(in_key)
        if values_in is None and dim in filters and isinstance(filters[dim], list):
            # backward compatibility with old schema that used `"vibe": [...]`, etc.
            values_in = filters[dim]

        if isinstance(values_in, list) and values_in:
            joins.append(f"LEFT JOIN {table} {alias} ON {alias}.product_id = p.id")
            placeholders = ", ".join(["%s"] * len(values_in))
            where_clauses.append(f"{alias}.label IN ({placeholders})")
            params.extend(values_in)

        # NOT IN values → use NOT EXISTS so we don't need extra joins
        values_not_in = filters.get(not_in_key)
        if isinstance(values_not_in, list) and values_not_in:
            placeholders = ", ".join(["%s"] * len(values_not_in))
            sub_alias = f"{alias}_ex"
            where_clauses.append(
                f"NOT EXISTS ("
                f"SELECT 1 FROM {table} {sub_alias} "
                f"WHERE {sub_alias}.product_id = p.id "
                f"AND {sub_alias}.label IN ({placeholders})"
                f")"
            )
            params.extend(values_not_in)

    # Numeric filters
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

    # Store filters: support single store, IN and NOT IN
    store_in = filters.get("store_in")
    store_not_in = filters.get("store_not_in")
    store = filters.get("store")  # backward compatible single store

    if isinstance(store_in, list) and store_in:
        placeholders = ", ".join(["%s"] * len(store_in))
        where_clauses.append(f"p.store IN ({placeholders})")
        params.extend(store_in)

    if isinstance(store_not_in, list) and store_not_in:
        placeholders = ", ".join(["%s"] * len(store_not_in))
        where_clauses.append(f"p.store NOT IN ({placeholders})")
        params.extend(store_not_in)

    if isinstance(store, str) and store.strip() and not store_in:
        # If store_in is present, assume it takes precedence over the legacy single store
        where_clauses.append("p.store = %s")
        params.append(store.strip())

    # main_category filters: support single, IN, NOT IN
    main_category_in = filters.get("main_category_in")
    main_category_not_in = filters.get("main_category_not_in")
    main_category = filters.get("main_category")  # backward compatible single value

    if isinstance(main_category_in, list) and main_category_in:
        placeholders = ", ".join(["%s"] * len(main_category_in))
        where_clauses.append(f"p.main_category IN ({placeholders})")
        params.extend(main_category_in)

    if isinstance(main_category_not_in, list) and main_category_not_in:
        placeholders = ", ".join(["%s"] * len(main_category_not_in))
        where_clauses.append(f"p.main_category NOT IN ({placeholders})")
        params.extend(main_category_not_in)

    if isinstance(main_category, str) and main_category.strip() and not main_category_in:
        # If main_category_in is present, treat it as the primary constraint
        where_clauses.append("p.main_category = %s")
        params.append(main_category.strip())

    # Assemble SQL
    sql_parts: List[str] = [base_select]

    # Deduplicate joins
    if joins:
        seen = set()
        uniq_joins: List[str] = []
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
