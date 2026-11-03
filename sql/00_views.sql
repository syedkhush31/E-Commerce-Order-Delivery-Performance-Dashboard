-- Indexes for join performance
CREATE INDEX idx_items_order ON order_items(order_id);
CREATE INDEX idx_pay_order ON payments(order_id);
CREATE INDEX idx_rev_order ON reviews(order_id);
CREATE INDEX idx_orders_cust ON orders(customer_id);

-- One row per order with delivery metrics (reviews de-duplicated to 1 per order)
CREATE VIEW order_facts AS
SELECT o.order_id, o.order_status, c.customer_unique_id, c.customer_state,
       substr(o.order_purchase_timestamp,1,7) AS order_month,
       o.order_purchase_timestamp, o.order_delivered_customer_date,
       i.items, i.price, i.freight, i.seller_id,
       p.payment_value,
       r.review_score,
       julianday(o.order_delivered_customer_date) - julianday(o.order_purchase_timestamp) AS delivery_days,
       julianday(o.order_delivered_customer_date) - julianday(o.order_estimated_delivery_date) AS delay_days,
       julianday(o.order_approved_at) - julianday(o.order_purchase_timestamp) AS approval_days,
       julianday(o.order_delivered_carrier_date) - julianday(o.order_approved_at) AS handling_days,
       julianday(o.order_delivered_customer_date) - julianday(o.order_delivered_carrier_date) AS transit_days,
       CASE WHEN o.order_status='delivered' AND o.order_delivered_customer_date > o.order_estimated_delivery_date THEN 1 ELSE 0 END AS is_late,
       CASE WHEN o.order_status IN ('canceled','unavailable') THEN 1 ELSE 0 END AS is_cancelled
FROM orders o
JOIN customers c ON c.customer_id = o.customer_id
LEFT JOIN (SELECT order_id, COUNT(*) items, SUM(price) price, SUM(freight_value) freight, MIN(seller_id) seller_id
           FROM order_items GROUP BY order_id) i ON i.order_id = o.order_id
LEFT JOIN (SELECT order_id, SUM(payment_value) payment_value FROM payments GROUP BY order_id) p ON p.order_id = o.order_id
LEFT JOIN (SELECT order_id, AVG(review_score) review_score FROM reviews GROUP BY order_id) r ON r.order_id = o.order_id;
