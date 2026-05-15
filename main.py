import streamlit as st

home = st.Page("pages/home.py",title="Home")
recommendations = st.Page("pages/recommendations.py",title="Get recommendations")
about_us = st.Page("pages/about_us.py",title="About us")
support = st.Page("pages/support.py",title="Support")

pg = st.navigation([home, recommendations, about_us, support])
pg.run()