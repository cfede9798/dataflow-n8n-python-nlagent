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