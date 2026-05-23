-- Staging model: Clean reviews data from raw zone
{{ config(materialized='view') }}

SELECT
    review_id,
    product_id,
    rating,
    review_text
FROM {{ source('raw', 'reviews') }}
WHERE review_id IS NOT NULL
