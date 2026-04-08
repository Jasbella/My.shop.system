import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# Database setup
def init_db():
    conn = sqlite3.connect('shop.db', check_same_thread=False)
    conn.execute('''CREATE TABLE IF NOT EXISTS stock 
                    (name TEXT PRIMARY KEY, qty INTEGER, price REAL)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS sales 
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, item TEXT, qty INTEGER, total REAL, date TEXT)''')
    conn.commit()
    return conn

conn = init_db()

st.set_page_config(page_title="Shop Manager Pro", layout="wide")
st.title("📦 Shop Inventory & Sales")

menu = ["Inventory Dashboard", "Add/Restock", "Record a Sale", "Sales History"]
choice = st.sidebar.radio("Menu", menu)

if choice == "Inventory Dashboard":
    st.subheader("Current Stock")
    df = pd.read_sql('SELECT * FROM stock', conn)
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        low_stock = df[df['qty'] < 5]
        if not low_stock.empty:
            st.warning(f"Low stock on: {', '.join(low_stock['name'].tolist())}")
    else:
        st.info("Inventory is empty.")

elif choice == "Add/Restock":
    with st.form("add_form"):
        name = st.text_input("Product Name").strip().title()
        qty = st.number_input("Quantity", min_value=1)
        price = st.number_input("Price", min_value=0.0)
        if st.form_submit_button("Update Stock") and name:
            existing = conn.execute("SELECT qty FROM stock WHERE name=?", (name,)).fetchone()
            if existing:
                conn.execute("UPDATE stock SET qty=qty+?, price=? WHERE name=?", (qty, price, name))
            else:
                conn.execute("INSERT INTO stock VALUES (?, ?, ?)", (name, qty, price))
            conn.commit()
            st.success(f"Updated {name}")

elif choice == "Record a Sale":
    items = [r[0] for r in conn.execute("SELECT name FROM stock WHERE qty > 0").fetchall()]
    if items:
        with st.form("sale_form"):
            item = st.selectbox("Select Product", items)
            q_sold = st.number_input("Quantity Sold", min_value=1)
            if st.form_submit_button("Sell"):
                res = conn.execute("SELECT qty, price FROM stock WHERE name=?", (item,)).fetchone()
                if res[0] >= q_sold:
                    total = q_sold * res[1]
                    conn.execute("UPDATE stock SET qty=qty-? WHERE name=?", (q_sold, item))
                    conn.execute("INSERT INTO sales (item, qty, total, date) VALUES (?,?,?,?)",
                                 (item, q_sold, total, datetime.now().strftime("%Y-%m-%d %H:%M")))
                    conn.commit()
                    st.success(f"Sold {q_sold} {item} for ${total:.2f}")
                else:
                    st.error("Not enough stock!")
    else:
        st.warning("No items available.")

elif choice == "Sales History":
    sales_df = pd.read_sql('SELECT * FROM sales ORDER BY id DESC', conn)
    if not sales_df.empty:
        st.metric("Total Revenue", f"${sales_df['total'].sum():,.2f}")
        st.table(sales_df)
