-- Q4: Where does time go? Average days per fulfillment stage
SELECT ROUND(AVG(approval_days),2) approval_days,
       ROUND(AVG(handling_days),2) seller_handling_days,
       ROUND(AVG(transit_days),2) carrier_transit_days,
       ROUND(AVG(delivery_days),2) total_days
FROM order_facts WHERE order_status='delivered' AND transit_days IS NOT NULL;
