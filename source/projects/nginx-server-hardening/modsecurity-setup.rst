Setting Up ModSecurity from the Source
======================================

This section provides a detailed guide for **building and installing ModSecurity v3 (libmodsecurity)** from the official GitHub repository on **Ubuntu Server 24.04 LTS**.

Cloning the Repository - `(Reference) <https://github.com/owasp-modsecurity/ModSecurity>`_
------------------------------------------------------------------------------------------

The project uses autotools to help the compilation process. Please note that if you are working with git, don't forget to initialize and update the submodules. 

Here's a quick how-to:

.. code-block:: bash

    git clone --recursive https://github.com/owasp-modsecurity/ModSecurity ModSecurity
    cd ModSecurity

Next, the building process:

.. code-block:: bash

    ./build.sh
    ./configure
    make
    sudo make install

The building process might take a while depending on your system specification. If everything goes well, you will receive a message like this:

.. image:: ../../assets/images/nginx-server-hardening/settingup-modsecurity-1.png
   :alt: Build Message - Successful
   :align: center

.. raw:: html

       <div style="height:25px;"></div>

As we can see from the above image that, Modsecurity have been installed at ``/usr/local/modsecurity`` and its libraries at ``/usr/local/modsecurity/lib``