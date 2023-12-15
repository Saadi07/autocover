
def map_chargebee_event_to_bubble_data(chargebee_event):
    chargebee_event = dict(chargebee_event)
    if(chargebee_event):
        if(chargebee_event['event_type'] == 'invoice_generated'):
            return {"first_name": chargebee_event['content']['invoice']['billing_address']['first_name'], "last_name": chargebee_event['content']['invoice']['billing_address']['last_name']}
            