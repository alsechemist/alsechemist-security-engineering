Introduction - Apache2 Server Hardening
=======================================

Apache2 server hardening is crucial for securing web applications against common threats. 
On Ubuntu 24.04 LTS, leveraging modules like Mod Evasive, Mod GeoIP, and ModSecurity (WAF) enhances protection. 
Mod Evasive helps mitigate DDoS attacks by detecting and blocking repeated requests. 
Mod GeoIP2 allows filtering of traffic based on geographical location, which can prevent access from suspicious regions. 
ModSecurity (WAF) acts as a Web Application Firewall, filtering and monitoring HTTP traffic to protect against vulnerabilities like
SQL injection and XSS, strengthening overall security for Apache2 servers.

.. toctree::
   :maxdepth: 3
   :hidden:

   ../../projects/apache2-server-hardening/scope-of-engagement
   ../../projects/apache2-server-hardening/generic-setup-and-prerquisites
   ../../projects/apache2-server-hardening/modevasive-setup
   ../../projects/apache2-server-hardening/modmaxminddb-setup