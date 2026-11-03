-- Q1: Headline KPIs
SELECT COUNT(*) AS total_orders,
       ROUND(SUM(CASE WHEN order_status<>'canceled' THEN payment_value END),2) AS revenue,
       ROUND(AVG(payment_value),2) AS avg_order_value,
       ROUND(AVG(CASE WHEN order_status='delivered' THEN delivery_days END),2) AS avg_delivery_days,
       ROUND(100.0*SUM(is_late)/SUM(order_status='delivered'),2) AS late_pct,
       ROUND(100.0*SUM(is_cancelled)/COUNT(*),2) AS cancel_pct,
       ROUND(AVG(review_score),2) AS avg_review
FROM order_facts;
