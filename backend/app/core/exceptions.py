class EmailDeliveryError(Exception):
    """Raise khi SMTP gửi email fail (timeout, auth, network)."""

    pass
