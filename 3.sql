-- ====================================================================
-- 1. СТВОРЕННЯ СХЕМИ «ЗІРКА» (STAR SCHEMA)
-- ====================================================================

DROP TABLE IF EXISTS fact_sales_star CASCADE;
DROP TABLE IF EXISTS dim_product_star CASCADE;
DROP TABLE IF EXISTS dim_customer_star CASCADE;
DROP TABLE IF EXISTS dim_store_star CASCADE;
DROP TABLE IF EXISTS dim_date_star CASCADE;

CREATE TABLE dim_date_star (
    date_id INT PRIMARY KEY,
    full_date DATE NOT NULL,
    day INT NOT NULL,
    month INT NOT NULL,
    quarter INT NOT NULL,
    year INT NOT NULL
);

CREATE TABLE dim_customer_star (
    customer_id INT PRIMARY KEY,
    customer_name VARCHAR(100),
    segment VARCHAR(50),
    city VARCHAR(50),
    region VARCHAR(50)
);

CREATE TABLE dim_product_star (
    product_id INT PRIMARY KEY,
    product_name VARCHAR(100),
    category_name VARCHAR(50),
    department VARCHAR(50)
);

CREATE TABLE dim_store_star (
    store_id INT PRIMARY KEY,
    store_name VARCHAR(100),
    city VARCHAR(50),
    region VARCHAR(50)
);

CREATE TABLE fact_sales_star (
    sale_id SERIAL PRIMARY KEY,
    date_id INT REFERENCES dim_date_star(date_id),
    customer_id INT REFERENCES dim_customer_star(customer_id),
    product_id INT REFERENCES dim_product_star(product_id),
    store_id INT REFERENCES dim_store_star(store_id),
    quantity INT NOT NULL,
    unit_price NUMERIC(10, 2) NOT NULL,
    total_amount NUMERIC(12, 2) NOT NULL
);

-- ====================================================================
-- 2. СТВОРЕННЯ СХЕМИ «СНІЖИНКА» (SNOWFLAKE SCHEMA)
-- ====================================================================

DROP TABLE IF EXISTS fact_sales_snowflake CASCADE;
DROP TABLE IF EXISTS dim_product_snowflake CASCADE;
DROP TABLE IF EXISTS dim_category_snowflake CASCADE;
DROP TABLE IF EXISTS dim_department_snowflake CASCADE;
DROP TABLE IF EXISTS dim_customer_snowflake CASCADE;
DROP TABLE IF EXISTS dim_store_snowflake CASCADE;
DROP TABLE IF EXISTS dim_city_snowflake CASCADE;
DROP TABLE IF EXISTS dim_region_snowflake CASCADE;
DROP TABLE IF EXISTS dim_date_snowflake CASCADE;

CREATE TABLE dim_region_snowflake (
    region_id INT PRIMARY KEY,
    region_name VARCHAR(50) NOT NULL
);

CREATE TABLE dim_city_snowflake (
    city_id INT PRIMARY KEY,
    city_name VARCHAR(50) NOT NULL,
    region_id INT REFERENCES dim_region_snowflake(region_id)
);

CREATE TABLE dim_customer_snowflake (
    customer_id INT PRIMARY KEY,
    customer_name VARCHAR(100),
    segment VARCHAR(50),
    city_id INT REFERENCES dim_city_snowflake(city_id)
);

CREATE TABLE dim_store_snowflake (
    store_id INT PRIMARY KEY,
    store_name VARCHAR(100),
    city_id INT REFERENCES dim_city_snowflake(city_id)
);

CREATE TABLE dim_department_snowflake (
    department_id INT PRIMARY KEY,
    department_name VARCHAR(50) NOT NULL
);

CREATE TABLE dim_category_snowflake (
    category_id INT PRIMARY KEY,
    category_name VARCHAR(50) NOT NULL,
    department_id INT REFERENCES dim_department_snowflake(department_id)
);

CREATE TABLE dim_product_snowflake (
    product_id INT PRIMARY KEY,
    product_name VARCHAR(100),
    category_id INT REFERENCES dim_category_snowflake(category_id)
);

CREATE TABLE dim_date_snowflake (
    date_id INT PRIMARY KEY,
    full_date DATE NOT NULL,
    day INT NOT NULL,
    month INT NOT NULL,
    quarter INT NOT NULL,
    year INT NOT NULL
);

CREATE TABLE fact_sales_snowflake (
    sale_id SERIAL PRIMARY KEY,
    date_id INT REFERENCES dim_date_snowflake(date_id),
    customer_id INT REFERENCES dim_customer_snowflake(customer_id),
    product_id INT REFERENCES dim_product_snowflake(product_id),
    store_id INT REFERENCES dim_store_snowflake(store_id),
    quantity INT NOT NULL,
    unit_price NUMERIC(10, 2) NOT NULL,
    total_amount NUMERIC(12, 2) NOT NULL
);

-- ====================================================================
-- 3. ГЕНЕРАЦІЯ ДАНИХ (POSTGRESQL DIALECT)
-- ====================================================================

-- Наповнення сніжинки
INSERT INTO dim_region_snowflake VALUES 
(1, 'Захід'), (2, 'Центр'), (3, 'Південь');

INSERT INTO dim_city_snowflake VALUES 
(1, 'Львів', 1), (2, 'Івано-Франківськ', 1), (3, 'Київ', 2), (4, 'Одеса', 3);

INSERT INTO dim_department_snowflake VALUES 
(1, 'Електроніка'), (2, 'Побут');

INSERT INTO dim_category_snowflake VALUES 
(1, 'Смартфони', 1), (2, 'Ноутбуки', 1), (3, 'Освітлення', 2);

INSERT INTO dim_product_snowflake VALUES 
(1, 'Телефон Alpha', 1), (2, 'Ноутбук Pro', 2), (3, 'LED Лампа', 3);

INSERT INTO dim_customer_snowflake VALUES 
(1, 'Іван Коваленко', 'Роздріб', 1), 
(2, 'Олена Бойко', 'Корпоративний', 3);

INSERT INTO dim_store_snowflake VALUES 
(1, 'Магазин №1', 1), (2, 'Магазин №2', 3);

-- Наповнення зірки на основі даних сніжинки
INSERT INTO dim_product_star (product_id, product_name, category_name, department)
SELECT p.product_id, p.product_name, c.category_name, d.department_name
FROM dim_product_snowflake p
JOIN dim_category_snowflake c ON p.category_id = c.category_id
JOIN dim_department_snowflake d ON c.department_id = d.department_id;

INSERT INTO dim_customer_star (customer_id, customer_name, segment, city, region)
SELECT cust.customer_id, cust.customer_name, cust.segment, ct.city_name, r.region_name
FROM dim_customer_snowflake cust
JOIN dim_city_snowflake ct ON cust.city_id = ct.city_id
JOIN dim_region_snowflake r ON ct.region_id = r.region_id;

INSERT INTO dim_store_star (store_id, store_name, city, region)
SELECT s.store_id, s.store_name, ct.city_name, r.region_name
FROM dim_store_snowflake s
JOIN dim_city_snowflake ct ON s.city_id = ct.city_id
JOIN dim_region_snowflake r ON ct.region_id = r.region_id;

-- Наповнення дат (365 днів)
INSERT INTO dim_date_star (date_id, full_date, day, month, quarter, year)
SELECT 
    to_char(d, 'YYYYMMDD')::INT,
    d::DATE,
    EXTRACT(DAY FROM d)::INT,
    EXTRACT(MONTH FROM d)::INT,
    EXTRACT(QUARTER FROM d)::INT,
    EXTRACT(YEAR FROM d)::INT
FROM generate_series('2025-01-01'::DATE, '2025-12-31'::DATE, '1 day'::interval) d;

INSERT INTO dim_date_snowflake SELECT * FROM dim_date_star;

-- Генерація 100 000 фактів продажів
INSERT INTO fact_sales_star (date_id, customer_id, product_id, store_id, quantity, unit_price, total_amount)
SELECT 
    (to_char('2025-01-01'::date + (random() * 360)::int * '1 day'::interval, 'YYYYMMDD'))::INT,
    floor(random() * 2 + 1)::INT,
    floor(random() * 3 + 1)::INT,
    floor(random() * 2 + 1)::INT,
    floor(random() * 5 + 1)::INT,
    150.00,
    (floor(random() * 5 + 1)::INT) * 150.00
FROM generate_series(1, 100000);

INSERT INTO fact_sales_snowflake SELECT * FROM fact_sales_star;

-- ====================================================================
-- 4. ТЕСТОВІ АНАЛІТИЧНІ ЗАПИТИ (ДЛЯ ПОРІВНЯННЯ ПЛАНІВ І ЧАСУ)
-- ====================================================================

-- 4.1. Запит до Схеми «Зірка»
EXPLAIN ANALYZE
SELECT 
    p.department,
    c.region,
    SUM(f.total_amount) AS revenue,
    SUM(f.quantity) AS total_units
FROM fact_sales_star f
JOIN dim_product_star p ON f.product_id = p.product_id
JOIN dim_customer_star c ON f.customer_id = c.customer_id
JOIN dim_date_star d ON f.date_id = d.date_id
WHERE d.quarter = 1 AND d.year = 2025
GROUP BY p.department, c.region;

-- 4.2. Запит до Схеми «Сніжинка»
EXPLAIN ANALYZE
SELECT 
    dep.department_name,
    reg.region_name,
    SUM(f.total_amount) AS revenue,
    SUM(f.quantity) AS total_units
FROM fact_sales_snowflake f
JOIN dim_product_snowflake p ON f.product_id = p.product_id
JOIN dim_category_snowflake cat ON p.category_id = cat.category_id
JOIN dim_department_snowflake dep ON cat.department_id = dep.department_id
JOIN dim_customer_snowflake c ON f.customer_id = c.customer_id
JOIN dim_city_snowflake city ON c.city_id = city.city_id
JOIN dim_region_snowflake reg ON city.region_id = reg.region_id
JOIN dim_date_snowflake d ON f.date_id = d.date_id
WHERE d.quarter = 1 AND d.year = 2025
GROUP BY dep.department_name, reg.region_name;
