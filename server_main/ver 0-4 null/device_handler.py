from utils import send_email_response
from key_handler import validate_key

# Handle the device key email
def handle_key_email(from_email, msg):
    try:
        # Extract key from email content
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    key = part.get_payload(decode=True).decode("utf-8", errors="replace").strip()
        else:
            key = msg.get_payload(decode=True).decode("utf-8", errors="replace").strip()

        # Validate the key
        if validate_key(key):
            # Send request for device details
            body = "approved"
            send_email_response(from_email, "Key answer", body)
        else:
            # If key is invalid, send error notification
            body = "unapproved"
            send_email_response(from_email, "Key answer", body)

    except Exception as e:
        print(f"Error processing key: {e}")

# Handle the Device Info email
def handle_device_info_email(from_email, msg):
    # Process the device info here
    body = "Device information has been successfully saved."
    send_email_response(from_email, "Device Registration", body)
