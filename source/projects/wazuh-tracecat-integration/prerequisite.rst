Prerequisite
============

Before getting started, we will be requiring to set some Credentials on our Tracecat Server. On the landing page of your Tracecat Server, 
you will notice the **Integrations** section under Workspace. You need to add the built-in credentials of ``wazuh-wui``, 
the user responsible with the Wazuh API Interactions. You can obtain it by following the `Quick Start <https://documentation.wazuh.com/current/quickstart.html>`_
section of Wazuh's Official Documentation Page if you are usign a single cluster.

Follow the image below for a high level view,

    .. image:: ../../assets/images/projects/wazuh-tracecat-integration/tracecat-server-wazuh-wui-credential-integration-1.png
        :alt: Tracecat Server Integration Guidance for Wazuh WUI Credential
        :align: center
    
    .. raw:: html

        <div style="height:25px;"></div>

Place the values in the required fields as follows,

1. ``WAZUH_WUI_PASSWORD``: Fill the parameter with the same password of your **wazuh-wui** user.
2. ``WAZUH_WUI_USERNAME``: Fill this parameter with the same name of your **wazuh-wui**, which is **wazuh-wui** itself by default.

.. tip::

    Apart from the buit-in integrations credentials, you can also add the credentials of a user that has access to Wazuh's Indexers (e.g. **A Wazuh Admin**) 
    and other users as well required for your workflows. This will be really helpful for you when you want to use those credentials as 
    secret keys for your various components in your workflows. This secrets can be used as expression variables in your components and can be called on demand.