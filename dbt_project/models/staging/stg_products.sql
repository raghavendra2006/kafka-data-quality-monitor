-- Staging model: Clean products data from raw zone
{{ config(materialized='view') }}

SELECT
    product_id,
    name AS product_name,
    category AS product_category,
    price
FROM {{ source('raw', 'products') }}
WHERE product_id IS NOT NULL
