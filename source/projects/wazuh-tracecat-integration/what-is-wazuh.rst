What is Wazuh?
==============

Wazuh is a comprehensive security monitoring platform that serves as the eyes and ears of your security infrastructure. 
Think of it as a vigilant security guard that never sleeps, continuously watching over your systems. 
At its core, Wazuh consists of several key components that work together seamlessly.

The **Wazuh Manager** acts as the central brain of the operation, collecting and analyzing security data from across your entire infrastructure. 
It processes logs, detects anomalies, and can trigger automated responses when threats are identified. 
The **Wazuh Indexer**, built on OpenSearch, serves as the memory bank where all security events, logs, and alerts are stored and 
indexed for lightning-fast retrieval and analysis. Meanwhile, **Wazuh Agents** are deployed across your endpoints, acting like distributed sensors that 
monitor file integrity, system calls, network connections, and other critical security indicators.
What makes Wazuh particularly powerful is its Active Response capability. 
This feature transforms Wazuh from a passive monitoring tool into an active defender that can automatically respond to threats in real-time. 
When suspicious activity is detected, Active Response can immediately execute predefined actions such as blocking 
IP addresses, disabling user accounts, or isolating compromised systems.

.. image:: ../../assets/images/wazuh-tracecat-integration/wazuh-logo.png
   :alt: Wazuh Logo
   :align: center