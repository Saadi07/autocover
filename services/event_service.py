from utils.utils import (
    send_to_bubble,
    get_vehicle_info,
    get_from_bubble,
    find_matching_record,
    calculate_tax,
    update_bubble,
    get_merchant_from_bubble,
    save_or_send_pdf,
    send_data_to_closeio,
    get_contract_count_from_bubble,
    create_contact,
)
from config.logger import logger
from jinja2 import Environment, FileSystemLoader
from datetime import datetime, timedelta

# TEMPLATE_FILE_PATH = "/home/saadi09/Documents/InsightHub Projects/AUTOCOVER/templates"
TEMPLATE_FILE_PATH = r"templates"

template_env = Environment(loader=FileSystemLoader(TEMPLATE_FILE_PATH))
template = template_env.get_template("SCOTT JONES Contract.html")
invoice_template = template_env.get_template("Invoice Template.html")
service_invoice_template = template_env.get_template(
    "Service Invoice Template.html"
)


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


def chargebee_payment_success_service(chargebee_event):
    logger.info("starting")
    # logger.info(f"CHARGEBEE DATA HERE: {chargebee_event}")

    customer_data = map_customer_data(chargebee_event)
    logger.info(f"customer_data: {customer_data}")
    cust_id = send_to_bubble(customer_data, data_type="User")
    if cust_id:
        logger.info(f"Customer Data sent to Bubble. Customer id: {cust_id}")
        vehicle_info = get_vehicle_info(chargebee_event)

        all_insurance_products = get_from_bubble(data_type="Insurance Product")

        rate_id_to_match = chargebee_event["content"]["invoice"]["line_items"][
            0
        ]["entity_id"]
        # rate_id_to_match = "Jigsaw-RTI-25"
        logger.info(f"rate id: {rate_id_to_match}")
        mileage_to_match = chargebee_event["content"]["subscription"][
            "cf_Vehicle Mileage"
        ]
        brokering_for = chargebee_event["content"]["subscription"][
            "cf_Brokering For"
        ]
        # product = find_matching_product(
        #     all_insurance_products, "209", mileage_to_match
        # )
        logger.info("all prods: {all_insurance_products}")
        product = find_matching_product(
            all_insurance_products, rate_id_to_match, mileage_to_match
        )
        merchant_id = ""
        if product:
            logger.info(f"found product {product}")
            merchant_id = get_merchant_from_bubble(
                data_type="Merchant", merchant_name=brokering_for
            )
            if merchant_id:
                print(f"found merchant id from bubble: {merchant_id}")
                logger.info(f"found merchant id from bubble: {merchant_id}")

            # if brokering_for == "Jigsaw Finance":
            #     merchant_id = "1694197230597x897747846563364900"
            # elif brokering_for == "Kandoo":
            #     merchant_id = "1698764936036x648723526821609500"
            # print("merchant_id from if elif: ", merchant_id)
            associated_insurance_product = [product["_id"]]
            # associated_merchant = merchant_id

            data_to_be_updated = {
                "Associated Merchants": [merchant_id],
                "Associated Merchant Group": [
                    "1694182693471x292524019912540160"
                ],
            }
            response = update_bubble(
                cust_id=cust_id, payload=data_to_be_updated, data_type="User"
            )
            logger.info(f"updating user data {response}")
            sold_price = product.get("Insurer 1 Premium Total", 0)
            wholesale_price = product.get("Wholesale Price", 0)
            tax_type = product.get("Tax Type", "")
            dealership = "yes" if product.get("Sales Plugin", False) else "no"
            short_code = (
                product.get("Product Short Code", "")
                if product.get("Product Short Code", "")
                else ""
            )
            print("sold_price", sold_price)
            print("wholesale_price", wholesale_price)
            print("tax_type", tax_type)
            print("dealership", dealership)
            print("short_code", short_code)

            output, rate = calculate_tax(
                sold_price,
                wholesale_price,
                tax_type,
                dealership,
                short_code,
            )

            logger.info(f"Tax Output: {output}, Tax Rate: {rate}")

            # logger.info(f"Product Info: {product}")
            # logger.info(f"Vehicle Data: {vehicle_data}")

        vehicle_data = map_vehicle_data(
            vehicle_info=vehicle_info,
            chargebee_data=chargebee_event,
            cust_id=cust_id,
            associated_insurance_product=associated_insurance_product,
            associated_merchant=merchant_id,
        )

        if vehicle_data:
            try:
                logger.info(f"vehicledata: {vehicle_data}")
                vehicle_id = send_to_bubble(vehicle_data, data_type="Vehicle")
                if vehicle_id:
                    update_bubble(
                        cust_id=cust_id,
                        payload={"Associated Vehicle": [vehicle_id]},
                        data_type="User",
                    )
            except Exception as e:
                logger.error(f"An unexpected error occurred: {e}")
            logger.info(f"vehicle Data send to bubble for {vehicle_id}")

            address = (
                customer_data["Line 1: Address"]
                + customer_data["Line 2: Address"]
                + customer_data["Line 3: Address"]
                + customer_data["Line 4: Address"]
            )
            fund = (
                chargebee_event["content"]["invoice"]["total"]
                - chargebee_event["content"]["invoice"]["amount_paid"]
            )
            funded = False if fund == 0 else True

            print("after funded")
            today_date = datetime.now()
            print("td", today_date)
            formatted_date = today_date.strftime("%d/%m/%Y")
            print("fd", formatted_date)

            date_from_timestamp = datetime.utcfromtimestamp(
                chargebee_event["content"]["invoice"]["line_items"][0][
                    "date_from"
                ]
            )
            iso8601_date_from = date_from_timestamp.strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
            formatted_from_date = date_from_timestamp.strftime("%d/%m/%Y")
            date_to_timestamp = datetime.utcfromtimestamp(
                chargebee_event["content"]["invoice"]["line_items"][0][
                    "date_to"
                ]
            )
            iso8601_date_to = date_to_timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
            formatted_to_date = date_to_timestamp.strftime("%d/%m/%Y")
            fund = (
                chargebee_event["content"]["invoice"]["total"]
                - chargebee_event["content"]["invoice"]["amount_paid"]
            )
            contract_count = get_contract_count_from_bubble()
            reference = str(contract_count + 1)
            print("after reference")
            sales_rep = chargebee_event["content"]["subscription"][
                "cf_Sales Agent"
            ]
            aspiration = vehicle_info["Response"]["DataItems"][
                "TechnicalDetails"
            ]["General"]["Engine"]["Aspiration"]
            if aspiration == "Turbocharged":
                turbocharged = "Yes"
            else:
                turbocharged = "No"

            DrivingAxle = vehicle_info["Response"]["DataItems"][
                "TechnicalDetails"
            ]["General"]["DrivingAxle"]
            if DrivingAxle == "4WD":
                four_wheel_drive = "Yes"
            else:
                four_wheel_drive = "No"

            rendered_html = template.render(
                title="Auto Cover",
                customer_data=customer_data,
                vehicle_data=vehicle_data,
                product_data=product,
                funded=funded,
                formatted_date=formatted_date,
                formatted_from_date=formatted_from_date,
                formatted_to_date=formatted_to_date,
                reference=reference,
                sales_rep=sales_rep,
                turbocharged=turbocharged,
                four_wheel_drive=four_wheel_drive,
                address=address,
            )
            print("rendered first html")
            service_invoice_data = map_invoice_data(
                chargebee_event=chargebee_event,
                product=product,
                rate=rate,
            )
            print("invoice data: ", service_invoice_data)
            invoice_rendered_html = invoice_template.render(
                data=service_invoice_data
            )
            print("invoice_rendered_html done")
            service_invoice_rendered_html = service_invoice_template.render(
                data=service_invoice_data
            )
            print("service_invoice_rendered_html done")
            contract_info = {}
            # print("I CAME HERE")
            contract_info = map_contract_data(
                vehicle_info=vehicle_info,
                chargebee_event=chargebee_event,
                product=product,
            )

            contract_info["Merchant Name"] = brokering_for
            contract_info["Sold Price"] = sold_price
            contract_info["Insurer"] = product["Insurer 1"]
            contract_info["Associated Vehicle"] = vehicle_id
            print("This is the contract info")
            contract_count = get_contract_count_from_bubble()
            print("contract_count", contract_count)
            if contract_count is not None:
                contract_info["Contract ID"] = "AC" + str(contract_count + 1)
            else:
                contract_info["Contract ID"] = "AC0"
            contract_info["Final Total Associated Costs"] = (
                product["Merchant Commission Value"] + sold_price
            )

            logger.info(
                f"sending this data in contract bubble: {contract_info}"
            )
            # print("I came here to bubble sending part 2")
            contract_id = send_to_bubble(contract_info, data_type="Contract")
            if contract_id:
                logger.info(f"Data stored in Contract table for {contract_id}")

                close_io_data = {}
                close_io_data["status_label"] = "Customer"
                close_io_data["opportunities"] = []
                close_io_data["html_url"] = (
                    "https://app.close.com/lead/lead_pJnSWX48EbdR87MrEXp50COJJTXAmpb3tyimyiTetoY/"
                )
                close_io_data["description"] = ""
                date_created_timestamp = datetime.utcfromtimestamp(
                    chargebee_event["content"]["subscription"]["created_at"]
                )
                iso8601_date_created = date_created_timestamp.strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                )
                close_io_data["date_created"] = iso8601_date_created
                close_io_data["updated_by"] = (
                    "user_Q6ReFolMojBwSlUB3g9qq8esW1hdbqhMUDwpKLoZ2F9"
                )
                close_io_data["id"] = (cust_id, "")
                close_io_data["name"] = customer_data["Full Name"]
                close_io_data["tasks"] = []
                base_url = "https://claims-gurus.co.uk/admin_customer_detail/"

                # Appending the variable to the base_url
                base_url += cust_id

                close_io_data["url"] = base_url
                date_updated_timestamp = datetime.utcfromtimestamp(
                    chargebee_event["content"]["invoice"]["updated_at"]
                )
                iso8601_date_updated = date_updated_timestamp.strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                )
                close_io_data["date_updated"] = iso8601_date_updated
                close_io_data["status_id"] = (
                    "stat_MjFlXA2c4yOUesIMAZISBqwTdiMdN4k7wKiTPQL8a4M"
                )
                close_io_data["display_name"] = customer_data["Full Name"]

                date_from_timestamp = datetime.utcfromtimestamp(
                    chargebee_event["content"]["invoice"]["line_items"][0][
                        "date_from"
                    ]
                )
                iso8601_date_from = date_from_timestamp.strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                )
                date_to_timestamp = datetime.utcfromtimestamp(
                    chargebee_event["content"]["invoice"]["line_items"][0][
                        "date_to"
                    ]
                )
                iso8601_date_to = date_to_timestamp.strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                )
                fund = (
                    chargebee_event["content"]["invoice"]["total"]
                    - chargebee_event["content"]["invoice"]["amount_paid"]
                )
                funded = False if fund == 0 else True

                close_io_data["custom"] = {
                    "1. End Date": iso8601_date_to,
                    "1. Price": chargebee_event["content"]["subscription"][
                        "subscription_items"
                    ][0]["amount"],
                    "1. Product": product["Variant Name"],
                    "1. Start Date": iso8601_date_from,
                    "ClaimsGurus Customer ID": cust_id,
                    "Engine Size": vehicle_data["Engine capacity *"],
                    "Financed?": funded,
                    "First Registered Date": vehicle_data[
                        "First registered *"
                    ],
                    "Make/Model": vehicle_data["Make"]
                    + "/"
                    + vehicle_data["Model"],
                    "Mileage": vehicle_data["Annual mileage"],
                    "Vehicle - Price": vehicle_data["Vehicle price *"],
                    "VRM": vehicle_info["Request"]["DataKeys"]["Vrm"],
                }
                # print("to send to close: ", close_io_data)
                lead_response = send_data_to_closeio(data=close_io_data)
                logger.info(
                    f"sending data to close, close response {lead_response}"
                )

                contact_data = {
                    "lead_id": lead_response["id"],
                    "name": customer_data["Full Name"],
                    "title": "President",
                    "country": chargebee_event["content"]["customer"][
                        "billing_address"
                    ]["country"],
                    "phones": [
                        {
                            "phone": chargebee_event["content"]["customer"][
                                "phone"
                            ],
                            "type": "mobile",
                        }
                    ],
                    "emails": [
                        {"email": customer_data["email"], "type": "office"}
                    ],
                    "urls": [
                        {"url": "http://twitter.com/google/", "type": "url"}
                    ],
                    "custom.cf_j0P7kHmgFTZZnYBFtyPSZ3uQw4dpW8xKcW7Krps8atj": "Account Executive",
                }

                contact_created = create_contact(data=contact_data)
                logger.info(f"contact response: {contact_created}")

                email_response = save_or_send_pdf(
                    rendered_html=rendered_html,
                    service_invoice_rendered_html=service_invoice_rendered_html,
                    invoice_rendered_html=invoice_rendered_html,
                    to_email=customer_data["email"],
                    cust_id=cust_id,
                )
                logger.info(f"Email sent {email_response['status_code']}")

                # updating contract for contract link
                contract_link = email_response["contract_s3_link"]
                print("link: ", contract_link)
                contract_data_to_be_updated = {
                    "Contract": contract_link,
                }
                print("about to update contract info")
                response = update_bubble(
                    cust_id=cust_id,
                    payload=contract_data_to_be_updated,
                    data_type="Contract",
                )
                logger.info(f"contract link update: {response}")

                if email_response["status_code"] == 202:
                    data_to_be_updated = {
                        "Customer Status": "Confirmed",
                    }
                    response = update_bubble(
                        cust_id=cust_id,
                        payload=data_to_be_updated,
                        data_type="User",
                    )
                    logger.info(f"user status update {response}")
                else:
                    data_to_be_updated = {
                        "Customer Status": "Awaiting Confirmation",
                    }
                    response = update_bubble(
                        cust_id=cust_id,
                        payload=data_to_be_updated,
                        data_type="User",
                    )
                    logger.error(f"user status update {response}")
        else:
            logger.warning("No contract id")
    else:
        logger.error("cust_id not found")


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
    print(chargebee_event)
    print("I WAS HERE INSIDE CONTRACT")
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


def map_invoice_data(chargebee_event, product, rate):
    invoice_number = chargebee_event["content"]["invoice"]["id"]
    invoice_date = datetime.utcfromtimestamp(
        chargebee_event["content"]["invoice"]["generated_at"]
    ).date()
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

    sub_total = amount * payment_terms
    total_amount = sub_total + (sub_total * rate)

    payment_schedule_list = []

    for i in range(1, payment_terms + 1):
        current_date = date_from_timestamp + timedelta(days=30 * i)
        formatted_date = current_date.strftime("%d/%m/%Y")

        # Create the payment_schedule string
        payment_schedule = f"Payment ({i} of {payment_terms})"

        # Create the dictionary for the current iteration and append it to the list
        payment_schedule_list.append(
            {
                "payment_schedule": payment_schedule,
                "date": formatted_date,
                "amount": amount,
            }
        )

    return {
        "Full Name": full_name,
        "Line 1: Address": line1,
        "Line 2: Address": line2,
        "invoice_number": invoice_number,
        "invoice_date": invoice_date,
        "payment_terms": payment_terms,
        "payment_schedule_list": payment_schedule_list,
        "sub_total": sub_total,
        "rate": rate,
        "total_amount": total_amount,
        "balance_due": total_amount - amount,
        "product_type": product["Product Type "],
        "variant_name": product["Variant Name"],
        "variant_term": product["Variant Term"],
    }
