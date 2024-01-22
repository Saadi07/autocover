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
)
from config.logger import logger
from jinja2 import Environment, FileSystemLoader
from datetime import datetime

# TEMPLATE_FILE_PATH = "/home/saadi09/Documents/InsightHub Projects/AUTOCOVER/templates"
TEMPLATE_FILE_PATH = r"templates"

template_env = Environment(loader=FileSystemLoader(TEMPLATE_FILE_PATH))
template = template_env.get_template("SCOTT JONES Contract.html")


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
    print("start")
    # print("all chargebee", chargebee_event)
    customer_data = map_customer_data(chargebee_event)
    # print("customer_data", customer_data)
    cust_id = send_to_bubble(customer_data, data_type="User")
    print("customer id", cust_id)
    if cust_id:
        logger.info(f"Customer Data sent to Bubble. Customer id: {cust_id}")
        vehicle_info = get_vehicle_info(chargebee_event)
        # print(vehicle_info)
        all_insurance_products = get_from_bubble(data_type="Insurance Product")

        # rate_id_to_match = chargebee_event["content"]["invoice"]["line_items"][
        #     0
        # ]["entity_id"]
        rate_id_to_match = "Jigsaw-RTI-25"
        print("rate id", rate_id_to_match)
        mileage_to_match = chargebee_event["content"]["subscription"][
            "cf_Vehicle Mileage"
        ]
        brokering_for = chargebee_event["content"]["subscription"][
            "cf_Brokering For"
        ]
        # product = find_matching_product(
        #     all_insurance_products, "209", mileage_to_match
        # )
        # print("all prods", all_insurance_products)
        product = find_matching_product(
            all_insurance_products, rate_id_to_match, mileage_to_match
        )
        # print("PRODUCT: ", product)

        if product:
            logger.info("found product")
            merchant_id = get_merchant_from_bubble(
                data_type="Merchant", merchant_name=brokering_for
            )
            if merchant_id:
                logger.info(f"found merchant id: {merchant_id}")
            associated_insurance_product = [product["_id"]]
            associated_merchant = merchant_id

            sold_price = product.get("Insurer 1 Premium Total", 0)
            wholesale_price = product.get("Wholesale Price", 0)
            tax_type = product.get("Tax Type", "")
            dealership = "yes" if product.get("Sales Plugin", False) else "no"
            short_code = product.get("Product Short Code", "")

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
            associated_merchant=associated_merchant,
        )
        # print("vehicledata", vehicle_data)
        if vehicle_data:
            try:
                # print("vehicle data", vehicle_data)
                vehicle_id = send_to_bubble(vehicle_data, data_type="Vehicle")
            except Exception as e:
                logger.error(f"An unexpected error occurred: {e}")
            logger.info(f"vehicle Data send to bubble for {vehicle_id}")

            rendered_html = template.render(
                title="Auto Cover",
                customer_data=customer_data,
                vehicle_data=vehicle_data,
                product_data=product,
            )

        contract_info = map_contract_data(
            vehicle_info=vehicle_info, chargebee_event=chargebee_event
        )
        contract_info = {}
        contract_info["Merchant Name"] = brokering_for
        contract_info["Sold Price"] = sold_price
        contract_info["Insurer"] = product["Insurer 1"]
        # contract_info[
        #     "Associated Insurance Product"
        # ] = associated_insurance_product
        contract_info["Associated Vehicle"] = vehicle_id
        # if product["Variant Claim limit"]:
        #     contract_info["Remaining Claim Budget"] = product[
        #         "Variant Claim limit"
        #     ]
        contract_id = send_to_bubble(contract_info, data_type="Contract")
        if contract_id:
            logger.info(f"Data stored in Contract table for {contract_id}")

            close_io_data = {}
            close_io_data["status_label"] = "Customer"
            close_io_data["opportunities"] = []
            close_io_data[
                "html_url"
            ] = "https://app.close.com/lead/lead_pJnSWX48EbdR87MrEXp50COJJTXAmpb3tyimyiTetoY/"
            close_io_data["description"] = ""
            date_created_timestamp = datetime.utcfromtimestamp(
                chargebee_event["content"]["subscription"]["created_at"]
            )
            iso8601_date_created = date_created_timestamp.strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
            close_io_data["date_created"] = iso8601_date_created
            close_io_data[
                "updated_by"
            ] = "user_Q6ReFolMojBwSlUB3g9qq8esW1hdbqhMUDwpKLoZ2F9"
            close_io_data["id"] = (cust_id, "")
            close_io_data["name"] = customer_data["Full Name"]
            close_io_data["tasks"] = []
            close_io_data[
                "url"
            ] = "https://claims-gurus.co.uk/version-test/admin_customer_detail/1699987991907x153592285691448000?"
            date_updated_timestamp = datetime.utcfromtimestamp(
                chargebee_event["content"]["invoice"]["updated_at"]
            )
            iso8601_date_updated = date_updated_timestamp.strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
            close_io_data["date_updated"] = iso8601_date_updated
            close_io_data[
                "status_id"
            ] = "stat_MjFlXA2c4yOUesIMAZISBqwTdiMdN4k7wKiTPQL8a4M"
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
            iso8601_date_to = date_to_timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
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
                "ClaimsGurus Customer ID": "1699987991907x153592285691448000",
                "Engine Size": vehicle_data["Engine capacity *"],
                "Financed?": funded,
                "First Registered Date": vehicle_data["First registered *"],
                "Make/Model": vehicle_data["Make"]
                + "/"
                + vehicle_data["Model"],
                "Mileage": vehicle_data["Annual mileage"],
                "Vehicle - Price": vehicle_data["Vehicle price *"],
                "VRM": vehicle_info["Request"]["DataKeys"]["Vrm"],
            }
            # print("to send to close: ", close_io_data)
            send_data_to_closeio(data=close_io_data)
            save_or_send_pdf(rendered_html, to_email=customer_data["email"])

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
        "First registered *": registration_details["DateFirstRegistered"],
        "Vehicle Type": smmt_details["BodyStyle"],
        # "Drive Type": smmt_details["DriveType"],
        # "Is the vehicle turbo charged? *": "Yes"
        # if technical_details["General"]["Engine"]["Aspiration"]
        # == "Turbocharged"
        # else "No",
        # "Catalytic Converter": "Yes"
        # if technical_details["General"]["Engine"]["FuelCatalyst"] == "C"
        # else "No",
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


def map_contract_data(chargebee_event, vehicle_info):
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
        "static_vehicle_mileage": subscription_content["cf_Vehicle Mileage"],
        "static_vehicle_vrm": vrm,
        "Monthly Product": "No",
        "Contract Status": "Live",
        "Contract": "PDF",
    }
    return contract_info
