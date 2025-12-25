Overview: Tracecat Server
=========================

**Tracecat Server:** Alright now let's work on the Tracecat Server. Create a workflow, now we will be working with only 3 components in order to 
complete our full setup on our Tracecat Server. They are as follows:

- **Workflow Trigger:** It's a default for every workflow. We will not be needing it to be turned on. It is fixed, in order for your workflows to be built from there, if you are using the latest Tracecat.
- **tool.wazuh.get_access_token:** This component fetches the Wazuh ``JWT Token`` by contacting the Wazuh Server API. It is the key component here, since it will be collecting the token every time for our every API call towards both Wazuh Server and Indexer for authentication.
- **core.http_request:** This component here will be sending the http requests to the Wazuh API servers for serving our cause. And we will be needing the ``JWT Token`` for that every time.

These are available by default on Tracecat.

Workflow Overview
-----------------

To give you a glimpse, this what it will look like on our workflow.

.. image:: ../../assets/images/projects/wazuh-tracecat-integration/tracecat-server-overview.png
    :alt: Tracecat Server Overview
    :align: center

.. raw:: html

   <div style="height:50px;"></div>