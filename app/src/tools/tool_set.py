####
# Tools for the LLM to use in completing tasks
####

import os
from pydantic import EmailStr, validate_call
import requests
from dotenv import load_dotenv

load_dotenv()

#Retrieve environment variables
CUSTOMER_URL = os.getenv("CUSTOMER_URL")
TRANSACTION_URL = os.getenv("TRANSACTION_URL")
VERIFICATION_URL = os.getenv("VERIFICATION_URL")
RESET_URL = os.getenv("RESET_URL")


@validate_call
def verify_customer_exist(customer_email: EmailStr)-> dict:
    """
    This function checks the database to see if a customer exists for the provided email address.
    :param customer_email: Valid email address of the customer
    :return: A dictionary with customer_id as the key, the value of customer_id is postive integer if the customer exists or Not Found if the customer does not exist.
    """
    # Prepare request parameters
    url = CUSTOMER_URL
    data = {'email': customer_email}
    header = {'Content-Type': 'application/json'}

    response = requests.post(url=url, headers=header, json=data)
    res = response.json()

    
    if  int(res["code"]) == 404:
        return {"customer_id": "Not Found"}
    
    elif int(res["code"]) == 200:
        return {"customer_id": res["result"]}
    elif  int(res["code"]) == 400:
        return f"Error with request - {res['result']}"
    

@validate_call
def fix_credit_topup_issue(customer_id: int, transaction_id: str) -> str:
    """
    This function resolves credit top up issues by verifying transactions and automatically crediting customer account with the correct amount.
    :param customer_id: The ID of the customer making the request
    :param transaction_id: The ID of the transaction to be used for crediting customer account.
    :return: Status of the request eg Resolved, Not Resolved, No Resolution Required.
    """
    url = TRANSACTION_URL
    data = {'user_id': customer_id, 'transaction_id': transaction_id}
    header = {'Content-Type': 'application/json'}

    response = requests.post(url=url, headers=header, json=data)

    res = response.json()

    if int(res["code"]) == 502:
        return "Not Resolved: Payment Gateway Error"
    elif int(res["code"]) == 402:
        return f"No Resolution Required: The transaction with ID - {transaction_id} was not completed by the customer"
    elif int(res["code"]) == 406:
        return f"No Resolution Required: The transaction with ID - {transaction_id} cannot be found or has already been credited to the customer"
    elif int(res["code"]) == 200:
        return f"Resolved: The transaction with ID - {transaction_id} has been credited to the customer successfully, customer should check UelloSend Dashboard"
    elif  int(res["code"]) == 400:
        return f"Error with request - {res['result']}"


#print(verify_transaction(675, "LVC3V1VTR08H"))


@validate_call
def resend_account_verification_link(customer_email: EmailStr)-> str:
    """
    This function will resend a account verification link to the provided email address of the customer if it exists on record.
    :param customer_email: Valid email address of the customer
    :return: A string value to indicate the status of the request eg Verification Link Sent, Unable To Send Verification Link, Customer Not Found.
    """
    # Prepare request parameters
    url = VERIFICATION_URL
    data = {'email': customer_email}
    header = {'Content-Type': 'application/json'}

    response = requests.post(url=url, headers=header, json=data)
    res = response.json()

    
    if  int(res["code"]) == 404:
        return f"No customer found for email: {customer_email}"
    elif int(res["code"]) == 500:
        return f"Unable To Send Verification Link - {res['result']}"
    elif int(res["code"]) == 200:
        return f"Verification Link Sent to {customer_email} with Subject - UelloSend Account Verification Link. Customer should check all mail folders including SPAM"
    elif  int(res["code"]) == 400:
        return f"Error with request - {res['result']}"
    elif  int(res["code"]) == 406:
        return f"Account has already been verified, you can login to UelloSend dashboard"
    


@validate_call
def send_password_reset_link(customer_email: EmailStr)-> str:
    """
    This function will send reset password link to the provided email address of the customer if it exists on record.
    :param customer_email: Valid email address of the customer
    :return: A string value to indicate the status of the request eg Reset Password Link Sent, Unable To Send Reset Password Link, Customer Not Found.
    """
    # Prepare request parameters
    url = RESET_URL
    data = {'email': customer_email}
    header = {'Content-Type': 'application/json'}

    response = requests.post(url=url, headers=header, json=data)
    res = response.json()
    
    if  int(res["code"]) == 404:
        return f"No customer found for email: {customer_email}"
    elif int(res["code"]) == 500:
        return f"Unable To Send Reset Password Link Sent - {res['result']}"
    elif int(res["code"]) == 200:
        return f"Reset Password Link Sent to {customer_email} with Subject - Reset Password Link. Customer should check all mail folders including SPAM"
    elif  int(res["code"]) == 400:
        return f"Error with request - {res['result']}"