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
Wazuh has already pretty much configured their active response for their Linux and Windows endpoint. An extensive documentation and community support can be found as well. 
But here we are going to focus more on **macOS** endpoints as a bit of configuration is need in order for the active response to work properly.

Refer to the :doc:`Configuring Active Response for macOS Devices at Wazuh Manager <../../knowledge-base/configuration-active-response-macos/configuration-active-response-macos>`
at the **Knowledge Base** Section to learn and understand the Manager and Agent configuration.
