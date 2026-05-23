-- Mart model: Aggregated daily sales fact table
-- Joins sales, products, and reviews for analytics
{{ config(materialized='table') }}

WITH daily_sales AS (
    SELECT
        s.sale_date AS date,
        s.product_id,
        SUM(s.quantity) AS total_quantity_sold,
        SUM(s.total_amount) AS total_revenue
    FROM {{ ref('stg_sales') }} s
    GROUP BY s.sale_date, s.product_id
),

product_reviews AS (
    SELECT
        product_id,
        ROUND(AVG(rating)::numeric, 2) AS avg_review_rating
    FROM {{ ref('stg_reviews') }}
    GROUP BY product_id
)

SELECT
    ds.date,
    ds.product_id,
    p.product_name,
    p.product_category,
    ds.total_quantity_sold,
    ds.total_revenue,
    COALESCE(pr.avg_review_rating, 0.0)::float AS avg_review_rating
FROM daily_sales ds
JOIN {{ ref('stg_products') }} p
    ON ds.product_id = p.product_id
LEFT JOIN product_reviews pr
    ON ds.product_id = pr.product_id
