"""Send a test email through Gmail. Real outreach is never sent automatically."""

import smtplib
from email.message import EmailMessage

import streamlit as st

# The only addresses we are allowed to send test mail to
ALLOWED_TEST_RECIPIENTS = (
    "santoshlatpate12@gmail.com",
    "santoshlatpate21@gmail.com",
)

# Seconds to wait before giving up on Gmail
SMTP_TIMEOUT = 30

# Shown when Gmail SMTP cannot be reached (common on Streamlit Cloud)
CLOUD_HINT = (
    "Streamlit Cloud often blocks outbound Gmail SMTP, so local "
    "`streamlit run demo_app.py` may work when the hosted app does not."
)


def send_email(subject, body, intended_for):
    """Send one test email. Returns True if it was sent, or an error string.

    Always sends FROM GMAIL_ADDRESS TO TEST_RECIPIENT.
    Raises an error (and does not send) if TEST_RECIPIENT is not on the allow-list.
    Tries Gmail SSL (465) first, then STARTTLS (587) if the connection drops.
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
        _send_via_ssl(from_addr, password, msg)
        return True
    except smtplib.SMTPAuthenticationError as e:
        return _readable_error(e)
    except Exception as first_error:
        if not _is_connection_problem(first_error):
            return _readable_error(first_error)
        # Connection dropped on 465 — try Gmail's other port
        try:
            _send_via_starttls(from_addr, password, msg)
            return True
        except Exception as second_error:
            return _readable_error(second_error)


def _send_via_ssl(from_addr, password, msg):
    """Gmail implicit SSL on port 465."""
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=SMTP_TIMEOUT) as smtp:
        smtp.login(from_addr, password)
        smtp.send_message(msg)


def _send_via_starttls(from_addr, password, msg):
    """Gmail STARTTLS on port 587 (retry path)."""
    with smtplib.SMTP("smtp.gmail.com", 587, timeout=SMTP_TIMEOUT) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(from_addr, password)
        smtp.send_message(msg)


def _is_connection_problem(exc):
    """True when the socket/SSL handshake died, not when the password is wrong."""
    if isinstance(exc, smtplib.SMTPAuthenticationError):
        return False
    if isinstance(
        exc,
        (smtplib.SMTPServerDisconnected, ConnectionError, TimeoutError, OSError),
    ):
        return True
    text = str(exc).lower()
    clues = (
        "connection unexpectedly closed",
        "connection closed",
        "timed out",
        "timeout",
        "ssl",
        "handshake",
        "eof",
        "broken pipe",
        "reset by peer",
        "network is unreachable",
    )
    return any(clue in text for clue in clues)


def _readable_error(exc):
    """Short message Santosh can actually use."""
    return f"Could not send test email ({exc}). {CLOUD_HINT}"
