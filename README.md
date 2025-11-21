# Introduction

... (existing introduction content)


## 🏁 Quick Start

To set up and use this repository, follow these steps:

1. **Database Setup**

   - Place your SQL dump file (e.g., `fashion_dump.sql`) in the directory expected by `scripts/load_sql_dump.py` (usually `scripts/sql/`, unless configured otherwise).
   - Run the SQL loader script to set up your database:

     ```bash
     python scripts/load_sql_dump.py
     ```

2. **Populate OpenSearch**

   - Once your database is set up, index products to OpenSearch:

     ```bash
     python scripts/index_products_to_opensearch.py
     ```

3. **Ready to Use**

   - The product is now set up with your data and ready for semantic search queries!

---

**Note**: Ensure your environment variables and configuration files are correctly set for database and OpenSearch connections before running these scripts.