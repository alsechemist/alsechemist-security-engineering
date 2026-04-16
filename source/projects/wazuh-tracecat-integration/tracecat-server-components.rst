Tracecat Server Components
==========================

In this section, we will explore the bare minimum components that we need to have on our Tracecat Server in order 
to be able to receive the alerts from Wazuh and trigger the corresponding playbooks.

Component - core.transform.reshape
----------------------------------

This is the component that is reponsible for showing the incoming json field from the Wazuh alerts in a more readable format. 
It is a built-in component that is available in Tracecat by default, so you don't need to create it from scratch. 
You can simply add it to your workflow and configure it to reshape the incoming json data as needed.

Basically, if the script is working right, then all the field from the json alert will directly be handled by the Trigger componnent. 
But you won't be able to see it and also the the relevant json path required to be used as expressions. 
So, you can use the Reshape component to have a more readable format of the incoming json data and also to be able 
to easily identify the relevant fields and their corresponding json paths that you can use in your workflow components.

Follow the image below for a high level view of how the Reshape component is configured in the workflow,

.. image:: ../../assets/images/projects/wazuh-tracecat-integration/tracecat-server-workflow-contifiguration-1.png
    :alt: Tracecat Server, Configuration of Reshape Component in the Workflow
    :align: center

.. raw:: html
    
    <div style="height:25px;"></div>

All you need to do is, in the **Inputs** section, set the value to ``${{ TRIGGER }}``. 
This will allow the Reshape component to recive the json field from the wazuh alerts.
You will be able to see all the field in the results section. Like the image below,

.. image:: ../../assets/images/projects/wazuh-tracecat-integration/tracecat-server-workflow-contifiguration-2.png
    :alt: Tracecat Server, Reshape Component Showing the Incoming Json Data from Wazuh Alerts
    :align: center

.. raw:: html
    
    <div style="height:25px;"></div>

This way, you can easily identify the relevant fields and their corresponding json paths that are required to be used in your workflow components.

Component - core.http_request
-----------------------------

This one the main components that we need in order to contact with any API of a third-party system, including Wazuh's API itself.
It is also a built-in component that is available in Tracecat by default, so you don't need to create it from scratch.
You can simply add it to your workflow and configure it to send the necessary API requests to Wazuh's API or any other third-party system as needed.

In almost every case of Wazuh related workflows, we will be needing to retrivge the Wazuh JWT token in order to be able to send authenticated API requests to Wazuh's API.
So, now we will be seeing how can we configure the Http Request component to send a POST request to Wazuh's API to retrive the JWT token.

Copy the configuration below and place it in the **YAML** tab of the **Inputs** section of the Http Request component,

.. code-block:: yaml

    url: https://[wazuh-server-ip-address]:55000/security/user/authenticate?raw=true
    method: POST
    auth:
        password: ${{ SECRETS.wazuh_wui.WAZUH_WUI_PASSWORD }}
        username: ${{ SECRETS.wazuh_wui.WAZUH_WUI_USERNAME }}
    verify_ssl: false

Make sure to replace ``[wazuh-server-ip-address]`` with the actual IP address of your Wazuh server.

The YAML tab allows you to place your configurations more freely than the Form tab. You will also see in the form tab that the fields are 
automatically filled based on the YAML configuration, but you can always edit the YAML configuration as needed.

Follow the image below for a high level view of how the Http Request component is configured in the workflow,

.. image:: ../../assets/images/projects/wazuh-tracecat-integration/tracecat-server-workflow-contifiguration-3.png
    :alt: Tracecat Server, Configuration of Http Request Component in the Workflow
    :align: center

.. raw:: html
    
    <div style="height:25px;"></div>

This way, you can easily configure the Http Request component to send the necessary API requests to Wazuh's API or any other third-party system as needed.

Expressions
-----------

Expressions are a powerful feature in Tracecat that allow you to dynamically access and manipulate data within your workflow components.

So, How can we use the expressions to access the fields from the incoming json data from Wazuh alerts?

You can use the following syntax to access the fields from the incoming json data: ``${{ [expression.field_name] }}``

Replace ``[expression.field_name]`` with the json path of the field that you want to access. 
For example, if you want to access the ``rule.id`` field from the incoming json data, you can just copy and 
replace it in the expression syntax like this: ``${{ rule.id }}``

Follow the image below for a high level view of how to use expressions to access the fields from the incoming json data from Wazuh alerts,

.. image:: ../../assets/images/projects/wazuh-tracecat-integration/tracecat-server-workflow-contifiguration-4.png
    :alt: Tracecat Server, Using Expressions to Access the Fields from the Incoming Json Data from Wazuh Alerts
    :align: center

.. raw:: html
    
    <div style="height:25px;"></div>

.. tip::
    
    Make sure to use the correct json path for the field that you want to access. 
    Best, if you just copy and paste it into the expression syntax to avoid any typos or mistakes.
    Follow Tracecat's `Expression Guideline and Concept <https://docs.tracecat.com/automations/core-concepts/expressions>`_ for more details about expressions and how to use them effectively in your workflows.

So far, this basically concludes the Integration of Wazuh with Tracecat, and the configuration of the main components that 
are required on the Tracecat server in order to be able to receive the alerts from Wazuh and trigger the corresponding playbooks.

Now we can always look for some uses cases and scenarios to further extend the explorations and possibilities of the integration, 
and to see how we can leverage the integration to automate various security operations and incident response workflows.