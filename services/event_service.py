
def map_chargebee_event_to_bubble_data(chargebee_event):
    chargebee_event = dict(chargebee_event)
    if(chargebee_event):
        if(chargebee_event['event_type'] == 'invoice_generated'):
            return {"first_name": chargebee_event['content']['invoice']['billing_address']['first_name'], "last_name": chargebee_event['content']['invoice']['billing_address']['last_name']}
            

def map_chargebee_event_to_bubble_data(chargebee_event):
    chargebee_event = dict(chargebee_event)
    if chargebee_event:
        if chargebee_event['event_type'] == 'payment_succeeded':
            billing_address = chargebee_event['content']['customer']['billing_address']
            customer = chargebee_event['content']['customer']

            # Full name
            full_name = f"{customer['first_name']} {customer['last_name']}"

            # Check for D&N
            has_dn = 'Yes'  # Assuming D&N is always present in this context

            # Address lines
            line1 = billing_address.get('line1', '')
            line2 = billing_address.get('line2', '')

            # City + Country
            city_country = f"{billing_address.get('city', '')}, {billing_address.get('country', '')}"

            # Postal Code (if available)
            postal_code = billing_address.get('postal_code', '')

            # Phone Number and Email
            phone_number = customer.get('phone', '')
            email = customer.get('email', '')

            # Associated Vehicle (hardcoded for illustration)
            associated_vehicle = "[id]"

            # List of insurance products, merchants, and merchant groups (hardcoded for illustration)
            insurance_products = ["product_id1", "product_id2"]
            merchants = ["merchant_id1", "merchant_id2"]
            merchant_groups = ["group_id1", "group_id2"]

            result = {
                "Full Name": full_name,
                # "Have D&N been done?": has_dn,
                # "Line 1: Address": line1,
                # "Line 2: Address": line2,
                # "Line 3: Address": city_country,
                # "Line 4: Address": postal_code if postal_code else '',
                # "Phone Number 2": phone_number,
                #"Email": email,
                # "Associated Vehicle": associated_vehicle,
                # "List of insurance products": insurance_products,
                # "List of merchants": merchants,
                # "List of merchants group": merchant_groups
            }

            return result

