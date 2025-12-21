Scope of Engagement
===================

The scope of this implementation is intentionally defined to ensure clarity, reproducibility, and alignment with real-world Security Operations Center (SOC) workflows.

Technology Stack
----------------

The following technologies and versions are used throughout this implementation:

- **ModSecurity v3 (libmodsecurity):** The latest stable **libmodsecurity** engine is used as the Web Application Firewall (WAF) core. This engine operates independently of the web server and is integrated using official connectors.

- **Web Server Connectors:** ModSecurity v3 is deployed using supported connectors for:

    - Apache HTTP Server
    - NGINX

- **OWASP Core Rule Set (CRS)**

    - Version: **4.21.0**
    - Provides standardized detection rules for common web application attacks including SQL injection, XSS, command injection, and protocol violations.

- **Wazuh SIEM**

    - Version: **4.14**
    - Custom decoders are developed to parse JSON-formatted ModSecurity audit logs.
    - Custom rules are applied to generate alerts based on decoded fields.

Operational Assumptions
-----------------------

This documentation assumes that:

- ModSecurity v3 is already installed and correctly integrated with the web server
- OWASP CRS v4.21.0 is enabled and operational
- The Wazuh manager and agent are properly deployed

