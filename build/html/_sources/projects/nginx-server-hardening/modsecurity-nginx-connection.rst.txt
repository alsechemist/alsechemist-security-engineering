Connecting ModSecurity with NGINX
=================================

This section explains how **ModSecurity v3 (libmodsecurity)** is connected to **NGINX** using the **ModSecurity–NGINX** connector. While ModSecurity provides the
core Web Application Firewall (WAF) engine, it does not operate independently. The connector enables NGINX to pass HTTP transaction data to ModSecurity for
inspection and enforcement.

Understanding the Integration Architecture
-------------------------------------------

ModSecurity v3 follows a **decoupled architecture**, where:

- **libmodsecurity** acts as the detection and rule-processing engine
- **NGINX** acts as the web server and request handler
- **ModSecurity-nginx** serves as the communication bridge between them

In this architecture, NGINX forwards each HTTP transaction to libmodsecurity, which evaluates the request against configured security rules and returns an
``allow`` or ``deny`` decision.

This design improves modularity, performance, and maintainability compared to earlier embedded implementations.

Connector Role and Function
---------------------------

The ModSecurity NGINX connector performs the following key functions:

- Hooks into NGINX request processing phases
- Passes HTTP request and response data to libmodsecurity
- Applies rule evaluation results in real time
- Enforces blocking or logging actions based on rule outcomes

Without this connector, ModSecurity cannot operate within NGINX.

Loading the Module in NGINX
---------------------------

Edit the main NGINX configuration file:

.. code-block:: bash

   vim /etc/nginx/nginx.conf

Add the following line **at the very top** of the configuration file:

.. code-block:: nginx

   load_module modules/ngx_http_modsecurity_module.so;

Follow the image below to have high level view,

.. image:: ../../assets/images/projects/nginx-server-hardening/settingup-modsecurity-connector-nginx-2.png
   :alt: Loading ngx_http_modsecurity_module.so Module on Nginx
   :align: center

.. raw:: html

   <div style="height:25px;"></div>

This directive must appear **before** the `events` and `http` blocks. Actually, it is always suggested to load the modules first at the beginning.

Attaching the ModSecurity Engine with NGINX
-------------------------------------------

Now for the final step, it's time to attach the ModSecurity Engine in the NGINX Server. 
Remember that we have placed the ``modsecurity.conf`` file at ``/usr/local/modsecurity`` while going through the :ref:`required-files-placement-reorganization` section.
This is the main configuration file of ModSecurity. We are going to load it in the http server configuration file of NGINX, basically including the Modsecurity engine in
the http server.

Turning On the ModSecurity Engine
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Edit the main ModSecurity Configuration file at ``/usr/local/modsecurity/modsecurity.conf``

.. code-block:: bash

   vim /usr/local/modsecurity/modsecurity.conf

Replace ``SecRuleEngine DetectionOnly`` with

.. code-block:: nginx

   SecRuleEngine On

Refer to the image below for high level view,

.. image:: ../../assets/images/projects/nginx-server-hardening/settingup-modsecurity-nginx-connection-1.png
   :alt: Attaching ModSecurity Engine in NGINX Server Configuration File
   :align: center

.. raw:: html

   <div style="height:25px;"></div>

Basically ModSecurity is now turned On. Its engine is active.

Turning On ModSecurity in Nginx
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Edit the main NGINX server configuration file at ``/conf.d/default.conf``

.. code-block:: bash

   vim /etc/nginx/conf.d/default.conf

Add this line inside the ``server`` block

.. code-block:: nginx

   modsecurity on;

And add this line in the ``location`` block

.. code-block:: nginx

   modsecurity_rules_file /usr/local/modsecurity/modsecurity.conf;

Refer to the image below for high level view,

.. image:: ../../assets/images/projects/nginx-server-hardening/settingup-modsecurity-nginx-connection-2.png
   :alt: Attaching ModSecurity Engine in NGINX Server Configuration File
   :align: center

.. raw:: html

   <div style="height:25px;"></div>

.. note::

   The above two lines can also be added in the ``server`` block. 
   This will basically load the same configuration file across all the locations following centralized manner.

Verification
------------

Test the NGINX configuration to confirm the module is loaded correctly:

.. code-block:: bash

   nginx -t

It should say the syntaxes are ``ok`` and the test is **successfully**!

At this stage, the ModSecurity connector is successfully integrated with NGINX, and the web server is ready to load ModSecurity rules and configurations.
