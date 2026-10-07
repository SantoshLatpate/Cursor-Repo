"""Send a test email through Gmail. Real outreach is never sent automatically."""

import smtplib
from email.message import EmailMessage

import streamlit as st

# The only addresses we are allowed to send test mail to
ALLOWED_TEST_RECIPIENTS = (
    "santoshlatpate12@gmail.com",
    "santoshlatpate21@gmail.com",
)


def send_email(subject, body, intended_for):
    """Send one test email. Returns True if it was sent, or an error string.

    Always sends FROM GMAIL_ADDRESS TO TEST_RECIPIENT.
    Raises an error (and does not send) if TEST_RECIPIENT is not on the allow-list.
    """
    from_addr = str(st.secrets["GMAIL_ADDRESS"]).strip()
    password = st.secrets["GMAIL_APP_PASSWORD"]
    to_addr = str(st.secrets["TEST_RECIPIENT"]).strip()

    # Safety: never send to anyone except Santosh's two test inboxes
    if to_addr.lower() not in ALLOWED_TEST_RECIPIENTS:
        raise ValueError(
            "Refusing to send: TEST_RECIPIENT must be "
            "santoshlatpate12@gmail.com or santoshlatpate21@gmail.com"
        )

    full_subject = f"[ZeroDesk TEST] {subject}"
    full_body = f"Intended for: {intended_for}\n\n{body}"

    msg = EmailMessage()
    msg["Subject"] = full_subject
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg.set_content(full_body)

    try:
        # Gmail SSL on port 465
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(from_addr, password)
            smtp.send_message(msg)
        return True
    except Exception as e:
        # Do not send a partial message; tell the caller what went wrong
        return str(e)
