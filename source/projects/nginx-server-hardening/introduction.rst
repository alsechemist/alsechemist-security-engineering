Introduction - Nginx Server Hardening
=====================================

ModSecurity is a widely adopted **open-source Web Application Firewall (WAF)** that provides robust protection against common web-based attacks such as SQL
Injection, Cross-Site Scripting (XSS), Remote Code Execution (RCE), and protocol violations. Originally designed as an Apache module, ModSecurity has evolved into
a **standalone security engine (libModSecurity)** starting from version 3, allowing it to be integrated with multiple web servers through dedicated connectors.

This documentation focuses on **ModSecurity v3 (libModSecurity)** integrated with **NGINX using the ModSecurity-nginx connector**. Unlike ModSecurity v2,
which tightly coupled the engine with Apache, ModSecurity v3 separates the **rule processing engine** from the **web server**, 
offering improved flexibility, performance, and extensibility.

NGINX, known for its high performance and event-driven architecture, does not natively support ModSecurity. To bridge this gap, the **ModSecurity-nginx
connector** acts as an interface between NGINX and libModSecurity, enabling full WAF capabilities without compromising NGINX’s design principles.

This guide provides a **complete and structured walkthrough** for setting up ModSecurity v3 with NGINX, including:

- Building and installing libModSecurity
- Integrating the NGINX connector
- Configuring ModSecurity directives
- Deploying and testing rule sets
- Validating security events and logs

.. toctree::
   :maxdepth: 3
   :hidden:

   ../../projects/nginx-server-hardening/scope-of-work
   ../../projects/nginx-server-hardening/prerequisites
   ../../projects/nginx-server-hardening/modsecurity-setup
   ../../projects/nginx-server-hardening/modsecurity-connector-setup
   ../../projects/nginx-server-hardening/modsecurity-crs-setup
   ../../projects/nginx-server-hardening/modsecurity-post-installation-setup