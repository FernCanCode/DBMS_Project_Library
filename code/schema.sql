-- 1. LIBRARY_CARD (The central entity)
CREATE TABLE Library_Card (
    card_id SERIAL PRIMARY KEY,              -- PK: ID # (Renamed for clarity)
    name VARCHAR(100) NOT NULL,
    dob DATE,                                 -- DOB (Date of Birth)
    card_type VARCHAR(50),                    -- TYPE
    status VARCHAR(50)                        -- STATUS (e.g., Active, Suspended)
);

-- 2. IDENTIFICATION (Links external ID to the card)
CREATE TABLE Identification (
    outside_id_pk VARCHAR(50) PRIMARY KEY,    -- PK: Outside ID#
    is_adult BOOLEAN,
    is_valid BOOLEAN,
    card_id INTEGER REFERENCES Library_Card(card_id), -- FK: LibID# (Links to Library_Card)
    is_local BOOLEAN,
    -- Constraint enforces the "One Card per ID" relationship:
    UNIQUE (card_id)
);

-- 3. COMPUTERS_SESSION (Tracks computer usage)
CREATE TABLE Computers_Session (
    session_id SERIAL PRIMARY KEY,            -- PK: SessionID
    card_id INTEGER REFERENCES Library_Card(card_id), -- FK: Links to Library_Card
    num_of_sessions INTEGER,
    -- Note: Remaining # of Computers is usually tracked in an inventory table, 
    -- but we include it here as requested.
    remaining_computers INTEGER,
    -- Constraint enforces the "One session per card" (if we track only current session):
    UNIQUE (card_id)
);

-- 4. BOOK (Contains book metadata and current transaction info)
-- NOTE: In a real database, transaction details (Checkout Date) would be in a separate table.
CREATE TABLE Book (
    isbn VARCHAR(20) PRIMARY KEY,             -- PK: ISBN (Standard unique identifier)
    title VARCHAR(255) NOT NULL,              -- TITLE
    author VARCHAR(100),                      -- Author
    condition VARCHAR(50),                    -- Condition
    purchase_date DATE,
    -- Transactional fields linked to the current borrower:
    lib_card_id INTEGER REFERENCES Library_Card(card_id), -- FK: LibID (Current borrower)
    checkout_date DATE,
    due_date DATE,
    checkout_status VARCHAR(50)               -- Checkout Status
);

-- 5. ITEMS (Catch-all for non-book items like DVDs, equipment)
CREATE TABLE Items (
    item_id SERIAL PRIMARY KEY,               -- PK: Item ID#
    card_id INTEGER REFERENCES Library_Card(card_id), -- FK: Lib ID# (Current borrower)
    name VARCHAR(255) NOT NULL,               -- Name (e.g., 'A/V Equipment')
    checkout_date DATE,
    due_date DATE
);

-- 6. FINE (Tracks fines accrued by patrons)
CREATE TABLE Fine (
    fine_id SERIAL PRIMARY KEY,               -- PK: Fine ID
    card_id INTEGER REFERENCES Library_Card(card_id), -- FK: LibID (Patron who owes the fine)
    item_id INTEGER REFERENCES Items(item_id), -- FK: Item ID# (What the fine is for)
    isbn VARCHAR(20) REFERENCES Book(isbn),   -- FK: ISBN (If the fine is for a book)
    amount NUMERIC(5, 2) NOT NULL,
    status VARCHAR(50)                        -- Status (e.g., Paid, Outstanding)
);
