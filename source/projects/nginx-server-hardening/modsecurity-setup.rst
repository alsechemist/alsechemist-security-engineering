Setting Up ModSecurity
======================

This section provides a detailed guide for **building and installing ModSecurity v3 (libModSecurity)** from the official GitHub repository on **Ubuntu Server 24.04 LTS**.

Cloning the Repository - `(Reference) <https://github.com/owasp-modsecurity/ModSecurity>`_
------------------------------------------------------------------------------------------

The project uses autotools to help the compilation process. Please note that if you are working with git, don't forget to initialize and update the submodules. 

Here's a quick how-to:

.. code-block:: bash

    git clone --recursive https://github.com/owasp-modsecurity/ModSecurity ModSecurity
    cd ModSecurity

Installing the ModSecurity Library - (Engine)
----------------------------------------------

The next step is to install the ModSecurity Engine

.. code-block:: bash

    ./build.sh
    ./configure
    make
    make install

The installation process might take a while depending on your system specification. If everything goes well, you will receive a message like this:

.. image:: ../../assets/images/projects/nginx-server-hardening/settingup-modsecurity-1.png
   :alt: Build Message - Successful
   :align: center

.. raw:: html

       <div style="height:25px;"></div>

As we can see from the above image that, Modsecurity have been installed at ``/usr/local/modsecurity`` and its libraries at ``/usr/local/modsecurity/lib``

.. _required-files-placement-reorganization:

Required Files Placement - Reorganization
-----------------------------------------

This is very important step where we will be reorganizing two required configuration files from the ``ModSecurity`` Github repository. Which are currently named:

- **modsecurity.conf-recommended**
- **unicode.mapping**

Both of these two files need to be in the same directory.

.. code-block:: bash

    cp /path/to/ModSecurity/modsecurity.conf-recommended /usr/local/modsecurity/modsecurity.conf
    cp /path/to/ModSecurity/unicode.mapping /usr/local/modsecurity/unicode.mapping

For only reorganization purposes, we will be transferring the file to ``/usr/local/modsecurity``
directory while renaming ``modsecurity.conf-recommended`` to ``modsecurity.conf`` so that the nginx services can identify the required file.
