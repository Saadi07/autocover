from config.configuration import (
    BUBBLE_API_URL,
    BUBBLE_HEADERS2,
    CHARGEBEE_WEBHOOK_SECRET,
    BUBBLE_HEADERS,
    SENDGRID_API_KEY,
    VEHICLE_DATA_API_KEY,
    VEHICLE_DATAPACKAGE,
    CLOSEIO_KEY,
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    AWS_REGION_NAME,
)

from config.logger import logger
import requests
import boto3
import json
from jinja2 import Undefined
import os
import pdfkit
import base64

import os
from pyhtml2pdf import converter
from closeio_api import Client


# from sendgrid import SendGridAPIClient
# from sendgrid.helpers.mail import Mail, Attachment

import sendgrid
import os
from sendgrid.helpers.mail import *


def send_to_bubble(data, data_type):
    response = requests.post(
        BUBBLE_API_URL + data_type, headers=BUBBLE_HEADERS, json=data
    )
    result = json.loads(response.text)
    # print("result", result)
    # print("status", result.get("status"))
    return (
        result["id"]
        if result.get("status") == "success" and "id" in result
        else False
    )


def update_bubble(cust_id, payload, data_type):
    bubble_update_url = f"{BUBBLE_API_URL}{data_type}/{cust_id}"
    logger.info(f"bubble_update_url {bubble_update_url}")
    # print("payload", payload)
    # print("headers", BUBBLE_HEADERS)

    response = requests.patch(
        bubble_update_url, headers=BUBBLE_HEADERS2, json=payload
    )
    logger.info(f" update bubble response {response}")

    logger.info(f"Bubble update response: {response.text}")
    if response.status_code == 204:
        return True
    # return json.loads(response.text)


def get_from_bubble(data_type, limit=100):
    all_results = {}
    cursor = 0

    while True:
        endpoint = f"{BUBBLE_API_URL}{data_type}?cursor={cursor}&limit={limit}"
        response = requests.get(endpoint, headers=BUBBLE_HEADERS)
        parsed_response = json.loads(response.text)

        results = parsed_response.get("response", {}).get("results", [])
        for record in results:
            rate_id = record.get("Rate id")
            all_results[rate_id] = record

        remaining = parsed_response.get("response", {}).get("remaining")
        if remaining and remaining > 0:
            cursor += limit
        else:
            break
    # print(all_results)
    return all_results


def find_matching_product(
    all_records_dict, rate_id_to_match, mileage_to_match
):
    # print("charge rate", rate_id_to_match)
    product = find_matching_record(
        all_records_dict, rate_id_to_match, mileage_to_match
    )

    if not product:
        logger.warning("No matching record found.")

    return product


def get_merchant_from_bubble(data_type, merchant_name):
    response = requests.get(
        f"{BUBBLE_API_URL}{data_type}", headers=BUBBLE_HEADERS
    )

    if response.status_code == 200:
        data = response.json().get("response", {}).get("results", [])

        for merchant in data:
            # print(merchant)
            if merchant.get("Merchant Name") == merchant_name:
                # print(merchant)
                return merchant.get("_id")
        return None
    else:
        print(f"Error: {response.status_code}")
        return None


def get_vehicle_info(chargebee_event):
    vehicle_reg_number = chargebee_event["content"]["subscription"].get(
        "cf_Vehicle Registration Number (Licence Plate)*", ""
    )
    ResponseJSON = ""

    Payload = {
        "v": 2,
        "api_nullitems": 1,
        "key_vrm": vehicle_reg_number,
        "auth_apikey": VEHICLE_DATA_API_KEY,
    }

    r = requests.get(
        "https://uk1.ukvehicledata.co.uk/api/datapackage/{}".format(
            VEHICLE_DATAPACKAGE
        ),
        params=Payload,
    )

    if r.status_code == requests.codes.ok:
        ResponseJSON = r.json()
        return ResponseJSON

    else:
        ErrorContent = "Status Code: {}, Reason: {}".format(
            r.status_code, r.reason
        )
        print(ErrorContent)


def find_matching_record(all_records, rate_id, mileage):
    matched_record = all_records.get(rate_id)
    if matched_record:
        vehicle_mileage_from = matched_record.get("Vehicle Mileage From", 0)
        vehicle_mileage_to = matched_record.get("Vehicle Mileage to", 0)

        if vehicle_mileage_from <= mileage <= vehicle_mileage_to:
            return matched_record
        else:
            return None
    else:
        return None


def calculate_tax(
    sold_price, wholesale_price, tax_type, dealership, short_code
):
    def is_empty(property):
        return (
            -1
            if property == "" or property is None or property is Undefined
            else property
        )

    sold_price = is_empty(sold_price)
    wholesale_price = is_empty(wholesale_price)
    tax_type = is_empty(tax_type)
    dealership = is_empty(dealership)
    short_code = is_empty(short_code)
    output = 0
    rate = 0

    if dealership == "yes":
        if tax_type == "IPT":
            if short_code in ["DLW", "DIW"]:
                output = 0.12 * wholesale_price
                rate = 0.12
            elif 0 < sold_price < wholesale_price:
                output = 0.2 * wholesale_price
                rate = 0.2
            elif sold_price > 0 and short_code in [
                "CTI",
                "FIN",
                "DEP",
                "ETI",
                "EPT",
            ]:
                output = 0.1072 * sold_price
                rate = 0.1072
            elif sold_price > 0 and short_code in [
                "RTI",
                "CHG",
                "CTR",
                "RPP",
                "CDI",
                "ALY",
                "TYR",
                "GAP",
                "CIW",
            ]:
                output = 0.1667 * sold_price
                rate = 0.1667
            elif sold_price == 0:
                output = 0.12 * wholesale_price
                rate = 0.12
            else:
                output = 0.1
                rate = 0
        else:
            if short_code in ["ASS", "DOG"]:
                output = 0.2 * wholesale_price
                rate = 0.2
            else:
                output = 0.2
                rate = 0
    else:
        if tax_type == "IPT":
            if short_code == "DLW":
                output = 0.12 * wholesale_price
                rate = 0.12
            elif 0 < sold_price < wholesale_price:
                output = 0.2 * wholesale_price
                rate = 0.2
            elif sold_price > 0 and short_code in [
                "CTI",
                "FIN",
                "DEP",
                "ETI",
                "EPT",
            ]:
                output = 0.1072 * sold_price
                rate = 0.1072
            elif sold_price > 0 and short_code not in ["DLW", "ASS", "DOG"]:
                output = 0.1072 * sold_price
                rate = 0.1072
            elif sold_price == 0:
                output = 0.12 * wholesale_price
                rate = 0.12
            else:
                output = 0.3
                rate = 0
        else:
            if short_code in ["ASS", "DOG"]:
                output = 0.2 * wholesale_price
                rate = 0.2
            else:
                output = 0.4
                rate = 0

    return output, rate


def save_or_send_pdf(
    rendered_html,
    service_invoice_rendered_html,
    invoice_rendered_html,
    cust_id,
    send_email=True,
    to_email=None,
):
    # contract file
    html_file_path = "output.html"
    with open(html_file_path, "w") as f:
        f.write(rendered_html)

    path = os.path.abspath("output.html")
    converter.convert(
        f"file:///{path}", "output.pdf", print_options={"scale": 0.5}
    )

    # save to s3
    s3 = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION_NAME,
    )
    lst_pdf_files = ["output.pdf", "invoice.pdf", "service_invoice.pdf"]
    # file_name = "output.pdf"
    bucket_name = "bubble-bucket-0001"
    for file_name in lst_pdf_files:
        s3_key = f"{cust_id}/{file_name}"
        try:
            s3.upload_file(file_name, bucket_name, s3_key)
            print(f"File uploaded successfully to S3: {cust_id}/{file_name}")
        except Exception as e:
            print("Error uploading file to S3:", e)
    # service invoice
    si_html_file_path = "service_invoice.html"
    with open(si_html_file_path, "w") as f:
        f.write(service_invoice_rendered_html)

    path = os.path.abspath("service_invoice.html")
    converter.convert(
        f"file:///{path}", "service_invoice.pdf", print_options={"scale": 0.5}
    )

    # invoice
    invoice_html_file_path = "invoice.html"
    with open(invoice_html_file_path, "w") as f:
        f.write(invoice_rendered_html)

    path = os.path.abspath("invoice.html")
    converter.convert(
        f"file:///{path}", "invoice.pdf", print_options={"scale": 0.5}
    )

    if send_email:
        print("Sending email...")
        # Set your SendGrid API key
        # sendgrid_api_key = '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'
        sg = sendgrid.SendGridAPIClient(SENDGRID_API_KEY)
        print(SENDGRID_API_KEY)
        # Set sender and recipient email addresses
        # from_email = "admin@claims-gurus.co.uk"
        # to_email = to_email or "marriam.siddiqui@gmail.com"

        from_email = Email("admin@claims-gurus.co.uk")
        # to_email = To("marriam.siddiqui@gmail.com")

        # Create a Mail object with the PDF attachment
        message = Mail(
            from_email=from_email,
            to_emails=to_email,
            subject="AutoCover Contract",
            html_content="Please find the attached PDF.",
        )
        print("about to send email")

        # creating list for sending all 3 in email
        lst_attachments = []

        for file_path in lst_pdf_files:
            with open(file_path, "rb") as f:
                print(f"Processing file: {file_path}")
                data = f.read()
                encoded_data = base64.b64encode(data).decode()
                attachedFile = Attachment(
                    FileContent(encoded_data),
                    FileName(file_path.split("/")[-1]),
                    FileType("application/pdf"),
                    Disposition("attachment"),
                )
                # message.attachment = attachedFile
                lst_attachments.append(attachedFile)

        message.attachment = lst_attachments

        # Send the email
        # logger.info(f"about to send email")
        print("about to send email")
        try:
            print("about to send email in try")
            # response = sg.send(message)
            response = sg.client.mail.send.post(request_body=message.get())
            logger.info(
                f"sendgrid stuff: {response.status_code},body: {response.body}"
            )
            print(
                "response from sendgrid:", response.status_code, response.body
            )
            # print(response.headers)
            logger.info(
                f"Email sent successfully. Status code: {response.status_code}"
            )
            return {
                "status_code": response.status_code,
                "contract_s3_link": f"https://bubble-bucket-0001.s3.eu-west-2.amazonaws.com/{cust_id}/output.pdf",
            }
        except Exception as e:
            print("error in sendgrid: ", e)
            logger.info(f"Error sending email: {str(e)}")

        # Clean up temporary files
        os.remove(html_file_path)
        os.remove("output.pdf")


def send_data_to_closeio(data):
    api = Client(CLOSEIO_KEY)
    resp = api.post("lead", data=data)
    return resp


def create_contact(data):
    api = Client(CLOSEIO_KEY)
    resp = api.post("contact", data=data)
    return resp


def get_contract_count_from_bubble():
    response = requests.get(
        f"{BUBBLE_API_URL}Contract", headers=BUBBLE_HEADERS
    )
    if response.status_code == 200:
        # print("contract response:", response)
        first_count = response.json().get("response", {}).get("count")
        remaining = response.json().get("response", {}).get("remaining")
        return first_count + remaining
    else:
        print(f"Error: {response.status_code}")
        return None
