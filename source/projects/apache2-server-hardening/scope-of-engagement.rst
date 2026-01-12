Scope of Engagement
===================

This document defines the scope of work for implementing and hardening an Apache HTTP Server environment using multiple security-focused modules. 
The objective is to enhance the overall security posture of the web server by mitigating common web-based threats, controlling access, and strengthening request inspection mechanisms.

Environment Overview
--------------------

The implementation is carried out in the following environment:

- **Operating System:** Ubuntu Server
    - Version: 24.04 LTS

- **Web Server:** Apache HTTP Server (Apache2)
    - Version: 2.4.x

- **Security Modules Implemented:**

    - **Mod Evasive** – Protection against DoS/DDoS attacks
        - Version: 1.10

    - **Mod MaxMind DB** – GeoIP-based access control using MaxMind databases
        - Version: 1.x.x

    - **ModSecurity** – Web Application Firewall (WAF) for deep request inspection
        - Version: 3.x.x

Scope Objectives
----------------

The primary objectives of this implementation are:

- To harden the Apache web server against common network and application-layer attacks.
- To reduce the attack surface by applying proactive and reactive security controls.
- To implement request filtering, rate limiting, and geographic access control.
- To enhance visibility and logging for security monitoring and incident response.

This documentation focuses on **real-world deployment scenarios**, emphasizing manual compilation, secure configuration, and 
operational validation suitable for production environments.