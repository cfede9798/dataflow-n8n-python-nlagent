#!/usr/bin/env python3

import pandas as pd
import duckdb
from datetime import datetime
import json
import sys
import os

def main():
    try:

        csv_path = "/home/jovyan/challenge/data/ads_spend.csv"
        db_path = "/home/jovyan/challenge/database/warehouse.db"

        # Verify csv file again
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"{csv_path} csv not found")
            
        # Read CSV and convert to dataframe
        input_data_df = pd.read_csv(csv_path)
        print(f"csv loaded: {input_data_df.shape[0]:,} rows, {input_data_df.shape[1]} columns")
        
        # Validate if csv is empty
        if input_data_df.empty:
            raise ValueError("csv is empty")

        # Validate columns name (we put the list of columns that we already know exist)    
        required_columns = ['date', 'platform', 'account', 'campaign', 
                           'country', 'device', 'spend', 'clicks', 
                           'impressions', 'conversions']
        
        # Check if we have missing columns
        missing_cols = [col for col in required_columns if col not in input_data_df.columns]
        if missing_cols:
            raise ValueError(f"Missing columns: {missing_cols}")

        # Check null or empty values in columns
        null_empty_columns = [col for col in required_columns if input_data_df[col].isnull().any() or input_data_df[col].apply(lambda x: isinstance(x, str) and x.strip() == "").any()]

        if null_empty_columns:
            raise ValueError(f"Columnas con valores nulos o vacíos: {null_empty_columns}")
        
        # Add metadata
        # Date
        input_data_df['load_date'] = datetime.now()
        # Filename
        input_data_df['source_file_name'] = 'ads_spend.csv'
        
        print(f"load_date: {input_data_df['load_date'].iloc[0]}")
        print(f"source_file_name: {input_data_df['source_file_name'].iloc[0]}")
        
        # Connect to duckDB
        conn = duckdb.connect(db_path)
        
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS ads_spend_db (
            date DATE,
            platform VARCHAR,
            account VARCHAR,
            campaign VARCHAR,
            country VARCHAR,
            device VARCHAR,
            spend DECIMAL(12,2),
            clicks INTEGER,
            impressions INTEGER,
            conversions INTEGER,
            -- Metadata challenge required
            load_date TIMESTAMP,
            source_file_name VARCHAR
        );
        """
        # Verify table is already created or just verify
        conn.execute(create_table_sql)
        print("Table ads_spend_db verified/created")
        
        # Count register before add
        count_before = conn.execute("SELECT COUNT(*) FROM ads_spend_db").fetchone()[0]
        
        # Insert data in append mode to demostrate persistence
        conn.register('df_new', input_data_df)
        conn.execute("INSERT INTO ads_spend_db SELECT * FROM df_new")
        
        # Count register after add
        count_after = conn.execute("SELECT COUNT(*) FROM ads_spend_db").fetchone()[0]
        
        conn.close()
        
        # Result for n8n in JSON format
        result = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "rows_inserted": len(input_data_df),
            "total_rows_before": count_before,
            "total_rows_after": count_after,
            "source_file": "ads_spend.csv",
            "message": f"Successfully ingested {len(input_data_df):,} rows into warehouse"
        }
        
        print(f"Register added: {len(input_data_df):,}")
        print(f"Total regiser in DB now: {count_after:,}")
        print(f"Increment: +{count_after - count_before:,}")
        
        print(json.dumps(result))
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
