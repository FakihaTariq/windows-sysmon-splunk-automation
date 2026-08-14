# Phase 1: Environment Provisioning & Sysmon Auditing

## Overview
Phase 1 establishes an isolated Windows 11 VirtualBox lab environment, overrides Windows 11 Home GUI limitations to enforce local audit logging, and deploys Microsoft Sysmon to capture process execution telemetry.


---



## Tools & Technologies
* **Virtualization Engine:** VirtualBox 7.2.14
* **Target Operating System:** Windows 11 64-bit (Evaluation Build, 7.9 GB ISO)
* **Resource Allocation:** 4096 MB RAM, 2 vCPUs, 80 GB Virtual Disk (VDI)
* **Auditing Utility:** `auditpol.exe` via Administrative PowerShell
* **Endpoint Telemetry Engine:** Microsoft Sysinternals Sysmon v15.x
* **Configuration Ruleset:** SwiftOnSecurity `sysmonconfig-export.xml`


## Technical Implementation

### 1. Virtual Machine Provisioning
Provisioned a Windows 11 guest VM inside VirtualBox 7.2.14, allocating 4096MB RAM, 2 vCPUs, and an 80GB dynamically allocated virtual hard disk to maintain endpoint stability during log generation.

### 2. Audit Policy Enforcement (`auditpol`)
Verified local auditing for Logon events to ensure both Success and Failure attempts are recorded without security blind spots.

```powershell
# Verify active audit category settings
auditpol /get /category:*
```

### 3. Sysmon Installation & Service Initialization
Selected SwiftOnSecurity's sysmonconfig-export.xml for its clear rules and comments. Extracted Sysmon files to C:\Sysmon\ and installed the service:

```powershell
cd C:\Sysmon
Sysmon64.exe -i sysmonconfig-export.xml -accepteula
```

* -i: Installs Sysmon as an automatic background service.
* sysmonconfig-export.xml: Applies process creation and network monitoring rules.
* -accepteula: Accepts the Sysinternals EULA automatically.


## Engineering & Troubleshooting
### Issue 1: Missing Local Security Policy Snap-in (secpol.msc)
Attempting to open secpol.msc to configure Audit Logon Events failed with a system file error.
#### Root Cause Analysis: 
secpol.msc is omitted from Windows 11 Home evaluation builds. This was an OS feature omission rather than a permission restriction.
#### Resolution:
Used command-line auditing tools (auditpol.exe), which remain functional across all Windows editions.

### Issue 2: Privilege Deficit on Command Execution
Running auditpol /get /category:* returned Error: "A required privilege is not held by the client".
#### Root Cause Analysis: 
Audit policy modifications require explicit administrative token elevation.

#### Resolution: 
Relaunched PowerShell using Run as Administrator and re-executed the command successfully.

## Phase Results & Verification
auditpol confirmed that Logon Success and Failure auditing are active across the system
![](../screenshots/01_auditpol_verification.png

## Next Steps
Proceed to Phase 2: Local Event Log Analysis & Attack Simulations to generate authentication failures and analyze local Windows Security logs.
