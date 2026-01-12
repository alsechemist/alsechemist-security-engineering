Setting Up Mod Evasive
======================

ModEvasive is an Apache module designed to provide evasive action against HTTP DoS (Denial of Service), 
DDoS (Distributed Denial of Service), and brute-force attacks. It works by tracking the number of requests per client and
temporarily blocking IPs that exceed configured thresholds, helping protect web servers from overload and malicious traffic.

Installing the apache2 evasive module
-------------------------------------

Run the below command to install ``libapache2-mod-evasive``

.. code-block:: bash

    sudo apt install libapache2-mod-evasive

Depending on whether we want to receive automated alerts at our email address, we would like to choose between these options.
If we want to receive email regarding the alerts, it will create a postfix server and run its services.
This is not recommended in a production environment, as this will create unnecessary services, if the instance is not dedicated for handling email services.
For now, we will go with ``No Connection``

.. image:: ../../assets/images/projects/apache2-server-hardening/apache2-server-hardening-img-3.png
    :alt: Email Server Setup Options
    :align: center

.. raw:: html

   <div style="height:25px;"></div>

Configuring the Evasive Module
------------------------------

Head over to the ``/etc/apache2/mods-available/`` directory and open ``evasive.conf`` file using your preferred text editor. I will be using vim.

.. image:: ../../assets/images/projects/apache2-server-hardening/apache2-server-hardening-img-4.png
    :alt: Mod Evasive Configuration File
    :align: center

.. raw:: html

   <div style="height:25px;"></div>

Parameter Description:
~~~~~~~~~~~~~~~~~~~~~~

- **DOSHashTableSize:** Increase or decrease the hash-table size according to your requirements. It is recommended to use higher values if your server is usually busy or receives a high amount of traffic.

- **DOSPageCount:** The number of requests it will consider for a single page within a given timeframe.

- **DOSSiteCount:** The number of requests it will consider throughout the whole site or application.

- **DOSPageInterval:** The time interval (in seconds) used to check the number of requests for the same page, corresponding to DOSPageCount.

- **DOSSiteInterval:** The time interval (in seconds) used to check the number of requests across the whole site, corresponding to DOSSiteCount.

- **DOSBlockingPeriod:** The time period (in seconds) for which the attacker will remain blocked after exceeding the limits.

- **DOSEmailNotify:** The email address where notifications will be sent when an attack is detected. (Not Required Since we didn’t set up the postfix server during the installation).

- **DOSSystemCommand:** The system command to be executed when an attack is detected. (Not Required because it, the module automatically does its job, and block all incoming requests from the attacker.)

- **DOSLogDir:** The directory path where the mod_evasive logs will be stored.

.. Note:: 
    
    It's always recommended to keep the value of the time interval to be shorter and precise than the ``DOSPageCount`` and ``DOSSiteCount``.
    It might vary depending on scenarios, but choose what’s best for you and to avoid false positives.

Creating The Directory for Storing Logs as specified
----------------------------------------------------

It is required to manually create the log directory as specified.

.. code:: bash

    sudo mkdir /var/log/mod_evasive

Next, it is also required to change the owner of the log directory as the evasive module uses ``www-data`` as the specified user to write in the log directory. 
Otherwise, the logs will also not be generated. If such a problem arises, you can check in the ``/var/log/syslog`` file for the details.

.. code:: bash

    sudo chown -R www-data:www-data /var/log/mod_evasive

Enabling the Evasive Module
---------------------------

Now let’s enable the evasive module, just in case if it's disabled.

.. code:: bash

    sudo a2enmod evasive

Then restart the apache2 server to make the configurations work accordingly and effectively.

.. code:: bash

    sudo systemctl restart apache2

Testing the Module
------------------

You will usually see a default apache2 page after sending an http request to your server/instance, with your server’s IP.

.. image:: ../../assets/images/projects/apache2-server-hardening/apache2-server-hardening-img-5.png
    :alt: Testing Mod Evasive Module
    :align: center

.. raw:: html

   <div style="height:25px;"></div>

.. tip::

    I would like to test it manually, as an attacker is more likely to use their custom script or any attacking tools. 
    Remember, we have set a time frame of 10 seconds to consider up to 20 requests in the same page from the source at a time. 
    After 20 requests within the 10 seconds time frame, it should forbid us from accessing the webpage. 
    Besides, the number of requests might vary due to the value of the ``hashtable`` sometimes.

.. image:: ../../assets/images/projects/apache2-server-hardening/apache2-server-hardening-img-6.png
    :alt: Testing Mod Evasive Module - Successful
    :align: center

.. raw:: html

   <div style="height:25px;"></div>

You should receive a status code of ``403``, which is Forbidden, if the module is working fine and accordingly.

Checking and Investigating Logs
-------------------------------

If an attack gets detected, a log should be generated in the specified directory. For us the directory is ``/var/log/mod_evasive``.
Head over there, and you will find the IP of the attacker, which means the module is blocking requests coming from this particular IP.

.. image:: ../../assets/images/projects/apache2-server-hardening/apache2-server-hardening-img-7.png
    :alt: Checking Mod Evasive Logs
    :align: center

.. raw:: html

   <div style="height:25px;"></div>

Inside the file you find a process ``id`` or a unique number. 

Besides, you can also head over to check the syslog to investigate the event.

.. image:: ../../assets/images/projects/apache2-server-hardening/apache2-server-hardening-img-8.png
    :alt: Checking Mod Evasive Syslog
    :align: center

.. raw:: html

   <div style="height:25px;"></div>

.. note::
    
    If an attacker IP shows up in the ``mod_evasive`` directory it will also be logged in the syslog file.

There we go, this concludes our apach2 server hardening using ``mod_evasive`` module to prevent the server from ``DDoS`` attack.