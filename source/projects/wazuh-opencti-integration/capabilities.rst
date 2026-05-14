Capabilities
============

The integration performs automated IOC extraction, normalization, and
enrichment across multiple log sources and indicator types.

**Extracts Indicators Across Multiple Sources**

The script understands the structure of common Wazuh log sources:

- **Native Wazuh alerts** — IPs, domains, file hashes, URLs, email addresses, registry keys
- **Suricata/IDS** — network IPs, domains, hostnames, URLs, TLS fingerprints, JA3 hashes, file hashes from content inspection
- **Sysmon** — process hashes, network connections, DNS queries
- **Wazuh FIM (syscheck)** — file hashes, file paths, ownership, audit context (which process wrote the file, as which user)
- **Windows Registry** — registry key paths from FIM changes
- **Firewall logs** — source and destination IP addresses
- **SSH/Authentication logs** — source IPs from failed login attempts
- **DNS logs** — queried domain names and resolution results
- **Generic logs** — fallback regex patterns for indicators in free text

For each indicator type, it extracts not just the value but contextual
metadata — if a hash matches, you also get the file path and ownership;
if an IP matches, you get the peer IP and protocol; if a URL matches,
you get the HTTP method, status code, and user-agent.

Normalizes and Filters Before Querying
--------------------------------------

Not every extracted value is worth querying OpenCTI about. The integration
filters out:

- Private IP ranges (RFC 1918, loopback, link-local, multicast, reserved)
- File extensions masquerading as domains ("svchost.exe", "report.pdf")
- Malformed hashes (wrong length, invalid hex)

.. note::

    More capabilties are also planned for future releases, stay tuned for updates.
