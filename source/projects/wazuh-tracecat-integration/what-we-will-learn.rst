What We'll Learn?
=================

In this project, we will learn how to integrate Wazuh with Tracecat to automate security responses. The key learning outcomes include:

- **Deploy Integration Scripts**: Place custom-tracecat.py and its wrapper into Wazuh's integration directory—then unlock the bridge
- **Create Custom Rules**: Create custom rules for Tracecat related events.
- **Configure ossec.conf for Automation**: Wire up webhook URLs, API keys, and alert triggers to make Wazuh talk to Tracecat
- **Master Tracecat Secrets**: Safely store and reference wazuh-wui credentials and other API keys across your workflows
- **Understand the Trigger Component**: The gatekeeper—how alerts flow in and workflows ignite
- **Reshape Alert JSON**: Transform raw Wazuh alerts into readable, navigable data structures using core.transform.reshape
- **Harness HTTP Requests as Actions**: Execute API calls from Tracecat back to Wazuh—and any other system with an endpoint
- **Write Powerful Expressions**: Access and manipulate alert fields using ``${{ }}`` syntax to create dynamic payloads and conditions
- **Conditionally Execute with "Run If"**: Prevent false positives—only trigger actions when the threat is real
- **Test End-to-End**: Send dummy alerts through the pipeline and watch your workflow run in real time
- **Monitor Logs & Workflow Runs**: Troubleshoot integration issues with tracecat.log and Tracecat's execution UI
- **Block SSH Brute Force (Linux, Windows, macOS)**: Implement a real-world use case with platform-specific firewall rules
- **Validate Active Response**: Verify blocked IPs in iptables, netsh, and pf — proof that automation works

By the end, you'll have a production-ready security pipeline.

.. attention::

    The motive of the project is to unlock bridge between Wazuh and Tracecat, and pave the way for its limitless possibilities. 
    So, we will not be going into too many details about the individual components of Wazuh and Tracecat, 
    but rather focus on how to leverage the integration between them to automate security orchestration effectively.

    The uses cases that will be demontrated on this project only serves as examples to show how the integration can be used,
    and also create curiosities to explore more about the integration and its capabilities. 
    You can always create your own use cases based on your needs and requirements, and also 
    share them with the community as well to inspire others to explore more about the integration and its capabilities.