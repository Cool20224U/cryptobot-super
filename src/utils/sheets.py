import gspread, time, os, json
from google.oauth2.service_account import Credentials

gc = gspread.authorize(Credentials.from_service_account_info(json.loads(os.getenv("GOOGLE_SHEETS_CREDENTIALS_JSON"))))
sheet = gc.open("CryptoBotState").worksheet("Heartbeat")

def claim_leadership(instance_id):
    current = sheet.cell(1, 1).value
    if not current or current == instance_id:
        sheet.update_cell(1, 1, instance_id)
        sheet.update_cell(2, 1, time.time())
        return True
    return False

def is_leader(instance_id):
    return sheet.cell(1, 1).value == instance_id
