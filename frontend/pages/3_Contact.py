import streamlit as st
import requests
from utils.theme import load_theme
from utils.i18n import t
from components.navbar import render_navbar
from utils import api_client
from components.icons import render_icon_title
from components.errors import render_error_page

st.set_page_config(page_title="Contact Us", page_icon="frontend/assets/logo.jpg", layout="wide")
load_theme()
render_navbar()

def main():
    render_icon_title("assets/message.svg", "Contact Us", "Get in touch with the Agri-Menya support team")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("""
        ### We're here to help!
        If you have any questions, feedback, or need assistance, please fill out the form and our team will get back to you as soon as possible.
        
        **Email:** support@agrimenya.rw  
        **Phone:** +250 123 456 789
        """)
        
    with col2:
        with st.form("contact_form"):
            name = st.text_input("Name")
            email = st.text_input("Email Address")
            subject = st.text_input("Subject")
            message = st.text_area("Message")
            
            submitted = st.form_submit_button("Send Message", type="primary")
            
            if submitted:
                if name and email and message:
                    success = api_client.send_contact_message(name, email, subject, message)
                    if success:
                        st.success("Thank you for reaching out! We have received your message.")
                    else:
                        st.error("Failed to send message. Please try again.")
                else:
                    st.error("Please fill out all required fields (Name, Email, Message).")

try:
    main()
except requests.exceptions.RequestException as e:
    render_error_page("network", str(e))
except Exception as e:
    render_error_page("system", str(e))
