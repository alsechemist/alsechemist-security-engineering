Introduction - Real Time Threat Hunting and IOC Detection with Wazuh & OpenCTI
==============================================================================

Overview
--------

This project is a **Wazuh ⇄ OpenCTI threat intelligence integration** that enriches Wazuh alerts with contextual threat intelligence from 
an OpenCTI platform in real time. Whenever a Wazuh rule fires and matches the configured filters, the integration extracts indicators of compromise (IOCs) from 
the alert, queries OpenCTI for matching intelligence, and writes structured enrichment events back into Wazuh's log pipeline for correlation and alerting.

The integration is built as a drop-in component for the Wazuh manager, 
designed to operate transparently alongside existing detection rules/rule groups without disrupting the alert flow.

The Problem
-----------

Wazuh excels at detecting events on endpoints and network devices, but its alerts on their own carry no external threat context. An alert that says *"file added to /home/user/downloads"* tells you something happened — it does not tell you whether the file's hash is associated with a known malware family, whether the source IP belongs to a tracked threat actor's infrastructure, or whether the domain in a DNS query has been linked to an active campaign.

OpenCTI holds exactly that context: indicators, observables, threat actors, intrusion sets, malware families, campaigns, MITRE ATT&CK mappings, reports, and the relationships between them. Without an integration layer, analysts must pivot manually between the two platforms — a workflow that does not scale and that loses context with every context switch.

This project closes that gap by performing the lookup automatically, on every relevant alert, and surfacing the result as a structured event that downstream Wazuh rules can act on.

What the Integration Does
-------------------------

For every Wazuh alert that matches the configured ``<integration>`` filters, the pipeline performs the following steps:

1. **Reads the triggering alert** from the temporary JSON file Wazuh provides.
2. **Extracts candidate IOCs** using a hybrid two-stage strategy:

   - *Known-field-path extraction* — high-precision lookups based on the alert's rule groups (Suricata, Sysmon, syscheck, firewall, sshd, and others).
   - *Regex fallback* — a secondary pass over the alert's string content to catch IOCs in free-text fields such as ``full_log`` or ``rule.description``.

3. **Normalizes and filters** each candidate — dropping private IP ranges, allowlisted domains, malformed hashes, and file extensions that masquerade as domain names — then deduplicates the surviving set.
4. **Queries OpenCTI's GraphQL API** for every IOC, performing a dual lookup against both ``indicators`` and ``stixCyberObservables`` in a single round trip.
5. **Writes one structured JSON event per IOC** to a dedicated log file, which Wazuh re-ingests through a ``<localfile>`` block so that custom decoders and rules can act on the enriched data.

Each enrichment event carries a flat, predictable schema: match type, severity score, TLP marking, MITRE technique IDs, threat actors, intrusion sets, malware, campaigns, tools, vulnerabilities, infrastructure, labels, reports, authorship, and (optionally) the full raw GraphQL response for analysts who need every detail.

Architecture at a Glance
------------------------

The integration consists of three layers, each with a clearly defined responsibility.

The Wrapper Script
~~~~~~~~~~~~~~~~~~

``custom-opencti`` is a thin POSIX shell script that Wazuh's integrator daemon invokes directly. It locates a working Python interpreter, enforces a hard execution timeout, optionally writes a wrapper-level audit log, and hands control to the Python script. It contains no enrichment logic.

The Python Integration
~~~~~~~~~~~~~~~~~~~~~~

``custom-opencti.py`` performs all of the real work: alert parsing, IOC extraction, normalization, OpenCTI querying, response flattening, and structured log emission.

The Wazuh Rule Set
~~~~~~~~~~~~~~~~~~

``opencti_rules.xml`` decodes the structured enrichment events written to ``/var/ossec/logs/opencti.log`` and converts them back into Wazuh alerts at appropriate severity levels — tiered by IOC type and confidence score, with platform-health rules for authentication failures, rate limiting, network errors, and sustained outages.

The flow is unidirectional and stateless: Wazuh → wrapper → Python → OpenCTI → log file → Wazuh decoder/rules → final alert.

Production Considerations
-------------------------

The integration was designed from the outset for production deployment, not as a proof of concept. Several properties are worth noting up front.

Failure Isolation
~~~~~~~~~~~~~~~~~

A failure on one IOC never stops processing of the remaining IOCs in an alert. Network errors, authentication failures, GraphQL errors, and unexpected exceptions are all logged as structured events that the rule set picks up — turning operational failures into actionable alerts of their own.

Bounded Execution Time
~~~~~~~~~~~~~~~~~~~~~~

The wrapper enforces a hard timeout via the ``timeout`` command, with a SIGKILL grace period as a fallback. The Python layer enforces per-request HTTP timeouts. Together these prevent a stalled OpenCTI from wedging the Wazuh integrator.

Sensitive Data Handling
~~~~~~~~~~~~~~~~~~~~~~~

The OpenCTI API token is never written to logs or echoed in interactive output, even in debug mode. The hook URL is logged because it is required for diagnostics and is not a secret.

Pre-Query Filtering
~~~~~~~~~~~~~~~~~~~

Private IP ranges, common file extensions, and operator-defined allowlists are filtered out before any network call is made — saving round trips, reducing log noise, and keeping the OpenCTI platform from being queried about IOCs that could not possibly be useful.

Schema Stability
~~~~~~~~~~~~~~~~

The structured log format is deliberately flat and predictable so that downstream decoders and rules do not have to walk nested JSON. Every field that a rule might key on lives at a known top-level path.

Visibility Into Platform Health
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Authentication failures, permission errors, rate limiting, 5xx responses, and network failures are all detected and surfaced as their own alert tiers, with frequency-based escalation for sustained outages.

Document Structure
------------------

The remainder of this documentation is organized as follows:

- **Installation** — prerequisites, file placement, ownership, and permissions.
- **Configuration** — the ``ossec.conf`` integration block, Python configuration knobs, allowlists, and IOC type toggles.
- **Architecture** — a deeper look at the wrapper, the Python integration, and the rule set.
- **IOC Extraction** — the known-field-path table, regex patterns, and normalization rules.
- **OpenCTI Query** — the GraphQL query, response parsing, and authorship handling.
- **Output Schema** — the structure of each enrichment event and the meaning of every field.
- **Rule Set** — the tiered rule design, severity assignment, and frequency-based escalation.
- **Operations** — log locations, debugging, common failure modes, and troubleshooting.
- **Reference** — exit codes, config defaults, and field-path catalogs.