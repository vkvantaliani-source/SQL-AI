CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS rag_examples (
    id BIGSERIAL PRIMARY KEY,
    report_name TEXT NOT NULL,
    description TEXT NOT NULL,
    sql_text TEXT NOT NULL,
    embedding VECTOR(1536) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS rag_examples_embedding_idx
    ON rag_examples
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

CREATE UNIQUE INDEX IF NOT EXISTS rag_examples_report_name_uidx
    ON rag_examples (report_name);


-- Starter rows so retrieval has initial context even before running the Python seeder.
WITH zero_vec AS (
    SELECT ('[' || rtrim(repeat('0,', 1536), ',') || ']')::vector AS embedding
)
INSERT INTO rag_examples (report_name, description, sql_text, embedding)
SELECT s.report_name, s.description, s.sql_text, z.embedding
FROM (
    VALUES
        (
            'Weekly Active Users by Country',
            'Count distinct active users per week and country for the last 90 days',
            'SELECT date_trunc(''week'', event_time) AS week_start, country, COUNT(DISTINCT user_id) AS weekly_active_users FROM user_events WHERE event_time >= now() - interval ''90 days'' GROUP BY 1, 2 ORDER BY 1 DESC, 3 DESC;'
        ),
        (
            'Monthly Revenue by Plan',
            'Summarize paid invoice revenue by month and subscription plan',
            'SELECT date_trunc(''month'', paid_at) AS month_start, plan_name, SUM(amount_usd) AS revenue_usd FROM invoices WHERE status = ''paid'' GROUP BY 1, 2 ORDER BY 1 DESC, 3 DESC;'
        ),
        (
            'Top 20 Products by Units Sold',
            'Find the top 20 products by units sold in the last 30 days',
            'SELECT p.product_name, SUM(oi.quantity) AS units_sold FROM order_items oi JOIN products p ON p.id = oi.product_id JOIN orders o ON o.id = oi.order_id WHERE o.created_at >= now() - interval ''30 days'' GROUP BY 1 ORDER BY 2 DESC LIMIT 20;'
        )
) AS s(report_name, description, sql_text)
CROSS JOIN zero_vec z
WHERE NOT EXISTS (
    SELECT 1
    FROM rag_examples r
    WHERE r.report_name = s.report_name
);
