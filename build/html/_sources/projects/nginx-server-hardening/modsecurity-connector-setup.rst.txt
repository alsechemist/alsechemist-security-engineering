Setting Up the ModSecurity NGINX Connector
==========================================

After successfully building and installing **ModSecurity v3 (libModSecurity)**, the next step is to integrate it with **NGINX** using the official
**ModSecurity-nginx connector**. This connector acts as a bridge between NGINX and the ModSecurity engine, enabling NGINX to pass HTTP transaction data to
libModSecurity for inspection.

Download the Official Release - `(ModSecurity-nginx) <https://github.com/owasp-modsecurity/ModSecurity-nginx>`_
---------------------------------------------------------------------------------------------------------------

Begin by downloading the latest official release of ModSecurity NGINX connector from their `Release <https://github.com/owasp-modsecurity/ModSecurity-nginx/releases>`_ Page

.. code-block:: bash

   wget https://github.com/owasp-modsecurity/ModSecurity-nginx/releases/download/<latest-release-version>/<nginx-connector-with-latest-release-version>.tar.gz

Replace the ``<latest-release-version>`` & ``<nginx-connector-with-latest-release-version>`` with their actual release version.

This repository contains the required source code that allows NGINX to interface with libModSecurity during compilation.

Preparing NGINX Source Code
----------------------------

The ModSecurity connector will be compiled as a **dynamic module** against the same version of NGINX that will be used in production. 
You can also do it without the dynamic module, just the difference is that, it will be installed as inbuilt feature of NGINX rather than a module itself.

Download and extract the NGINX source code matching your installed version.

.. code-block:: bash

   wget https://nginx.org/download/<nginx-with-latest-release-version>.tar.gz
   tar -xzvf <nginx-with-latest-release-version>
   cd <nginx-with-latest-release-version>

.. attention::

   The version name must be the same as the one we deployed during our production ready NGINX setup phase that we saw in the :ref:`setup-nginx-production` section.
   Otherwise, there are high chances of version compatibility/collision issues.

Configuring NGINX with the ModSecurity Connector
------------------------------------------------

Configure NGINX to build the ModSecurity connector as a dynamic module.

.. code-block:: bash

   ./configure --add-dynamic-module=/path/to/ModSecurity-nginx --with-compat

If everything goes well, you will see an output similar to this image below,

.. image:: ../../assets/images/projects/nginx-server-hardening/settingup-modsecurity-connector-nginx-1.png
   :alt: Configure Message - Successful
   :align: center

.. raw:: html

   <div style="height:25px;"></div>

.. note::

   The `--with-compat` flag ensures binary compatibility with existing NGINX installations, allowing the module to be loaded dynamically without rebuilding
   the entire NGINX binary.

Building the Module
-------------------

Build the dynamic module using.

.. code-block:: bash

   make modules

After building, it successfully, the ModSecurity module for nginx will be available as 
``objs/ngx_http_modsecurity_module.so`` under ``<nginx-with-latest-release-version>`` directory.

Installing the Module via Reorganization
----------------------------------------

Copy the compiled module to the NGINX modules directory.

.. code-block:: bash

   cp objs/ngx_http_modsecurity_module.so /usr/lib/nginx/modules

Directory ``/usr/lib/nginx/modules`` is symbolic link for ``/etc/nginx/modules/``. 
Which mean, any module you put there will also be dynamically available in ``/etc/nginx/modules/`` directory.
