import streamlit as st
import pandas as pd
from db import connect_db


connection = connect_db()
cursor = connection.cursor(buffered=True)

#step:1

def build_filters(location, cuisine, rating_outof_5,
                  online_order="All",
                  table_booking="All"):

    filters = "WHERE 1=1"

    if location != "All":
        filters += f" AND location = '{location}'"

    if cuisine != "All":
        filters += f" AND cuisines = '{cuisine}'"

    if location != "All":
        filters += f" AND rating_outof_5 = '{rating_outof_5}'"

    if online_order != "All":
        filters += f" AND online_order = '{online_order}'"

    if table_booking != "All":
        filters += f" AND table_booking = '{table_booking}'"

    filters += f" AND rating_outof_5 >= {rating_outof_5}"

    return filters

page = st.sidebar.selectbox("PAGE SELECTION",
    [
        "Restaurant Questions",
        "Dynamic Filters",
        "Orders Analysis"])


#PAGE 1: Questions (10 selected questions)

if page == "Restaurant Questions":
    st.title("Restaurant's Business Questions")

    questions = {
        "Q1 - Which Bangalore locations have the highest average restaurant ratings?": "location_rating",
        "Q2 - Which locations are over-saturated with restaurants?": "over_saturated",
        "Q3 - Does online ordering improve restaurant ratings?": "online_impact",
        "Q4 - Does table booking correlate with higher customer ratings?": "table_impact",
        "Q5 - What price range delivers the best customer satisfaction?": "pricing_best",
        "Q6 - How do low, mid, and premium-priced restaurants perform in terms of ratings?": "pricing_performance",
        "Q7 - Which cuisines are most common in Bangalore?": "cuisine_count",
        "Q8 - Which locations show high demand but lower average ratings?": "low_rating_locations",
        "Q9 - Do restaurants offering both online ordering and table booking perform better?": "feature adoption for partners",
        "Q10 - Which restaurants are top performers within each pricing segment?": "top_performers"
    }

    selected_q = st.selectbox("Choose Question", list(questions.keys()))
    q = questions[selected_q]
    st.session_state["question"] = questions[selected_q]

    filters = "WHERE 1=1"


    # Q1 Location rating

    if q == "location_rating":
        cursor.execute("""SELECT location, ROUND(AVG(rating_outof_5),1) as avg_rating, COUNT(*) as restaurant_count
        FROM restaurants_data
        GROUP BY location
        HAVING restaurant_count > 25
        ORDER BY avg_rating DESC
        LIMIT 10""")

    # Q2 Over saturated

    elif q == "over_saturated":
        cursor.execute("""SELECT location, COUNT(*) AS restaurant_count
        FROM restaurants_data
        GROUP BY location
        ORDER BY restaurant_count DESC
        LIMIT 10""")

    # Q3 Online order impact

    elif q == "online_impact":
        cursor.execute("""SELECT online_order, AVG(rating_outof_5) AS avg_rating, COUNT(*) AS restaurant_count
        FROM restaurants_data
        GROUP BY online_order""")

    # Q4 Table booking impact

    elif q == "table_impact":
        cursor.execute("""SELECT pricing_segment,table_booking,
        COUNT(*) AS total_restaurants,
        ROUND(AVG(rating_outof_5),1) AS avg_rating
        FROM restaurants_data
        GROUP BY pricing_segment, table_booking
        ORDER BY pricing_segment, avg_rating ASC""")

    # Q5 Pricing best

    elif q == "pricing_best":
        cursor.execute("""
        SELECT pricing_segment, COUNT(*) AS total_restaurants, ROUND(AVG(rating_outof_5), 2) AS avg_rating,
        ROUND(COUNT(CASE WHEN rating_category = 'Excellent' THEN 1 END) * 100.0 / COUNT(*), 2) AS excellent_percentage
        FROM restaurants_data
        GROUP BY pricing_segment
        ORDER BY avg_rating DESC""")



    # Q6 Cuisine rating

    elif q == "pricing_performance":
        cursor.execute("""SELECT pricing_segment, ROUND(AVG(rating_outof_5),1) AS avg_rating, COUNT(*) AS restaurant_count,
        SUM(votes) AS total_customer_engagement FROM restaurants_data
        GROUP BY pricing_segment
        ORDER BY avg_rating DESC""")

    # Q7 Cuisine demand

    elif q == "cuisine_count":

        from collections import Counter

        cursor.execute("""
        SELECT cuisines
        FROM restaurants_data
        WHERE cuisines IS NOT NULL
        """)

        rows = cursor.fetchall()

        all_cuisines = []

        for row in rows:
            split_names = [i.strip() for i in row[0].split(',')]
            all_cuisines.extend(split_names)

        cuisine_counts = Counter(all_cuisines).most_common(10)

        cuisine_df = pd.DataFrame(
            cuisine_counts,
            columns=["Cuisine Name", "Frequency"]
        )

        st.dataframe(cuisine_df)



    # Q8 Low rating areas

    elif q == "low_rating_locations":
        cursor.execute("""SELECT location, COUNT(*) AS total_restaurants, ROUND(AVG(rating_outof_5),2) AS avg_low_rated
        FROM restaurants_data
        GROUP BY location
        HAVING COUNT(*) > 50 
        AND AVG(rating_outof_5) < 3.7
        ORDER BY total_restaurants DESC, avg_low_rated ASC""")

    # Q9 Feature combo

    elif q == "feature adoption for partners":
        cursor.execute("""SELECT online_order, table_booking, ROUND(AVG(rating_outof_5),1) AS avg_rating, AVG(votes) AS avg_popularity,
        COUNT(*) AS restaurant_count FROM restaurants_data
        GROUP BY online_order, table_booking
        ORDER BY avg_rating DESC""")

    # Q10 Top performers

    elif q == "top_performers":
        cursor.execute("""SELECT pricing_segment, restaurant_name, rating_outof_5, location
        FROM restaurants_data
        WHERE (pricing_segment, rating_outof_5) IN (SELECT pricing_segment, MAX(rating_outof_5) FROM restaurants_data
        GROUP BY pricing_segment)
        ORDER BY pricing_segment""")


    if q != "cuisine_count":
        data = cursor.fetchall()

        columns = [desc[0] for desc in cursor.description]

        df = pd.DataFrame(data, columns=columns)

        st.dataframe(df)


#PAGE 2 — DYNAMIC FILTERS

elif page == "Dynamic Filters":
    st.title("Dynamic Restaurant Filters")

    cursor.execute("SELECT DISTINCT location FROM restaurants_data")
    locations = ["All"] + [i[0] for i in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT cuisines FROM restaurants_data")
    cuisines = ["All"] + [i[0] for i in cursor.fetchall()]

    location = st.selectbox("Location", locations)

    cuisine = st.selectbox("Cuisine", cuisines)

    rating_outof_5 = st.selectbox("Minimum Rating",[0, 1, 2, 3, 4, 5])

    online_order = st.selectbox("Online Order",["All", "Yes", "No"])

    table_booking = st.selectbox("Table Booking",["All", "Yes", "No"])

    filters = build_filters(location,cuisine,rating_outof_5,online_order,table_booking)

    query = f"""
       SELECT restaurant_name,
              cuisines,
              location,
              rating_outof_5,
              pricing_segment,
              online_order,
              table_booking
       FROM restaurants_data
       {filters}
       """

    cursor.execute(query)
    data = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    df = pd.DataFrame(data, columns=columns)
    st.dataframe(df, hide_index=True)

#ORDERS TABLE

elif page == "Orders Analysis":
    st.title("Orders Business Questions")

    order_questions = {
        "Q1 - Which restaurants are the top 10 revenue generators, and how much total income have they contributed?": "top_revenue",
        "Q2 - Which restaurants have processed the highest volume of orders, and what is the total count for each?": "most_orders",
        "Q3 - How does the average order value (AOV) vary across different top-performing restaurants?": "avg_order",
        "Q4 - How does the use of discounts impact the average order value and the total number of orders placed?": "discount_analysis",
        "Q5 - What are the most preferred payment methods used by customers, and which one dominates the transactions?": "payment_popularity",
        "Q6 - Which date had the highest sales?": "peak dates"
    }

    selected_order_q = st.selectbox(
        "Choose Order Question",
        list(order_questions.keys())
    )

    oq = order_questions[selected_order_q]

    #q1:

    if oq == "top_revenue":
        cursor.execute("""
        SELECT restaurant_name,
               SUM(order_value) total_revenue
        FROM orders_data
        GROUP BY restaurant_name
        ORDER BY total_revenue DESC
        LIMIT 10
        """)

    #q2:

    elif oq == "most_orders":

        cursor.execute("""
        SELECT restaurant_name,
               COUNT(order_id) total_orders
        FROM orders_data
        GROUP BY restaurant_name
        ORDER BY total_orders DESC
        LIMIT 10
        """)

    #q3:

    elif oq == "avg_order":

        cursor.execute("""
        SELECT restaurant_name,
        ROUND(AVG(order_value),2) avg_order_value
        FROM orders_data
        GROUP BY restaurant_name
        ORDER BY avg_order_value DESC
        LIMIT 10
        """)

    #q4:

    elif oq == "discount_analysis":

        cursor.execute("""
        SELECT discount_used,
        ROUND(AVG(order_value),2) avg_order_value,
        COUNT(*) total_orders
        FROM orders_data
        GROUP BY discount_used
        """)

    #q5:

    elif oq == "payment_popularity":

        cursor.execute("""
        SELECT payment_method,
        COUNT(*) total_transactions
        FROM orders_data
        GROUP BY payment_method
        ORDER BY total_transactions DESC
        """)

    #q6:

    elif oq == "peak dates":

        cursor.execute("""
        SELECT order_date,
        SUM(order_value) AS total_sales
        FROM orders_data
        GROUP BY order_date
        ORDER BY total_sales DESC
        LIMIT 10
        """)

    orders_data = cursor.fetchall()

    orders_columns = [desc[0] for desc in cursor.description]

    orders_df = pd.DataFrame(
        orders_data,
        columns=orders_columns
    )

    st.dataframe(orders_df, hide_index=True)






