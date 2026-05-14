Introduction - Realtime IOC Detection and Threat Intelligence Enrichment for Wazuh with OpenCTI
===============================================================================================

This project is an **automated IOC detection and threat intelligence
enrichment engine** that bridges Wazuh and OpenCTI. It hunts for
indicators of compromise across your security logs and automatically
enriches them with real-world threat context — in real time, without
analyst intervention.

When a Wazuh alert fires, the integration extracts every recognizable
indicator (IPs, domains, file hashes, URLs, email addresses, registry
keys, and more), queries OpenCTI for threat intelligence, and delivers
the result back as an enriched alert. Analysts immediately see whether
the indicator is associated with a known threat actor, malware family,
campaign, or MITRE technique — and how confident the intelligence is.

The integration operates in three modes: as a silent background enricher
on a production Wazuh manager, as a standalone batch threat-hunting tool
against historical alerts, or as a native component in a SOAR platform
for automated response workflows.

.. toctree::
   :maxdepth: 3
   :hidden:

   ../../projects/wazuh-opencti-integration/why-you-would-use-this
   ../../projects/wazuh-opencti-integration/capabilities
   ../../projects/wazuh-opencti-integration/scope-of-engagement
   ../../projects/wazuh-opencti-integration/prerequisites-essentials