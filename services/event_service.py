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
    find_matching_product,
)
from utils.mapping_utils import *
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

            sales_rep = chargebee_event["content"]["subscription"][
                "cf_Sales Agent"
            ]

            contract_pdf_data = map_contract_pdf_data(
                customer_data=customer_data,
                vehicle_data=vehicle_data,
                product_data=product,
                chargebee_event=chargebee_event,
                vehicle_info=vehicle_info,
            )
            print("mapped data for cpdf", contract_pdf_data)
            rendered_html = template.render(data=contract_pdf_data)
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
                    customer_name=customer_data["Full Name"],
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
