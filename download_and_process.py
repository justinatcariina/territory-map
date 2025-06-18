import os
import re
import io
import base64
import zipfile
import requests

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

DATA_DIR = "data"
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
HUBSPOT_ACCESS_TOKEN = os.environ['HUBSPOT_ACCESS_TOKEN']

REPORT_SUBJECTS = [
    "Calls by State",
    "Discos Scheduled by State",
    "Closed Won by State",
    "Connects by State",
    "Deals by Name"
]

REPORT_FILENAME_MAP = {
    "Calls by State": "calls.csv",
    "Discos Scheduled by State": "discos.csv",
    "Closed Won by State": "customers.csv",
    "Connects by State": "connects.csv",
    "Deals by Name": "deals.csv"
}

def authenticate_gmail():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token_file:
            token_file.write(creds.to_json())
    return creds

def extract_notification_links(body):
    # extract notification-station CTA links
    pattern = r"https:\/\/app\.hubspot\.com\/api\/notification-station\/general\/v1\/notifications\/cta\/[a-f0-9\-]+\?[^\"<]+"
    return re.findall(pattern, body)

def resolve_notification_url(notification_url):
    headers = {
        'Authorization': f"Bearer {HUBSPOT_ACCESS_TOKEN}",
        'Accept': 'application/json'
    }
    resp = requests.get(notification_url, headers=headers, allow_redirects=False)
    if resp.status_code in (302, 303):
        redirected_url = resp.headers.get('Location')
        match = re.search(r'/files/(\d+)/signed-url-redirect', redirected_url)
        if match:
            return match.group(1)
    return None

def get_file_ids_by_subject(service, subjects):
    subject_to_file_ids = {}

    for subject in subjects:
        query = f'subject:"{subject}"'
        results = service.users().messages().list(userId='me', q=query, maxResults=1).execute()
        messages = results.get('messages', [])
        file_ids = set()

        for msg in messages:
            msg_id = msg['id']
            message = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
            payload = message.get('payload', {})
            body = ""

            if 'parts' in payload:
                for part in payload['parts']:
                    if part['mimeType'] in ['text/html', 'text/plain']:
                        data = part['body'].get('data')
                        if data:
                            decoded = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                            body += decoded
            else:
                data = payload.get('body', {}).get('data')
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')

            links = extract_notification_links(body)
            for link in links:
                file_id = resolve_notification_url(link)
                if file_id:
                    file_ids.add(file_id)

        subject_to_file_ids[subject] = list(file_ids)

    return subject_to_file_ids

def get_hubspot_signed_url(file_id):
    url = f"https://api.hubapi.com/files/v3/files/{file_id}/signed-url"
    headers = {
        'Authorization': f"Bearer {HUBSPOT_ACCESS_TOKEN}",
        'Accept': 'application/json'
    }
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        return resp.json().get('url')
    else:
        print(f"Error getting signed URL for file ID {file_id}: {resp.status_code} {resp.text}")
        return None

def download_and_extract_zip(signed_url, extract_to, expected_csv_name):
    resp = requests.get(signed_url)
    if resp.status_code != 200:
        print(f"Error downloading file: {resp.status_code}")
        return False

    with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
        if "hubspot-export-summary.csv" not in z.namelist():
            print("hubspot-export-summary.csv not found in ZIP.")
            return False

        # Extract only the target file
        z.extract("hubspot-export-summary.csv", extract_to)

        # Rename it to the desired output name
        extracted_path = os.path.join(extract_to, "hubspot-export-summary.csv")
        final_path = os.path.join(extract_to, expected_csv_name)

        if extracted_path != final_path:
            os.replace(extracted_path, final_path)

        print(f"Extracted {expected_csv_name}")
        return True

def download_and_save_csv(signed_url, output_path):
    resp = requests.get(signed_url)
    if resp.status_code != 200:
        print(f"Error downloading CSV: {resp.status_code}")
        return False

    with open(output_path, "wb") as f:
        f.write(resp.content)

    print(f"Saved CSV to {output_path}")
    return True


def main():
    if not HUBSPOT_ACCESS_TOKEN:
        print("Set HUBSPOT_ACCESS_TOKEN before running!")
        return

    os.makedirs(DATA_DIR, exist_ok=True)
    creds = authenticate_gmail()
    service = build('gmail', 'v1', credentials=creds)

    file_ids_map = get_file_ids_by_subject(service, REPORT_SUBJECTS)

    for subject, file_ids in file_ids_map.items():
        print(f"Found file IDs for {subject}: {file_ids}")
        for file_id in file_ids:
            signed_url = get_hubspot_signed_url(file_id)
            if not signed_url:
                continue
            expected_csv_name = REPORT_FILENAME_MAP[subject]
            if subject == "Deals by Name":
                download_and_save_csv(signed_url, os.path.join(DATA_DIR, expected_csv_name))
            else:
                download_and_extract_zip(signed_url, DATA_DIR, expected_csv_name)

    print("Running build_sales_metrics.py...")
    os.system("python build_sales_metrics.py")

if __name__ == "__main__":
    main()
