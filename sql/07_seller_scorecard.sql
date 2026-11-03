-- Q7: Seller scorecard with ranking (sellers with 30+ delivered orders)
SELECT seller_id, COUNT(*) orders, ROUND(100.0*SUM(is_late)/COUNT(*),1) late_pct,
       ROUND(AVG(review_score),2) avg_review,
       RANK() OVER (ORDER BY 1.0*SUM(is_late)/COUNT(*) DESC) AS worst_late_rank
FROM order_facts WHERE order_status='delivered' AND seller_id IS NOT NULL
GROUP BY seller_id HAVING COUNT(*)>=30 ORDER BY worst_late_rank LIMIT 20;
