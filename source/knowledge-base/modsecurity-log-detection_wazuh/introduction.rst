Introduction
============

Modern web applications are constantly exposed to a wide range of attacks such as SQL injection, cross-site scripting (XSS), command injection, and automated scanning.
To mitigate these threats, Web Application Firewalls (WAFs) like **ModSecurity** are widely deployed to inspect and block malicious HTTP traffic at the application layer.

While ModSecurity is highly effective at detecting and preventing web-based attacks, its security value is significantly enhanced when its logs are centrally collected,
parsed, and correlated within a Security Information and Event Management (SIEM) platform. **Wazuh**, an open-source security monitoring and threat detection platform, 
provides powerful log analysis, decoding, and alerting capabilities that make it an ideal choice for this purpose.

This documentation describes the design and implementation of **custom Wazuh decoders and rules** to detect and analyze **ModSecurity audit logs**. 
The primary goal is to transform raw ``JSON`` ModSecurity logs into structured, meaningful security events that can be monitored, alerted on, and 
investigated by Security Operations Center (SOC) teams.

By creating custom decoders, ModSecurity logs are normalized into fields such as client IP, request method, request URI, rule ID, severity, and attack category. 
Custom rules are then applied on top of these decoded fields to generate actionable alerts with appropriate severity levels inside Wazuh.

This guide is intended for:

- SOC analysts and security engineers
- Blue team and defensive security practitioners
- Wazuh administrators and integrators
- Anyone looking to improve visibility into web application attacks using ModSecurity and Wazuh

At the end of this documentation, readers will be able to:

- Understand the structure of ModSecurity audit logs
- Create custom Wazuh decoders for JSON-based ModSecurity logs
- Develop detection rules for web application attacks
- Validate and test decoders and rules using Wazuh tools
- Integrate ModSecurity alerts into a centralized security monitoring workflow

.. toctree::
   :maxdepth: 3
   :hidden:

   ../../knowledge-base/modsecurity-log-detection_wazuh/scope-of-engagement
   ../../knowledge-base/modsecurity-log-detection_wazuh/configuration-modsecutity-logs
   ../../knowledge-base/modsecurity-log-detection_wazuh/decoder-creation
   ../../knowledge-base/modsecurity-log-detection_wazuh/rule-creation
   