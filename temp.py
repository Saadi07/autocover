# from jinja2 import Undefined
# from config.configuration import (
#     BUBBLE_API_URL,
#     CHARGEBEE_WEBHOOK_SECRET,
#     BUBBLE_HEADERS,
# )
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


# import sendgrid
# import os
# from sendgrid.helpers.mail import *

# sg = sendgrid.SendGridAPIClient(
#     api_key="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"
# )
# from_email = Email("admin@claims-gurus.co.uk")
# to_email = To("saadiawan09@gmail.com")
# subject = "Sending with SendGrid is Fun"
# content = Content("text/plain", "and easy to do anywhere, even with Python")
# mail = Mail(from_email, to_email, subject, content)
# response = sg.client.mail.send.post(request_body=mail.get())
# print(response.status_code)
# print(response.body)
# print(response.headers)


# from config.configuration import (
#     BUBBLE_API_URL,
#     CHARGEBEE_WEBHOOK_SECRET,
#     BUBBLE_HEADERS,
#     VEHICLE_DATA_API_KEY,
#     VEHICLE_DATAPACKAGE,
# )
# import requests
# import json
# from jinja2 import Undefined
# import os
# import pdfkit

# # import base64
# # from sendgrid import SendGridAPIClient
# # from sendgrid.helpers.mail import Mail, Attachment
# from jinja2 import Environment, FileSystemLoader

# TEMPLATE_FILE_PATH = "C:/Users/hp/Desktop/autocover"
# template_env = Environment(loader=FileSystemLoader(TEMPLATE_FILE_PATH))
# template = template_env.get_template("SCOTT JONES Contract.html")


# def save_or_send_pdf(rendered_html, send_email=True, to_email=None):
#     # Save HTML to a file
#     html_file_path = "output.html"
#     with open(html_file_path, "w") as f:
#         f.write(rendered_html)

#     pdf_file_path = r"C:/Users/hp/Desktop/autocover/output.pdf"
#     # config = pdfkit.configuration(
#     #     wkhtmltopdf=b"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
#     # )
#     pdfkit.from_file(html_file_path, pdf_file_path)


# def pdf():
#     pdfkit.from_file("output.html", options={"enable-local-file-access": ""})


# pdf = pdf()

#     # Set your SendGrid API key


#     sendgrid_api_key = (
#         "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"
#     )
#     sg = SendGridAPIClient(sendgrid_api_key)
#     # Set sender and recipient email addresses
#     from_email = "admin@claims-gurus.co.uk"
#     to_email = to_email or "saadawanofficial09@gmail.com"
#     # Create a Mail object with the PDF attachment
#     message = Mail(
#         from_email=from_email,
#         to_emails=to_email,
#         subject="AutoCover Contract",
#         html_content="Please find the attached PDF.",
#     )
#     with open(pdf_file_path, "rb") as f:
#         data = f.read()
#         encoded_data = base64.b64encode(data).decode()
#         attachment = Attachment()
#         attachment.file_content = encoded_data
#         attachment.file_type = "application/pdf"
#         attachment.file_name = "output.pdf"
#         attachment.disposition = "attachment"
#         message.attachment = attachment
#     # Send the email
#     try:
#         response = sg.send(message)
#         print("Email sent successfully. Status code:", response.status_code)
#     except Exception as e:
#         print("Error sending email:", str(e))
#     # Clean up temporary files
#     os.remove(html_file_path)
#     os.remove(pdf_file_path)


# rendered_html = template.render(
#     title="Auto Cover", customer_data={}, vehicle_data={}, product_data={}
# )
# save_or_send_pdf(rendered_html)

from closeio_api import Client

api = Client("api_06gU305xuXbhUchfk8dFkz.5Q65L7KKqdX33i446JWMvn")

# data = {
#     # "lead_id":"lead_QyNaWw4fdSwxl5Mc5daMFf3Y27PpIcH0awPbC9l7uyo",
#     "name":"John Smith",
#     "title":"President",
#     "phones":[
#         {"phone":"9045551234","type":"mobile"}
#     ],
#     "emails":[
#         {"email":"john@example.com","type":"office"}
#     ],
#     "urls":[
#         {"url":"http://twitter.com/google/","type":"url"}
#     ],
#     "custom.cf_j0P7kHmgFTZZnYBFtyPSZ3uQw4dpW8xKcW7Krps8atj": "Account Executive"
# }

# resp = api.post('contact', data=data)
# print(resp)

id = "lead_svUZz2eg0wS86q7Zu2m0kcaJseBgzSJljYwsepcRnhl"
resp = api.get("lead/{id}")
print(resp)


# data = {
#     "status_label": "Customer",
#     "opportunities": [],
#     "html_url": "https://app.close.com/lead/lead_cinQ7TktJYK2Nzp2uCHC6Pe1t8lO3B7VhX0Cqnc7Y1Y/",
#     "description": "",
#     "created_by": "user_Q6ReFolMojBwSlUB3g9qq8esW1hdbqhMUDwpKLoZ2F9",
#     "created_by_name": "Thomas Bellessort",
#     "updated_by_name": "Thomas Bellessort",
#     "date_created": "2024-01-01T08:02:16.106000+00:00",
#     "updated_by": "user_Q6ReFolMojBwSlUB3g9qq8esW1hdbqhMUDwpKLoZ2F9",
#     "id": "lead_cinQ7TktJYK2Nzp2uCHC6Pe1t8lO3B7VhX0Cqnc7Y1Y",
#     "name": "Mya Eccleston",
#     "tasks": [],
#     "url": "https://claims-gurus.co.uk/version-test/admin_customer_detail/1704096129238x838973979615255300?",
#     "date_updated": "2024-01-16T02:52:33.385000+00:00",
#     "status_id": "stat_MjFlXA2c4yOUesIMAZISBqwTdiMdN4k7wKiTPQL8a4M",
#     "display_name": "Mya Eccleston",
#     "custom": {
#         "1. End Date": "2026-11-27",
#         "1. Price": 359.88,
#         "1. Product": "Asset Protection Combined RTI and Finance GAP",
#         "1. Start Date": "2023-11-28",
#         "ClaimsGurus Customer ID": "1704096129238x838973979615255300",
#     },
# }

# data = {
#     "status_label": "Customer",
#     "opportunities": [],
#     "html_url": "https://app.close.com/lead/lead_pJnSWX48EbdR87MrEXp50COJJTXAmpb3tyimyiTetoY/",
#     "description": "",
#     "created_by": "user_Q6ReFolMojBwSlUB3g9qq8esW1hdbqhMUDwpKLoZ2F9",
#     "created_by_name": "Thomas Bellessort",
#     "updated_by_name": "Thomas Bellessort",
#     "date_created": "2023-11-14T18:53:19.960000+00:00",
#     "updated_by": "user_Q6ReFolMojBwSlUB3g9qq8esW1hdbqhMUDwpKLoZ2F9",
#     "id": "lead_pJnSWX48EbdR87MrEXp50COJJTXAmpb3tyimyiTetoY",
#     "name": "Molly Robinson",
#     "tasks": [],
#     "url": "https://claims-gurus.co.uk/version-test/admin_customer_detail/1699987991907x153592285691448000?",
#     "date_updated": "2024-01-13T06:40:35.750000+00:00",
#     "status_id": "stat_MjFlXA2c4yOUesIMAZISBqwTdiMdN4k7wKiTPQL8a4M",
#     "display_name": "Molly Robinson",
#     "custom": {
#         "1. End Date": "2026-11-07",
#         "1. Price": 359.88,
#         "1. Product": "Asset Protection Combined RTI and Finance GAP",
#         "1. Start Date": "2023-11-08",
#         "ClaimsGurus Customer ID": "1699987991907x153592285691448000",
#         "Engine Size": "998",
#         "Financed?": "False",
#         "First Registered Date": "2018-08-31T19:00:00+00:00",
#         "Make/Model": "HYUNDAI I10 SE SEPetrol",
#         "Mileage": 69089,
#         "Vehicle - Price": 6495,
#         "VRM": "EO68DYV",
#     },
# }
# resp = api.post("lead", data=data)
# print(resp)
