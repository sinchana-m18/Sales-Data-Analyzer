import streamlit as st
import pandas as pd
import sqlite3
import datetime
import matplotlib.pyplot as plt
import plotly.express as px
import os
import random

def get_data_as_df(start_date=None, end_date=None, product_name=None):
    """
    Connects to the database and retrieves all sales data as a pandas DataFrame, with optional date and product filtering.
    """
    conn = sqlite3.connect('sales.db')
    query = '''
    SELECT 
        s.sale_date, 
        p.product_name, 
        p.stock_quantity,
        s.quantity, 
        p.price,
        p.last_cost_per_unit AS cost_price, 
        s.quantity * p.price AS total_revenue
    FROM sales s
    JOIN products p ON s.product_id = p.product_id
    '''
    where_clauses = []
    if start_date and end_date:
        where_clauses.append(f"s.sale_date BETWEEN '{start_date}' AND '{end_date}'")
    if product_name and product_name != "All Products":
        where_clauses.append(f"p.product_name = '{product_name}'")
    
    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)
    
    query += " ORDER BY s.sale_date"
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_product_names_and_stock():
    """
    Retrieves a list of product names, IDs, and their current stock quantity.
    """
    conn = sqlite3.connect('sales.db')
    query = 'SELECT product_id, product_name, stock_quantity FROM products'
    df = pd.read_sql_query(query, conn)
    conn.close()
    return {row['product_name']: {'id': row['product_id'], 'stock': row['stock_quantity']} for index, row in df.iterrows()}

def add_new_sale_form(product_names_dict):
    """
    Creates a form to add new sales records to the database, with stock validation.
    """
    with st.form(key='add_sale_form'):
        st.header("Add New Sale")
        selected_product = st.selectbox("Select Product", list(product_names_dict.keys()), key="sale_product_select")
        quantity = st.number_input("Enter Quantity", min_value=1, step=1, key="sale_quantity_input")
        
        product_id = product_names_dict[selected_product]['id']
        
        sale_date = st.date_input("Enter Sale Date", datetime.date.today(), key="sale_date_input")

        submit_button = st.form_submit_button(label='Add Sale')

        if submit_button:
            conn = sqlite3.connect('sales.db')
            cursor = conn.cursor()

            try:
                cursor.execute('SELECT stock_quantity FROM products WHERE product_id = ?', (product_id,))
                current_stock = cursor.fetchone()[0]

                if quantity > current_stock:
                    st.error(f"Not enough stock! Current stock for {selected_product} is {current_stock}.")
                else:
                    new_stock = current_stock - quantity
                    cursor.execute(
                        'INSERT INTO sales (product_id, sale_date, quantity) VALUES (?, ?, ?)',
                        (product_id, sale_date.strftime('%Y-%m-%d'), quantity)
                    )
                    cursor.execute(
                        'UPDATE products SET stock_quantity = ? WHERE product_id = ?',
                        (new_stock, product_id)
                    )
                    conn.commit()
                    st.success(f"New sale added successfully. {selected_product} stock is now {new_stock}.")
            
            except Exception as e:
                st.error(f"An error occurred: {e}")
            finally:
                conn.close()

def add_inventory_form(product_names_dict):
    """
    Creates a form to add inventory to a product's stock.
    """
    with st.form(key='add_inventory_form'):
        st.header("Add to Inventory")
        selected_product = st.selectbox("Select Product", list(product_names_dict.keys()), key="inv_product_select")
        quantity_to_add = st.number_input("Quantity to Add", min_value=1, step=1, key="inv_quantity_input")
        cost_per_unit = st.number_input("Cost per Unit", min_value=0.01, step=0.01, key="inv_cost_input")

        submit_button = st.form_submit_button(label='Add to Stock')

        if submit_button:
            conn = sqlite3.connect('sales.db')
            cursor = conn.cursor()

            try:
                product_id = product_names_dict[selected_product]['id']
                current_stock = product_names_dict[selected_product]['stock']
                
                new_stock = current_stock + quantity_to_add
                
                cursor.execute(
                    'INSERT INTO inventory (product_id, purchase_date, quantity_added, cost_per_unit) VALUES (?, ?, ?, ?)',
                    (product_id, datetime.date.today().strftime('%Y-%m-%d'), quantity_to_add, cost_per_unit)
                )

                cursor.execute(
                    'UPDATE products SET stock_quantity = ?, last_cost_per_unit = ? WHERE product_id = ?',
                    (new_stock, cost_per_unit, product_id)
                )
                
                conn.commit()
                st.success(f"{quantity_to_add} units added to {selected_product}. New stock is {new_stock}.")

            except Exception as e:
                st.error(f"An error occurred: {e}")
            finally:
                conn.close()

def total_sales_per_product(df):
    """
    Calculates total revenue per product and returns a DataFrame.
    """
    summary_df = df.groupby('product_name').agg(
        total_quantity_sold=('quantity', 'sum'),
        total_revenue=('total_revenue', 'sum')
    ).sort_values(by='total_revenue', ascending=False).reset_index()
    return summary_df

def sales_over_time(df):
    """
    Calculates total revenue per day and returns a DataFrame.
    """
    df['sale_date'] = pd.to_datetime(df['sale_date'])
    daily_revenue_df = df.groupby('sale_date')['total_revenue'].sum().reset_index()
    return daily_revenue_df

def plot_total_sales_per_product_plotly_bar_chart(df):
    """
    Generates an interactive bar chart of total sales per product.
    """
    summary_df = df.groupby('product_name')['quantity'].sum().reset_index()
    fig = px.bar(
        summary_df,
        x='product_name',
        y='quantity',
        title='Total Number of Sales per Product',
        labels={'product_name': 'Product Name', 'quantity': 'Number of Sales'},
        color='quantity',
        color_continuous_scale=px.colors.sequential.Viridis
    )
    fig.update_layout(
        title_font_color='white',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        xaxis_tickangle=-45
    )
    st.plotly_chart(fig, use_container_width=True)

def get_recent_sales_with_profit(df):
    """
    Calculates profit/loss for recent sales.
    """
    recent_sales = df.sort_values(by='sale_date', ascending=False).head(10)
    recent_sales['profit'] = (recent_sales['price'] - recent_sales['cost_price']) * recent_sales['quantity']
    recent_sales['profit_status'] = recent_sales['profit'].apply(lambda x: 'Profit' if x > 0 else 'Loss' if x < 0 else 'Break-even')
    return recent_sales[['sale_date', 'product_name', 'quantity', 'total_revenue', 'profit', 'profit_status']]

def get_recent_inventory_with_cost():
    """
    Retrieves recent inventory additions and their cost.
    """
    conn = sqlite3.connect('sales.db')
    query = '''
    SELECT 
        i.purchase_date,
        p.product_name,
        i.quantity_added,
        i.cost_per_unit,
        (i.quantity_added * i.cost_per_unit) AS total_cost
    FROM inventory i
    JOIN products p ON i.product_id = p.product_id
    ORDER BY i.purchase_date DESC
    LIMIT 10
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

st.set_page_config(layout="wide")
st.title("Sales Data Analyzer Dashboard")
st.write("*(All sales data is for demonstration purposes only.)*")

st.sidebar.header("Filters")
full_data = get_data_as_df()
min_date = pd.to_datetime(full_data['sale_date']).min().to_pydatetime().date()
max_date = pd.to_datetime(full_data['sale_date']).max().to_pydatetime().date()

date_range = st.sidebar.slider(
    "Select a Date Range",
    min_value=min_date,
    max_value=max_date,
    value=(min_date, max_date),
    format="YYYY-MM-DD"
)
product_options = list(full_data['product_name'].unique())
product_options.insert(0, "All Products")
selected_product = st.sidebar.selectbox("Select a Product", product_options)

filtered_data = get_data_as_df(
    start_date=date_range[0].strftime('%Y-%m-%d'),
    end_date=date_range[1].strftime('%Y-%m-%d'),
    product_name=selected_product
)

total_revenue = filtered_data['total_revenue'].sum()
total_sales = filtered_data['quantity'].sum()
total_products = filtered_data['product_name'].nunique()
total_profit = (filtered_data['total_revenue'] - (filtered_data['cost_price'] * filtered_data['quantity'])).sum()


col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Revenue", f"₹{total_revenue:,.2f}")
with col2:
    st.metric("Total Profit", f"₹{total_profit:,.2f}")
with col3:
    st.metric("Total Sales", f"{total_sales:,.0f} units")
with col4:
    st.metric("Total Products", f"{total_products}")

st.header("Sales Trend Over Time")
st.line_chart(sales_over_time(filtered_data), x='sale_date', y='total_revenue')

st.header("Total Sales per Product")
plot_total_sales_per_product_plotly_bar_chart(filtered_data)

st.header("Total Sales per Product Table")
st.dataframe(total_sales_per_product(filtered_data), use_container_width=True)

st.header("Recent Sales with Profit/Loss")
st.dataframe(
    get_recent_sales_with_profit(filtered_data), 
    use_container_width=True,
    column_config={
        "sale_date": st.column_config.DatetimeColumn(
            "Sale Date",
            format="YYYY-MM-DD"
        )
    }
)

st.header("Recent Inventory Additions")
st.dataframe(get_recent_inventory_with_cost(), use_container_width=True)

add_new_sale_form(get_product_names_and_stock())

add_inventory_form(get_product_names_and_stock())

st.header("Raw Sales Data")
st.dataframe(
    filtered_data, 
    height=300,
    column_config={
        "sale_date": st.column_config.DatetimeColumn(
            "Sale Date",
            format="YYYY-MM-DD"
        )
    }
)