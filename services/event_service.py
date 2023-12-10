
def map_chargebee_event_to_bubble_data(chargebee_event):
    # Implement your mapping logic here based on the Chargebee event data
    # This is just a placeholder, customize it according to your needs
    return {
        'event_type': chargebee_event.event_type,
        'data': chargebee_event.content,
        # Add more fields as needed
    }