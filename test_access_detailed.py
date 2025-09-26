import gspread
from google.oauth2.service_account import Credentials

SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
client = gspread.authorize(creds)

print("=== Testing Google Sheets Access ===")

try:
    # List all accessible spreadsheets (to check if "Quiz responses" is visible)
    spreadsheets = client.list_spreadsheet_files()
    print("Available Spreadsheets:")
    for sp in spreadsheets:
        print(f"- {sp['name']} (ID: {sp['id']})")

    # Try to open "Quiz responses" specifically
    print("\n--- Trying to open 'Quiz responses' ---")
    spreadsheet = client.open("Quiz responses")
    print(f"Spreadsheet found: {spreadsheet.url}")

    # List all worksheets in it
    worksheets = spreadsheet.worksheets()
    print("Available Worksheets:")
    for ws in worksheets:
        print(f"- {ws.title}")

    # Try to access "Quiz Responses" specifically
    try:
        sheet = spreadsheet.worksheet("Quiz Responses")
        print("Success: 'Quiz Responses' sheet accessed! Row count:", len(sheet.get_all_values()))
    except gspread.WorksheetNotFound:
        print("Error: Worksheet 'Quiz Responses' not found. Check sheet name spelling/case.")
    except Exception as ws_e:
        print("Error accessing worksheet:", ws_e)

except gspread.SpreadsheetNotFound:
    print("Error: Spreadsheet 'Quiz responses' not found. Check name spelling/case.")
except gspread.exceptions.APIError as api_e:
    print("API Error:", api_e)
except Exception as e:
    print("General Error:", e)