import streamlit as st
import psycopg2
import pandas as pd

# Page Config
st.set_page_config(
    page_title="Library Management System",
    page_icon="📚",
    layout="wide"
)

# Database Connection
@st.cache_resource
def init_connection():
    return psycopg2.connect(
        host=st.secrets["postgres"]["host"],
        port=st.secrets["postgres"]["port"],
        database=st.secrets["postgres"]["dbname"],
        user=st.secrets["postgres"]["user"],
        password=st.secrets["postgres"]["password"]
    )

conn = init_connection()

# Helper function to run queries
def run_query(query, params=None):
    with conn.cursor() as cur:
        cur.execute(query, params)
        if query.strip().upper().startswith("SELECT"):
            col_names = [desc[0] for desc in cur.description]
            data = cur.fetchall()
            return pd.DataFrame(data, columns=col_names)
        else:
            conn.commit()
            return None

# Sidebar Navigation
st.sidebar.title("Navigation")

# Session State for Admin
if 'is_admin' not in st.session_state:
    st.session_state['is_admin'] = False

# Login/Logout Logic
if not st.session_state['is_admin']:
    with st.sidebar.expander("Admin Login"):
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit_login = st.form_submit_button("Login")
            
            if submit_login:
                if username == "admin" and password == "password":
                    st.session_state['is_admin'] = True
                    st.rerun()
                else:
                    st.error("Invalid credentials")
else:
    if st.sidebar.button("Logout"):
        st.session_state['is_admin'] = False
        st.rerun()
    st.sidebar.success("Logged in as Admin")

# Define Pages
pages = ["Dashboard", "Book Search", "Member Lookup", "Checkout", "Return"]
if st.session_state['is_admin']:
    pages.extend(["All Members", "All Books"])

page = st.sidebar.radio("Go to", pages)

if page == "Dashboard":
    st.title("📚 Library Dashboard")
    
    # Key Metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_books = run_query("SELECT COUNT(*) FROM Book").iloc[0, 0]
        st.metric("Total Books", total_books)
        
    with col2:
        active_members = run_query("SELECT COUNT(*) FROM Library_Card WHERE status = 'Active'").iloc[0, 0]
        st.metric("Active Members", active_members)
        
    with col3:
        checked_out = run_query("SELECT COUNT(*) FROM Book WHERE checkout_status = 'Checked Out'").iloc[0, 0]
        st.metric("Books Checked Out", checked_out)

    with col4:
        active_sessions = run_query("SELECT COUNT(*) FROM Computers_Session").iloc[0, 0]
        st.metric("Active Computer Sessions", active_sessions)

    with col5:
        # Taking the most recent value for remaining computers
        computers_avail = run_query("SELECT remaining_computers FROM Computers_Session ORDER BY session_id DESC LIMIT 1")
        if not computers_avail.empty:
            st.metric("Computers Avail", computers_avail.iloc[0, 0])
        else:
            st.metric("Computers Avail", "N/A")

    st.markdown("---")
    
    # Recent Activity or Overview
    st.subheader("Recent Books Added")
    recent_books = run_query("SELECT title, author, purchase_date FROM Book ORDER BY purchase_date DESC LIMIT 5")
    st.table(recent_books)

elif page == "Book Search":
    st.title("🔍 Book Search")
    
    search_term = st.text_input("Search by Title, Author, or ISBN")
    
    if search_term:
        query = """
            SELECT isbn, title, author, condition, checkout_status 
            FROM Book 
            WHERE title ILIKE %s OR author ILIKE %s OR isbn ILIKE %s
        """
        search_pattern = f"%{search_term}%"
        results = run_query(query, (search_pattern, search_pattern, search_pattern))
        
        if not results.empty:
            st.dataframe(results, use_container_width=True)
        else:
            st.info("No books found matching your search.")
    else:
        # Show all books by default (limit to 50)
        st.subheader("All Books")
        all_books = run_query("SELECT isbn, title, author, condition, checkout_status FROM Book LIMIT 50")
        st.dataframe(all_books, use_container_width=True)

elif page == "Member Lookup":
    st.title("👤 Member Lookup")
    
    member_search = st.text_input("Search by Name or Card ID")
    
    if member_search:
        # Try to parse as ID if it's a number, otherwise search name
        if member_search.isdigit():
            query = "SELECT * FROM Library_Card WHERE card_id = %s"
            params = (int(member_search),)
        else:
            query = "SELECT * FROM Library_Card WHERE name ILIKE %s"
            params = (f"%{member_search}%",)
            
        members = run_query(query, params)
        
        if not members.empty:
            for _, member in members.iterrows():
                with st.expander(f"{member['name']} (ID: {member['card_id']}) - {member['status']}"):
                    st.write(f"**Type:** {member['card_type']}")
                    st.write(f"**DOB:** {member['dob']}")
                    
                    # Show computer session info
                    comp_session = run_query("SELECT num_of_sessions FROM Computers_Session WHERE card_id = %s", (member['card_id'],))
                    sessions_used = comp_session.iloc[0, 0] if not comp_session.empty else 0
                    st.write(f"**Computer Sessions Used:** {sessions_used}")
                    
                    # Show current checkouts
                    checkouts = run_query("""
                        SELECT title, due_date 
                        FROM Book 
                        WHERE lib_card_id = %s AND checkout_status = 'Checked Out'
                    """, (member['card_id'],))
                    
                    if not checkouts.empty:
                        st.subheader("Current Checkouts")
                        st.table(checkouts)
                    else:
                        st.write("No active checkouts.")
                        
                    # Show fines
                    fines = run_query("SELECT amount, status FROM Fine WHERE card_id = %s", (member['card_id'],))
                    if not fines.empty:
                        st.subheader("Fines")
                        st.table(fines)
        else:
            st.warning("No members found.")

elif page == "Checkout":
    st.title("📖 Checkout Book")
    
    with st.form("checkout_form"):
        isbn = st.text_input("Book ISBN")
        card_id = st.text_input("Library Card ID")
        submitted = st.form_submit_button("Checkout")
        
        if submitted:
            if not isbn or not card_id:
                st.error("Please provide both ISBN and Card ID.")
            else:
                # Check if book exists and is available
                book_check = run_query("SELECT checkout_status, title FROM Book WHERE isbn = %s", (isbn,))
                
                if book_check.empty:
                    st.error("Book not found.")
                elif book_check.iloc[0]['checkout_status'] == 'Checked Out':
                    st.error(f"'{book_check.iloc[0]['title']}' is already checked out.")
                else:
                    # Check if card exists and is active
                    card_check = run_query("SELECT status, name FROM Library_Card WHERE card_id = %s", (card_id,))
                    
                    if card_check.empty:
                        st.error("Library Card not found.")
                    elif card_check.iloc[0]['status'] != 'Active':
                        st.error(f"Card for {card_check.iloc[0]['name']} is not Active (Status: {card_check.iloc[0]['status']}).")
                    else:
                        # Perform Checkout
                        from datetime import datetime, timedelta
                        checkout_date = datetime.now().date()
                        due_date = checkout_date + timedelta(days=14)
                        
                        run_query("""
                            UPDATE Book 
                            SET lib_card_id = %s, checkout_date = %s, due_date = %s, checkout_status = 'Checked Out'
                            WHERE isbn = %s
                        """, (card_id, checkout_date, due_date, isbn))
                        
                        st.success(f"Successfully checked out '{book_check.iloc[0]['title']}' to {card_check.iloc[0]['name']}!")

elif page == "Return":
    st.title("🔙 Return Book")
    
    with st.form("return_form"):
        isbn = st.text_input("Book ISBN")
        submitted = st.form_submit_button("Return")
        
        if submitted:
            if not isbn:
                st.error("Please provide an ISBN.")
            else:
                # Check if book exists and is checked out
                book_check = run_query("SELECT checkout_status, title FROM Book WHERE isbn = %s", (isbn,))
                
                if book_check.empty:
                    st.error("Book not found.")
                elif book_check.iloc[0]['checkout_status'] == 'Available':
                    st.info(f"'{book_check.iloc[0]['title']}' is already marked as Available.")
                else:
                    # Perform Return
                    run_query("""
                        UPDATE Book 
                        SET lib_card_id = NULL, checkout_date = NULL, due_date = NULL, checkout_status = 'Available'
                        WHERE isbn = %s
                    """, (isbn,))
                    
                    st.success(f"Successfully returned '{book_check.iloc[0]['title']}'!")

elif page == "All Members":
    st.title("👥 All Members")
    members = run_query("SELECT * FROM Library_Card ORDER BY card_id")
    st.dataframe(members, use_container_width=True)

elif page == "All Books":
    st.title("📚 All Books")
    books = run_query("SELECT * FROM Book ORDER BY title")
    st.dataframe(books, use_container_width=True)
