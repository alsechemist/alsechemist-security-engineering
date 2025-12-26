Decoder Creation - ModSecurity Audit Logs 
=========================================

The decoder enables Wazuh to normalize raw audit log entries into structured fields that can be used for rule-based detection and alerting.

Decoder Objective
-----------------

The primary objective of this decoder is to:

- Identify ModSecurity audit log events
- Validate that the log entry is in JSON format
- Invoke Wazuh’s built-in JSON decoder
- Extract structured fields from the ModSecurity ``transaction`` object

This approach avoids complex regular expressions and ensures high reliability when processing structured audit logs.

Prerequisite - Decoder creation
-------------------------------

Before going further it is required to understand how JSON decoders work. 
Follow :doc:`Wazuh JSON Decoder Manipulation <../../knowledge-base/manipulation-json-decoders-wazuh/manipulation-json-decoders-wazuh>` to understand, how to
handle custom JSON Decoder in Wazuh. 

Decoder Definition
------------------

The following custom decoder is used to process ModSecurity audit logs:

.. code-block:: xml

    <decoder name="modsecurity_decoder">
        <prematch>^{"transaction":</prematch>
        <plugin_decoder>JSON_Decoder</plugin_decoder>
        <use_own_name>true</use_own_name>
    </decoder>

Add this block before the built-in/generic decoder. Check the image below for better understanding.

.. image:: ../../assets/images/research/modsecurity-log-detection-wazuh/decoder-creation-1.png
   :alt: Testing decoders
   :align: center

.. raw:: html

   <div style="height:25px;"></div>

.. tip::

    Checkout Wazuh's `Decoder Documentation <https://documentation.wazuh.com/current/user-manual/ruleset/decoders/index.html>`_ 
    for a comprehensive overview over decoder, how to make them and learn about syntaxes and more.

Decoder Testing
---------------

Once applied, it's time to test the decoder. If everything goes well, your **Phase - 1** should be able to decode the full event and **Phase - 2** should be able to catch every decoded field. 
In other words, ``**Phase 2: Completed decoding`` should not show any signs of ``No decoder matched``.

Check the image below for reference,

.. image:: ../../assets/images/research/modsecurity-log-detection-wazuh/decoder-creation-2.png
   :alt: Testing decoders
   :align: center

.. raw:: html

   <div style="height:25px;"></div>

You will also notice the ``decoder name`` has been changed to ``modsecurity_decoder``.

Besides, this decoder allows Wazuh to extract relevant fields such as:

- ``transaction.client_ip``
- ``transaction.time_stamp``
- ``transaction.request.method``
- ``transaction.request.uri``
- ``transaction.messages.ruleId``
- ``transaction.messages.message``
- ``transaction.messages.severity``

These fields form the foundation for building custom detection rules and alerts.

Why Use JSON_Decoder?
---------------------

Using the ``JSON_Decoder`` plugin provides several advantages:

- Eliminates complex regular expressions
- Improves parsing accuracy and maintainability
- Supports deeply nested JSON structures
- Ensures compatibility with future ModSecurity versions

This design choice aligns with best practices for SIEM integrations involving structured logs.

.. _unexpected-rule-trigger:

Unexpected Rule Trigger During Decoder Testing
----------------------------------------------

During decoder validation using the Wazuh log testing tool, you may encounter an automatic alert similar to the following::

    **Phase 3: Completed filtering (rules).
      id: '1002'
      level: '2'
      description: 'Unknown problem somewhere in the system.'
      groups: '["syslog","errors"]'
      firedtimes: '1'
      gpg13: '["4.3"]'
      mail: 'false'

Why This Alert Occurred?
~~~~~~~~~~~~~~~~~~~~~~~~

This output does not indicate an actual security event or error in your decoder logic. Instead, it is generated because:

- No specific rule matched the decoded fields: At this point in testing, only the built-in default rules are applied.

- Wazuh’s default rule ``1002`` acts as a fallback Rule ``1002`` is a generic “catch-all” alert triggered when, 
  logs are successfully decoded, but no custom or specific rule matches the decoded event

In other words, Wazuh is telling you: “I saw a log and decoded it, but I don’t yet know how to classify it.”

This message is expected during early decoder development. Until you create custom detection rules that reference the decoded JSON fields, 
Wazuh has nothing specific to match — and so falls back to rule ``1002``.

Next, we will be seeing how we can handle this exception and trigger alerts by creating custom rules. 
