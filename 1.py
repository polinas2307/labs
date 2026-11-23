import psycopg2
from faker import Faker
import random

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "lab0",       
    "user": "postgres",
    "password": "your_password",  
}

fake = Faker("uk_UA")


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


# ---------------------------------------------------------------
# Наповнення даними
# ---------------------------------------------------------------
def seed_data(conn, n_customers=15, n_products=10, n_orders=20):
    with conn.cursor() as cur:
        # Клієнти
        cities = ["Львів", "Київ", "Одеса", "Харків", "Дніпро", "Івано-Франківськ"]
        for _ in range(n_customers):
            cur.execute(
                "INSERT INTO customers (full_name, email, phone, city) VALUES (%s, %s, %s, %s)",
                (fake.name(), fake.unique.email(), fake.phone_number(), random.choice(cities)),
            )

        # Товари
        catalog = [
            ("Ноутбук ASUS", "Електроніка", 24999.00),
            ("Смартфон Samsung", "Електроніка", 15999.00),
            ("Навушники JBL", "Аксесуари", 1899.00),
            ("Кава в зернах 1кг", "Продукти", 349.00),
            ("Книга 'Кобзар'", "Книги", 199.00),
            ("Кросівки Nike", "Одяг", 2799.00),
            ("Рюкзак міський", "Аксесуари", 1299.00),
            ("Настільна лампа", "Дім", 599.00),
            ("Термос 1л", "Дім", 449.00),
            ("Ігрова миша", "Електроніка", 899.00),
        ]
        for name, category, price in catalog[:n_products]:
            cur.execute(
                "INSERT INTO products (name, category, price) VALUES (%s, %s, %s)",
                (name, category, price),
            )

        conn.commit()

        cur.execute("SELECT customer_id FROM customers")
        customer_ids = [row[0] for row in cur.fetchall()]
        cur.execute("SELECT product_id, price FROM products")
        products = cur.fetchall()  # [(id, price), ...]

        statuses = ["new", "paid", "shipped", "cancelled"]

        # Замовлення + позиції замовлень
        for _ in range(n_orders):
            cur.execute(
                "INSERT INTO orders (customer_id, order_date, status) VALUES (%s, %s, %s) RETURNING order_id",
                (random.choice(customer_ids), fake.date_this_year(), random.choice(statuses)),
            )
            order_id = cur.fetchone()[0]

            # у кожне замовлення додамо 1-3 товари
            for _ in range(random.randint(1, 3)):
                product_id, price = random.choice(products)
                qty = random.randint(1, 3)
                cur.execute(
                    "INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (%s, %s, %s, %s)",
                    (order_id, product_id, qty, price),
                )

        conn.commit()
    print(f"Додано: {n_customers} клієнтів, {n_products} товарів, {n_orders} замовлень.")


# ---------------------------------------------------------------
# SELECT
# ---------------------------------------------------------------
def select_examples(conn):
    with conn.cursor() as cur:
        print("\n--- Усі клієнти ---")
        cur.execute("SELECT customer_id, full_name, email, city FROM customers ORDER BY customer_id")
        for row in cur.fetchall():
            print(row)

        print("\n--- Сума замовлень по кожному клієнту (JOIN + GROUP BY) ---")
        cur.execute("""
            SELECT c.full_name, COUNT(DISTINCT o.order_id) AS orders_count,
                   COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS total_spent
            FROM customers c
            LEFT JOIN orders o ON o.customer_id = c.customer_id
            LEFT JOIN order_items oi ON oi.order_id = o.order_id
            GROUP BY c.customer_id, c.full_name
            ORDER BY total_spent DESC
            LIMIT 10
        """)
        for row in cur.fetchall():
            print(row)

        print("\n--- Найпопулярніші товари ---")
        cur.execute("""
            SELECT p.name, SUM(oi.quantity) AS total_sold
            FROM order_items oi
            JOIN products p ON p.product_id = oi.product_id
            GROUP BY p.name
            ORDER BY total_sold DESC
        """)
        for row in cur.fetchall():
            print(row)


# ---------------------------------------------------------------
# INSERT
# ---------------------------------------------------------------
def insert_example(conn):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO customers (full_name, email, phone, city) VALUES (%s, %s, %s, %s) RETURNING customer_id",
            ("Тестовий Клієнт", "test.customer@example.com", "+380000000000", "Львів"),
        )
        new_id = cur.fetchone()[0]
        conn.commit()
        print(f"\nДодано нового клієнта з id={new_id}")
        return new_id


# ---------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------
def update_example(conn, customer_id):
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE customers SET city = %s WHERE customer_id = %s",
            ("Київ", customer_id),
        )
        conn.commit()
        print(f"Оновлено клієнта id={customer_id}: місто -> Київ")


# ---------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------
def delete_example(conn, customer_id):
    with conn.cursor() as cur:
        cur.execute("DELETE FROM customers WHERE customer_id = %s", (customer_id,))
        conn.commit()
        print(f"Видалено клієнта id={customer_id}")


def main():
    conn = get_connection()
    try:
        seed_data(conn)
        select_examples(conn)
        new_id = insert_example(conn)
        update_example(conn, new_id)
        delete_example(conn, new_id)

        print("\n--- Стан таблиці customers після усіх операцій ---")
        select_examples(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
