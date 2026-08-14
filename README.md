# Windows Endpoint Telemetry, Sysmon Auditing & Splunk API Automation

A hands-on security engineering and automation project focused on Windows endpoint detection and response (EDR), local security auditing, Sysmon process tracking, SIEM log forwarding, and programmatic SOC report generation using Python and Splunk's REST API.


## Table of Contents

- [Executive Summary](#executive-summary)
- [System Architecture & Data Flow](#system-architecture--data-flow)
- [Tech Stack & Security Tools](#tech-stack--security-tools)
- [Phase-by-Phase Summary](#phase-by-phase-summary)
  - [Phase 1: Environment Provisioning & Sysmon Auditing](./docs/01-vm-setup-endpoint-auditing.md)
  - [Phase 2: Local Event Log Analysis & Attack Simulations](./docs/02-logon-events-account-management.md)
  - [Phase 3: Multi-Layer Network & Forwarder Pipeline](./docs/03-splunk-pipeline-ingestion.md)
  - [Phase 4: Python REST API Polling & HTML Report Automation](./docs/04-api-python-automation.md)
- [Repository Artifacts & Scripts](#repository-artifacts--scripts)
- [Quick Start & Script Execution](#quick-start--script-execution)
- [Author & Contact](#author--contact)

---

## Executive Summary

This project establishes a Windows endpoint security monitoring environment designed to evaluate native auditing controls, deploy advanced process telemetry, stream enterprise event logs into Splunk Enterprise, and automate daily security reporting. 

The project began by deploying a Windows 11 64-bit VirtualBox virtual machine. To overcome Windows Home evaluation build restrictions where the Local Security Policy GUI (`secpol.msc`) was missing, command-line auditing was configured using elevated `auditpol` commands to guarantee coverage across all Logon Success and Failure events. System Monitor (Sysmon) was subsequently installed alongside SwiftOnSecurity's `sysmonconfig-export.xml` configuration to capture process creations (Event ID 1) and network activity without excessive production noise.

Controlled security exercises were conducted locally, including simulated password brute-forcing (Event ID 4625), interactive vs. service session differentiation (Event ID 4624 Logon Types 2 and 5), user account creation (Event ID 4720), and explicit credential usage (Event ID 4648). To centralize telemetry, a Splunk Universal Forwarder was configured inside the guest VM to route events to a host-hosted Splunk Enterprise instance. Overcoming four distinct networking, firewall, and OS-level permission barriers (including ICMP blockades, port 9997 inbound rules, `inputs.conf` syntax fixes, and Service Account `errorCode=5` access denials), raw Security and Sysmon logs were successfully ingested and queried using Splunk Processing Language (SPL).

Finally, the project addressed SOC workflow efficiency by replacing manual SIEM searches with a custom Python script. Utilizing Splunk's REST API on management port `8089`, the script authenticates via an environment variable stored Bearer Token, submits asynchronous search jobs, extracts Search IDs (`sid`), polls job execution status via JSON parsing loops, and compiles structured security metrics into a timestamped HTML daily SOC summary report.

---

## System Architecture & Data Flow
```text
  [ Attack Simulation / Endpoint Activity ]
      │
      ├─► Failed/Successful Interactive Logons (EventCode 4624/4625)
      ├─► PowerShell & CLI Execution Trees (Sysmon Event ID 1)
      └─► Synthetic Attacks (Encoded PowerShell, Local Admin Creation)
              │
              ▼
  ┌─────────────────────────────────────────────────────────────┐
  │                 TARGET: WINDOWS 11 ENDPOINT                 │
  │                                                             │
  │  [ Endpoint Security Controls ]                             │
  │   ├─ Command-Line Audit Policy (auditpol /set)              │
  │   └─ System Monitor (Sysmon Service + SwiftOnSecurity Rules) │
  │                                                             │
  │  [ Telemetry Generation ]                                   │
  │   ├─ WinEventLog:Security ──────────────────┐               │
  │   └─ WinEventLog:Sysmon/Operational ────────┴─► Event Log   │
  │                                                     │       │
  │  [ Log Transport ]                                  │       │
  │   └─ Splunk Universal Forwarder (WinAeService) ◄────┘       │
  └──────────────────────────┬──────────────────────────────────┘
                             │
                             │ Encrypted Transport (TCP / Port 9997)
                             ▼
  ┌─────────────────────────────────────────────────────────────┐
  │                    SIEM: SPLUNK ENTERPRISE                  │
  │                                                             │
  │  [ Data Pipeline ]                                          │
  │   ├─ Receiver Port: 9997                                    │
  │   ├─ Index: main                                            │
  │   └─ XML-Rendered Event Logs                                │
  │                                                             │
  │  [ SOC Analytics & Operations ]                             │
  │   ├─ Custom SPL Threat Detection Queries                    │
  │   ├─ Suspicious Execution & Logon Alerts                    │
  │   └─ Endpoint Threat Monitoring SOC Dashboard               │
  └─────────────────────────────────────────────────────────────┘
```
## Tech Stack & Security Tools

**Virtualization & OS:** VirtualBox 7.2.14, Windows 11 64-bit (Evaluation Edition, 4096MB RAM, 2 CPUs, 80GB VDI)

**Auditing & Telemetry:** `auditpol.exe`, Microsoft Sysinternals Sysmon v15.x, SwiftOnSecurity Config (`sysmonconfig-export.xml`)

**SIEM & Ingestion:** Splunk Enterprise 10.4.2 (Host), Splunk Universal Forwarder (Guest VM), `inputs.conf`

**Programming & Automation:** Python 3.x, PowerShell, Windows Command Prompt, Splunk REST API (`port 8089`)

**Python Libraries:** `requests`, `xml.etree.ElementTree`, `os`, `time`, `datetime`, `urllib3`


## Phase-by-Phase Summary

### Phase 1: Environment Provisioning & Sysmon Auditing
Deployed a dedicated Windows 11 VirtualBox virtual machine and established low-level command-line auditing and Sysmon process tracking. Successfully provisioned a 4GB RAM / 2 CPU guest endpoint. When `secpol.msc` failed due to Windows Home GUI limitations, administrative PowerShell was used to execute `auditpol` and verify complete Logon Success and Failure tracking. Sysmon was installed with SwiftOnSecurity's rule file to track process execution lineage (Event ID 1) while filtering benign background noise.

Refer to [01 VM Setup Endpoint Auditing](./docs/01-vm-setup-endpoint-auditing.md) for more information


### Phase 2: Local Event Log Analysis & Attack Simulations
Simulated brute-force login attempts, privilege escalation, and account creation to analyze Windows Event Viewer logging logic. Generated 5 rapid failed login attempts to produce Event ID 4625 entries, analyzing Sub Status diagnostic codes (`0xC000006A` for bad password vs. `0xC0000064` for invalid username). Differentiated human interactive logons (Logon Type 2) from background system service noise (SYSTEM account Logon Type 5). Simulated local account creation (`net user testuser`) to verify Event ID 4720 and explicit credential reuse via `runas` (Event ID 4648).

Refer to [02 Logon Events Account Management](./docs/02-logon-events-account-management.md) for more information


### Phase 3: Multi-Layer Network & Forwarder Pipeline
Established host-to-guest networking, deployed Splunk Universal Forwarder, and resolved four distinct ingestion blockades. Configured Bridged Networking and enabled host Windows Defender ICMP rules to establish ping reachability. Resolved shared folder issues by installing VirtualBox Guest Additions, fixed `inputs.conf` typos (`Secuirty`) and integer formatting (`disabled = 0`), and opened host TCP port 9997. Reconfigured the `SplunkForwarder` service from a restricted account to `Local System` to fix `errorCode=5` read denials on Sysmon channels, enabling raw Splunk aggregation via SPL queries (`stats`, `timechart`, `table`).

Refer to [03 Splunk Pipeline Ingestion](./docs/03-splunk-pipeline-ingestion.md) for more information


### Phase 4: Python REST API Polling & HTML Report Automation
Stored a 90-day Splunk API token as an environment variable (`SPLUNK_TOKEN`) for credential security. Built a Python script that submits POST requests to Splunk's management port (`8089`), parses the returned XML Search ID (`sid`), executes a JSON polling loop until `isDone == True`, and compiles aggregated Splunk metrics into a clean, timestamped HTML report (`soc_report_YYYY-MM-DD_HH-MM.html`).

Refer to [04 API Python Automation](./docs/04-api-python-automation.md) for more information



## Repository Artifacts & Scripts

* **`scripts/soc_report_generator.py`**: Complete Python script for API authentication, search submission, polling, and HTML report construction.
* **`configs/inputs.conf`**: Corrected Splunk Universal Forwarder configuration for Windows Security and Sysmon log channels.

## Quick Start & Script Execution

### Prerequisites
* Windows 11 Guest VM + Host running Splunk Enterprise (port 8089 accessible)
* Python 3.x installed on host/management machine
* `requests` library installed (`pip install requests`)

### Environment Setup & Script Execution
1. **Set your Splunk API Bearer Token:**
   ```powershell
   # PowerShell
   $env:SPLUNK_TOKEN="your_splunk_bearer_token_here"
   ```
2. **Execute the Automated SOC Daily Report Generator:**
    ```powershell
    python scripts/soc_report_generator.py
    ```
  Output: A timestamped HTML summary report (soc_report_YYYY-MM-DD_HH-MM.html)    generated in the working directory.

  Refer to [Execution & Environment Setup](./scripts/execution-environment-setup) for more information

## Author & Contact
**Author:** [Fakiha Tariq](https://github.com/FakihaTariq)

**Email:** fakihatariq1@outlook.com

**LinkedIn:** https://www.linkedin.com/in/fakiha-tariq-665aa8344/
