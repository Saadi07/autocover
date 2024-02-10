from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from utils.utils import *


def map_customer_data(chargebee_event):
    billing_address = chargebee_event["content"]["customer"]["billing_address"]
    customer = chargebee_event["content"]["customer"]
    full_name = f"{customer['first_name']} {customer['last_name']}"
    has_dn = "Yes"  # Assuming D&N is always present in this context
    line1 = billing_address.get("line1", "")
    line2 = billing_address.get("line2", "")
    city_country = f"{billing_address.get('city', '')}, {billing_address.get('country', '')}"
    postal_code = billing_address.get("postal_code", "")
    phone_number = customer.get("phone", "")
    email = customer.get("email", "")

    result = {
        "Full Name": full_name,
        "Have D&N been done?": has_dn,
        "Line 1: Address": line1,
        "Line 2: Address": line2,
        "Line 3: Address": city_country,
        "Line 4: Address": postal_code if postal_code else "",
        "Phone Number 2": phone_number,
        "email": email,
    }

    return result


def map_vehicle_data(
        vehicle_info,
        chargebee_data,
        cust_id,
        associated_insurance_product,
        associated_merchant,
):
    classification_details = vehicle_info["Response"]["DataItems"][
        "ClassificationDetails"
    ]
    registration_details = vehicle_info["Response"]["DataItems"][
        "VehicleRegistration"
    ]
    smmt_details = vehicle_info["Response"]["DataItems"]["SmmtDetails"]

    technical_details = vehicle_info["Response"]["DataItems"][
        "TechnicalDetails"
    ]

    subscription_content = chargebee_data["content"]["subscription"]

    is_new_vehicle = int(subscription_content["cf_Vehicle Mileage"]) == 0
    imported = "yes" if registration_details["Imported"] == True else "no"
    vehicle_info = {
        "Make": classification_details["Smmt"]["Make"],
        "Model": classification_details["Dvla"]["Model"],
        "Vehicle Trim": classification_details["Smmt"]["Trim"],
        "Style": registration_details["DoorPlanLiteral"],
        "Colour": registration_details["Colour"],
        "VIN number": registration_details["Vin"],
        "Is the vehicle imported?": imported,
        "Engine capacity *": registration_details["EngineCapacity"],
        "Fuel Type": smmt_details["FuelType"],
        "First registered *": registration_details[
            "DateFirstRegistered"
        ].split("T")[0],
        "Vehicle Type": smmt_details["BodyStyle"],
        "VRN": subscription_content[
            "cf_Vehicle Registration Number (Licence Plate)*"
        ],
        "Annual mileage": subscription_content["cf_Vehicle Mileage"],
        "Vehicle price *": subscription_content["cf_Vehicle Price"],
        "Dealer bought from": subscription_content["cf_Dealer Name"],
        # "Sales Agent": subscription_content["cf_Sales Agent"],
        "Sale Type": "New" if is_new_vehicle else "Used",
        "Delivery date": subscription_content["created_at"],
        "Associated User": cust_id,
        "Associated Insurance Product": associated_insurance_product,
        "Associated Merchant": associated_merchant,
    }

    return vehicle_info


def map_contract_data(chargebee_event, vehicle_info, product):
    fund = (
            chargebee_event["content"]["invoice"]["total"]
            - chargebee_event["content"]["invoice"]["amount_paid"]
    )
    funded = "No" if fund == 0 else "Yes"
    billing_address = chargebee_event["content"]["customer"]["billing_address"]

    customer = chargebee_event["content"]["customer"]
    full_name = f"{customer['first_name']} {customer['last_name']}"
    line1 = billing_address.get("line1", "")
    phone_number = customer.get("phone", "")
    email = customer.get("email", "")
    line_items = chargebee_event["content"]["invoice"]["line_items"]
    total_tax_amount = 0
    for line_item in line_items:
        total_tax_amount += line_item.get("tax_amount", 0)
    registration_details = vehicle_info["Response"]["DataItems"][
        "VehicleRegistration"
    ]
    subscription_content = chargebee_event["content"]["subscription"]
    vrm = vehicle_info["Request"]["DataKeys"]["Vrm"]
    date_from_timestamp = datetime.utcfromtimestamp(
        chargebee_event["content"]["invoice"]["line_items"][0]["date_from"]
    )
    iso8601_date_from = date_from_timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
    date_to_timestamp = datetime.utcfromtimestamp(
        chargebee_event["content"]["invoice"]["line_items"][0]["date_to"]
    )
    iso8601_date_to = date_to_timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
    contract_info = {
        "static_customer_name": full_name,
        "static_customer_email": email,
        "static_customer_phone_text": phone_number,
        "static_customer_address": line1,
        "Funded Product": funded,
        "Final Full Payment Facilitator Cost": 0 if funded == "Yes" else fund,
        "Final Funded Payment Facilitator Cost": 0 if funded == "No" else fund,
        "Final Customer Tax Amount": total_tax_amount,
        "Reconciled": "Yes",
        "static_vehicle_colour": registration_details["Colour"],
        "static_vehicle_engine_capacity": registration_details[
            "EngineCapacity"
        ],
        "Policy End Date": iso8601_date_to,
        "Policy Start Date": iso8601_date_from,
        "static_vehicle_mileage": subscription_content["cf_Vehicle Mileage"],
        "static_vehicle_vrm": vrm,
        "Accelerated Commission Amount": product[
            "Acc. Flow Monthly Instalment Amount"
        ],
        "Accelerated Flow Type": product["Acc. Flow Type"],
        "Accelerated Number of Instalments": product[
            "Acc. Flow Number of Instalments"
        ],
        "Associated Insurance Product": product["_id"],
        "Final RRP": product["RRP"],
        "Monthly Product": "No",
        "Contract Status": "Live",
        "Associated Sales Reps": ["1639925052421x587860159738907000"],
        "Final Insurer 1 Underwriting Price": 100,  # dummy value
        "Final Other Merchant Costs": 100,
        "Final Regional Manager Profit": 100,
        "Final Merchant Tax Amount": 0,
        "Final Merchant Wholesale Tax Rate": 0.12,
        "Final Merchant Wholesale Price": 0,
        # "Contract": contract_link,
    }
    # print(contract_info)
    return contract_info


def map_contract_pdf_data(
        customer_data,
        vehicle_data,
        vehicle_info,
        product_data,
        chargebee_event,
):
    # print("prod", product_data)

    contract_count = get_contract_count_from_bubble()
    reference = str(contract_count + 1)
    address = (
            customer_data["Line 1: Address"]
            + customer_data["Line 2: Address"]
            + customer_data["Line 3: Address"]
            + customer_data["Line 4: Address"]
    )
    first_registered_date = vehicle_data["First registered *"]
    first_registered_date = (
        datetime.fromisoformat(first_registered_date)
        .date()
        .strftime("%d/%m/%Y")
    )

    aspiration = vehicle_info["Response"]["DataItems"]["TechnicalDetails"][
        "General"
    ]["Engine"]["Aspiration"]
    if aspiration == "Turbocharged":
        turbocharged = "Yes"
    else:
        turbocharged = "No"

    DrivingAxle = vehicle_info["Response"]["DataItems"]["TechnicalDetails"][
        "General"
    ]["DrivingAxle"]
    if DrivingAxle == "4WD":
        four_wheel_drive = "Yes"
    else:
        four_wheel_drive = "No"

    fund = (
            chargebee_event["content"]["invoice"]["total"]
            - chargebee_event["content"]["invoice"]["amount_paid"]
    )
    funded = "No" if fund == 0 else "Yes"

    date_from_timestamp = datetime.utcfromtimestamp(
        chargebee_event["content"]["invoice"]["line_items"][0]["date_from"]
    )
    # iso8601_date_from = date_from_timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
    formatted_from_date = date_from_timestamp.strftime("%d/%m/%Y")

    term = int(product_data["Variant Term"])
    print(term, type(term))
    date_after_term = date_from_timestamp + relativedelta(months=term)
    formatted_to_date = date_after_term.strftime("%d/%m/%Y")
    vehicle_price = round(int(vehicle_data["Vehicle price *"]), 2)
    if "Variant Claim limit" in product_data:
        claim_limit = product_data["Variant Claim limit"]
    else:
        claim_limit = " "

    response = {
        "title": "Auto Cover",
        "reference": reference,
        "Full Name": customer_data["Full Name"],
        "Address": address,
        "Phone Number 2": customer_data["Phone Number 2"],
        "email": customer_data["email"],
        "VRN": vehicle_data["VRN"],
        "VIN number": vehicle_data["VIN number"],
        "Delivery date": vehicle_data["Delivery date"],
        "Make": vehicle_data["Make"],
        "Engine capacity *": vehicle_data["Engine capacity *"],
        "Vehicle price *": vehicle_price,
        "Model": vehicle_data["Model"],
        "First registered *": first_registered_date,
        "Dealer": "AutoCover",
        "Annual mileage": vehicle_data["Annual mileage"],
        "Vehicle Type": vehicle_data["Vehicle Type"],
        "Merchant": "AutoCover",
        "Sale Type": vehicle_data["Sale Type"],
        "Is the vehicle imported?": vehicle_data["Is the vehicle imported?"],
        "turbocharged": turbocharged,
        "four wheel drive": four_wheel_drive,
        "Product Type": product_data["Product Type "],
        "Variant Name": product_data["Variant Name"],
        "Variant Term": product_data["Variant Term"],
        "Variant Claim limit": claim_limit,
        "Variant Excess": product_data["Variant Excess"],
        "Wholesale Price": product_data["Wholesale Price"],
        "funded": funded,
        "formatted_from_date": formatted_from_date,
        "formatted_to_date": formatted_to_date,
        "sales_rep": "Online Journey",
    }
    return response


def map_invoice_data(chargebee_event, product, rate):
    invoice_number = chargebee_event["content"]["invoice"]["id"]
    # invoice_date = datetime.utcfromtimestamp(
    #     chargebee_event["content"]["invoice"]["generated_at"]
    # ).date()
    invoice_date = datetime.utcfromtimestamp(
        chargebee_event["content"]["invoice"]["generated_at"]).date().strftime("%d/%m/%Y")
    # print("invoice date", invoice_date)

    billing_address = chargebee_event["content"]["customer"]["billing_address"]
    customer = chargebee_event["content"]["customer"]
    full_name = f"{customer['first_name']} {customer['last_name']}"
    line1 = billing_address.get("line1", "")
    line2 = billing_address.get("line2", "")
    date_from_timestamp = datetime.utcfromtimestamp(
        chargebee_event["content"]["invoice"]["line_items"][0]["date_from"]
    ).date()
    print("from date", date_from_timestamp)

    amount = product["Acc. Flow Monthly Instalment Amount"]
    payment_terms = product["Acc. Flow Number of Instalments"]
    monthly_amount = round(amount + (amount * rate), 2)
    IPT_Amount = round(product["RRP"] * 0.107202400800267, 2)
    sub_total = round((amount * payment_terms) - IPT_Amount, 2)

    # total_amount = sub_total + (sub_total * rate)
    total_amount = product["RRP"]
    payment_schedule_list = []

    payment_schedule_list.append(
        {
            "payment_schedule": "Payment (1 of {})".format(payment_terms),
            "date": date_from_timestamp.strftime("%d/%m/%Y"),
            "amount": monthly_amount,
        }
    )
    for i in range(1, payment_terms):
        # Increment month and year, keep the day the same as the first date
        current_date = date_from_timestamp.replace(month=date_from_timestamp.month + i, year=date_from_timestamp.year)
        formatted_date = current_date.strftime("%d/%m/%Y")

        # Create the payment_schedule string
        payment_schedule = f"Payment ({i + 1} of {payment_terms})"

        # Create the dictionary for the current iteration and append it to the list
        payment_schedule_list.append(
            {
                "payment_schedule": payment_schedule,
                "date": formatted_date,
                "amount": monthly_amount,
            }
        )

    return {
        "Full Name": full_name,
        "Line 1: Address": line1,
        "Line 2: Address": line2,
        # "monthly_amount": monthly_amount,
        "invoice_number": invoice_number,
        "invoice_date": invoice_date,
        "payment_terms": payment_terms,
        "payment_schedule_list": payment_schedule_list,
        "sub_total": sub_total,
        "rate": rate,
        "IPT_Amount": IPT_Amount,
        "total_amount": total_amount,
        "balance_due": total_amount - amount,
        "product_type": product["Product Type "],
        "variant_name": product["Variant Name"],
        "variant_term": product["Variant Term"],
    }
