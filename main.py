import gspread
import pandas as pd
import streamlit as st
import json
from google.oauth2.service_account import Credentials
from coordinator import DroneCoordinator

# Replace with your actual Google Sheet name
SHEET_NAME = "Skylark_Operations_Database"

def get_gspread_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    
    # --- CLOUD VS LOCAL LOGIC ---
    if "gcp_service_account" in st.secrets:
        # Load from Streamlit Cloud Secrets
        creds_info = json.loads(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(creds_info, scopes=scope)
    else:
        # Load from Local File
        creds = Credentials.from_service_account_file("service_account.json", scopes=scope)
    # ----------------------------
    
    return gspread.authorize(creds)

def load_coordinator():
    client = get_gspread_client()
    sheet = client.open(SHEET_NAME)
    
    pilots = pd.DataFrame(sheet.worksheet("pilot_roster").get_all_records())
    drones = pd.DataFrame(sheet.worksheet("drone_fleet").get_all_records())
    missions = pd.DataFrame(sheet.worksheet("missions").get_all_records())
    
    return DroneCoordinator(pilots, drones, missions)

def update_sheet_status(tab_name, id_col_name, row_id, new_status):
    client = get_gspread_client()
    ws = client.open(SHEET_NAME).worksheet(tab_name)
    
    # 1. Search for the ID
    cell = ws.find(row_id)
    
    # 2. Safety Check
    if cell is None:
        return False, f"Error: ID '{row_id}' not found in the {tab_name} tab."
    
    # 3. Find 'status' column dynamically
    headers = ws.row_values(1)
    if "status" not in headers:
        return False, "Error: Could not find 'status' column."
    
    status_col = headers.index("status") + 1
    
    # 4. Perform update
    ws.update_cell(cell.row, status_col, new_status)
    return True, "Success"
