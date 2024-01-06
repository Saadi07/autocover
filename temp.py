# from jinja2 import Undefined
# from config.configuration import BUBBLE_API_URL , CHARGEBEE_WEBHOOK_SECRET , BUBBLE_HEADERS
# import requests
# import json

# def get_from_bubble(data_type, limit=100):
#     all_results = {}
#     cursor = 0

#     while True:
#         endpoint = f'{BUBBLE_API_URL}{data_type}?cursor={cursor}&limit={limit}'
#         response = requests.get(endpoint, headers=BUBBLE_HEADERS)

#         parsed_response = json.loads(response.text)

#         results = parsed_response.get('response', {}).get('results', [])
#         for record in results:
#             rate_id = record.get('Rate id')
#             all_results[rate_id] = record

#         remaining = parsed_response.get('response', {}).get('remaining')
#         if remaining and remaining > 0:
#             cursor += limit
#         else:
#             break

#     return all_results

# def find_matching_record(all_records, rate_id, mileage):
#     matched_record = all_records.get(rate_id)

#     if matched_record:
#         vehicle_mileage_from = matched_record.get('Vehicle Mileage From', 0)
#         vehicle_mileage_to = matched_record.get('Vehicle Mileage to', 0)

#         if vehicle_mileage_from <= mileage <= vehicle_mileage_to:
#             return matched_record
#         else:
#             return None
#     else:
#         return None

# def calculate_tax(sold_price, wholesale_price, tax_type, dealership, short_code):
#     def is_empty(property):
#         return -1 if property == '' or property is None or property is Undefined else property

#     sold_price = is_empty(sold_price)
#     wholesale_price = is_empty(wholesale_price)
#     tax_type = is_empty(tax_type)
#     dealership = is_empty(dealership)
#     short_code = is_empty(short_code)
#     output = 0
#     rate = 0

#     if dealership == 'yes':
#         if tax_type == 'IPT':
#             if short_code in ['DLW', 'DIW']:
#                 output = 0.12 * wholesale_price
#                 rate = 0.12
#             elif 0 < sold_price < wholesale_price:
#                 output = 0.2 * wholesale_price
#                 rate = 0.2
#             elif sold_price > 0 and short_code in ['CTI', 'FIN', 'DEP', 'ETI', 'EPT']:
#                 output = 0.1072 * sold_price
#                 rate = 0.1072
#             elif sold_price > 0 and short_code in ['RTI', 'CHG', 'CTR', 'RPP', 'CDI', 'ALY', 'TYR', 'GAP', 'CIW']:
#                 output = 0.1667 * sold_price
#                 rate = 0.1667
#             elif sold_price == 0:
#                 output = 0.12 * wholesale_price
#                 rate = 0.12
#             else:
#                 output = 0.1
#                 rate = 0
#         else:
#             if short_code in ['ASS', 'DOG']:
#                 output = 0.2 * wholesale_price
#                 rate = 0.2
#             else:
#                 output = 0.2
#                 rate = 0
#     else:
#         if tax_type == 'IPT':
#             if short_code == 'DLW':
#                 output = 0.12 * wholesale_price
#                 rate = 0.12
#             elif 0 < sold_price < wholesale_price:
#                 output = 0.2 * wholesale_price
#                 rate = 0.2
#             elif sold_price > 0 and short_code in ['CTI', 'FIN', 'DEP', 'ETI', 'EPT']:
#                 output = 0.1072 * sold_price
#                 rate = 0.1072
#             elif sold_price > 0 and short_code not in ['DLW', 'ASS', 'DOG']:
#                 output = 0.1072 * sold_price
#                 rate = 0.1072
#             elif sold_price == 0:
#                 output = 0.12 * wholesale_price
#                 rate = 0.12
#             else:
#                 output = 0.3
#                 rate = 0
#         else:
#             if short_code in ['ASS', 'DOG']:
#                 output = 0.2 * wholesale_price
#                 rate = 0.2
#             else:
#                 output = 0.4
#                 rate = 0

#     return output, rate



# # Example: Retrieve all records for "Insurance Product" and create a dictionary with "Rate id" as the key
# all_records_dict = get_from_bubble("Insurance Product")

# # Specify the rate_id and mileage for matching
# rate_id_to_match = '91'
# mileage_to_match = 5000  # Adjust as needed

# # Find and display the matching record based on rate_id and mileage
# product = find_matching_record(all_records_dict, rate_id_to_match, mileage_to_match)

# if product:
#        sold_price = product.get('Insurer 1 Premium Total', 0) # Which sold price........... 
#        wholesale_price = product.get('Wholesale Price', 0)
#        tax_type = product.get('Tax Type', '')
#        dealership = 'yes' if product.get('Sales Plugin', False) else 'no' # From to get this as well..........
#        short_code = product.get('Product Short Code', '') 
#        print(tax_type, sold_price)
#        # Calculate tax
#        output, rate = calculate_tax(sold_price, wholesale_price, tax_type, dealership, short_code)
#        print("tXX", output, rate)

#        #print(matching_record)
# else:
#     print("No matching record found.")


# import os
# from weasyprint import HTML

# def convert_html_to_pdf(html_file_path, output_pdf_filename):
#     try:
#         # Assuming the HTML file is in the same directory as the script
#         html_path = os.path.join(os.path.dirname(__file__), html_file_path)
#         output_pdf_path = os.path.join(os.path.dirname(__file__), output_pdf_filename)

#         HTML(string=open(html_path, 'r').read()).write_pdf(output_pdf_path)
#         print(f"Conversion successful. PDF saved to {output_pdf_path}")
#     except Exception as e:
#         print(f"Conversion failed: {str(e)}")

# # Example usage:
# html_file_name = 'output.html'
# output_pdf_filename = 'output_file.pdf'

# convert_html_to_pdf(html_file_name, output_pdf_filename)

import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

message = Mail(
    from_email='from_email@example.com',
    to_emails='to@example.com',
    subject='Sending with Twilio SendGrid is Fun',
    html_content='<strong>and easy to do anywhere, even with Python</strong>')
try:
    sg = SendGridAPIClient('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')
    response = sg.send(message)
    print(response.status_code)
    print(response.body)
    print(response.headers)
except Exception as e:
    print(e)