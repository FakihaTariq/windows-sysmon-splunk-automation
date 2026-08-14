"""
soc_report.py

Automates daily SOC reporting by querying Splunk's REST API for key
security events (failed/successful logons, Sysmon process activity,
account creation), then compiles the results into a timestamped HTML
report — turning manual log-checking into a one-command summary.

Requires:
    - A running Splunk Enterprise instance (management port 8089)
    - An environment variable SPLUNK_TOKEN containing a valid Splunk
      auth token (Settings -> Tokens in Splunk web)
    - Python 3.10+ and the `requests` library

Usage:
    python soc_report.py
"""

import os
import time
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import urllib3

# Local Splunk dev instance uses a self-signed cert; suppressing the
# resulting warning since verify=False is a deliberate, understood
# choice here. This should NOT be disabled against a production system.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SPLUNK_HOST = "https://localhost:8089"  # Splunk's management port, not 8000 (web UI)
TOKEN = os.environ.get("SPLUNK_TOKEN")

headers = {
    "Authorization": f"Bearer {TOKEN}"
}

# Add or remove report sections here — nothing else in the script needs
# to change to add a new monitored event type.
REPORT_SECTIONS = [
    {"title": "Failed Logons (Event ID 4625)",
     "query": "search index=main EventCode=4625 | stats count by Account_Name"},
    {"title": "Successful Logons (Event ID 4624)",
     "query": "search index=main EventCode=4624 | stats count by Account_Name"},
    {"title": "Recent Process Creation (Sysmon Event ID 1)",
     "query": "search index=main EventCode=1 | table _time, Image | head 10"},
    {"title": "Account Creation (Event ID 4720)",
     "query": "search index=main EventCode=4720 | table _time, Account_Name"},
]


def run_search(query: str) -> list:
    """
    Submit a Splunk search job, poll until it completes, and return
    the parsed results.

    Splunk's search API is asynchronous: submitting a query returns a
    job ID (sid), not results. Results must be fetched separately once
    the job reports isDone == True.

    Args:
        query: A full SPL query string, prefixed with "search".

    Returns:
        A list of result dictionaries (one per matching row/event).
    """
    # Step 1: submit the search job (POST creates a new job)
    response = requests.post(
        f"{SPLUNK_HOST}/services/search/jobs",
        headers=headers,
        data={"search": query},
        verify=False
    )

    # Splunk's API returns XML by default; extract the job ID (sid)
    root = ET.fromstring(response.text)
    sid = root.find("sid").text.strip()

    status_url = f"{SPLUNK_HOST}/services/search/jobs/{sid}"

    # Step 2: poll until the job is done
    while True:
        status_response = requests.get(
            f"{status_url}?output_mode=json",
            headers=headers,
            verify=False
        )
        status_data = status_response.json()
        is_done = status_data["entry"][0]["content"]["isDone"]
        print("Job done?", is_done)

        if is_done:
            break
        time.sleep(1)  # avoid hammering the API; check back in 1 second

    # Step 3: fetch the actual results now that the job has completed
    results_response = requests.get(
        f"{status_url}/results?output_mode=json",
        headers=headers,
        verify=False
    )

    results_data = results_response.json()
    return results_data["results"]


def generate_html_report(sections_data: dict) -> str:
    """
    Compile query results into a single timestamped HTML report.

    Args:
        sections_data: dict of {section_title: results_list}

    Returns:
        The filename of the generated HTML report.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"soc_report_{timestamp}.html"

    html = f"<html><head><title>SOC Daily Report - {timestamp}</title></head><body>"
    html += f"<h1>SOC Daily Report — {timestamp}</h1>"

    for title, results in sections_data.items():
        html += f"<h2>{title}</h2><table border='1' cellpadding='5'>"
        if results:
            field_names = results[0].keys()
            html += "<tr>" + "".join(f"<th>{h}</th>" for h in field_names) + "</tr>"
            for row in results:
                html += "<tr>" + "".join(f"<td>{row[h]}</td>" for h in field_names) + "</tr>"
        else:
            html += "<tr><td>No results</td></tr>"
        html += "</table>"

    html += "</body></html>"

    with open(filename, "w") as f:
        f.write(html)

    return filename


def main():
    sections_data = {}
    for section in REPORT_SECTIONS:
        print(f"Running: {section['title']}...")
        sections_data[section["title"]] = run_search(section["query"])

    report_file = generate_html_report(sections_data)
    print(f"Report generated: {report_file}")

    # --- Future alternative: alert delivery instead of / alongside the
    # HTML file. Could use smtplib for email or a Teams/Slack webhook,
    # ideally gated behind a threshold (e.g., only alert if failed-logon
    # count exceeds N) rather than firing on every scheduled run. ---


if __name__ == "__main__":
    main()