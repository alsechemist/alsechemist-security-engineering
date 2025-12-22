ModSecurity Log Ingestion into Wazuh
====================================

This section explains how **ModSecurity JSON-formatted audit logs** are ingested into **Wazuh** using the Wazuh agent log collection mechanism.
Proper log ingestion is a prerequisite for successful decoding, rule matching, and alert generation.

Wazuh Log Collection Configuration
----------------------------------

Wazuh collects local log files through the ``localfile`` configuration block defined in the agent configuration file.

The following configuration is used to ingest ModSecurity audit logs:

.. code-block:: xml

    <localfile>
        <log_format>json</log_format>
        <location>/var/log/modsec_audit.log</location>
    </localfile>

This configuration instructs the Wazuh agent to monitor the ModSecurity audit log file and process each entry as a JSON event.

After updating the Wazuh agent configuration, restart the agent service:

.. code-block:: bash

    sudo systemctl restart wazuh-agent

Validating Log Ingestion
------------------------

To validate that ModSecurity audit logs are correctly ingested into Wazuh, it is recommended to **actively trigger a ModSecurity rule** and 
observe the resulting alert inside Wazuh. This confirms that the entire pipeline—from log generation to alerting—is functioning as expected.

A simple way to trigger a ModSecurity alert is by simulating a common web attack, such as **SQL Injection, Path Traversal, File Access Attempt, RCE**.

SQL Injection Test
^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    curl "http://<target-host>/?id=1' OR '1'='1"

This request is designed to match OWASP CRS SQL Injection detection rules and should result in a ModSecurity audit log entry.

Path Traversal Test
^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    curl "http://<target-host>/?id=../../../etc"

    ../../../etc

This request is designed to match OWASP CRS Path Traversal detection rules and should result in a ModSecurity audit log entry.

File Access Attempt Test
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    curl "http://<target-host>/?id=....//....//....//etc/passwd"

This request is designed to match OWASP CRS File Access Attempt detection rules and should result in a ModSecurity audit log entry.

RCE Test
^^^^^^^^

.. code-block:: bash

    curl "http://<target-host>/?exec=/bin/bash"

This request is designed to match OWASP CRS RCE detection rules and should result in a ModSecurity audit log entry.

Try these examples, and event logs should appear in the threat hunting section.

.. image:: ../../assets/images/modsecurity-log-detection_wazuh/modsecurity-log-ingestion-1.png
   :alt: Modsecurity Logs Appearing in Wazuh Event Section
   :align: center

.. raw:: html

   <div style="height:25px;"></div>

Through deeper log inspection, Modsecurity brings vast range and variety of fields to indept analysis

.. image:: ../../assets/images/modsecurity-log-detection_wazuh/modsecurity-log-ingestion-2.png
   :alt: Modsecurity Logs Appearing in Wazuh Event Section
   :align: center

.. raw:: html

   <div style="height:25px;"></div>

.. note::

   **Ongoing Rule Development**

   This documentation presents a **baseline implementation** for detecting and analyzing ModSecurity events in Wazuh using custom decoders and rules.  
   Additional ModSecurity detection rules will be **added and refined over time** to improve coverage, accuracy, and attack visibility.

   The current ruleset is intentionally kept minimal to demonstrate the **core detection logic**, rule inheritance model, and analysis workflow for ModSecurity audit logs within Wazuh.

.. tip::

   **Community Contribution Encouraged**

   Security analysts and engineers are encouraged to **actively contribute** to ModSecurity log detection engineering by:

   - Adding new detection rules for additional OWASP CRS categories (e.g., XSS, RFI, protocol & API abuse, SSRF, CSRF)
   - Enhancing severity classification and contextual enrichment
   - Improving MITRE ATT&CK mappings and compliance tagging
   - Identifying new attack patterns from real-world ModSecurity events

   Collaborative rule development strengthens detection capabilities and enables faster identification of emerging web application threats across diverse environments.