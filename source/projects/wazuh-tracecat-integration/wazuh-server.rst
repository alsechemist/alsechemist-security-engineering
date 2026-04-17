Wazuh Server
============

The Wazuh server is the core component of the Wazuh security monitoring system. 
It is responsible for collecting, analyzing, and correlating security events from various sources, 
including agents installed on endpoints, network devices, and cloud services. 
The Wazuh server processes the data received from these sources to identify potential security threats and generate alerts.

It is also responsible for managing various third-party integrations, including Tracecat itself.

Integration Scripts
-------------------

To integrate Tracecat with the Wazuh server, you need to download the integration script and also the wrapper script that Wazuh is programmed to execute. 

- :download:`custom-tracecat.py <../../assets/scripts/wazuh-tracecat-integration/custom-tracecat.py>` - This is the main script that is reponsible for sending Wazuh alerts to Tracecat and triggering the corresponding playbooks.
- :download:`custom-tracecat <../../assets/scripts/wazuh-tracecat-integration/custom-tracecat>` - This the wrapper script that Wazuh will execute. It is responsible for calling the main script and passing the necessary parameters to it.

.. note::
    
    Make sure to place these scripts in the ``/var/ossec/integrations`` directory on your Wazuh server. 
    And, if you are having mutiple Wazuh Manager Clusters, you will need to place these scripts in each of the Wazuh Manager Clusters.

Set Appropriate Permissions
~~~~~~~~~~~~~~~~~~~~~~~~~~~

After placing the scripts in the correct directory, you need to set the appropriate permissions to ensure that they can be executed by the Wazuh server.

You can use the following command to set the permissions:

.. code-block:: bash
    
    sudo chmod 750 /var/ossec/integrations/custom-tracecat
    sudo chmod 750 /var/ossec/integrations/custom-tracecat.py
    sudo chown root:wazuh /var/ossec/integrations/custom-tracecat
    sudo chown root:wazuh /var/ossec/integrations/custom-tracecat.py

This command sets the permissions to allow the owner (root) and the group (wazuh) to read, write, and execute the scripts, while others can only read and execute them.

Configuring Wazuh to Execute the Integration Script
---------------------------------------------------

After placing the scripts and setting the appropriate permissions, you need to configure Wazuh to execute the integration script when certain alerts are generated.
Go the Wazuh manager configuration file, which is typically located at ``/var/ossec/etc/ossec.conf``, and add the following configuration to the ``<integrations>`` section:

.. code-block:: xml
    
    <integration>
        <name>custom-tracecat</name>
        <hook_url>[tracecat-workflow-webhook-url]</hook_url>
        <api_key>[tracecat-workflow-api-key]</api_key> <!-- Optional: Only if your Tracecat workflow requires an API key for authentication -->
        <level>10</level>
        <alert_format>json</alert_format>
    </integration>

.. note::

    - The script is designed to handle mutiple workflow triggers, so you can add multiple ``<integration>`` blocks in the same way with different webhook URLs and API keys if needed.
    - You can also adjust the ``<level>`` tag to specify the minimum alert level that should trigger the integration script.
    - You can also use ``<rule_id>`` tag instead of ``<level>`` tag, if you want to trigger the integration based on specific rule IDs rather than alert levels. Multiple rule IDs are also supported as well by separating them with commas (e.g., ``<rule_id>1001,1002,1003</rule_id>``).

Make sure to replace ``[tracecat-workflow-webhook-url]`` with the actual webhook URL of your Tracecat workflow, 
and if your workflow requires an API key for authentication, replace ``[tracecat-workflow-api-key]`` with the actual API key.

The script is desined for both cases where the Tracecat workflow requires an API key for authentication and where it does not. Either way it will work just fine.

After adding this configuration, save the file and restart the Wazuh manager to apply the changes:

.. code-block:: bash
    
    sudo systemctl restart wazuh-manager

This will ensure that the Wazuh server is now configured to execute the ``custom-tracecat`` integration script whenever an alert with 
the specified level or higher is generated, allowing you to automate your incident response workflows using Tracecat.