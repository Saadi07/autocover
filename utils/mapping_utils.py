import calendar
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
        "User Type": "Customer",
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
    print("registration details", registration_details)
    smmt_details = vehicle_info["Response"]["DataItems"]["SmmtDetails"]

    technical_details = vehicle_info["Response"]["DataItems"][
        "TechnicalDetails"
    ]
    aspiration = vehicle_info["Response"]["DataItems"]["TechnicalDetails"][
        "General"
    ]["Engine"]["Aspiration"]
    if aspiration == "Turbocharged":
        turbocharged = "Yes"
    else:
        turbocharged = "No"

    subscription_content = chargebee_data["content"]["subscription"]
    sales_agent = subscription_content["cf_Sales Agent"]
    print("sales agent", sales_agent)

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
        "First registered *": registration_details["DateFirstRegistered"].split("T")[0] if registration_details[
                                                                                    "DateFirstRegistered"] is not None else None,
        "Vehicle Type": registration_details["VehicleClass"],
        "Is the vehicle turbo charged? *":turbocharged,
        "VRN": subscription_content[
            "cf_Vehicle Registration Number (Licence Plate)*"
        ],

        "Current or point of sale mileage *": subscription_content["cf_Vehicle Mileage"],
        "Annual mileage": subscription_content["cf_Vehicle Mileage"],
        "Vehicle price *": subscription_content["cf_Vehicle Price"],
        "Dealer bought from": subscription_content["cf_Dealer Name"],
        "Sale Type": "New" if is_new_vehicle else "Used",

        "Associated User": cust_id,
        "If available on the level of cover you choose, would you like to include the optional cover for Catalytic Convertor? *": "No",
        "If available on the level of cover you choose, would you like to include the optional cover for the motorised / powered roof? *": "No",
        "If available on the level of cover you choose, would you like to include the optional cover for the vehicle's factory fitted Satellite Navigation, Media and Command Centre? *": "No",
        "Associated Insurance Product": associated_insurance_product,
        "Associated Merchant": associated_merchant,
    }

    return vehicle_info


def map_contract_data(chargebee_event, vehicle_info, product, merchant,merchant_name):
    fund = (
            chargebee_event["content"]["invoice"]["total"]
            - chargebee_event["content"]["invoice"]["amount_paid"]
    )
    funded = "No" if fund == 0 else "Yes"
    billing_address = chargebee_event["content"]["customer"]["billing_address"]
    ipt_amount = round(product["RRP"] * 0.107202400800267, 2)
    regional_manager_profit = product.get("Regional Manager Commission Rate", 0)
    sold_price = product["RRP"]
    regional_manager_value = product.get("Regional Manager Commission Value", 0)
    final_regional_manager_profit = regional_manager_profit * sold_price + regional_manager_value
    account_manager_2_rate = product.get("Account Manager 2 Commission Rate", 0)
    account_manager_2_value = product.get("Account Manager 2 Commission Value", 0)
    final_regional_manager_2_profit = account_manager_2_rate * sold_price + account_manager_2_value
    account_manager_3_rate = product.get("Account Manager 3 Commission Rate", 0)
    account_manager_3_value = product.get("Account Manager 3 Commission Value", 0)
    final_regional_manager_3_profit = account_manager_3_rate * sold_price + account_manager_3_value
    sales_rep_commision_rate = product.get("Sales Rep Commission Rate", 0)
    sales_rep_commission_value = product.get("Sales Rep Commission Value", 0)
    final_sales_rep_profit = sales_rep_commision_rate * sold_price + sales_rep_commission_value
    sales_rep_2_commision_rate = product.get("Sales Rep 2 Commission Rate", 0)
    sales_rep_2_commision_value = product.get("Sales Rep 2 Commission Value", 0)
    final_sales_rep_2_profit = sales_rep_2_commision_rate * sold_price + sales_rep_2_commision_value
    sales_comission_rate = product.get("Sales Plugin Commission Rate", 0)
    sales_plugin_commission_value = product.get("Sales Plugin Commission Value", 0)
    final_sales_plugin_profit = sales_comission_rate * sold_price + sales_plugin_commission_value
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
    ipt_amount = round(product["RRP"] * 0.107202400800267, 2)

    subscription_content = chargebee_event["content"]["subscription"]
    vrm = vehicle_info["Request"]["DataKeys"]["Vrm"]
    date_from_timestamp = datetime.utcfromtimestamp(
        chargebee_event["content"]["invoice"]["line_items"][0]["date_from"]
    )
    iso8601_date_from = date_from_timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
    date_to_timestamp = datetime.utcfromtimestamp(
        chargebee_event["content"]["invoice"]["line_items"][0]["date_to"]

    )
    merchat_other_cost = merchant.get("Other Costs Commission Rate", 0)
    final_merchent_other_cost = merchat_other_cost * sold_price
    merchant_comission_rate = product.get("Merchant Commission Rate", 0)
    merchant_comission_value = product.get("Merchant Commission Value", 0)
    final_merchant_profit = merchant_comission_rate * sold_price + merchant_comission_value
    iso8601_date_to = date_to_timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
    term = int(product["Variant Term"])
    print(term, type(term))
    date_after_term = date_from_timestamp + relativedelta(months=term)
    formatted_to_date = date_after_term.strftime("%Y-%m-%dT%H:%M:%SZ")
    formatted_to_date = (datetime.strptime(formatted_to_date, "%Y-%m-%dT%H:%M:%SZ") - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    associated_sales_rep = ["1707822104052x108486888219653470", product.get("Sales Rep 2", ""),
                            product.get("Account Manager 2", ""), product.get("Account Manager 3", ""),
                            product.get("Sales Rep", "")],
    filtered_sales_rep = [entry for entry in associated_sales_rep if entry and entry != ""]

    print("final_regional_manager_profit:", final_regional_manager_profit)
    print("final_regional_manager_2_profit:", final_regional_manager_2_profit)
    print("final_regional_manager_3_profit:", final_regional_manager_3_profit)
    print("final_sales_rep_profit:", final_sales_rep_profit)
    print("final_sales_rep_2_profit:", final_sales_rep_2_profit)
    print("final_sales_plugin_profit:", final_sales_plugin_profit)
    print("final_merchant_profit:", final_merchant_profit)

    final_total_associatied_cost = (
            final_regional_manager_profit +
            final_regional_manager_2_profit +
            final_regional_manager_3_profit +
            final_sales_rep_profit +
            final_sales_rep_2_profit +
            final_sales_plugin_profit +
            final_merchant_profit
    )
    sales_agent = subscription_content["cf_Sales Agent"]
    print("final_total_associatied_cost:", final_total_associatied_cost)
    final_full_payment_facilitator_cost = 0.022 * sold_price if funded == "No" else 0
    final_funded_payment_facilitator_cost = 0.15 * sold_price if funded == "Yes" else 0
    print("final_full_payment_facilitator_cost:", final_full_payment_facilitator_cost)
    print("final_funded_payment_facilitator_cost:", final_funded_payment_facilitator_cost)
    contract_info = {
        "static_customer_name": full_name,
        "static_customer_email": email,
        "static_customer_phone_text": phone_number,
        "static_customer_address": line1,
        "Funded Product": funded,
        "static_product_name": product["Variant Name"],
        "Sales Agent 2": sales_agent if sales_agent else "",

        "Final Full Payment Facilitator Cost": final_full_payment_facilitator_cost,
        "Final Funded Payment Facilitator Cost": final_funded_payment_facilitator_cost,
        "Final Customer Tax Amount": ipt_amount,
        "Reconciled": "Yes",
        "Merchant Commission Amount": final_merchant_profit,
        "static_vehicle_colour": registration_details["Colour"],
        "static_vehicle_engine_capacity": registration_details[
            "EngineCapacity"
        ],
        "Policy End Date": formatted_to_date,
        "Policy Start Date": iso8601_date_from,
        "static_vehicle_mileage": subscription_content["cf_Vehicle Mileage"],
        "static_vehicle_vrm": vrm,
        "Accelerated Commission Amount": (
            product["Acc. Flow Monthly Instalment Amount"]
            if "Acc. Flow Monthly Instalment Amount" in product
            else product["RRP"]
        ),
        # "Accelerated Flow Type": product["Acc. Flow Type"],
        "Accelerated Flow Type": (
            product["Acc. Flow Type"]
            if "Acc. Flow Type" in product
            else "One-Time"
        ),
        "Accelerated Number of Instalments": (
            product["Acc. Flow Number of Instalments"]
            if "Acc. Flow Number of Instalments" in product
            else 1
        ),
        "Associated Insurance Product": product["_id"],
        "Final RRP": product["RRP"],
        "Monthly Product": "No",
        "Contract Status": "Live",
        "Associated Sales Reps": ["1707822104052x108486888219653470"],
        "Final Insurer 1 Underwriting Price": product.get("Insurer 1 Premium Total", 0),  # dummy value
        "Final Sales Plugin Profit": final_sales_plugin_profit if final_sales_plugin_profit is not None else 0,
        "Final Insurer 1 Underwriting Tax Amount": round(product.get("Insurer 1 Premium Total", 0) * 0.12, 2),
        # dummy value
        # "Remaining Claim Budget": product.get("Variant Claim limit", 0),
        # "Remaining Number of Claims": product.get("Number of Claims", 0),
        "Final Other Merchant Costs": final_merchent_other_cost if final_merchent_other_cost is not None else 0,

        "Final Total Associated Costs": final_total_associatied_cost,
        "Final Regional Manager Profit": final_regional_manager_profit if final_regional_manager_profit is not None else 0,
        "Final Account Manager 2 Profit": final_regional_manager_2_profit if final_regional_manager_2_profit is not None else 0,
        "Final Account Manager 3 Profit": final_regional_manager_3_profit if final_regional_manager_3_profit is not None else 0,
        "Final Sales Rep 1 Profit": final_sales_rep_profit if final_sales_rep_profit is not None else 0,
        "Final Sales Rep 2 Profit": final_sales_rep_2_profit if final_sales_rep_2_profit is not None else 0,
        "Final Merchant Tax Amount": 0,
        "Final Merchant Wholesale Tax Rate": 0.12,
        "Final Merchant Wholesale Price": 0,
        # "Contract": contract_link,
    }
    print("HERE IS CONTRACT",contract_info)
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
            + " " + customer_data["Line 2: Address"]
            + " " + customer_data["Line 3: Address"]
            + " " + customer_data["Line 4: Address"]
    )
    print("inside mapping for address", address)
    first_registered_date = vehicle_data["First registered *"]
    if first_registered_date is not None:
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
    print("from date", formatted_from_date)
    term = int(product_data["Variant Term"])
    print(term, type(term))
    date_after_term = date_from_timestamp + relativedelta(months=term)
    formatted_to_date = date_after_term.strftime("%d/%m/%Y")
    formatted_to_date = (datetime.strptime(formatted_to_date, "%d/%m/%Y") - timedelta(days=1)).strftime("%d/%m/%Y")

    print("to date", formatted_to_date)
    vehicle_price = round(int(vehicle_data["Vehicle price *"]), 2)
    if "Product Claim Type" in product_data:
        claim_limit = product_data["Product Claim Type"]
    else:
        claim_limit = " "

    # del_date = datetime.utcfromtimestamp(
    #     vehicle_data["Delivery date"]
    # ).strftime("%m/%d/%Y")

    sold_price = product_data["RRP"]

    response = {
        "title": "Auto Cover",
        "reference": reference,
        "Full Name": customer_data["Full Name"],
        "Address": address,
        "Phone Number 2": customer_data["Phone Number 2"],
        "email": customer_data["email"],
        "VRN": vehicle_data["VRN"],
        "VIN number": vehicle_data["VIN number"],
        "Delivery date": formatted_from_date,
        "Make": vehicle_data["Make"],
        "Engine capacity *": vehicle_data["Engine capacity *"],
        "Vehicle price *": vehicle_price,
        "Model": vehicle_data["Model"],
        "First registered *": first_registered_date if first_registered_date is not None else None,
        "Dealer": "AutoCover",
        "Annual mileage": vehicle_data["Annual mileage"],
        "Vehicle Type": vehicle_data["Vehicle Type"],
        "Merchant": "AutoCover",
        "Sale Type": vehicle_data["Sale Type"],
        "Is the vehicle imported?": vehicle_data["Is the vehicle imported?"],
        "turbocharged": turbocharged,
        "four wheel drive": four_wheel_drive,
        "Product Type": "Asset Protection",
        "Variant Name": product_data["Variant Name"],
        "Variant Term": product_data["Variant Term"],
        "Variant Claim limit": claim_limit,
        "Variant Excess": product_data["Variant Excess"],
        "Sold Price": sold_price,
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
    invoice_date = (
        datetime.utcfromtimestamp(
            chargebee_event["content"]["invoice"]["generated_at"]
        )
        .date()
        .strftime("%d/%m/%Y")
    )
    # print("invoice date", invoice_date)

    billing_address = chargebee_event["content"]["customer"]["billing_address"]
    customer = chargebee_event["content"]["customer"]
    full_name = f"{customer['first_name']} {customer['last_name']}"
    line1 = billing_address.get("line1", "")
    line2 = billing_address.get("line2", "")
    city_country = f"{billing_address.get('city', '')}, {billing_address.get('country', '')}"
    postal_code = billing_address.get("postal_code", "")

    date_from_timestamp = datetime.utcfromtimestamp(
        chargebee_event["content"]["invoice"]["line_items"][0]["date_from"]
    ).date()
    print("from date", date_from_timestamp)

    amount = (
        product["Acc. Flow Monthly Instalment Amount"]
        if "Acc. Flow Monthly Instalment Amount" in product
        else product["RRP"]
    )
    payment_terms = (
        product["Acc. Flow Number of Instalments"]
        if "Acc. Flow Number of Instalments" in product
        else 1
    )
    monthly_amount = round(amount + (amount * rate), 2)
    IPT_Amount = round(product["RRP"] * 0.107202400800267, 2)
    sub_total = round((amount * payment_terms), 2)

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
        current_date = date_from_timestamp + timedelta(days=30 * i)

        # Adjust month if it exceeds 12
        current_year = current_date.year + (current_date.month + i - 1) // 12
        current_month = (current_date.month + i - 1) % 12 + 1

        current_date = current_date.replace(year=current_year, month=current_month)

        # Get the number of days in the current month
        num_days_in_month = calendar.monthrange(current_date.year, current_date.month)[1]

        # Adjust the day value if it's greater than the number of days in the month
        current_date = current_date.replace(day=min(current_date.day, num_days_in_month))

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
        "Line 3: Address": city_country,
        "Line 4: Address": postal_code,
        # "monthly_amount": monthly_amount,
        "invoice_number": invoice_number,
        "invoice_date": invoice_date,
        "payment_terms": payment_terms,
        "payment_schedule_list": payment_schedule_list,
        "sub_total": sub_total,
        "rate": rate,
        "IPT_Amount": IPT_Amount,
        "total_amount": total_amount,
        "balance_due": total_amount - monthly_amount,
        "product_type": "Asset Protection",
        "variant_name": product["Variant Name"],
        "variant_term": product["Variant Term"],
    }
