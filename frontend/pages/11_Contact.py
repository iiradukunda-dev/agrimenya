"""
Contact page — user support and feedback form.
"""
import os

import streamlit as st
from components.icons import render_icon_title
from components.navbar import render_navbar
from utils import api_client
from utils.theme import load_theme

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
LOGO_PATH = os.path.join(ASSETS_DIR, "logo.jpg")

st.set_page_config(page_title="Contact Us", page_icon=LOGO_PATH, layout="wide")
load_theme()
render_navbar()


def main() -> None:
    render_icon_title("assets/message.svg", "Contact Us", "Get in touch with the agrimenya support team")

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.markdown("""
        ### We're here to help!
        If you have any questions, feedback, or need assistance, please fill out
        the form and our team will get back to you as soon as possible.
        """)

        # Contact details as styled info cards
        st.html("""
        <div style="margin-top: 16px;">
            <div class="ag-alert ag-alert-info" style="border-left-width: 3px;">
                <div>
                    <strong style="font-size: 0.88rem;">📧 Email</strong><br/>
                    <span style="font-size: 0.92rem; color: #374151;">support@agrimenya.rw</span>
                </div>
            </div>
            <div class="ag-alert ag-alert-info" style="border-left-width: 3px;">
                <div>
                    <strong style="font-size: 0.88rem;">📞 Phone</strong><br/>
                    <span style="font-size: 0.92rem; color: #374151;">+250 123 456 789</span>
                </div>
            </div>
            <div class="ag-alert ag-alert-info" style="border-left-width: 3px;">
                <div>
                    <strong style="font-size: 0.88rem;">📍 Location</strong><br/>
                    <span style="font-size: 0.92rem; color: #374151;">Kigali, Rwanda</span>
                </div>
            </div>
        </div>
        """)

    with col2:
        with st.form("contact_form"):
            name = st.text_input("Name")
            email = st.text_input("Email Address")
            subject = st.text_input("Subject")
            message = st.text_area("Message", height=150)

            submitted = st.form_submit_button("Send Message", type="primary", use_container_width=True)

            if submitted:
                if name and email and message:
                    success = api_client.send_contact_message(name, email, subject, message)
                    if success:
                        st.success("Thank you for reaching out! We have received your message.")
                    else:
                        st.error("Failed to send message. Please try again.")
                else:
                    st.error("Please fill out all required fields (Name, Email, Message).")


main()
