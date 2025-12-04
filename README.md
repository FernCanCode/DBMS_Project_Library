# Library Management System 📚

A comprehensive Library Management System built with **Python**, **Streamlit**, and **PostgreSQL**. This application allows library staff to manage books, members, and transactions efficiently through a modern web interface.

## 🚀 Features

*   **Dashboard**: Real-time overview of library statistics, including total books, active members, checked-out items, and active computer sessions.
*   **Book Search**: Search the catalog by Title, Author, or ISBN.
*   **Member Lookup**: View member profiles, including personal details, current checkouts, fines, and computer session usage.
*   **Checkout & Return**: Streamlined process for checking out books to members and returning them to the inventory.
*   **Computer Session Tracking**: Monitor active computer sessions and available terminals.
*   **Reports & Analytics**: Advanced analytics featuring 5 queries with JOINs and GROUP BY operations:
    *   Top Borrowers (members with most checkouts)
    *   Member Fines Analysis (aggregated fine data)
    *   Active Checkouts (current borrowers with book details)
    *   Computer Usage by Card Type (session analytics)
    *   Overdue Books (late returns with member contact info)
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
git clone https://github.com/FernCanCode/DBMS_Project_Library.git
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
psql -d library -f code/schema.sql
```

(Optional) Seed the database with dummy data:
```bash
python3 data/seed_data.py
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
streamlit run code/project.py
```

The app will open automatically in your default web browser at `http://localhost:8501`.

## 🔐 Admin Access

To access the Admin features (All Members & All Books views), use the sidebar login:

*   **Username**: `admin`
*   **Password**: `password`

## 📂 Project Structure

*   `code/project.py`: Main application entry point and UI logic.
*   `code/schema.sql`: Database schema definitions.
*   `data/seed_data.py`: Script to generate and insert dummy data.
*   `requirements.txt`: Python dependencies.

---

## 📊 Required Queries Overview

This project implements **5 user interactions** that execute SQL queries with **JOINs** and/or **GROUP BY** operations, as required by the project specifications. All queries are accessible through the **"Reports & Analytics"** page.

### Query 1: Members with Most Checkouts
**Type:** `JOIN + GROUP BY`  
**Location:** Reports & Analytics → Top Borrowers tab  
**Description:** Displays members ranked by the number of books they currently have checked out. Groups books by borrower and counts the total per member.

**SQL:**
```sql
SELECT lc.card_id, lc.name, lc.card_type, COUNT(b.isbn) as num_books_checked_out
FROM Library_Card lc
JOIN Book b ON lc.card_id = b.lib_card_id
WHERE b.checkout_status = 'Checked Out'
GROUP BY lc.card_id, lc.name, lc.card_type
ORDER BY num_books_checked_out DESC
```

**User Interaction:** Automatically displays when the tab is opened. Shows summary statistics including max books checked out and average per borrower.

---

### Query 2: Total Fines by Member
**Type:** `JOIN + GROUP BY + HAVING`  
**Location:** Reports & Analytics → Member Fines tab  
**Description:** Aggregates fine amounts by member, showing total fines, number of fines, and outstanding amounts. Users can filter by fine status (All/Outstanding/Paid).

**SQL (All Fines):**
```sql
SELECT lc.card_id, lc.name, lc.card_type, 
       SUM(f.amount) as total_fines,
       COUNT(f.fine_id) as num_fines,
       SUM(CASE WHEN f.status = 'Outstanding' THEN f.amount ELSE 0 END) as outstanding_amount
FROM Library_Card lc
JOIN Fine f ON lc.card_id = f.card_id
GROUP BY lc.card_id, lc.name, lc.card_type
ORDER BY total_fines DESC
```

**User Interaction:** Radio button filter to select fine status (All, Outstanding, or Paid). Query dynamically adjusts based on selection.

---

### Query 3: Currently Checked Out Books with Member Information
**Type:** `JOIN`  
**Location:** Reports & Analytics → Active Checkouts tab  
**Description:** Joins the Book and Library_Card tables to show all currently checked-out books along with borrower information and due dates.

**SQL:**
```sql
SELECT b.isbn, b.title, b.author, lc.name as borrower, 
       lc.card_id, b.checkout_date, b.due_date,
       CURRENT_DATE - b.due_date as days_until_due
FROM Book b
JOIN Library_Card lc ON b.lib_card_id = lc.card_id
WHERE b.checkout_status = 'Checked Out'
ORDER BY b.due_date ASC
```

**User Interaction:** Displays complete list of active checkouts with member names, showing which books are due soonest.

---

### Query 4: Computer Sessions by Card Type
**Type:** `JOIN + GROUP BY`  
**Location:** Reports & Analytics → Computer Usage tab  
**Description:** Analyzes computer usage patterns across different membership types (Standard, Student, Senior, Child). Aggregates session counts and calculates averages per card type.

**SQL:**
```sql
SELECT lc.card_type, 
       COUNT(cs.session_id) as total_active_sessions,
       AVG(cs.num_of_sessions) as avg_sessions_per_member,
       SUM(cs.num_of_sessions) as total_sessions_all_time
FROM Library_Card lc
JOIN Computers_Session cs ON lc.card_id = cs.card_id
GROUP BY lc.card_type
ORDER BY total_active_sessions DESC
```

**User Interaction:** Displays aggregated data in a table and bar chart visualization showing session distribution across card types.

---

### Query 5: Overdue Books with Member Contact Information
**Type:** `JOIN` (with date-based filtering)  
**Location:** Reports & Analytics → Overdue Books tab  
**Description:** Finds all overdue books by joining Book and Library_Card tables, filtering for items past their due date. Calculates days overdue and potential fines.

**SQL:**
```sql
SELECT b.isbn, b.title, b.author, lc.card_id, lc.name as borrower, 
       lc.card_type, b.checkout_date, b.due_date,
       CURRENT_DATE - b.due_date as days_overdue
FROM Book b
JOIN Library_Card lc ON b.lib_card_id = lc.card_id
WHERE b.checkout_status = 'Checked Out' 
  AND b.due_date < CURRENT_DATE
ORDER BY days_overdue DESC
```

**User Interaction:** Automatically displays overdue items with warning indicators. Shows metrics for total days overdue and calculates potential fines at $0.50/day.

---

### Implementation Summary

All 5 queries are implemented in the `code/project.py` file within the "Reports & Analytics" page (lines 249-430). Each query:
- Combines data from multiple tables using JOINs
- Uses aggregation functions (COUNT, SUM, AVG) with GROUP BY where applicable
- Provides meaningful user interactions (filters, radio buttons, tabs)
- Displays results in interactive Streamlit dataframes with metrics and visualizations
- Returns interesting results based on the realistic data loaded via `seed_data.py`

The queries satisfy the project requirement of "at least 5 kinds of user interactions that lead to executing a query with a join, a group by, or both."
