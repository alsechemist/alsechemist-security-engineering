Testing → macOS Agent
=====================

.. note::

    Replace ``[username]``, ``[path/to/wordlist]`` and ``[ip-of-linux-machine]`` according to your preferences.
    You can skip the ``-I`` option if no previous sessions are saved.

Copy and paste the below command on your attacking machine.

.. code-block:: bash

   sudo hydra -t 4 -l [username] -P [path/to/wordlist] [ip-of-linux-machine] ssh -v -I

An image has been attached below for demonstration.

.. image:: ../../assets/images/projects/wazuh-tracecat-integration/tracecat-proof-of-concept-14.png
   :alt: Tracecat Workflow Run, Testing macOS Agents
   :align: center

.. raw:: html

   <div style="height:25px;"></div>

Now back to our Wazuh Dashboard, we should be seeing the related logs are being generated. 

.. image:: ../../assets/images/projects/wazuh-tracecat-integration/tracecat-proof-of-concept-15.png
   :alt: Tracecat Workflow Run, Checking Wazuh Dashboard for macOS Agent Test Case
   :align: center

.. raw:: html

   <div style="height:25px;"></div>

Now run the workflow that we have created on Tracecat

.. image:: ../../assets/images/projects/wazuh-tracecat-integration/tracecat-proof-of-concept-16.png
   :alt: Tracecat Workflow Run, macOS Agent Test Case Successfully Ran
   :align: center

.. raw:: html

   <div style="height:25px;"></div>

You should notice that, the active response component executed. Checking the result section will show further details.

.. image:: ../../assets/images/projects/wazuh-tracecat-integration/tracecat-proof-of-concept-17.png
   :alt: Tracecat Workflow Run, macOS Agent Test Case Result Inspection
   :align: center

.. raw:: html

   <div style="height:25px;"></div>

Checking back on our Wazuh Dashboard, we should notice that an event appeared showing ``AActive response: active-response/bin/pf - add`` on that
specific Agent,as shown in the below image.

.. image:: ../../assets/images/projects/wazuh-tracecat-integration/tracecat-proof-of-concept-18.png
   :alt: Tracecat Workflow Run, Checking Wazuh Dashboard for Active Response Logs of netsh
   :align: center

.. raw:: html

   <div style="height:25px;"></div>

Checking on the attacker side, after some time, we will see errors, as shown below.

.. image:: ../../assets/images/projects/wazuh-tracecat-integration/tracecat-proof-of-concept-19.png
   :alt: Tracecat Workflow Run, Checking Attacker Side for Failed Attempts of Brute Force Attack
   :align: center

.. raw:: html

   <div style="height:25px;"></div>

This settles that, our setup is functional and working.
