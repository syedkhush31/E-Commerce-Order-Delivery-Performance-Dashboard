-- Q8: Repeat-customer rate
SELECT COUNT(*) unique_customers,
       SUM(CASE WHEN n>1 THEN 1 ELSE 0 END) repeat_customers,
       ROUND(100.0*SUM(CASE WHEN n>1 THEN 1 ELSE 0 END)/COUNT(*),2) repeat_pct
FROM (SELECT customer_unique_id, COUNT(*) n FROM order_facts WHERE order_status<>'canceled' GROUP BY customer_unique_id);
