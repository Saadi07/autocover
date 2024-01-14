from utils.utils import (
    send_to_bubble,
    get_vehicle_info,
    get_from_bubble,
    find_matching_record,
    calculate_tax,
    update_bubble,
    get_merchant_from_bubble,
    save_or_send_pdf,
)
from config.logger import logger
from jinja2 import Environment, FileSystemLoader

# TEMPLATE_FILE_PATH = "/home/saadi09/Documents/InsightHub Projects/AUTOCOVER/templates"
TEMPLATE_FILE_PATH = r"templates"

template_env = Environment(loader=FileSystemLoader(TEMPLATE_FILE_PATH))
template = template_env.get_template("SCOTT JONES Contract.html")


def find_matching_product(
    all_records_dict, rate_id_to_match, mileage_to_match
):
    print("charge rate", rate_id_to_match)
    product = find_matching_record(
        all_records_dict, rate_id_to_match, mileage_to_match
    )

    if not product:
        logger.warning("No matching record found.")

    return product


def chargebee_payment_success_service(chargebee_event):
    # print("all chargebee", chargebee_event)
    customer_data = map_customer_data(chargebee_event)
    # print("customer_data", customer_data)
    cust_id = send_to_bubble(customer_data, data_type="User")

    if cust_id:
        vehicle_info = get_vehicle_info(chargebee_event)
        # print(vehicle_info)

        all_insurance_products = get_from_bubble(data_type="Insurance Product")
        rate_id_to_match = chargebee_event["content"]["invoice"]["line_items"][
            0
        ]["entity_id"]
        mileage_to_match = chargebee_event["content"]["subscription"][
            "cf_Vehicle Mileage"
        ]
        brokering_for = chargebee_event["content"]["subscription"][
            "cf_Brokering For"
        ]
        product = find_matching_product(
            all_insurance_products, "91", mileage_to_match
        )

        if product:
            merchant_id = get_merchant_from_bubble(
                data_type="Merchant", merchant_name=brokering_for
            )

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
            vehicle_id = send_to_bubble(vehicle_data, data_type="Vehicle")
            logger.info(f"Data send to bubble for {vehicle_id}")

            rendered_html = template.render(
                title="Auto Cover",
                customer_data=customer_data,
                vehicle_data=vehicle_data,
                product_data=product,
            )

            save_or_send_pdf(rendered_html)

        else:
            logger.warning("Failed to map vehicle data.")
    else:
        logger.warning("cust_id not found")


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

    technical_details = vehicle_info["Response"]["DataItems"]["TechnicalDetails"]

    subscription_content = chargebee_data["content"]["subscription"]

    is_new_vehicle = int(subscription_content["cf_Vehicle Mileage"]) == 0


    vehicle_info = {
        "Make": classification_details["Smmt"]["Make"],
        "Model": classification_details["Dvla"]["Model"],
        "Vehicle Trim": classification_details["Smmt"]["Trim"],
        "Style": registration_details["DoorPlanLiteral"],
        "Colour": registration_details["Colour"],
        "VIN number": registration_details["Vin"],
        "Imported": registration_details["Imported"],
        "Engine capacity *": registration_details["EngineCapacity"],
        "Fuel Type": smmt_details["FuelType"],
        "First registered *": registration_details["DateFirstRegistered"],
        "Vehicle Type": smmt_details["BodyStyle"],
        "Drive Type": smmt_details["DriveType"],
        "Turbo Charged": "Yes" if technical_details["General"]['Engine']['Aspiration'] == "Turbocharged" else "No",
        "Catalytic Converter": "Yes" if technical_details["General"]['Engine']['FuelCatalyst'] == "C" else "No",
        "VRN": subscription_content[
            "cf_Vehicle Registration Number (Licence Plate)*"
        ],
        "Annual mileage": subscription_content["cf_Vehicle Mileage"],
        "Vehicle price *": subscription_content["cf_Vehicle Price"],
        "Dealer bought from": subscription_content["cf_Dealer Name"],
        "Sales Agent": subscription_content["cf_Sales Agent"],
        "Sale Type": "New" if is_new_vehicle else "Used",
        "Delivery date": subscription_content["created_at"],
        "Associated User": cust_id,
        "Associated Insurance Product": associated_insurance_product,
        "Associated Merchant": associated_merchant,
    }

    return vehicle_info
