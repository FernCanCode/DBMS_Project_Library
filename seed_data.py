import psycopg2
from faker import Faker
import random
from datetime import datetime, timedelta

fake = Faker()

# Database connection parameters - UPDATE THESE IF NEEDED
DB_HOST = "localhost"
DB_NAME = "library"
DB_USER = "ferncancode"
DB_PASS = "123Lyons420"

def create_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def seed_data():
    conn = create_connection()
    if not conn:
        return

    cur = conn.cursor()

    try:
        # Clear existing data (optional, be careful in production)
        cur.execute("TRUNCATE TABLE Fine, Items, Book, Computers_Session, Identification, Library_Card RESTART IDENTITY CASCADE;")
        
        print("Seeding Library_Card...")
        card_ids = []
        for _ in range(50):
            name = fake.name()
            dob = fake.date_of_birth(minimum_age=5, maximum_age=90)
            card_type = random.choice(['Standard', 'Student', 'Senior', 'Child'])
            status = random.choice(['Active', 'Active', 'Active', 'Suspended'])
            
            cur.execute(
                "INSERT INTO Library_Card (name, dob, card_type, status) VALUES (%s, %s, %s, %s) RETURNING card_id;",
                (name, dob, card_type, status)
            )
            card_ids.append(cur.fetchone()[0])

        print("Seeding Identification...")
        for card_id in card_ids:
            outside_id = fake.unique.ssn()
            is_adult = fake.boolean()
            is_valid = True
            is_local = fake.boolean()
            
            cur.execute(
                "INSERT INTO Identification (outside_id_pk, is_adult, is_valid, card_id, is_local) VALUES (%s, %s, %s, %s, %s);",
                (outside_id, is_adult, is_valid, card_id, is_local)
            )

        print("Seeding Computers_Session...")
        # Not all cards have sessions
        for card_id in random.sample(card_ids, 20):
            num_sessions = random.randint(0, 10)
            remaining = random.randint(0, 5)
            cur.execute(
                "INSERT INTO Computers_Session (card_id, num_of_sessions, remaining_computers) VALUES (%s, %s, %s);",
                (card_id, num_sessions, remaining)
            )

        print("Seeding Book...")
        book_isbns = []
        for _ in range(100):
            isbn = fake.unique.isbn13()
            title = fake.sentence(nb_words=4).replace(".", "")
            author = fake.name()
            condition = random.choice(['New', 'Good', 'Fair', 'Poor'])
            purchase_date = fake.date_between(start_date='-5y', end_date='today')
            
            # Randomly checkout some books
            lib_card_id = None
            checkout_date = None
            due_date = None
            checkout_status = 'Available'
            
            if random.random() < 0.3: # 30% checked out
                lib_card_id = random.choice(card_ids)
                checkout_date = fake.date_between(start_date='-1M', end_date='today')
                due_date = checkout_date + timedelta(days=14)
                checkout_status = 'Checked Out'

            cur.execute(
                """INSERT INTO Book (isbn, title, author, condition, purchase_date, lib_card_id, checkout_date, due_date, checkout_status) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING isbn;""",
                (isbn, title, author, condition, purchase_date, lib_card_id, checkout_date, due_date, checkout_status)
            )
            book_isbns.append(cur.fetchone()[0])

        print("Seeding Items...")
        item_ids = []
        for _ in range(20):
            card_id = random.choice(card_ids) if random.random() < 0.5 else None
            name = random.choice(['Laptop', 'Projector', 'Headphones', 'Tablet'])
            checkout_date = fake.date_between(start_date='-1M', end_date='today') if card_id else None
            due_date = checkout_date + timedelta(days=3) if checkout_date else None
            
            cur.execute(
                "INSERT INTO Items (card_id, name, checkout_date, due_date) VALUES (%s, %s, %s, %s) RETURNING item_id;",
                (card_id, name, checkout_date, due_date)
            )
            item_ids.append(cur.fetchone()[0])

        print("Seeding Fine...")
        for _ in range(15):
            card_id = random.choice(card_ids)
            amount = round(random.uniform(1.0, 50.0), 2)
            status = random.choice(['Paid', 'Outstanding'])
            
            # Link to item or book randomly
            item_id = None
            isbn = None
            if random.random() < 0.5 and item_ids:
                item_id = random.choice(item_ids)
            elif book_isbns:
                isbn = random.choice(book_isbns)
                
            cur.execute(
                "INSERT INTO Fine (card_id, item_id, isbn, amount, status) VALUES (%s, %s, %s, %s, %s);",
                (card_id, item_id, isbn, amount, status)
            )

        conn.commit()
        print("Database seeded successfully!")

    except Exception as e:
        conn.rollback()
        print(f"Error seeding data: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    seed_data()
