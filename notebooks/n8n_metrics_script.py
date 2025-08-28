#!/usr/bin/env python3

import importlib
import subprocess
import sys

# We list special packages that don't exist in jupyter installation
special_required_packages = {
    "duckdb": "duckdb",
    "pandas": "pandas"
}

# Verify special packages
for module_name, pip_name in special_required_packages.items():
    try:
        importlib.import_module(module_name)
        print(f"{module_name} already installed")
    except ImportError:
        print(f"Installing {pip_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name])

#import sys
import pandas as pd
import duckdb
from datetime import datetime
import json
import os

def main():
        # Error handling
    try:

        # Localprobe
        #db_path = "/home/jovyan/challenge/database/warehouse.db"
        # Production
        db_path = "/database/warehouse.db"
        
        # Verify database exists
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Database not found: {db_path}")
        
        # Connect to DuckDB
        conn = duckdb.connect(db_path)
        print("Connected to warehouse database")
        
        # Check if we have enough data for 60 days analysis
        days_available = conn.execute("""
            SELECT COUNT(DISTINCT date) as unique_days 
            FROM ads_spend_db
        """).fetchone()[0]
        
        print(f"Unique days in dataset: {days_available}")
        
        if days_available < 30:
            print("Warning: Less than 30 days of data available")
        elif days_available < 60:
            print("Warning: Less than 60 days of data available for comparison")

        # Final kpi query        
        kpi_query = """
        WITH last_30_days AS (
            SELECT 
                SUM(spend) as total_spend,
                SUM(conversions) as total_conversions,
                SUM(conversions * 100) as total_revenue,
                COUNT(DISTINCT date) as days_count
            FROM ads_spend_db 
            WHERE date >= (SELECT MAX(date) - INTERVAL 29 DAY FROM ads_spend_db)
              AND date <= (SELECT MAX(date) FROM ads_spend_db)
        ),
        
        prior_30_days AS (
            SELECT 
                SUM(spend) as total_spend,
                SUM(conversions) as total_conversions,
                SUM(conversions * 100) as total_revenue,
                COUNT(DISTINCT date) as days_count
            FROM ads_spend_db 
            WHERE date >= (SELECT MAX(date) - INTERVAL 59 DAY FROM ads_spend_db)
              AND date <= (SELECT MAX(date) - INTERVAL 30 DAY FROM ads_spend_db)
        ),
        
        metrics_comparison AS (
            SELECT 
                -- Last 30 Days Metrics
                ROUND(l.total_spend / NULLIF(l.total_conversions, 0), 2) as cac_last_30,
                ROUND(l.total_revenue / NULLIF(l.total_spend, 0), 2) as roas_last_30,
                
                -- Prior 30 Days Metrics  
                ROUND(p.total_spend / NULLIF(p.total_conversions, 0), 2) as cac_prior_30,
                ROUND(p.total_revenue / NULLIF(p.total_spend, 0), 2) as roas_prior_30,
                
                -- Raw values for context
                l.total_spend as spend_last_30,
                l.total_conversions as conversions_last_30,
                l.days_count as days_last_30,
                p.total_spend as spend_prior_30,
                p.total_conversions as conversions_prior_30,
                p.days_count as days_prior_30
                
            FROM last_30_days l
            CROSS JOIN prior_30_days p
        )
        
        SELECT 
            'CAC (Cost per Acquisition)' as metric,
            '$' || CAST(cac_last_30 AS VARCHAR) as last_30_days,
            '$' || CAST(cac_prior_30 AS VARCHAR) as prior_30_days,
            CASE 
                WHEN cac_prior_30 = 0 OR cac_prior_30 IS NULL THEN 'N/A'
                ELSE CAST(ROUND(((cac_last_30 - cac_prior_30) / cac_prior_30) * 100, 1) AS VARCHAR) || '%'
            END as percent_change
        FROM metrics_comparison
        
        UNION ALL
        
        SELECT 
            'ROAS (Return on Ad Spend)' as metric,
            CAST(roas_last_30 AS VARCHAR) as last_30_days,
            CAST(roas_prior_30 AS VARCHAR) as prior_30_days,
            CASE 
                WHEN roas_prior_30 = 0 OR roas_prior_30 IS NULL THEN 'N/A'
                ELSE CAST(ROUND(((roas_last_30 - roas_prior_30) / roas_prior_30) * 100, 1) AS VARCHAR) || '%'
            END as percent_change
        FROM metrics_comparison;
        """
        
        # Get kpi table
        kpi_results = conn.execute(kpi_query).fetchdf()
        print(kpi_results.to_string(index=False))

        # Get some database info
        data_overview = conn.execute("""
            SELECT 
                MIN(date) as earliest_date,
                MAX(date) as latest_date,
                COUNT(*) as total_records,
                COUNT(DISTINCT platform) as platforms,
                SUM(spend) as total_spend,
                SUM(conversions) as total_conversions
            FROM ads_spend_db
        """).fetchdf()

        # Results in dictionary format
        results_summary = {
            "analysis_date": datetime.now().isoformat(),
            "data_range": {
                "earliest_date": str(data_overview['earliest_date'].iloc[0]),
                "latest_date": str(data_overview['latest_date'].iloc[0]),
                "total_records": int(data_overview['total_records'].iloc[0])
            },
            "kpi_comparison": kpi_results.to_dict('records')
        }
        print(json.dumps(results_summary))
                
        conn.close()
        return 0
        
    except Exception as e:
        error = {
            "status": "error",
            "error_message": str(e),
            "error_type": type(e).__name__,
            "timestamp": datetime.now().isoformat()
        }
        print(json.dumps(error))
        return 1

if __name__ == "__main__":
    sys.exit(main())
