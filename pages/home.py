import streamlit as st
import pymongo

client = pymongo.MongoClient(st.secrets["MONGO_URI"])
database = client['demoDb']
collection = database['users']

recommendations = st.Page("pages/recommendations.py")

tab1, tab2 = st.tabs(["Login","SignUp"])

with tab2:

    def set_user():
        collection.insert_one({
            'user_name' : st.session_state['user_name'],
            'email' : st.session_state['email'],
            'password' : pass1
        })

    st.markdown("<h1 style = 'text-align : center;'>CineVerseAI</h1>",unsafe_allow_html=True)
    left, middle, right = st.columns([1,1.5,1])

    with middle:
        with st.form("signUp_form",border=True):
            if 'user_name' not in st.session_state:
                st.session_state['user_name'] = ""
            if 'email' not in st.session_state:
                st.session_state['email'] = ""
            st.markdown("<h2>Create Account</h2>",unsafe_allow_html=True)
            st.text_input("Username",key='user_name',placeholder="e.g john_123")
            user = collection.find_one({'user_name':st.session_state['user_name']})
            if user:
                st.error("Username Already taken")
            st.text_input("Email Address",key='email',placeholder="e.g user@example.com")
            user = collection.find_one({'email':st.session_state['email']})
            if user:
                st.error("Email Already Registered")
            pass1 = st.text_input("Choose Password",type="password")
            pass2 = st.text_input("Renter Password",type="password")

            st.write(" ")
            try:    
                if st.form_submit_button("sign Up",width="stretch"):
                    if not st.session_state.user_name.strip():
                        st.warning("Choose a Username")
                    elif not st.session_state.email.strip():
                        st.warning("Enter Email Address")
                    elif not pass1.strip():
                        st.warning("Please choose a password")
                    elif not pass2.strip():
                        st.warning("Enter confirm password")
                    elif not pass1 == pass2:
                        st.error("Confirm password should match the password")
                    else:
                        set_user()
                        st.success("signed Up successfully!!")
                        pass
            except Exception:
                pass

with tab1:
    @st.dialog("Reset your passwrod",width="small")
    def reset_pass():
     st.markdown("<p style = 'text-align: center; color: grey;'> Enter your details to reset your password.</p>",unsafe_allow_html=True)

     st.text_input("Username",placeholder="Enter your username",value=st.session_state.email)
     mob = st.text_input("Mobile No.",placeholder="Enter registered mobile number")
     new_pass = st.text_input("New Password",type="password",placeholder="Enter new password")

     if st.button("Reset Password",width="stretch"):
          if not mob.strip():
            st.error("Enter Mobile Number")
          elif not new_pass.strip():
              st.error("Enter New Password")
          else:
              collection.update_one({"email": st.session_state['email']},{'$set':{'password':new_pass}})
              st.success("Password Reset Successful")
     
    st.markdown("<h1 style = 'text-align: center;'>Welcome Back</h1>",unsafe_allow_html=True)
    st.markdown("<p style = 'text-align: center; color: grey;'>Enter your details to continue</p>",unsafe_allow_html=True)

    st.write(" ")

    left, middle, right = st.columns([1,2,1])

    with middle:
        with st.container(border=True):
            st.markdown("### Login")

            email = st.text_input("Enter Registered Email",placeholder="test@example.com")
            password  = st.text_input("Password",key="password",type="password",placeholder="Enter password")

            st.write(" ")

            if st.button("Login",width="stretch"):
                if not email.strip():
                    st.error("Enter email")
                elif not password.strip():
                    st.error("Enter password")
                else:
                    user = collection.find_one({"email": email,"password": password})
                    if user:
                        st.session_state.logged_in = True
                        st.session_state.logged_in_user = user
                        st.switch_page("pages/recommendations.py")
                    else:
                        st.error("invaild User Details! Check and Try again")

            col1, col2 = st.columns(2)
            with col1:
                st.checkbox("Remember me")
                    
            with col2:
                if st.button("Forgot Password?",type="tertiary",width="stretch"):
                    reset_pass()