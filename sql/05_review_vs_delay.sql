-- Q5: Impact of delivery delay on customer review score
SELECT CASE WHEN delay_days<=0 THEN '1. On time/early'
            WHEN delay_days<=3 THEN '2. 1-3 days late'
            WHEN delay_days<=7 THEN '3. 4-7 days late'
            WHEN delay_days<=14 THEN '4. 8-14 days late'
            ELSE '5. 15+ days late' END AS delay_bucket,
       COUNT(*) orders, ROUND(AVG(review_score),2) avg_review,
       ROUND(100.0*SUM(review_score<=2)/COUNT(review_score),1) low_review_pct
FROM order_facts WHERE order_status='delivered' AND delay_days IS NOT NULL
GROUP BY delay_bucket ORDER BY delay_bucket;
