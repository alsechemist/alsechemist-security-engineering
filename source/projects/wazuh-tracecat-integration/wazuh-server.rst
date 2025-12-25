Wazuh Server
============

The Wazuh Server acts as the central component within the Wazuh architecture, responsible for managing agents, collecting security data, and
correlating alerts. It coordinates with the Wazuh Indexer and Dashboard to provide a unified security monitoring environment.
Before configuring the Wazuh Indexer API or Active Response, it’s essential to ensure that the Wazuh Server is properly set up and
synchronized with all endpoints.

Wazuh Indexer API
-----------------

At first lets start with configuring Wazuh Indexer API. You will find the configuration file at ``/etc/wazuh-indexer/opensearch.yml`` of your Wazuh Server. 
It's a very simple configuration, we only need to change one parameter. By default, the ``network.host`` parameter is set to **127.0.0.1**, 
which means the API is only accessible within the ``localhost`` itself. Tracecat won't be able to access the API if it's ``localhost`` only, 
for that it is recommended to set the parameter to,

.. code-block:: yaml

    network.host: "0.0.0.0"

and ``restart`` the **Wazuh Indexer**,

.. code-block:: bash

    sudo systemctl restart wazuh-indexer

.. Warning::

    If you want, you can set the parameter to your desired IP address, but you might face some issues while logging in, which you probably have to deal it in your own way. 
    That's why it is recommended to set the parameter to be able to be accessible from every network interface of local machine. 
    If you have more than 2 network interfaces, have it your way of configuring it through about how you would like to give access.

Wazuh Active Response
---------------------

Now let's configure Wazuh's Active Response at your Wazuh Server. To get started it's already available on `Wazuh's Offical Documentation <https://documentation.wazuh.com/current/user-manual/capabilities/active-response/ar-use-cases/blocking-ssh-brute-force.html>`_ site. 
Wazuh has already pretty much configured their active response for their Linux and Windows endpoint.
An extensive documentation and community support can be found as well. 
But here we are going to focus more on **macOS** endpoints as a bit of configuration is need in order for the active response to work properly.

Configuring Active Response for macOS Devices at Wazuh Manager
--------------------------------------------------------------

Go to your Wazuh Server, you can make changes at your manager node both via Wazuh Web GUI and 
by finding the configuration file at ``/var/ossec/etc/ossec.conf``, make sure you have ``sudo`` privileges before accessing through terminal.
But it more recommended that you access via the Web GUI as it's more easily manageable and accessible. Follow ``Server management → Settings → Edit configuration``. 
There you have to look out for something like ``<!-- Active response -->``, in that specific section you will notice various active response scripts as shown in the below image:

.. image:: ../../assets/images/projects/wazuh-tracecat-integration/wazuh-server-img-1.png
   :alt: Wazuh Server Configuration File Active Response Settings
   :align: center

.. raw:: html

   <div style="height:25px;"></div>

Since Wazuh leverages their active response scripts based on their respective OS, for example, ``firewall-drop`` for Linux endpoints, ``netsh`` for
windows endpoints. Similarly, for macOS endpoints, there is a specific script called ``pf``, which is an active response script for
channeling **Packet Filter** as default stateful kernel level firewall used in almost every macOS devices.
You can look into more details of `Wazuh Active Response Scripts <https://documentation.wazuh.com/current/user-manual/capabilities/active-response/default-active-response-scripts.html>`_
via clicking on the hyperlink. These are all available at your Linux, Windows and macOS endpoints.

.. code-block:: xml
    
    <command>
        <name>pf</name>
        <executable>pf</executable>
        <timeout_allowed>yes</timeout_allowed>
    </command>

Copy and paste the above code block under that section. And this will enable the ``pf`` active response script.

Moving forward, find ``<!-- Active Response Rules -->`` just below and paste the below code block.

.. code-block:: xml

    <active-response>
        <disabled>no</disabled>
        <command>pf</command>
        <location>local</location>
        <timeout>180</timeout>
    </active-response>

This will execute the active response script.

Last, but the least, don't forget to save and ``restart`` your Wazuh Manager.

.. note::

    Make sure the above code are under ``<ossec_config> * </ossec_config>`` block. You can also put under a separate **ossec_config** block at 
    the last of the configuration file for tracing and managing it a bit more conveniently.
