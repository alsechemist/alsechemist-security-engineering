Conditional Executions of The Active Response Components
========================================================

Now we will look, how we can make the active response components to execute whenever there is an actual SSH Brute Force Attack. So, let's get started.

Switch to the **Control Flow** tab beside **Inputs,** you will notice that there is a **Run if** field asking for some **JSON Path Expressions** to be specified.
It will execute the components only if the specified parameter is found.

For Linux Agents
----------------

As for the linux endpoints, Wazuh has already specified rule-ids for SSH Brute force attacks along with the severity level.
A unique parameter can be the ``rule.id`` of the attack that is generated on the Wazuh Indexer Server. The unique rule.id that is generated for
SSH Brute Force Attacks is ``5763``

Go to the **Wazuh Indexer Logs** component and check the results tab, you will find the rule.id, something like as the image shown below:

.. image:: ../../assets/images/projects/wazuh-tracecat-integration/tracecat-conditional-workflow-configuration-1.png
    :alt: Tracecat, Copying JSON Path Guideline for Linux Agents
    :align: center

.. raw:: html

   <div style="height:25px;"></div>

.. code-block:: yaml

    ${{ ACTIONS.wazuh_indexer_logs.result.data.hits.hits[0]._source.rule.id == "5763" }}

Copy the JSON path and paste it on the **Run if** section of the **Active Response for Linux** component or 
we can say the ``core.http_request`` component that we have configured for the linux agents.
An image has been attached below for showcasing it.

.. image:: ../../assets/images/projects/wazuh-tracecat-integration/tracecat-conditional-workflow-configuration-2.png
    :alt: Tracecat Conditional Workflow Execution for Linux Agents
    :align: center

.. raw:: html

   <div style="height:25px;"></div>

And that's it, we have enabled conditional execution for the AR of linux Endpoints.

For Windows Agents
------------------

Similarly, for the windows endpoints, Wazuh has already specified rule-ids for
both RDP and SSH Brute force attacks along with the severity level. Since we have already looked at SSH Brute force attack,
we will focus on RDP Brute force attack here.

A unique parameter can be the ``rule.id`` of the attack that is generated on the Wazuh Indexer Server.
The unique ``rule.id`` that is generated for RDP Brute Force Attacks is ``60204``

Go to the **Wazuh Indexer Logs** component and check the results tab, you will find the ``rule.id``, something like as the image shown below:

.. image:: ../../assets/images/projects/wazuh-tracecat-integration/tracecat-conditional-workflow-configuration-3.png
    :alt: Tracecat, Copying JSON Path Guideline for Windows Agents
    :align: center

.. raw:: html

   <div style="height:25px;"></div>

.. code-block:: yaml

    ${{ ACTIONS.wazuh_indexer_logs.result.data.hits.hits[0]._source.rule.id == "60204"}}

Copy the JSON path and paste it on the **Run if** section of the **Active Response for Windows** component or
we can say the ``core.http_request`` component that we have configured for the windows agents.
An image has been attached below for showcasing it.

.. image:: ../../assets/images/projects/wazuh-tracecat-integration/tracecat-conditional-workflow-configuration-4.png
    :alt: Tracecat Conditional Workflow Execution for Windows Agents
    :align: center

.. raw:: html

   <div style="height:25px;"></div>

And that's it, we have enabled conditional execution for AR of windows endpoints.

For macOS Agents
----------------

Finally, for the macOS endpoints, Wazuh has already specified rule-ids for SSH Brute force attacks along with the severity level.
A unique parameter can be the ``rule.id`` of the attack that is generated on the Wazuh Indexer Server.
The unique ``rule.id`` that is generated for SSH Brute Force Attacks is ``5712``

Go to the **Wazuh Indexer Logs** component and check the results tab, you will find the ``rule.id``, something like as the image shown below:

.. image:: ../../assets/images/projects/wazuh-tracecat-integration/tracecat-conditional-workflow-configuration-5.png
    :alt: Tracecat, Copying JSON Path Guideline for macOS Agents
    :align: center

.. raw:: html

   <div style="height:25px;"></div>

.. code-block:: yaml

    ${{ ACTIONS.wazuh_indexer_logs.result.data.hits.hits[0]._source.rule.id == "5712" }}

Copy the JSON path and paste it on the **Run if** section of the **Active Response for macOS** component or
we can say the ``core.http_request`` component that we have configured for the windows agents.
An image has been attached below for showcasing it.

.. image:: ../../assets/images/projects/wazuh-tracecat-integration/tracecat-conditional-workflow-configuration-6.png
    :alt: Tracecat Conditional Workflow Execution for macOS Agents
    :align: center

.. raw:: html

   <div style="height:25px;"></div>

And that's it, we have enabled conditional execution for AR of macOS endpoints.

.. warning::
    The JSON paths in the above code blocks are just like variables named after the naming convention of the Title given to each component. 
    For example, **ACTIONS.** ``wazuh_indexer_logs`` **.result.data.hits.hits[0]._source.rule.id**, the quoted red colored area is 
    exactly as the Title set the to the Wazuh_Indexer_Logs core.http_response component.
    
    Blindly copying and pasting the above code blocks might result in workflow execution ``errors``.
    Viewers are advised to work with the comfort oftheir local environmental setup.
    
    The above code blocks are given only for representation purposes. The JSON path might be different from what has been showcased here. 
    That is why images have been given to follow it as a reference.

