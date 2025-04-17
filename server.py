from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import httpx
import os
import json
import asyncio
from datetime import date
import xmlrpc.client

load_dotenv()

# initialize server
mcp = FastMCP("odoo-blaze-mcp")

ODOO_URL = os.getenv("ODOO_URL", "https://mcp-research.odoo.com")
ODOO_DB = os.getenv("ODOO_DB", "mcp-research")
ODOO_USER = os.getenv("ODOO_USER", "shanmugam@blaze.ws")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD", "KjD9?.W4p4XJKz@q")

async def Fetch_list_leads():
    """ It pulls the employees list from the FocusRO API. """

     # Common endpoint for authentication
    common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")

    # Authenticate
    uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASSWORD, {})
    if not uid:
        print("Authentication failed.")
        exit()

    # Access the object endpoint
    models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")

    # Example: Search for CRM leads
    crm_leads = models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD,
        'crm.lead', 'search_read',  # Model and method
        [[]],  # Domain filter
        {'fields': ['name', 'contact_name', 'email_from']}  # Fields to fetch
    )

    return crm_leads


async def Fetch_lead_by_id(lead_id: int):
    """ It pulls the specific lead details from Odoo CRM by ID. """
    # Common endpoint for authentication
    common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")

    # Authenticate
    uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASSWORD, {})
    if not uid:
        print("Authentication failed.")
        return None

    # Access the object endpoint
    models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")

    # Search for specific CRM lead
    crm_lead = models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD,
        'crm.lead', 'search_read',  # Model and method
        [[['id', '=', lead_id]]],  # Domain filter for specific ID
        {'fields': ['name', 'contact_name', 'email_from', 'phone', 'description']}  # Fields to fetch
    )

    return crm_lead[0] if crm_lead else None


async def create_lead(lead_data:dict):
    """ It will created the new lead in odoo crm. """
    try:
        # Authenticate and get user ID
        common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
        uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASSWORD, {})
        if not uid:
            return {"code": 400, "message": "Authentication failed. Please check your credentials." }
        
        # Access the 'object' endpoint
        models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")
        
        # Create a new lead
        lead_id = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'crm.lead', 'create',  # Model and method
            [lead_data]  # Data for the new lead
        )
        
        return {"code": "200", "message": f"Lead created successfully with ID: {lead_id}"}
    
    except Exception as e:
        return {"code": 400, "message": f"An error occurred: {str(e)}"}


# Proper way to run async function
# if __name__ == "__main__":
#     print(asyncio.run(Fetch_weather_info("karachi")))


@mcp.tool()
async def list_leads():
    """ 
    Run to get leads list from odoo crm. 
    Example:
        list_leads()
    Returns:
        dict: The lead details.
    """

    leads = await Fetch_list_leads()
    if leads:
        return json.dumps(leads)
    return None


@mcp.tool()
async def get_lead_by_id(lead_id: int):
    """ 
    Run to get lead details by ID from odoo crm. 
    Parameters:
        lead_id: ID of the lead to fetch
    Example:
        get_lead_by_id(6)
    Returns:
        dict: The lead details.
    """
    lead = await Fetch_lead_by_id(lead_id)
    if lead:
        return json.dumps(lead)
    return json.dumps({"error": "Lead not found"})


@mcp.tool()
async def create_leads(name: str, contact_name: str, email_from: str, phone: str, description: str):
    """ 
    Run to create a lead in odoo crm. 
    Parameters:
        name: Name of the new lead - REQUIRED
        contact_name: person name of contact
        email_from: lead person's email address
        phone: lead person's phone number
        description: lead description
    Example:
        list_lead(lead_data)
    Returns:
        dict: sucess/error response.
    """

    lead_data = {
        'name': name,  # Required field
        'contact_name': contact_name,
        'email_from': email_from,
        'phone': phone,
        'description': description,
    }
    

    leads = await create_lead(lead_data)
    if leads:
        return json.dumps(leads)
    return None



if __name__ == "__main__":
    mcp.run(transport="stdio")


