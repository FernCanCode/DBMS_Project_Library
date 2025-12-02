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
pages = ["Dashboard", "Book Search", "Member Lookup", "Checkout", "Return", "Reports & Analytics"]
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

elif page == "Reports & Analytics":
    st.title("📊 Reports & Analytics")
    st.markdown("### Advanced queries with JOINs and GROUP BY operations")
    
    # Create tabs for different reports
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📚 Top Borrowers", 
        "💰 Member Fines", 
        "📖 Active Checkouts",
        "💻 Computer Usage",
        "⏰ Overdue Books"
    ])
    
    with tab1:
        st.subheader("Members with Most Checkouts")
        st.markdown("**Query Type:** JOIN + GROUP BY")
        st.markdown("**Tables Involved:** Library_Card, Book")
        st.markdown("Shows members ranked by number of currently checked-out books")
        
        # Query 1: Member with Most Checkouts (GROUP BY + JOIN)
        query1 = """
            SELECT lc.card_id, lc.name, lc.card_type, COUNT(b.isbn) as num_books_checked_out
            FROM Library_Card lc
            JOIN Book b ON lc.card_id = b.lib_card_id
            WHERE b.checkout_status = 'Checked Out'
            GROUP BY lc.card_id, lc.name, lc.card_type
            ORDER BY num_books_checked_out DESC
            LIMIT 15
        """
        result1 = run_query(query1)
        
        if not result1.empty:
            st.dataframe(result1, use_container_width=True)
            
            # Show summary stats
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Active Borrowers", len(result1))
            with col2:
                st.metric("Max Books Out", result1['num_books_checked_out'].max())
            with col3:
                st.metric("Avg Books/Borrower", f"{result1['num_books_checked_out'].mean():.2f}")
        else:
            st.info("No active checkouts found.")
    
    with tab2:
        st.subheader("Total Fines by Member")
        st.markdown("**Query Type:** JOIN + GROUP BY + HAVING")
        st.markdown("**Tables Involved:** Library_Card, Fine")
        st.markdown("Displays members with outstanding or paid fines, aggregated by member")
        
        # Filter options
        fine_status_filter = st.radio("Filter by Fine Status:", ["All", "Outstanding", "Paid"], horizontal=True)
        
        # Query 2: Total Fines by Member (GROUP BY + JOIN)
        if fine_status_filter == "All":
            query2 = """
                SELECT lc.card_id, lc.name, lc.card_type, 
                       SUM(f.amount) as total_fines,
                       COUNT(f.fine_id) as num_fines,
                       SUM(CASE WHEN f.status = 'Outstanding' THEN f.amount ELSE 0 END) as outstanding_amount
                FROM Library_Card lc
                JOIN Fine f ON lc.card_id = f.card_id
                GROUP BY lc.card_id, lc.name, lc.card_type
                ORDER BY total_fines DESC
            """
        else:
            query2 = f"""
                SELECT lc.card_id, lc.name, lc.card_type, 
                       SUM(f.amount) as total_fines,
                       COUNT(f.fine_id) as num_fines
                FROM Library_Card lc
                JOIN Fine f ON lc.card_id = f.card_id
                WHERE f.status = '{fine_status_filter}'
                GROUP BY lc.card_id, lc.name, lc.card_type
                HAVING SUM(f.amount) > 0
                ORDER BY total_fines DESC
            """
        
        result2 = run_query(query2)
        
        if not result2.empty:
            st.dataframe(result2, use_container_width=True)
            
            # Summary metrics
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Fines Recorded", f"${result2['total_fines'].sum():.2f}")
            with col2:
                if 'outstanding_amount' in result2.columns:
                    st.metric("Total Outstanding", f"${result2['outstanding_amount'].sum():.2f}")
                else:
                    st.metric("Members with Fines", len(result2))
        else:
            st.info(f"No {fine_status_filter.lower()} fines found.")
    
    with tab3:
        st.subheader("Currently Checked Out Books with Member Information")
        st.markdown("**Query Type:** JOIN")
        st.markdown("**Tables Involved:** Book, Library_Card")
        st.markdown("Lists all checked-out books along with borrower details and due dates")
        
        # Query 3: Books Checked Out with Member Info (JOIN)
        query3 = """
            SELECT b.isbn, b.title, b.author, lc.name as borrower, 
                   lc.card_id, b.checkout_date, b.due_date,
                   CURRENT_DATE - b.due_date as days_until_due
            FROM Book b
            JOIN Library_Card lc ON b.lib_card_id = lc.card_id
            WHERE b.checkout_status = 'Checked Out'
            ORDER BY b.due_date ASC
        """
        result3 = run_query(query3)
        
        if not result3.empty:
            st.dataframe(result3, use_container_width=True)
            st.metric("Total Books Checked Out", len(result3))
        else:
            st.info("No books currently checked out.")
    
    with tab4:
        st.subheader("Computer Sessions by Card Type")
        st.markdown("**Query Type:** JOIN + GROUP BY")
        st.markdown("**Tables Involved:** Library_Card, Computers_Session")
        st.markdown("Analyzes computer usage patterns across different membership types")
        
        # Query 4: Computer Sessions by Card Type (GROUP BY + JOIN)
        query4 = """
            SELECT lc.card_type, 
                   COUNT(cs.session_id) as total_active_sessions,
                   AVG(cs.num_of_sessions) as avg_sessions_per_member,
                   SUM(cs.num_of_sessions) as total_sessions_all_time
            FROM Library_Card lc
            JOIN Computers_Session cs ON lc.card_id = cs.card_id
            GROUP BY lc.card_type
            ORDER BY total_active_sessions DESC
        """
        result4 = run_query(query4)
        
        if not result4.empty:
            st.dataframe(result4, use_container_width=True)
            
            # Visualization
            st.markdown("#### Session Distribution by Card Type")
            chart_data = result4.set_index('card_type')['total_active_sessions']
            st.bar_chart(chart_data)
        else:
            st.info("No computer session data available.")
    
    with tab5:
        st.subheader("Overdue Books with Member Contact Information")
        st.markdown("**Query Type:** JOIN with Date Filtering")
        st.markdown("**Tables Involved:** Book, Library_Card")
        st.markdown("Shows all overdue books with borrower details for follow-up")
        
        # Query 5: Overdue Books with Member Contact (JOIN)
        query5 = """
            SELECT b.isbn, b.title, b.author, lc.card_id, lc.name as borrower, 
                   lc.card_type, b.checkout_date, b.due_date,
                   CURRENT_DATE - b.due_date as days_overdue
            FROM Book b
            JOIN Library_Card lc ON b.lib_card_id = lc.card_id
            WHERE b.checkout_status = 'Checked Out' 
              AND b.due_date < CURRENT_DATE
            ORDER BY days_overdue DESC
        """
        result5 = run_query(query5)
        
        if not result5.empty:
            st.warning(f"⚠️ {len(result5)} overdue book(s) found!")
            st.dataframe(result5, use_container_width=True)
            
            # Calculate potential fines (assuming $0.50/day)
            total_days_overdue = result5['days_overdue'].sum()
            potential_fines = total_days_overdue * 0.50
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Days Overdue", int(total_days_overdue))
            with col2:
                st.metric("Potential Fines (@$0.50/day)", f"${potential_fines:.2f}")
        else:
            st.success("✅ No overdue books!")

elif page == "All Members":
    st.title("👥 All Members")
    members = run_query("SELECT * FROM Library_Card ORDER BY card_id")
    st.dataframe(members, use_container_width=True)

elif page == "All Books":
    st.title("📚 All Books")
    books = run_query("SELECT * FROM Book ORDER BY title")
    st.dataframe(books, use_container_width=True)
