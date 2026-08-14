## Execution & Environment Setup

### 1. Prerequisites & Dependencies
The Python automation script relies on standard Python libraries (`os`, `time`, `xml.etree.ElementTree`, `datetime`) and `requests` for handling HTTPS REST calls to Splunk's API management port (`8089`).

```bash
pip install requests
```
### 2. Credential Security
To avoid hardcoding sensitive API keys into version control, the script reads a 90-day Splunk Bearer Token directly from the system environment variable SPLUNK_TOKEN:

```powershell
# Set token in administrative PowerShell session
$env:SPLUNK_TOKEN="your_bearer_token_here"
```
### 3. Execution Command
Run the report generator from the project root directory:

```bash
python scripts/soc_report_generator.py
```
