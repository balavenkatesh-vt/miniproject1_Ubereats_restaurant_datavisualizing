import mysql.connector
import streamlit as st

@st.cache_resource
def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        port=3307,
        password="",
        database="ubereats_restaurant"
    )