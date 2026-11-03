-- Q3: Delivery performance by customer state
SELECT customer_state, COUNT(*) delivered_orders,
       ROUND(AVG(delivery_days),1) avg_days,
       ROUND(100.0*SUM(is_late)/COUNT(*),1) late_pct,
       ROUND(AVG(review_score),2) avg_review
FROM order_facts
WHERE order_status='delivered' AND delivery_days IS NOT NULL
GROUP BY customer_state ORDER BY late_pct DESC;
