Use Cases
=========

In this section, we will explore some of the use cases that can be implemented using the integration between Wazuh and Tracecat Server. 
These use cases will demonstrate how to leverage the capabilities of both systems to explore more about your security operations and incident response processes.

- **Use Case - 1:** Lerveraging Wazuh Active Response with Tracecat Server to Automate Incident Response Playbooks.

.. note::

    More use cases will be added in the future as we continue to explore the integration and its capabilities.

.. attention::

    The Use cases part of the section contains some images of tracecat, that are much older than the latest version of tracecat.
    Since this whole documentation was a part of a continuous development, the images demonstrated here, we a part of the same
    wazuh and tracecat integration project, but the ingration process was different where, integration via the webhook was not
    introduced yet, so there were more components involved, such as the contacting the wazuh indexer to get alerts related to specific
    rule ids, and then parsing the alert data to get the source IP address and agent ID, and then finally sending the API request to wazuh server to trigger the active response action.

    You can still refer to the previous version of this documentation to see, by checking the version ``v1.0.0`` from 
    the dropdown menu at the bottom-right corner to the page, but that version is no longer maintained.

.. toctree::
   :maxdepth: 3
   :hidden:

   ../../projects/wazuh-tracecat-integration/use-case-1-wazuh-ar