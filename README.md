# Library Management System 📚

A comprehensive Library Management System built with **Python**, **Streamlit**, and **PostgreSQL**. This application allows library staff to manage books, members, and transactions efficiently through a modern web interface.

## 🚀 Features

*   **Dashboard**: Real-time overview of library statistics, including total books, active members, checked-out items, and active computer sessions.
*   **Book Search**: Search the catalog by Title, Author, or ISBN.
*   **Member Lookup**: View member profiles, including personal details, current checkouts, fines, and computer session usage.
*   **Checkout & Return**: Streamlined process for checking out books to members and returning them to the inventory.
*   **Computer Session Tracking**: Monitor active computer sessions and available terminals.
*   **Admin Portal**: Secure login for administrators to view complete lists of all members and books.

## 🛠️ Tech Stack

*   **Frontend**: [Streamlit](https://streamlit.io/)
*   **Backend**: Python
*   **Database**: PostgreSQL
*   **Libraries**: `psycopg2-binary`, `pandas`, `faker` (for seeding data)

## ⚙️ Installation & Setup

### Prerequisites
*   Python 3.8+
*   PostgreSQL installed and running locally

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/library-management-system.git
cd library-management-system
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Database Setup
Create the database and apply the schema:
```bash
createdb library
psql -d library -f schema.sql
```

(Optional) Seed the database with dummy data:
```bash
python3 seed_data.py
```

### 4. Configure Secrets
Create a file named `.streamlit/secrets.toml` in the project root directory and add your database credentials:

```toml
[postgres]
host = "localhost"
port = 5432
dbname = "library"
user = "your_postgres_user"
password = "your_postgres_password"
```

## 🏃‍♂️ Running the Application

Launch the Streamlit application:

```bash
streamlit run app.py
```

The app will open automatically in your default web browser at `http://localhost:8501`.

## 🔐 Admin Access

To access the Admin features (All Members & All Books views), use the sidebar login:

*   **Username**: `admin`
*   **Password**: `password`

## 📂 Project Structure

*   `app.py`: Main application entry point and UI logic.
*   `schema.sql`: Database schema definitions.
*   `seed_data.py`: Script to generate and insert dummy data.
*   `requirements.txt`: Python dependencies.
