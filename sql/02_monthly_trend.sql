-- Q2: Monthly orders, revenue and month-over-month growth (window function)
WITH m AS (
  SELECT order_month, COUNT(*) orders, ROUND(SUM(payment_value),0) revenue
  FROM order_facts WHERE order_month BETWEEN '2017-01' AND '2018-08'
  GROUP BY order_month)
SELECT order_month, orders, revenue,
       ROUND(100.0*(orders - LAG(orders) OVER (ORDER BY order_month)) / LAG(orders) OVER (ORDER BY order_month),1) AS orders_mom_pct
FROM m ORDER BY order_month;
