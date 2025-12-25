Configuring Active Response for macOS Devices at Wazuh Manager
==============================================================

Go to your Wazuh Server, you can make changes at your manager node both via Wazuh Web GUI and 
by finding the configuration file at ``/var/ossec/etc/ossec.conf``, make sure you have ``sudo`` privileges before accessing through terminal.
But it more recommended that you access via the Web GUI as it's more easily manageable and accessible. Follow ``Server management → Settings → Edit configuration``. 
There you have to look out for something like ``<!-- Active response -->``, in that specific section you will notice various active response scripts as shown in the below image:

.. image:: ../../assets/images/knowledge-base/configuration-active-response-macos/active-response-macos-1.png
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

Wazuh Agent: macOS
------------------

While wazuh agents of Linux and Windows are pre-configured to log active response logs, agents of the macOS devices however not pre-configured as so.
That's why, now we will be configuring the macOS agent to log the active response logs.

Head towards your macOS agent configuration file, you will find it at ``/Library/Ossec/etc/ossec.conf`` path of your macOS device.
And this code block under ``<ossec_config> * </ossec_config>``, if it's not present.

.. code-block:: xml

    <localfile>
        <log_format>syslog</log_format>
        <location>/var/ossec/logs/active-responses.log</location>
    </localfile>

Save and ``restart`` the **Wazuh Agent** via the command below on your macOS machine.

.. code-block:: bash

    sudo /Library/Ossec/bin/ossec-control restart


Now, the Wazuh Agent will read logs from the ``active-responses.log``.