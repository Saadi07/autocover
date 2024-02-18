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

    customer_data = map_customer_data(chargebee_event)
    logger.info(f"customer_data: {customer_data}")
    cust_id = send_to_bubble(customer_data, data_type="User")
    if cust_id:
        logger.info(f"Customer Data sent to Bubble. Customer id: {cust_id}")
        vehicle_info = get_vehicle_info(chargebee_event)
        print("VEHICLE INFO", vehicle_info)
        all_insurance_products = get_from_bubble(data_type="Insurance Product")

        rate_id_to_match = chargebee_event["content"]["invoice"]["line_items"][
            0
        ]["entity_id"]
        # rate_id_to_match = "Jigsaw-RTI-25"
        logger.info(f"rate id: {rate_id_to_match}")
        mileage_to_match = chargebee_event["content"]["subscription"][
            "cf_Vehicle Mileage"
        ]
        price_to_match = chargebee_event["content"]["subscription"][
            "cf_Vehicle Price"
        ]
        brokering_for = chargebee_event["content"]["subscription"][
            "cf_Brokering For"
        ]
        # product = find_matching_product(
        #     all_insurance_products, "209", mileage_to_match
        # )
        logger.info("all prods: {all_insurance_products}")
        product = find_matching_product(
            all_insurance_products,
            rate_id_to_match,
            mileage_to_match,
            price_to_match,
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
            merchant_group = get_merchant(
                "1694182693471x292524019912540160", "Merchant Group"
            )
            if merchant_group:
                print(f"found merchant group id from bubble: {merchant_group}")
                logger.info(
                    f"found merchant group id from bubble: {merchant_group}"
                )

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
            sold_price = product.get("RRP", 0)
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
                product_id = product["_id"]
                if vehicle_id:
                    update_bubble(
                        cust_id=cust_id,
                        payload={"Associated Vehicle": [vehicle_id]},
                        data_type="User",
                    )
                    update_bubble(
                        cust_id=product_id,
                        payload={"Associated Vehicle": vehicle_id},
                        data_type="Insurance Product",
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

            mapped_invoice_data = map_invoice_data(
                chargebee_event=chargebee_event,
                product=product,
                rate=rate,
            )

            invoice_rendered_html = invoice_template.render(
                data=mapped_invoice_data
            )
            print("invoice_rendered_html done")
            service_invoice_rendered_html = None
            if "full" in rate_id_to_match.lower():
                logger.warning(
                    "Rate ID contains 'full', service invoice will not be rendered."
                )
                print(
                    "Rate ID contains 'full', service invoice will not be rendered."
                )
            else:
                service_invoice_rendered_html = (
                    service_invoice_template.render(data=mapped_invoice_data)
                )
                print("service_invoice_rendered_html done")

            contract_info = {}
            # print("I CAME HERE")
            contract_info = map_contract_data(
                vehicle_info=vehicle_info,
                chargebee_event=chargebee_event,
                product=product,
                merchant=merchant_group,
                merchant_name=merchant_id,
            )
            if merchant_id and cust_id:
                print(
                    "Merchant ID is ", merchant_id, "and cust_id is ", cust_id
                )
                data_to_update = {
                    "Associated Merchant Users": [cust_id]
                }  # Fixed the dictionary definition
                data_to_update_in_users = {
                    "Associated Merchants": [merchant_id]
                }  # Fixed the dictionary definition
                updated_merchant = update_bubble(
                    merchant_id, data_to_update, "Merchant"
                )
                updated_user = update_bubble(
                    cust_id, data_to_update_in_users, "User"
                )
                print("updated_merchant", updated_merchant)

            if vehicle_id:
                contract_info["Associated Vehicle"] = vehicle_id

            logger.info(
                f"sending this data in contract bubble: {contract_info}"
            )

            try:
                contract_id = send_to_bubble(
                    contract_info, data_type="Contract"
                )
            except Exception as e:
                logger.error(f"An unexpected error occurred in contract: {e}")
            if contract_id:
                if vehicle_id:
                    date_from_timestamp = datetime.utcfromtimestamp(
                        chargebee_event["content"]["invoice"]["line_items"][0][
                            "date_from"
                        ]
                    )
                    # iso8601_date_from = date_from_timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
                    formatted_from_date = date_from_timestamp.strftime(
                        "%m/%d/%Y"
                    )
                    data_to_update = {
                        "Associated Contract": [contract_id],
                        "Associated Merchant": merchant_id,
                        "Delivery date": formatted_from_date,
                    }
                    data_updated = update_bubble(
                        cust_id=vehicle_id,
                        payload=data_to_update,
                        data_type="Vehicle",
                    )
                    print("data_updated", data_updated)
                logger.info(f"Data stored in Contract table for {contract_id}")

                close_io_data = {}
                close_io_data = map_closeio_data(
                    chargebee_event=chargebee_event,
                    cust_id=cust_id,
                    customer_data=customer_data,
                    product=product,
                    vehicle_info=vehicle_info,
                )

                lead_response = send_data_to_closeio(data=close_io_data)
                logger.info(
                    f"sending data to close, close response {lead_response}"
                )

                contact_data = map_contact_data(
                    lead_response=lead_response,
                    customer_data=customer_data,
                    chargebee_event=chargebee_event,
                )

                contact_created = create_contact(data=contact_data)
                logger.info(f"contact response: {contact_created}")

                email_response = save_or_send_pdf(
                    rendered_html=rendered_html,
                    service_invoice_rendered_html=(
                        service_invoice_rendered_html
                        if "full" not in rate_id_to_match.lower()
                        else None
                    ),
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
                    cust_id=contract_id,
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
                logger.warning("no contract id")
        else:
            logger.warning("No vehicle data")
    else:
        logger.error("cust_id not found")
