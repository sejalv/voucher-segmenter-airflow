CREATE SCHEMA IF NOT EXISTS voucher_customer;

CREATE TABLE IF NOT EXISTS voucher_customer.customer_segments
(
    segment_name VARCHAR(35),   -- try changing to STRING
    segment_type VARCHAR(35),   -- try changing to STRING
    min_range  INT,
    max_range  INT
);

TRUNCATE TABLE voucher_customer.customer_segments;

INSERT INTO voucher_customer.customer_segments VALUES ('frequent_segment', '0-4', 0, 4),
                                               ('frequent_segment', '5-13', 5, 13),
                                               ('frequent_segment', '13-37', 14, 37),
                                               ('frequent_segment', '37+', 38, 99999999),
                                               ('recency_segment', '30-60', 30, 60),
                                               ('recency_segment', '60-90', 61, 90),
                                               ('recency_segment', '90-120', 91, 120),
                                               ('recency_segment', '120-180', 121, 180),
                                               ('recency_segment', '180+', 180, 99999999);
