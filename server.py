from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import httpx
import os
import json
import asyncio
from datetime import date
import xmlrpc.client
from typing import Optional, Tuple

load_dotenv()

# initialize server
mcp = FastMCP("odoo-blaze-mcp")

ODOO_URL = os.getenv("ODOO_URL")
ODOO_DB = os.getenv("ODOO_DB")
ODOO_USER = os.getenv("ODOO_USER")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD")

async def get_odoo_connection() -> Tuple[Optional[int], Optional[xmlrpc.client.ServerProxy]]:
    """Utility function to handle Odoo authentication and connection"""
    common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
    uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASSWORD, {})
    if not uid:
        return None, None
    
    models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")
    return uid, models

async def execute_odoo_operation(operation: str, *args, **kwargs):
    """Utility function to execute Odoo operations with error handling"""
    uid, models = await get_odoo_connection()
    if not uid or not models:
        return None
    
    try:
        result = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, *args, **kwargs)
        return result
    except Exception as e:
        print(f"Error in {operation}: {str(e)}")
        return None

async def Fetch_list_leads():
    """It pulls the leads list from Odoo CRM."""
    result = await execute_odoo_operation(
        'fetch_leads',
        'crm.lead', 'search_read',
        [[]],
        {'fields': ['name', 'contact_name', 'email_from']}
    )
    return result

async def Fetch_lead_by_id(lead_id: int):
    """It pulls the specific lead details from Odoo CRM by ID."""
    result = await execute_odoo_operation(
        'fetch_lead_by_id',
        'crm.lead', 'search_read',
        [[['id', '=', lead_id]]],
        {'fields': ['name', 'contact_name', 'email_from', 'phone', 'description']}
    )
    return result[0] if result else None

async def create_lead(lead_data: dict):
    """It will create a new lead in odoo crm."""
    try:
        result = await execute_odoo_operation(
            'create_lead',
            'crm.lead', 'create',
            [lead_data]
        )
        return {"code": "200", "message": f"Lead created successfully with ID: {result}"} if result else {
            "code": 400,
            "message": "Failed to create lead"
        }
    except Exception as e:
        return {"code": 400, "message": f"An error occurred: {str(e)}"}

# MCP Tool functions remain unchanged
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
        'name': name,
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


