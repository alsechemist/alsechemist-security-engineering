Wazuh Server
============

**Wazuh Indexer API:** At first lets start with configuring Wazuh Indexer API. 
You will find the configuration file at /etc/wazuh-indexer/opensearch.yml of your Wazuh Server. 
It's a very simple configuration, we only need to change one parameter. By default, the network.host parameter is set to 127.0.0.1, 
which means the API is only accessible within the localhost itself. Tracecat won't be able to access the API if it's localhost only, 
for that it is recommended to set the parameter to,

.. code-block:: xml

   network.host: "0.0.0.0"


