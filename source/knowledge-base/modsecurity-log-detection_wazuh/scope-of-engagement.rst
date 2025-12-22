Scope of Engagement
===================

The scope of this implementation is intentionally defined to ensure clarity, reproducibility, and alignment with real-world Security Operations Center (SOC) workflows.

Technology Stack
----------------

The following technologies and versions are used throughout this implementation:

- **Ubuntu Server**

    - Version: 24.04 LTS

- **ModSecurity v3 (libmodsecurity):** The latest stable **libmodsecurity** engine is used as the Web Application Firewall (WAF) core. This engine operates independently of the web server and is integrated using official connectors.

    - Version: 3.x.x

- **Web Server Connectors:** ModSecurity v3 is deployed using supported connectors for:

    - Apache HTTP Server (latest)
    - NGINX (latest)

- **OWASP Core Rule Set (CRS)**

    - Version: **4.x.x**

- **Wazuh SIEM**

    - Version: **4.x**

Operational Assumptions
-----------------------

This documentation assumes that:

- ModSecurity v3 is already installed and correctly integrated with the web server
- OWASP CRS v4.21.0 is enabled and operational
- The Wazuh manager and agent are properly deployed

