-- Q6: Return-risk proxy (canceled/unavailable OR review<=2) by product category
WITH cat AS (
  SELECT oi.order_id, COALESCE(t.product_category_name_english, p.product_category_name, 'unknown') category,
         ROW_NUMBER() OVER (PARTITION BY oi.order_id ORDER BY oi.order_item_id) rn
  FROM order_items oi JOIN products p ON p.product_id=oi.product_id
  LEFT JOIN category_translation t ON t.product_category_name=p.product_category_name)
SELECT c.category, COUNT(*) orders, ROUND(SUM(f.price),0) revenue,
       ROUND(100.0*SUM(CASE WHEN f.is_cancelled=1 OR f.review_score<=2 THEN 1 ELSE 0 END)/COUNT(*),1) risk_pct,
       ROUND(AVG(f.review_score),2) avg_review
FROM cat c JOIN order_facts f ON f.order_id=c.order_id
WHERE c.rn=1 GROUP BY c.category HAVING COUNT(*)>=300 ORDER BY risk_pct DESC LIMIT 15;
