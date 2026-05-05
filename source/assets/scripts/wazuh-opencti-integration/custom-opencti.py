#!/var/ossec/framework/python/bin/python3
# -*- coding: utf-8 -*-
#
# ============================================================================
# custom-opencti — Wazuh ⇄ OpenCTI integration
# ============================================================================
#
# WHAT THIS DOES
# --------------
# Wazuh invokes this script (via the <integration> block in ossec.conf) every
# time a rule/level/group filter you defined matches an alert. The script:
#
#   1. Reads the triggering alert from the temp file Wazuh passed us.
#   2. Extracts candidate IOCs (IPs, domains, hashes, URLs) from the alert,
#      using two complementary strategies:
#         a. Known-field-path lookup, based on the alert's rule groups.
#         b. Regex fallback over remaining string content.
#   3. Normalizes and filters each IOC (drops private IPs, allowlist entries,
#      bad formats) then deduplicates within this alert.
#   4. Queries OpenCTI's GraphQL API for every surviving IOC.
#   5. Writes one single-line JSON event per IOC to /var/ossec/logs/opencti.log.
#
# That log file is then re-ingested by Wazuh via a <localfile> block so you
# can write custom decoders + rules on top of it. Those decoders/rules are a
# SEPARATE deliverable — this script only produces the enriched log lines.
#
# INVOCATION (Wazuh does this for you)
# ------------------------------------
#   /var/ossec/integrations/custom-opencti  <alert_file>  <api_key>  <hook_url>
#
#   arg1  alert_file  — path to a temp JSON file containing the alert
#   arg2  api_key     — value of <api_key> from ossec.conf  (OpenCTI token)
#   arg3  hook_url    — value of <hook_url> from ossec.conf (GraphQL endpoint)
#
# CONFIGURATION
# -------------
# Behavior knobs live in the CONFIG section below. Edit once per deployment.
# Everything else is driven by the alert content itself.
#
# FILES
# -----
#   /var/ossec/integrations/custom-opencti          — this script (permissions 750, root:wazuh)
#   /var/ossec/logs/opencti.log                     — output log (permissions 660, wazuh:wazuh)
#   /var/ossec/logs/integrations.log                — Wazuh's integrator log (for diagnostics)
#
# ============================================================================

import hashlib
import json
import os
import re
import sys
import time
import ipaddress
import traceback
from datetime import datetime, timezone

# `requests` ships with Wazuh's bundled Python — no pip install needed.
import requests
# Silence warnings when VERIFY_TLS=False (self-signed certs on internal OpenCTI).
from requests.packages.urllib3.exceptions import InsecureRequestWarning


# ============================================================================
# CONFIG — edit these to suit your deployment
# ============================================================================

# ── HTTP behavior ───────────────────────────────────────────────────────────
# How long to wait for OpenCTI to respond before giving up (seconds).
# Keep tight — this runs per-alert, so you don't want to stall Wazuh.
TIMEOUT_SECONDS = 5

# Retry once on transient failures (network errors, HTTP 5xx, timeouts).
# We do NOT retry on 4xx — those are config errors that won't fix themselves.
RETRY_ON_FAILURE = True
RETRY_BACKOFF_SECONDS = 1

# Verify TLS certificates when talking to OpenCTI.
# Default False because many users deploy OpenCTI internally with self-signed
# certs. Flip to True for production deployments with proper PKI.
VERIFY_TLS = False

# ── Logging behavior ────────────────────────────────────────────────────────
# Diagnostic log level for messages emitted to stderr (which Wazuh captures
# in /var/ossec/logs/integrations.log). Controls verbosity of the script's
# own operational messages — NOT the IOC enrichment events written to
# opencti.log (those are always written regardless of this setting).
# One of: "DEBUG", "INFO", "WARN", "ERROR". Default INFO is appropriate for
# production. Set to DEBUG temporarily when troubleshooting.
LOG_LEVEL = "INFO"

# Write a log line even when OpenCTI has no record of the IOC, and when we
# pre-filter an IOC (e.g. private IP). Useful for gap analysis ("how often
# does Wazuh see IOCs that OpenCTI doesn't know?"). Disable if disk space is
# tight or the log gets too noisy.
LOG_MISSES = False

# Embed the full raw GraphQL response in each log line under "raw_response".
# Default ON so analysts have every detail OpenCTI returned. Disable to shrink
# log lines significantly if you only need the flat summary fields.
INCLUDE_RAW_RESPONSE = False

# ── IOC types to extract ────────────────────────────────────────────────────
# Turn off any type you don't want to query. Useful if e.g. FIM alerts generate
# thousands of hashes per hour and you only care about network IOCs.
EXTRACT_IOC_TYPES = {
    "ipv4-addr":           True,
    "ipv6-addr":           True,
    "domain-name":         True,
    "url":                 True,
    "sha256":              True,
    "sha1":                True,
    "md5":                 True,
    "email-addr":          False,  # enable if your alerts carry email IOCs
    "windows-registry-key": True,  # enabled by default; set False if you don't
                                    # ingest registry events or find them noisy
    "user-agent":          True,   # enabled; useful for Suricata HTTP events
                                    # and web server/proxy logs
}

# ── Output file ─────────────────────────────────────────────────────────────
OUTPUT_LOG_PATH  = "/var/ossec/logs/opencti.log"
OUTPUT_LOG_PERMS = 0o660
OUTPUT_LOG_OWNER = ("wazuh", "wazuh")   # (user, group) — used on first creation

# ── Allowlists (IOCs matching these are skipped pre-query) ──────────────────
# Add your corporate domains, public IPs you never want to query about, etc.
# Domains match as exact OR as suffix (".example.com" matches anything.example.com).
ALLOWLIST_DOMAINS = [
    "localhost",
    ".local",
    ".arpa",
    # "yourcorp.com",
    # ".internal.yourcorp.com",
]
ALLOWLIST_IPS = [
    # "203.0.113.10",
]

# ── Known alert-field IOC paths ─────────────────────────────────────────────
# Mapping from rule group → list of (dotted_json_path, ioc_type) tuples.
# When an alert's rule.groups contains any of these keys, we read the listed
# paths directly. This is the "high confidence" extraction arm.
#
# IMPORTANT — PATH PREFIXING:
#   Wazuh's integrator passes the raw alerts.json JSON to this script. In that
#   format, some objects live at the TOP LEVEL (syscheck, rule, agent, full_log)
#   while other decoder output lives under `data.*` (Sysmon, Suricata, etc).
#
#   The script's `_get_dotted` helper tries both "data.X" and "X" automatically,
#   so you can write either form here and it'll work. The paths below use the
#   form that matches what Wazuh actually produces in alerts.json.
#
# You can extend this freely — it's the most useful place to tune the script
# for your specific log sources.
KNOWN_FIELD_PATHS = {
    # Suricata / generic IDS — decoders put output under `data`.
    # Suricata's EVE JSON produces different sub-objects depending on event_type:
    #   - event_type=alert    always: src_ip, dest_ip, proto, alert.*
    #   - event_type=http     http.* (hostname, url, http_user_agent)
    #   - event_type=dns      dns.rrname (query name); dns.answers[*].rdata is
    #                         an array (handled by regex fallback)
    #   - event_type=tls      tls.sni, tls.fingerprint (cert SHA1), tls.ja3.hash
    #   - event_type=fileinfo fileinfo.{md5,sha1,sha256} (when content inspection on)
    #
    # "ids" and "suricata" groups both fire on Suricata alerts — identical
    # coverage keeps behavior predictable regardless of which group matched.
    #
    # TYPE NOTES:
    #   - tls.fingerprint is Suricata's server-cert SHA1 fingerprint. It gets
    #     matched against OpenCTI's X509-Certificate hash indicators via
    #     substring pattern match — the sha1 IOC type is the correct mapping.
    #   - tls.ja3.hash is a 32-char hex MD5 (JA3 client fingerprint). Matches
    #     OpenCTI indicators that encode JA3 as file:hashes.MD5 patterns.
    "ids": [
        # Core network fields
        ("data.src_ip",                "ipv4-addr"),
        ("data.dest_ip",               "ipv4-addr"),
        # Flow sub-object (pre-NAT, sometimes present and different from top-level)
        ("data.flow.src_ip",           "ipv4-addr"),
        ("data.flow.dest_ip",          "ipv4-addr"),
        # HTTP sub-object
        ("data.http.hostname",         "domain-name"),
        ("data.http.url",              "url"),
        ("data.http.http_user_agent",  "user-agent"),
        # TLS sub-object
        ("data.tls.sni",               "domain-name"),
        ("data.tls.fingerprint",       "sha1"),   # certificate SHA1 fingerprint
        ("data.tls.ja3.hash",          "md5"),    # JA3 client fingerprint
        # DNS sub-object (array answers handled by regex fallback)
        ("data.dns.rrname",            "domain-name"),
        # File content inspection
        ("data.fileinfo.sha256",       "sha256"),
        ("data.fileinfo.sha1",         "sha1"),
        ("data.fileinfo.md5",          "md5"),
        ("data.fileinfo.filename",     "filepath"),  # context only, not queried
        # Alert sub-object — some Suricata rules put hostname here
        ("data.alert.hostname",        "domain-name"),
    ],
    "suricata": [
        # Identical to "ids" — see comments above
        ("data.src_ip",                "ipv4-addr"),
        ("data.dest_ip",               "ipv4-addr"),
        ("data.flow.src_ip",           "ipv4-addr"),
        ("data.flow.dest_ip",          "ipv4-addr"),
        ("data.http.hostname",         "domain-name"),
        ("data.http.url",              "url"),
        ("data.http.http_user_agent",  "user-agent"),
        ("data.tls.sni",               "domain-name"),
        ("data.tls.fingerprint",       "sha1"),
        ("data.tls.ja3.hash",          "md5"),
        ("data.dns.rrname",            "domain-name"),
        ("data.fileinfo.sha256",       "sha256"),
        ("data.fileinfo.sha1",         "sha1"),
        ("data.fileinfo.md5",          "md5"),
        ("data.fileinfo.filename",     "filepath"),
        ("data.alert.hostname",        "domain-name"),
    ],

    # Sysmon — Windows endpoint telemetry (under `data.win.eventdata`)
    "sysmon_event1": [     # Process creation
        ("data.win.eventdata.hashes", "mixed-hashes"),  # parsed specially below
        ("data.win.eventdata.image",  "filepath"),      # not queried, but kept for context
    ],
    "sysmon_event3": [     # Network connection
        ("data.win.eventdata.destinationIp",       "ipv4-addr"),
        ("data.win.eventdata.destinationHostname", "domain-name"),
    ],
    "sysmon_event22": [    # DNS query
        ("data.win.eventdata.queryName", "domain-name"),
    ],

    # FIM (syscheck) — LIVES AT TOP LEVEL in alerts.json, not under `data`.
    # Covers files added/modified on Linux and generic file targets.
    "syscheck": [
        ("syscheck.sha256_after", "sha256"),
        ("syscheck.sha1_after",   "sha1"),
        ("syscheck.md5_after",    "md5"),
        ("syscheck.path",         "filepath"),  # context only, not queried
    ],
    # FIM syscheck file-specific group (same paths, explicit for clarity)
    "syscheck_file": [
        ("syscheck.sha256_after", "sha256"),
        ("syscheck.sha1_after",   "sha1"),
        ("syscheck.md5_after",    "md5"),
        ("syscheck.path",         "filepath"),
    ],
    # Windows Registry changes (FIM on registry). The hashes here are hashes
    # of the registry value's CONTENT, not file hashes — matching them against
    # OpenCTI's File observables will rarely succeed. The meaningful IOC is
    # the registry path itself.
    "syscheck_registry": [
        ("syscheck.path",         "windows-registry-key"),
        # We capture value_name separately so the extracted IOC is the full
        # key path joined with the value name — that's the form threat intel
        # typically references (e.g., "HKLM\...\Run\MaliciousService").
        # This concatenation happens in _extract_from_known_paths below.
        ("syscheck.value_name",   "registry-value-name"),  # special-cased
    ],

    # Firewall (pfSense, iptables, Windows Firewall, etc.)
    "firewall": [
        ("data.srcip", "ipv4-addr"),
        ("data.dstip", "ipv4-addr"),
    ],

    # SSH & generic authentication
    "sshd": [
        ("data.srcip", "ipv4-addr"),
    ],
    "authentication_failed": [
        ("data.srcip", "ipv4-addr"),
    ],

    # Generic DNS logs
    "dns": [
        ("data.dns.rrname", "domain-name"),
        ("data.dns.rdata",  "ipv4-addr"),
    ],
}


# ============================================================================
# THE GRAPHQL QUERY
# ============================================================================
# This is the validated query you built. It performs a dual lookup in one
# round trip:
#   - indicators (preferred — has scoring, validity, relationships)
#   - stixCyberObservables (fallback — raw SCOs without a promoted indicator)
#
# The filter set:
#   - pattern contains $ioc
#   - revoked = false
#   - valid_until > now  OR  valid_until is null
#
# We embed it as a string here; $ioc is a GraphQL variable bound at call time.

GRAPHQL_QUERY = """
query EnrichForWazuh($ioc: Any!) {
  indicators(
    filters: {
      mode: and
      filters: [
        { key: "pattern",  values: [$ioc], operator: contains }
        { key: "revoked",  values: ["false"] }
      ]
      filterGroups: [
        {
          mode: or
          filters: [
            { key: "valid_until", values: ["now"], operator: gt }
            { key: "valid_until", values: [],      operator: nil }
          ]
          filterGroups: []
        }
      ]
    }
  ) {
    edges {
      node {
        id
        standard_id
        name
        pattern
        pattern_type
        valid_from
        valid_until
        x_opencti_score
        confidence
        indicator_types
        revoked
        created_at
        updated_at

        # ── Authorship / Provenance ────────────────────────────────
        # createdBy — STIX-level author (the org/individual that authored
        # this piece of intel). Travels with the object across systems.
        createdBy {
          ... on Identity {
            id
            standard_id
            entity_type
            identity_class
            name
            description
          }
        }
        # creators — OpenCTI-local users who created/modified the record.
        # Separate concept from `createdBy`; don't conflate.
        creators {
          id
          name
        }
        # objectOrganization — orgs granted access (multi-tenant context).
        objectOrganization {
          id
          name
        }

        killChainPhases { kill_chain_name phase_name }

        observables {
          edges { node { id entity_type observable_value } }
        }

        stixCoreRelationships {
          edges {
            node {
              id
              relationship_type
              start_time
              stop_time
              confidence
              createdBy {
                ... on Identity { id name identity_class }
              }
              from { ... on BasicObject { id entity_type } }
              to {
                ... on BasicObject   { id entity_type }
                ... on ThreatActor   { name description aliases }
                ... on IntrusionSet  { name description aliases }
                ... on Malware       { name description malware_types is_family }
                ... on Campaign      { name description }
                ... on AttackPattern { name x_mitre_id }
                ... on Tool          { name description }
                ... on Infrastructure{ name infrastructure_types }
                ... on Vulnerability { name description }
                ... on Incident      { name description }
                ... on CourseOfAction{ name description }
                ... on Identity      { name identity_class }
                ... on Location {
                  name
                  ... on City              { country { name } }
                  ... on Country           { region  { name } }
                  ... on AdministrativeArea{ country { name } }
                  ... on Position          { latitude longitude }
                }
              }
            }
          }
        }

        objectLabel { value }
        objectMarking { definition definition_type }
        externalReferences {
          edges { node { source_name url description } }
        }
        reports(first: 5) {
          edges {
            node {
              id
              name
              published
              report_types
              description
              createdBy {
                ... on Identity { id name identity_class }
              }
            }
          }
        }
      }
    }
  }

  stixCyberObservables(
    filters: {
      mode: and
      filters: [
        { key: "value", values: [$ioc], operator: eq }
      ]
      filterGroups: []
    }
  ) {
    edges {
      node {
        id
        standard_id
        entity_type
        observable_value
        x_opencti_score
        created_at
        updated_at

        # ── Authorship / Provenance (mirrors indicators) ──────────
        createdBy {
          ... on Identity {
            id
            standard_id
            entity_type
            identity_class
            name
            description
          }
        }
        creators {
          id
          name
        }
        objectOrganization {
          id
          name
        }

        objectLabel { value }
        objectMarking { definition definition_type }

        # Any indicators linked back to this observable
        indicators {
          edges {
            node {
              id
              name
              pattern
              x_opencti_score
              valid_until
              revoked
              createdBy {
                ... on Identity { id name identity_class }
              }
            }
          }
        }

        # Relationships from the observable — FULL COVERAGE matching
        # the indicator section, so observable_only matches get the same
        # enrichment depth as indicator_hit_valid matches.
        stixCoreRelationships {
          edges {
            node {
              id
              relationship_type
              start_time
              stop_time
              confidence
              createdBy {
                ... on Identity { id name identity_class }
              }
              from { ... on BasicObject { id entity_type } }
              to {
                ... on BasicObject   { id entity_type }
                ... on ThreatActor   { name description aliases }
                ... on IntrusionSet  { name description aliases }
                ... on Malware       { name description malware_types is_family }
                ... on Campaign      { name description }
                ... on AttackPattern { name x_mitre_id }
                ... on Tool          { name description }
                ... on Infrastructure{ name infrastructure_types }
                ... on Vulnerability { name description }
                ... on Incident      { name description }
                ... on CourseOfAction{ name description }
                ... on Identity      { name identity_class }
                ... on Location {
                  name
                  ... on City              { country { name } }
                  ... on Country           { region  { name } }
                  ... on AdministrativeArea{ country { name } }
                  ... on Position          { latitude longitude }
                }
              }
            }
          }
        }

        reports(first: 5) {
          edges {
            node {
              id
              name
              published
              report_types
              description
              createdBy {
                ... on Identity { id name identity_class }
              }
            }
          }
        }
      }
    }
  }
}
"""


# ============================================================================
# REGEX PATTERNS — fallback extraction
# ============================================================================
# These run AFTER known-field extraction, on remaining string content. They're
# more promiscuous (more false positives) but catch IOCs in free-text fields
# like `full_log` or `rule.description`.

RE_IPV4   = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
RE_IPV6   = re.compile(r"\b(?:[A-Fa-f0-9]{1,4}:){2,7}[A-Fa-f0-9]{1,4}\b")
RE_SHA256 = re.compile(r"\b[A-Fa-f0-9]{64}\b")
RE_SHA1   = re.compile(r"\b[A-Fa-f0-9]{40}\b")
RE_MD5    = re.compile(r"\b[A-Fa-f0-9]{32}\b")
RE_URL    = re.compile(r"\bhttps?://[^\s\"'<>]+", re.IGNORECASE)
# Domain regex: conservative — must have at least one dot and a 2+ letter TLD.
RE_DOMAIN = re.compile(
    r"\b(?=[a-z0-9])(?:[a-z0-9-]{1,63}\.)+[a-z]{2,63}\b",
    re.IGNORECASE,
)
RE_EMAIL  = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")


# ============================================================================
# HELPERS — logging, file ops, dotted-path access
# ============================================================================

# Numeric severity ranks for level filtering. Higher number = more severe.
_LOG_LEVELS = {"DEBUG": 10, "INFO": 20, "WARN": 30, "ERROR": 40}


def _log(level, msg):
    """Emit a diagnostic message to stderr with a timestamp and severity
    level. Wazuh captures stderr in /var/ossec/logs/integrations.log.

    Messages below the configured LOG_LEVEL threshold are suppressed, so
    flipping LOG_LEVEL to DEBUG temporarily reveals everything without
    requiring code changes.

    Format: <iso_timestamp> [custom-opencti] [<LEVEL>] <message>
    """
    if _LOG_LEVELS.get(level, 100) < _LOG_LEVELS.get(LOG_LEVEL, 20):
        return
    sys.stderr.write("{} [custom-opencti] [{}] {}\n".format(
        _now_iso(), level, msg))

#def _stderr(msg):
#    """Backwards-compatible shim for the old _stderr() helper. New code
#    should call _log(level, msg) directly with an explicit severity."""
#    _log("ERROR", msg)

def _now_iso():
    """ISO 8601 UTC timestamp with millisecond precision, formatted to match
    Wazuh's exact `alerts.json` convention: `YYYY-MM-DDTHH:MM:SS.mmm+0000`.

    Note the `+0000` (not `Z`) suffix — both are valid ISO 8601 representations
    of UTC, but every downstream tool treats them as semantically identical.
    Matching Wazuh's format makes log lines visually consistent and avoids
    the rare edge case where a strict parser only accepts one form.

    Captures `now` once to avoid sub-millisecond drift between the seconds
    and milliseconds components."""
    timenow = datetime.now(timezone.utc)
    return timenow.strftime("%Y-%m-%dT%H:%M:%S.") + \
           "{:03d}+0000".format(timenow.microsecond // 1000)


def _get_dotted(obj, path):
    """Read a value from a nested dict using a dotted path string.
    Returns None if any segment is missing. Handles the common Wazuh pattern
    of deeply nested JSON (e.g. 'data.win.eventdata.destinationIp').

    DEFENSIVE LAYOUT HANDLING:
    Wazuh's integrator passes alerts in alerts.json format, where some objects
    live at the TOP LEVEL (syscheck, rule, agent) while decoder output is
    under `data.*` (Sysmon, Suricata). The Indexer (OpenSearch) schema, on the
    other hand, sometimes promotes everything under `data`. To handle both
    without the config table caring, we try the literal path first and — if
    that misses — we also try with/without a leading `data.` segment.
    """
    def _walk(o, p):
        cur = o
        for segment in p.split("."):
            if isinstance(cur, dict) and segment in cur:
                cur = cur[segment]
            else:
                return None
        return cur

    # Try the literal path
    v = _walk(obj, path)
    if v is not None:
        return v

    # Try toggling the `data.` prefix — handles top-level vs nested layouts
    if path.startswith("data."):
        return _walk(obj, path[len("data."):])
    else:
        return _walk(obj, "data." + path)


def _ensure_log_file():
    """Create the output log file on first run with correct ownership and
    permissions. Failing silently here would hide problems, so we surface any
    errors to stderr — they'll show up in Wazuh's integrations.log."""
    try:
        if not os.path.exists(OUTPUT_LOG_PATH):
            # Touch the file
            with open(OUTPUT_LOG_PATH, "a"):
                pass
            # chown wazuh:wazuh — but only if those users exist on this host.
            # On some minimal containers they don't, so we tolerate failure.
            try:
                import pwd, grp
                uid = pwd.getpwnam(OUTPUT_LOG_OWNER[0]).pw_uid
                gid = grp.getgrnam(OUTPUT_LOG_OWNER[1]).gr_gid
                os.chown(OUTPUT_LOG_PATH, uid, gid)
            except Exception as e:
                _log("WARN", "could not chown {} to {}: {}".format(
                    OUTPUT_LOG_PATH, OUTPUT_LOG_OWNER, e))
            os.chmod(OUTPUT_LOG_PATH, OUTPUT_LOG_PERMS)
    except Exception as e:
        _log("ERROR", "could not create {}: {}".format(OUTPUT_LOG_PATH, e))


def _write_log_line(event):
    try:
        line = json.dumps(event, separators=(",", ":"), ensure_ascii=False)
        with open(OUTPUT_LOG_PATH, "a") as f:
            f.write(line + "\n")
    except Exception as e:
        # Include current file state in the error so operators can diagnose
        # without needing a separate ls -la. If the stat itself fails we
        # fall back to the bare error.
        details = ""
        try:
            st = os.stat(OUTPUT_LOG_PATH)
            import pwd, grp
            owner = pwd.getpwuid(st.st_uid).pw_name
            group = grp.getgrgid(st.st_gid).gr_name
            permissions = oct(st.st_mode & 0o777)
            details = " (current: owner={}:{}, permissions={})".format(owner, group, permissions)
        except Exception:
            pass
        _log("ERROR", "failed to write to {}{}: {}".format(
            OUTPUT_LOG_PATH, details, e))


# ============================================================================
# IOC NORMALIZATION & FILTERING
# ============================================================================

def _normalize_ioc(value, ioc_type):
    """Canonicalize an IOC value for consistent matching + dedup. Returns the
    normalized string, or None if the value is obviously invalid for its type.

    This is where we reject junk BEFORE it hits OpenCTI — saves round trips
    and avoids polluting logs with nonsense lookups."""
    if not isinstance(value, str):
        return None
    v = value.strip()

    if ioc_type in ("domain-name",):
        v = v.lower().rstrip(".")
        # Reject anything that doesn't have at least one dot or is just digits.
        if "." not in v or v.replace(".", "").isdigit():
            return None
        # Reject common file extensions masquerading as domains — the regex
        # fallback happily matches "svchost.exe" or "report.pdf" as "domains"
        # since they fit the shape. This is an incomplete list; extend as needed.
        NON_DOMAIN_SUFFIXES = {
            # Executables and binary formats
            "exe", "dll", "sys", "bat", "ps1", "vbs", "jar", "msi", "so",
            "o", "pyc", "bin", "elf", "apk", "dmg", "iso", "img",
            # Document formats
            "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt", "rtf",
            "odt", "ods",
            # Archives and compressed
            "zip", "rar", "7z", "tar", "gz", "bz2", "tgz", "xz",
            # Media
            "png", "jpg", "jpeg", "gif", "bmp", "ico", "svg", "webp",
            "mp3", "mp4", "avi", "mkv", "mov", "wav", "flac",
            # Data and config
            "log", "csv", "json", "xml", "yaml", "yml",
            "conf", "cfg", "ini", "tmp", "bak", "old",
            # Source code and scripts — NOT domains when they appear in URL
            # paths or command-line arguments
            "sh", "py", "rb", "pl", "lua", "c", "cpp", "h", "hpp",
            "js", "ts", "jsx", "tsx", "go", "rs", "java",
            # Server-side web scripts (commonly appear in URL paths)
            "php", "asp", "aspx", "jsp", "cgi",
        }
        tld = v.rsplit(".", 1)[-1]
        if tld in NON_DOMAIN_SUFFIXES:
            return None
        return v

    if ioc_type == "url":
        # Keep case in path/query (URLs are case-sensitive after the host), but
        # lowercase the scheme + host portion. Leave OpenCTI's pattern match
        # to handle the rest — we just want to skip trivially-broken URLs.
        if not v.lower().startswith(("http://", "https://")):
            return None
        return v

    if ioc_type in ("sha256", "sha1", "md5"):
        v = v.lower()
        expected = {"sha256": 64, "sha1": 40, "md5": 32}[ioc_type]
        if len(v) != expected or not all(c in "0123456789abcdef" for c in v):
            return None
        return v

    if ioc_type == "ipv4-addr":
        try:
            ip = ipaddress.IPv4Address(v)
        except ValueError:
            return None
        # Drop private, loopback, link-local, multicast, reserved, unspecified.
        if (ip.is_private or ip.is_loopback or ip.is_link_local
                or ip.is_multicast or ip.is_reserved or ip.is_unspecified):
            return None
        return str(ip)

    if ioc_type == "ipv6-addr":
        try:
            ip = ipaddress.IPv6Address(v)
        except ValueError:
            return None
        if (ip.is_private or ip.is_loopback or ip.is_link_local
                or ip.is_multicast or ip.is_reserved or ip.is_unspecified):
            return None
        return str(ip)

    if ioc_type == "email-addr":
        v = v.lower()
        return v if "@" in v else None

    if ioc_type == "windows-registry-key":
        # Canonicalize to match how OpenCTI stores registry keys. STIX uses
        # full hive names (HKEY_LOCAL_MACHINE, HKEY_CURRENT_USER) and backslash
        # separators. We accept both short and long hive names and normalize
        # to the long form.
        HIVE_MAP = {
            "HKLM":  "HKEY_LOCAL_MACHINE",
            "HKCU":  "HKEY_CURRENT_USER",
            "HKU":   "HKEY_USERS",
            "HKCR":  "HKEY_CLASSES_ROOT",
            "HKCC":  "HKEY_CURRENT_CONFIG",
        }
        # Normalize separators (the alert may have double backslashes from JSON
        # escaping already decoded; we want literal single backslashes).
        v = v.replace("/", "\\").strip()
        # Expand short hive prefix if present
        parts = v.split("\\", 1)
        if parts[0].upper() in HIVE_MAP:
            parts[0] = HIVE_MAP[parts[0].upper()]
            v = "\\".join(parts)
        # Reject empty or hive-only paths (too generic to query)
        if "\\" not in v:
            return None
        return v

    if ioc_type == "user-agent":
        # User-Agent strings are often noisy (browsers, bots, installers), so we
        # apply a light filter: keep case (OpenCTI matches them verbatim), but
        # reject obvious junk — too short, or a single token with no structure.
        # An indicator pattern containing a UA substring will still match via
        # OpenCTI's `contains` operator.
        if len(v) < 8:
            return None
        # Reject things like "curl" or "Mozilla" with no version — these match
        # way too broadly and are almost never the actual C2 UA you want.
        if " " not in v and "/" not in v:
            return None
        return v

    return v  # unknown types pass through untouched


def _is_allowlisted(value, ioc_type):
    """Final pre-query check — user's allowlists take precedence even over
    normalization. Return True to skip this IOC entirely."""
    if ioc_type in ("ipv4-addr", "ipv6-addr"):
        return value in ALLOWLIST_IPS
    if ioc_type == "domain-name":
        for d in ALLOWLIST_DOMAINS:
            d_norm = d.lower().rstrip(".")
            # Exact match or suffix match (.corp.com matches foo.corp.com)
            if value == d_norm.lstrip("."):
                return True
            if d_norm.startswith(".") and value.endswith(d_norm):
                return True
        return False
    return False


# ============================================================================
# IOC EXTRACTION — the hybrid strategy
# ============================================================================

def _extract_from_known_paths(alert):
    """Strategy 3a: pull IOCs from pre-mapped field paths based on rule.groups.

    Yields dicts with extraction_method='field_path' and the source path.
    High precision — these paths are known to contain IOCs."""
    groups = _get_dotted(alert, "rule.groups") or []
    seen_paths = set()
    for group in groups:
        for path, ioc_type in KNOWN_FIELD_PATHS.get(group, []):
            if path in seen_paths:
                continue  # same path appears in multiple groups — extract once
            seen_paths.add(path)
            raw_value = _get_dotted(alert, path)
            if raw_value is None:
                continue
            # Sysmon hashes come as a multi-algorithm blob like:
            #   "MD5=abc...,SHA256=def..."
            # Parse it into individual hash IOCs.
            if ioc_type == "mixed-hashes":
                for chunk in str(raw_value).split(","):
                    if "=" in chunk:
                        algo, h = chunk.split("=", 1)
                        algo = algo.strip().lower()
                        if algo in ("md5", "sha1", "sha256") \
                                and EXTRACT_IOC_TYPES.get(algo, False):
                            yield {"value": h.strip(), "type": algo,
                                   "extraction_method": "field_path",
                                   "source_field": path}
                continue
            if ioc_type == "filepath":
                # We capture this for context but don't query OpenCTI on it.
                continue
            if ioc_type == "registry-value-name":
                # Special case: the alert has the registry KEY in `syscheck.path`
                # and the VALUE NAME in `syscheck.value_name` as separate fields.
                # Threat intel typically references the combined form
                # "HKLM\...\Run\MaliciousEntry", so we join them here and emit
                # as a single windows-registry-key IOC.
                #
                # We only emit the combined form if both pieces exist. The key
                # alone was already extracted via the "syscheck.path" entry.
                key_path = _get_dotted(alert, "syscheck.path")
                if key_path and EXTRACT_IOC_TYPES.get("windows-registry-key", False):
                    combined = "{}\\{}".format(str(key_path).rstrip("\\"),
                                               str(raw_value))
                    yield {"value": combined, "type": "windows-registry-key",
                           "extraction_method": "field_path",
                           "source_field": "syscheck.path+value_name"}
                continue
            if EXTRACT_IOC_TYPES.get(ioc_type, False):
                yield {"value": str(raw_value), "type": ioc_type,
                       "extraction_method": "field_path",
                       "source_field": path}


def _extract_from_regex(alert):
    """Strategy 3b: regex scan over the alert's string content. Lower precision
    but catches IOCs in free-text fields like full_log or rule.description.

    Yields dicts with extraction_method='regex'."""
    # Flatten the whole alert into one string blob. JSON-dumping preserves
    # structure without us having to walk it ourselves.
    blob = json.dumps(alert)

    def _yield(pattern, ioc_type):
        if not EXTRACT_IOC_TYPES.get(ioc_type, False):
            return
        for match in pattern.findall(blob):
            yield {"value": match, "type": ioc_type,
                   "extraction_method": "regex",
                   "source_field": "<scanned>"}

    # Order matters: SHA256 (64 chars) before SHA1 (40) before MD5 (32),
    # because the shorter patterns would also match prefixes of longer hashes.
    # However we use \b...\b anchors so they shouldn't cross-match — this
    # ordering is defensive.
    for item in _yield(RE_SHA256,  "sha256"):      yield item
    for item in _yield(RE_SHA1,    "sha1"):        yield item
    for item in _yield(RE_MD5,     "md5"):         yield item
    for item in _yield(RE_IPV4,    "ipv4-addr"):   yield item
    for item in _yield(RE_IPV6,    "ipv6-addr"):   yield item
    for item in _yield(RE_URL,     "url"):         yield item
    for item in _yield(RE_DOMAIN,  "domain-name"): yield item
    for item in _yield(RE_EMAIL,   "email-addr"):  yield item


def extract_iocs(alert):
    """Run both extraction strategies, normalize/filter, deduplicate.
    Returns a list of IOC dicts ready for querying.

    Dedup key = (type, normalized_value). The FIRST occurrence wins — this
    means field_path extraction (which runs first) takes precedence over
    regex, so we keep the more-precise source_field info."""
    seen = {}    # key -> ioc dict
    skipped = []  # IOCs that were dropped pre-query (for optional logging)

    def _process(raw_ioc):
        value = _normalize_ioc(raw_ioc["value"], raw_ioc["type"])
        if value is None:
            # Normalization rejected it (invalid format, private IP, etc.)
            skipped.append({**raw_ioc, "reason": "normalization_rejected"})
            return
        if _is_allowlisted(value, raw_ioc["type"]):
            skipped.append({**raw_ioc, "value": value,
                            "reason": "allowlisted"})
            return
        key = (raw_ioc["type"], value)
        if key in seen:
            return  # already have this IOC from an earlier source
        seen[key] = {**raw_ioc, "value": value}

    for ioc in _extract_from_known_paths(alert):
        _process(ioc)
    for ioc in _extract_from_regex(alert):
        _process(ioc)

    return list(seen.values()), skipped


# ============================================================================
# OPENCTI QUERY
# ============================================================================

def query_opencti(ioc_value, api_key, hook_url):
    """Execute the GraphQL query against OpenCTI for a single IOC value.

    Returns (response_dict, error_string). On success: (dict, None).
    On failure: (None, "error message").

    Handles:
      - one retry on network errors / 5xx / timeouts (if RETRY_ON_FAILURE)
      - no retry on 4xx (config/auth errors won't fix themselves)
      - TLS verification toggle via VERIFY_TLS
    """
    if not VERIFY_TLS:
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    headers = {
        "Content-Type":  "application/json",
        "Authorization": "Bearer " + api_key,
    }
    body = {
        "query":     GRAPHQL_QUERY,
        "variables": {"ioc": ioc_value},
    }

    attempts = 2 if RETRY_ON_FAILURE else 1
    last_err = None

    for attempt in range(1, attempts + 1):
        try:
            resp = requests.post(
                hook_url, json=body, headers=headers,
                timeout=TIMEOUT_SECONDS, verify=VERIFY_TLS,
            )
            # 4xx — stop immediately, no retry
            if 400 <= resp.status_code < 500:
                return None, "HTTP {}: {}".format(resp.status_code, resp.text[:200])
            # 5xx — retry if we have budget
            if resp.status_code >= 500:
                last_err = "HTTP {}".format(resp.status_code)
                if attempt < attempts:
                    time.sleep(RETRY_BACKOFF_SECONDS)
                    continue
                return None, last_err
            # 2xx — parse JSON
            data = resp.json()
            # OpenCTI can return 200 with an "errors" array — treat as failure.
            if "errors" in data and data["errors"]:
                return None, "GraphQL errors: " + json.dumps(data["errors"])[:300]
            return data, None

        except (requests.Timeout, requests.ConnectionError) as e:
            last_err = "{}: {}".format(type(e).__name__, e)
            if attempt < attempts:
                time.sleep(RETRY_BACKOFF_SECONDS)
                continue
            return None, last_err
        except Exception as e:
            # Anything else (JSON decode errors, unexpected exceptions) — no retry.
            return None, "{}: {}".format(type(e).__name__, e)

    return None, last_err or "unknown error"


# ============================================================================
# RESPONSE PARSING — flatten GraphQL result into summary fields
# ============================================================================

# TLP ordering for "most restrictive wins" selection.
_TLP_RANK = {"CLEAR": 0, "WHITE": 0, "GREEN": 1, "AMBER": 2,
             "AMBER+STRICT": 3, "RED": 4}


def _parse_relationships(rel_edges):
    """Walk stixCoreRelationships edges and extract flat arrays by entity type.
    Returns a dict with keys: threat_actors, intrusion_sets, malware,
    campaigns, tools, attack_patterns (MITRE IDs), vulnerabilities,
    infrastructure, incidents, courses_of_action, identities, locations."""
    buckets = {
        "threat_actors":   [],
        "intrusion_sets":  [],
        "malware":         [],
        "campaigns":       [],
        "tools":           [],
        "mitre_ids":       [],
        "vulnerabilities": [],
        "infrastructure":  [],
        "incidents":       [],
        "courses_of_action": [],
        "identities":      [],
        "locations":       [],
    }
    for edge in rel_edges or []:
        target = (edge.get("node") or {}).get("to") or {}
        etype = target.get("entity_type")
        name  = target.get("name")
        if etype == "Threat-Actor" and name:
            buckets["threat_actors"].append(name)
        elif etype == "Intrusion-Set" and name:
            buckets["intrusion_sets"].append(name)
        elif etype == "Malware" and name:
            buckets["malware"].append(name)
        elif etype == "Campaign" and name:
            buckets["campaigns"].append(name)
        elif etype == "Tool" and name:
            buckets["tools"].append(name)
        elif etype == "Attack-Pattern":
            mid = target.get("x_mitre_id") or name
            if mid:
                buckets["mitre_ids"].append(mid)
        elif etype == "Vulnerability" and name:
            buckets["vulnerabilities"].append(name)
        elif etype == "Infrastructure" and name:
            buckets["infrastructure"].append(name)
        elif etype == "Incident" and name:
            buckets["incidents"].append(name)
        elif etype == "Course-Of-Action" and name:
            buckets["courses_of_action"].append(name)
        elif etype == "Identity" and name:
            buckets["identities"].append(name)
        elif etype and etype.startswith("Location") or etype in (
                "City", "Country", "Region", "Position", "Administrative-Area"):
            if name:
                buckets["locations"].append(name)
    # Deduplicate while preserving order
    for k in buckets:
        seen = set()
        deduped = []
        for item in buckets[k]:
            if item not in seen:
                seen.add(item)
                deduped.append(item)
        buckets[k] = deduped
    return buckets


def _select_tlp(markings):
    """Pick the most restrictive TLP from a list of objectMarking entries.
    Returns a string like 'CLEAR'/'GREEN'/'AMBER'/'RED' or None."""
    best = None
    best_rank = -1
    for m in markings or []:
        if m.get("definition_type") != "TLP":
            continue
        label = (m.get("definition") or "").replace("TLP:", "").strip().upper()
        rank = _TLP_RANK.get(label, -1)
        if rank > best_rank:
            best_rank = rank
            best = label
    return best


def _extract_authorship(node):
    """Pull authorship/provenance fields from a GraphQL node (indicator or
    observable). Returns a dict with flat top-level fields.

    STRICT DISTINCTION (per our spec):
    - `author` / `author_type` / `author_id` come ONLY from `createdBy`
      (the STIX-level author — the organization or individual that authored
      this intel as a matter of data provenance).
    - `creators` is always the OpenCTI-local user list from `creators[]`
      (these are platform users, not intel authors). Kept SEPARATE so
      decoder/rule writers don't conflate the two concepts.
    - `organizations` is from `objectOrganization` (multi-tenant access grants)."""
    out = {
        "author":        None,
        "author_type":   None,
        "author_id":     None,
        "creators":      [],
        "organizations": [],
    }
    if not node:
        return out

    cb = node.get("createdBy")
    if cb and isinstance(cb, dict):
        out["author"]      = cb.get("name")
        out["author_type"] = cb.get("identity_class")
        out["author_id"]   = cb.get("standard_id") or cb.get("id")

    for c in (node.get("creators") or []):
        name = c.get("name") if isinstance(c, dict) else None
        if name and name not in out["creators"]:
            out["creators"].append(name)

    for o in (node.get("objectOrganization") or []):
        name = o.get("name") if isinstance(o, dict) else None
        if name and name not in out["organizations"]:
            out["organizations"].append(name)

    return out


def _collect_relationship_authors(rel_edges):
    """Walk the relationships and collect distinct STIX authors (`createdBy`)
    attached to each edge. Returns a deduplicated list of author names.
    Empty list if no relationship has a createdBy set."""
    names = []
    seen = set()
    for edge in rel_edges or []:
        node = edge.get("node") or {}
        cb = node.get("createdBy")
        if cb and isinstance(cb, dict):
            name = cb.get("name")
            if name and name not in seen:
                seen.add(name)
                names.append(name)
    return names


def _collect_report_authors(report_edges):
    """Walk the reports and collect distinct STIX authors (`createdBy`) on
    each report node. Returns a deduplicated list of author names."""
    names = []
    seen = set()
    for edge in report_edges or []:
        node = edge.get("node") or {}
        cb = node.get("createdBy")
        if cb and isinstance(cb, dict):
            name = cb.get("name")
            if name and name not in seen:
                seen.add(name)
                names.append(name)
    return names


def _merge_authorship(primary, secondary):
    """Merge authorship from a secondary source (e.g. observable) into primary
    (e.g. indicator). The primary `author`/`author_type`/`author_id` are kept
    (indicator authorship wins for the top-level scalar fields), but scalar
    fields are also captured in a separate `also_authored_by` entry if the
    secondary source has different authorship. Array fields (creators,
    organizations) are union-merged with dedup.

    This supports the spec: when BOTH an indicator and an observable match
    the same IOC, both authorships are surfaced — indicator-level as primary,
    observable-level in a separate field so nothing is lost."""
    merged = dict(primary)

    # If secondary has a different STIX author, preserve it separately
    if secondary.get("author") and secondary["author"] != primary.get("author"):
        merged["also_authored_by"] = {
            "author":      secondary.get("author"),
            "author_type": secondary.get("author_type"),
            "author_id":   secondary.get("author_id"),
            "source":      "observable",
        }

    # Union-merge creators and organizations
    for key in ("creators", "organizations"):
        for v in secondary.get(key) or []:
            if v not in merged[key]:
                merged[key].append(v)

    return merged


def build_summary(ioc, gql_response):
    """Turn the raw GraphQL response into a flat summary + raw payload.
    This is where we make decoder/rule authoring easy downstream — every
    interesting field is at a predictable top-level path.

    AUTHORSHIP HANDLING:
    When an indicator match exists, the indicator's authorship populates the
    top-level `author` / `author_type` / `author_id` scalar fields. If an
    observable ALSO matches the same IOC and has a different STIX author,
    that secondary authorship is preserved under `also_authored_by`. Both
    sources' `creators` and `organizations` arrays are union-merged. This
    ensures no provenance information is lost when both arms match."""
    data = (gql_response or {}).get("data") or {}
    ind_edges = ((data.get("indicators") or {}).get("edges")) or []
    obs_edges = ((data.get("stixCyberObservables") or {}).get("edges")) or []

    # Default summary for a miss — includes authorship placeholders so decoder
    # writers always see the same set of top-level fields regardless of outcome.
    summary = {
        "match_type":           "no_match",
        "severity_score":       None,
        "tlp":                  None,
        "mitre_ids":            [],
        "threat_actors":        [],
        "intrusion_sets":       [],
        "malware":              [],
        "campaigns":            [],
        "tools":                [],
        "vulnerabilities":      [],
        "infrastructure":       [],
        "labels":               [],
        "indicator_summary":    None,
        "reports":              [],
        # Authorship / provenance (always present, null/empty on no-match)
        "author":               None,
        "author_type":          None,
        "author_id":            None,
        "creators":             [],
        "organizations":        [],
        "relationship_authors": [],
        "report_authors":       [],
    }

    if ind_edges:
        # Preferred: indicator hit. If multiple, use the first (highest-score
        # indicators tend to be returned first, but OpenCTI doesn't guarantee
        # ordering — sophisticated consumers can walk all of them via
        # raw_response).
        node = ind_edges[0]["node"]
        rel_edges = ((node.get("stixCoreRelationships") or {}).get("edges")) or []
        report_edges = ((node.get("reports") or {}).get("edges")) or []
        rels = _parse_relationships(rel_edges)
        score = node.get("x_opencti_score") or 0
        conf  = node.get("confidence") or 0
        labels = [l.get("value") for l in (node.get("objectLabel") or [])
                  if l.get("value")]
        reports = [
            {"id":           r["node"].get("id"),
             "name":         r["node"].get("name"),
             "published":    r["node"].get("published"),
             "report_types": r["node"].get("report_types") or [],
             # Per-report author too — analysts often want to see report-level
             # attribution separate from indicator-level
             "author":       ((r["node"].get("createdBy") or {}).get("name")
                              if r["node"].get("createdBy") else None)}
            for r in report_edges
        ]
        authorship = _extract_authorship(node)

        summary.update({
            "match_type":           "indicator_hit_valid",
            "severity_score":       round(score * (conf / 100.0)) if conf else score,
            "tlp":                  _select_tlp(node.get("objectMarking")),
            "mitre_ids":            rels["mitre_ids"],
            "threat_actors":        rels["threat_actors"],
            "intrusion_sets":       rels["intrusion_sets"],
            "malware":              rels["malware"],
            "campaigns":            rels["campaigns"],
            "tools":                rels["tools"],
            "vulnerabilities":      rels["vulnerabilities"],
            "infrastructure":       rels["infrastructure"],
            "labels":               labels,
            "reports":              reports,
            "relationship_authors": _collect_relationship_authors(rel_edges),
            "report_authors":       _collect_report_authors(report_edges),
            "indicator_summary": {
                "id":              node.get("id"),
                "standard_id":     node.get("standard_id"),
                "name":            node.get("name"),
                "pattern":         node.get("pattern"),
                "pattern_type":    node.get("pattern_type"),
                "valid_from":      node.get("valid_from"),
                "valid_until":     node.get("valid_until"),
                "x_opencti_score": score,
                "confidence":      conf,
                "revoked":         node.get("revoked"),
            },
        })
        # Layer in authorship from the indicator (primary)
        summary.update(authorship)

        # If the observable arm ALSO matched the same IOC, merge its
        # authorship in too — we want to preserve both sources' provenance
        # without letting observable authorship overwrite the indicator's
        # primary fields. `_merge_authorship` handles this correctly.
        if obs_edges:
            obs_authorship = _extract_authorship(obs_edges[0]["node"])
            merged = _merge_authorship(
                {"author":        summary["author"],
                 "author_type":   summary["author_type"],
                 "author_id":     summary["author_id"],
                 "creators":      summary["creators"],
                 "organizations": summary["organizations"]},
                obs_authorship,
            )
            summary["author"]         = merged["author"]
            summary["author_type"]    = merged["author_type"]
            summary["author_id"]      = merged["author_id"]
            summary["creators"]       = merged["creators"]
            summary["organizations"]  = merged["organizations"]
            if "also_authored_by" in merged:
                summary["also_authored_by"] = merged["also_authored_by"]

    elif obs_edges:
        # Fallback: observable exists but no promoted indicator.
        node = obs_edges[0]["node"]
        rel_edges = ((node.get("stixCoreRelationships") or {}).get("edges")) or []
        report_edges = ((node.get("reports") or {}).get("edges")) or []
        rels = _parse_relationships(rel_edges)
        labels = [l.get("value") for l in (node.get("objectLabel") or [])
                  if l.get("value")]
        reports = [
            {"id":           r["node"].get("id"),
             "name":         r["node"].get("name"),
             "published":    r["node"].get("published"),
             "report_types": r["node"].get("report_types") or [],
             "author":       ((r["node"].get("createdBy") or {}).get("name")
                              if r["node"].get("createdBy") else None)}
            for r in report_edges
        ]
        authorship = _extract_authorship(node)

        summary.update({
            "match_type":           "observable_only",
            "severity_score":       node.get("x_opencti_score"),
            "tlp":                  _select_tlp(node.get("objectMarking")),
            "mitre_ids":            rels["mitre_ids"],
            "threat_actors":        rels["threat_actors"],
            "intrusion_sets":       rels["intrusion_sets"],
            "malware":              rels["malware"],
            "campaigns":            rels["campaigns"],
            "tools":                rels["tools"],
            "vulnerabilities":      rels["vulnerabilities"],
            "infrastructure":       rels["infrastructure"],
            "labels":               labels,
            "reports":              reports,
            "relationship_authors": _collect_relationship_authors(rel_edges),
            "report_authors":       _collect_report_authors(report_edges),
        })
        summary.update(authorship)

    return summary


# ============================================================================
# EVENT ASSEMBLY — the final log line
# ============================================================================
def _build_context(alert, ioc):
    """Capture per-IOC contextual fields from the original alert that help
    analysts act on a match without going back to alerts.json. The fields
    we pull depend on the IOC type — for file hashes we want the file path
    on disk, for network IOCs we want flow context, etc.

    Returns a dict (possibly empty). Empty dicts are kept rather than
    omitted so the field shape is consistent across all events — important
    for OpenSearch dynamic mapping (recall the indicator_summary lesson)."""
    ctx = {}

    # File hash IOCs — pull the on-disk path so the analyst knows which
    # file triggered the match. Covers FIM (syscheck) and Suricata fileinfo.
    if ioc["type"] in ("md5", "sha1", "sha256"):
        path = (_get_dotted(alert, "syscheck.path")
                or _get_dotted(alert, "data.fileinfo.filename"))
        if path:
            ctx["file_path"] = str(path)
        
        # File ownership at time of detection
        user = _get_dotted(alert, "syscheck.uname_after")
        group = _get_dotted(alert, "syscheck.gname_after")
        if user: ctx["file_owner"] = str(user)
        if group: ctx["file_group"] = str(group)
        
        # Process that wrote/modified the file (when audit subsystem provides it)
        proc_name = _get_dotted(alert, "syscheck.audit.process.name")
        proc_user = _get_dotted(alert, "syscheck.audit.user.name")
        if proc_name: ctx["written_by_process"] = str(proc_name)
        if proc_user: ctx["written_by_user"] = str(proc_user)
        
        # File size and modification info — useful for triage
        size = _get_dotted(alert, "syscheck.size_after")
        if size: ctx["file_size"] = str(size)

    # Network IOCs — capture the flow direction (was this src or dst?)
    # so analysts don't have to figure it out from source_field alone.
    elif ioc["type"] in ("ipv4-addr", "ipv6-addr", "domain-name"):
        sf = ioc.get("source_field", "")
        
        # ioc_position tells the analyst where in the connection the matched
        # IOC appeared — NOT the traffic direction in a security sense.
        # The IOC could be the source endpoint (likely outbound from peer's
        # perspective) or destination endpoint (likely inbound to peer).
        if any(token in sf for token in ("src", "source")):
            ctx["ioc_position"] = "source"
            peer_ip = (_get_dotted(alert, "data.dstip")
                    or _get_dotted(alert, "data.dest_ip")
                    or _get_dotted(alert, "data.win.eventdata.destinationIp"))
            peer_port = (_get_dotted(alert, "data.dstport")
                        or _get_dotted(alert, "data.dest_port")
                        or _get_dotted(alert, "data.win.eventdata.destinationPort"))
        elif any(token in sf for token in ("dst", "dest", "destination")):
            ctx["ioc_position"] = "destination"
            peer_ip = (_get_dotted(alert, "data.srcip")
                    or _get_dotted(alert, "data.src_ip")
                    or _get_dotted(alert, "data.win.eventdata.sourceIp"))
            peer_port = (_get_dotted(alert, "data.srcport")
                        or _get_dotted(alert, "data.src_port")
                        or _get_dotted(alert, "data.win.eventdata.sourcePort"))
        else:
            peer_ip = peer_port = None

        if peer_ip:
            ctx["peer_ip"] = str(peer_ip)
        if peer_port:
            ctx["peer_port"] = str(peer_port)

        # Transport protocol (TCP, UDP, ICMP) — try each source's field name.
        proto = (_get_dotted(alert, "data.proto")
                or _get_dotted(alert, "data.protocol")
                or _get_dotted(alert, "data.win.eventdata.protocol"))
        if proto:
            ctx["protocol"] = str(proto)

        # Application-layer protocol (HTTP, DNS, TLS, SSH, etc.) — Suricata only.
        # No equivalent for Wazuh native or Sysmon, so this is best-effort.
        app_proto = _get_dotted(alert, "data.app_proto")
        if app_proto:
            ctx["app_protocol"] = str(app_proto)

        # Suricata flow_id — uniquely identifies a TCP/UDP flow across
        # multiple log lines (alert + http + tls + dns events for one flow
        # share the same id). Lets analysts pivot to the full flow context.
        flow_id = _get_dotted(alert, "data.flow_id")
        if flow_id:
            ctx["flow_id"] = str(flow_id)

        # DNS-specific refinement — when a domain IOC matches inside a
        # Suricata DNS event, the src/dest IPs above represent the DNS
        # resolver and the client, not malicious infrastructure. The
        # actually interesting datum is what the domain RESOLVED to, since
        # OpenCTI may also have intel on those IPs. We capture up to 5
        # resolved values (rdata) to keep the event size bounded.

        if ioc["type"] == "domain-name":
            dns_answers = _get_dotted(alert, "data.dns.answers")
            if isinstance(dns_answers, list) and dns_answers:
                # answers is a list of {rrname, rrtype, ttl, rdata}
                rdatas = [a.get("rdata") for a in dns_answers if isinstance(a, dict) and a.get("rdata")]
                if rdatas:
                    ctx["dns_resolved_to"] = rdatas[:5]  # cap at 5 to keep size sane
    
    elif ioc["type"] == "url":
        method = _get_dotted(alert, "data.http.http_method")
        ua = _get_dotted(alert, "data.http.http_user_agent")
        status = _get_dotted(alert, "data.http.status")
        if method: ctx["http_method"] = str(method)
        if ua: ctx["user_agent"] = str(ua)
        if status: ctx["http_status"] = str(status)

    return ctx

def _correlation_id(alert, ioc):
    """Generate a stable identifier that's the same across every enrichment
    event for the same <agent, ioc-type, ioc-value> triplet. Lets analysts
    pivot in the dashboard — "show me everything tied to correlation_id=X"
    returns the full history of this IOC on this host across time.

    The hash is intentionally short (16 hex chars = 64 bits) — long enough
    to be effectively unique in any realistic SIEM dataset, short enough to
    fit comfortably in dashboard columns and URLs.

    Inputs that go into the hash:
      - agent identity (id preferred, name as fallback)
      - IOC type (so md5=abc and sha1=abc don't collide)
      - IOC value (the actual matched indicator)

    Inputs that DO NOT go into the hash:
      - timestamps (would defeat the purpose)
      - source_alert_id (every alert is unique; we want grouping ACROSS alerts)
      - severity_score (changes when OpenCTI is updated)
    """
    agent = (_get_dotted(alert, "agent.id")
             or _get_dotted(alert, "agent.name")
             or "unknown")
    seed = "{}|{}|{}".format(agent, ioc["type"], ioc["value"])
    return hashlib.sha1(seed.encode("utf-8")).hexdigest()[:16]

def build_event(alert, ioc, summary, gql_response, error=None):
    """Compose the single-line JSON event we write to opencti.log.

    Structure is stable and predictable so your custom decoder can map each
    field mechanically — no nested walks required in the decoder/rule layer."""
    event = {
        "timestamp":                _now_iso(),
        "event_timestamp":          _get_dotted(alert, "timestamp"),
        "integration":              "opencti",
        "source_alert_id":          _get_dotted(alert, "id"),
        "source_rule_id":           _get_dotted(alert, "rule.id"),
        "source_rule_description":  _get_dotted(alert, "rule.description"),
        "source_rule_level":        _get_dotted(alert, "rule.level"),
        "source_agent":             _get_dotted(alert, "agent.name")
                                       or _get_dotted(alert, "agent.id"),
        "source_groups":            _get_dotted(alert, "rule.groups") or [],
        "ioc": {
            "value":             ioc["value"],
            "type":              ioc["type"],
            "extraction_method": ioc["extraction_method"],
            "source_field":      ioc["source_field"],
        },
        "context": _build_context(alert, ioc),
        "correlation_id":       _correlation_id(alert, ioc),
    }
    # Merge in the summary (match_type, mitre_ids, etc.)
    event.update(summary)

    if error:
        event["match_type"]    = "error"
        event["error_message"] = error

    if INCLUDE_RAW_RESPONSE and gql_response is not None:
        event["raw_response"] = gql_response

    # Strip null-valued nested objects that cause OpenSearch dynamic mapping
    # conflicts. If indicator_summary is None for observable_only matches but
    # an object for indicator_hit_valid matches, OpenSearch locks the field
    # type on first ingestion and silently drops conflicting documents.
    if event.get("indicator_summary") is None:
        event.pop("indicator_summary", None)

    return event

def build_skipped_event(alert, skipped):
    """Build an event for an IOC that was filtered out pre-query (private IP,
    allowlisted, malformed format, file extension masquerading as domain, etc).
    Only written when LOG_MISSES is True.

    match_type will be:
      - 'skipped_allowlist'  if the user's allowlist matched
      - 'skipped_filtered'   for everything else the normalizer rejected
                             (private IPs, bad hashes, file extensions, etc)
    The specific reason is always in skip_reason for finer-grained rules."""
    return {
        "timestamp":               _now_iso(),
        "event_timestamp":         _get_dotted(alert, "timestamp"),
        "integration":             "opencti",
        "source_alert_id":         _get_dotted(alert, "id"),
        "source_rule_id":          _get_dotted(alert, "rule.id"),
        "source_rule_description": _get_dotted(alert, "rule.description"),
        "source_rule_level":       _get_dotted(alert, "rule.level"),
        "source_agent":            _get_dotted(alert, "agent.name")
                                      or _get_dotted(alert, "agent.id"),
        "source_groups":           _get_dotted(alert, "rule.groups") or [],
        "ioc": {
            "value":             skipped["value"],
            "type":              skipped["type"],
            "extraction_method": skipped["extraction_method"],
            "source_field":      skipped["source_field"],
        },
        "context":         _build_context(alert, skipped),
        "correlation_id":  _correlation_id(alert, skipped),
        "match_type":              "skipped_allowlist"
                                      if skipped.get("reason") == "allowlisted"
                                      else "skipped_filtered",
        "skip_reason":             skipped.get("reason"),
    }


# ============================================================================
# MAIN
# ============================================================================

def main(argv):
    # --- Parse Wazuh's arguments -------------------------------------------
    # Wazuh passes: sys.argv[1]=alert_file, [2]=api_key, [3]=hook_url
    # Any additional args are optional flags we don't use here.
    if len(argv) < 4:
        _log("ERROR", "usage: custom-opencti <alert_file> <api_key> <hook_url>")
        return 1

    alert_file = argv[1]
    api_key    = argv[2]
    hook_url   = argv[3]

    # --- Load the alert -----------------------------------------------------
    try:
        with open(alert_file, "r") as f:
            alert = json.load(f)
    except Exception as e:
        _log("ERROR", "could not read alert file {}: {}".format(alert_file, e))
        return 1

    _ensure_log_file()

    # --- Extract IOCs -------------------------------------------------------
    try:
        iocs, skipped = extract_iocs(alert)
    except Exception as e:
        _log("ERROR", "IOC extraction failed: {}\n{}".format(e, traceback.format_exc()))
        return 1

    # Optional: log the skips (private IPs, allowlisted, malformed) so you
    # can see what the pre-filter is dropping.
    if LOG_MISSES:
        for sk in skipped:
            try:
                _write_log_line(build_skipped_event(alert, sk))
            except Exception as e:
                _log("WARN", "failed to log skipped ioc: {}".format(e))

    if not iocs:
        # No candidate IOCs survived extraction + filtering. We don't write
        # anything here because there's nothing IOC-shaped to report on.
        return 0

    # --- Query OpenCTI for each IOC ----------------------------------------
    for ioc in iocs:
        try:
            gql_response, err = query_opencti(ioc["value"], api_key, hook_url)

            if err:
                # Query failed. Log an error-type event and move on — we never
                # want to stop the loop because one IOC's query blew up.
                event = build_event(alert, ioc, build_summary(ioc, None),
                                    gql_response=None, error=err)
                _write_log_line(event)
                continue

            summary = build_summary(ioc, gql_response)

            # Respect LOG_MISSES for no_match events.
            if summary["match_type"] == "no_match" and not LOG_MISSES:
                continue

            event = build_event(alert, ioc, summary, gql_response)
            _write_log_line(event)

        except Exception as e:
            # Truly unexpected failure on this specific IOC. Log and continue.
            _log("ERROR", "unhandled error processing {}: {}\n{}".format(
                ioc.get("value"), e, traceback.format_exc()))
            try:
                event = build_event(alert, ioc,
                                    build_summary(ioc, None),
                                    gql_response=None,
                                    error="{}: {}".format(type(e).__name__, e))
                _write_log_line(event)
            except Exception:
                pass

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
