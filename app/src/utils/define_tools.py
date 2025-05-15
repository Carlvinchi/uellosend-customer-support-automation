####
# Defines the tools schema for the LLM to use in completing tasks
# This tools definition format is for Google Gemini Models
####

TOOLS_SCHEMA = [
            
            {
                "name": "verify_customer_exist",
                "description": "Checks the database to see if a customer exists for the provided email address, it returns a dictionary with customer_id as the key, the value of customer_id is postive integer if the customer exists or Not Found if the customer does not exist.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "customer_email": {
                            "type": "string",
                            "description": "Valid email address of the customer which will be used to check if the customer exists."
                        }
                    },
                    "required": ["customer_email"]
                }
            },

            {
                    "name": "fix_credit_topup_issue",
                    "description": "Resolves credit top up issues by verifying transactions and automatically crediting customer account with the correct amount, it returns the Status of the request eg Resolved, Not Resolved, No Resolution Required",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "customer_id": {
                                "type": "integer",
                                "description": "The ID of the customer making the request."
                            },
                            "transaction_id": {
                                "type": "string",
                                "description": "The ID of the transaction to be used for crediting customer account."
                            },
                        },
                        "required": ["customer_id", "transaction_id"]
                    }
            },
            {
                "name": "resend_account_verification_link",
                "description": "This function will resend a account verification link to the provided email address of the customer if it exists on record, it returns a string value to indicate the status of the request eg Verification Link Sent, Unable To Send Verification Link, Customer Not Found.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "customer_email": {
                            "type": "string",
                            "description": "Valid email address of the customer which will be used as the recipient of the account verification link."
                        }
                    },
                    "required": ["customer_email"]
                }
            },
            {
                "name": "send_password_reset_link",
                "description": "This function will send reset password link to the provided email address of the customer if it exists on record, it returns a string value to indicate the status of the request eg Reset Password Link Sent, Unable To Send Reset Password Link, Customer Not Found.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "customer_email": {
                            "type": "string",
                            "description": "Valid email address of the customer which will be used as the recipient of the reset password link."
                        }
                    },
                    "required": ["customer_email"]
                }
            },
        ]