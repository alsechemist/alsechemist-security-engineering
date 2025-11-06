Wazuh Agent: macOS
==================

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