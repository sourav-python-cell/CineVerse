import streamlit as st
import pymongo

client = pymongo.MongoClient('mongodb://127.0.0.1:27017/?directConnection=true&serverSelectionTimeoutMS=2000&appName=mongosh+2.8.2')
database = client['demoDb']
collection = database['questions']

st.title("Support & Help Center")
st.write("Need help? We're here for you!")

st.header("Frequently Asked Questions")
with st.expander("How do I reset my password?"):
    st.write("You can reset your password from the Login page by clicking on the 'Forgot Password?' button and entering your registered email and mobile number.")

with st.expander("Why are my recommendations not loading?"):
    st.write("Ensure you are logged in. If you are, the AI model might take a few moments to analyze our extensive database. If the problem persists, try refreshing the page or checking your internet connection.")

with st.expander("How are the AI recommendations generated?"):
    st.write("Our system uses natural language processing (TF-IDF Vectorization) and cosine similarity to find movies with similar genres, descriptions, and other features to the ones you search for.")

st.header("Contact Us")
st.write("If you have any other questions, issues, or feedback, please reach out to our support team.")

with st.form("support_form"):
    name = st.text_input("Name")
    email = st.text_input("Email")
    message = st.text_area("Message / Issue Description")
    submit = st.form_submit_button("Send Message", type="primary", width="stretch")
    if submit:
        collection.insert_one({'name': name,
                                'email' : email,
                                'message' : message
                               ,})
        st.success("Thank you for reaching out! Our team will get back to you shortly.")