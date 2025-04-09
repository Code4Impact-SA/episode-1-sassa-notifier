import requests
import logging
from django.contrib.auth import get_user_model
from django.conf import settings
from django.shortcuts import get_object_or_404
from .models import SassaApplication, SassaStatusCheck, SassaOutcome
from django.db import transaction  # Import transaction

User = get_user_model()

# Get the logger configured in settings
logger = logging.getLogger(__name__)


def fetch_sassa_status(id_number, mobile_number):
    """
    Fetches SASSA status from the API.

    Args:
        id_number (str): The ID number to query.
        mobile_number (str): The mobile number to use.

    Returns:
        dict: The JSON response from the SASSA API, or None on error.
    """
    url = 'https://srd.sassa.gov.za/srdweb/api/web/outcome'  # The SASSA API endpoint
    headers = {'Content-Type': 'application/json'}
    payload = {
        'idnumber': id_number,
        'mobile': mobile_number,
    }
    logger.info(f"Fetching SASSA status for ID: {id_number}, Mobile: {mobile_number}")  # Log the request

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()  # Parse the JSON response
        logger.debug(f"Received data from SASSA API: {data}")  # Log the response data
        return data
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching data from SASSA API: {e}")  # Log the error
        return None  # Return None on error


def update_sassa_database(data, id_number, mobile_number):
    """
    Updates the database with SASSA status data.
    Creates a user if the SassaApplication is newly created.
    Updates existing SassaStatusCheck and SassaOutcome records.
    Uses the mobile number as the username.

    Args:
        data (dict): The JSON data from the SASSA API.
        id_number (str): The ID number associated with the application.
        mobile_number (str): The mobile number.
    """
    if data is None:
        logger.warning("No data to update database.")  # Log a warning
        return  # Exit if no data was fetched.

    # Use a transaction to ensure data consistency.
    with transaction.atomic():
        # Get or create the user.  Use the mobile number as the username.
        user, user_created = User.objects.get_or_create(username=mobile_number)
        if user_created:
            logger.info(f"Created user with username: {mobile_number}")
        else:
            logger.info(f"User already exists: {mobile_number}")

        # Get or create the SassaApplication.
        sassa_app, created = SassaApplication.objects.get_or_create(
            user=user,
            id_number=id_number,
            defaults={
                'app_id': data.get('appId', 'N/A'),
                'phone_number': mobile_number,
                'sapo': data.get('sapo', 'N/A'),
                'status': data.get('status', 'N/A'),
                'risk': data.get('risk', False),
            }
        )
        if created:
            logger.info(f"Created SassaApplication with ID number: {id_number}")
        else:  # Update the existing application
            logger.info(f"Updating existing SassaApplication with ID number: {id_number}")
            sassa_app.app_id = data.get('appId', 'N/A')
            sassa_app.sapo = data.get('sapo', 'N/A')
            sassa_app.status = data.get('status', 'N/A')
            sassa_app.risk = data.get('risk', False)
            sassa_app.save()

        # Get or create the latest SassaStatusCheck.
        sassa_status_check, status_check_created = SassaStatusCheck.objects.get_or_create(
            application=sassa_app,
            defaults={
                'status': data.get('status', 'N/A'),
            }
        )
        if not status_check_created:
            logger.info(f"Updating SassaStatusCheck for application: {sassa_app.id}")
            sassa_status_check.status = data.get('status', 'N/A')
            sassa_status_check.save()
        else:
            logger.info(f"Created new SassaStatusCheck for application: {sassa_app.id}")

        # Update or create SassaOutcome instances.  Crucially, use the 'period' to identify them.
        for outcome_data in data.get('outcomes', []):
            period = outcome_data.get('period')
            SassaOutcome.objects.update_or_create(
                status_check=sassa_status_check,
                period=period,  # Use 'period' as the unique identifier
                defaults={  # update all the fields
                    'paid': outcome_data.get('paid'),
                    'filed': outcome_data.get('filed'),
                    'payday': outcome_data.get('payday'),
                    'outcome': outcome_data.get('outcome'),
                    'reason': outcome_data.get('reason'),
                }
            )
            logger.info(f"Updated/Created SassaOutcome for period: {period}, StatusCheck: {sassa_status_check.id}")
        return sassa_status_check


def fetch_and_save_sassa_status(id_number, mobile_number):
    """
    Fetches SASSA status from the API and saves it to the database.
    Creates a user if the SassaApplication is newly created.
    Updates existing SassaStatusCheck and SassaOutcome records.
    Uses the mobile number as the username.

    Args:
        id_number (str): The ID number to query.
        mobile_number (str): The mobile number to use.
    """
    sassa_data = fetch_sassa_status(id_number, mobile_number)
    if sassa_data:
        return update_sassa_database(sassa_data, id_number, mobile_number)
    return None
