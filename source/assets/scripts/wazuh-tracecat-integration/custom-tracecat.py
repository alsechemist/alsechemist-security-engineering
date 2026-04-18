# Wazuh to Tracecat SOAR Integration Script
# Based on the Shuffle integration by Shuffle, AS. <frikky@shuffler.io>
# Adapted for Tracecat SOAR by using Tracecat Webhook endpoints.
#
# Created and Developed by Alsechemist. A.K.A Syed Golam Abid
#
# This program is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public
# License (version 2) as published by the FSF - Free Software
# Foundation.
#
# Error Codes:
#   1 - Module 'requests' not found
#   2 - Incorrect input arguments
#   6 - Alert file does not exist
#   7 - Error parsing JSON alert or options

# =======================================================================
# CONFIGURATION GUIDE — ossec.conf integration blocks
# =======================================================================
#
# Place this script at:   /var/ossec/integrations/custom-tracecat
# Set permissions:
#   sudo chmod 750 /var/ossec/integrations/custom-tracecat
#   sudo chown root:wazuh /var/ossec/integrations/custom-tracecat
#
# -----------------------------------------------------------------------
# MODE 1 — WITHOUT API KEY AUTHENTICATION (webhook is open/public)
# -----------------------------------------------------------------------
# Use this if your Tracecat webhook has no API key configured.
# The <api_key> tag is omitted entirely.
#
# <integration>
#   <n>custom-tracecat</n>
#   <hook_url>http://<TRACECAT_IP>/api/webhooks/<WORKFLOW_ID>/<SECRET></hook_url>
#   <level>3</level>
#   <alert_format>json</alert_format>
# </integration>
#
# -----------------------------------------------------------------------
# MODE 2 — WITH API KEY AUTHENTICATION (recommended for production)
# -----------------------------------------------------------------------
# Use this if your Tracecat webhook has an API key enabled.
#
# HOW TO GET YOUR API KEY FROM TRACECAT:
#   1. Open your Tracecat workflow in the UI
#   2. Click on the Trigger action node
#   3. Scroll to the "API key" section
#   4. Click "Generate API key"
#   5. Copy the value immediately — it is only shown once
#   6. The UI will confirm: "Webhook senders must pass the key
#      in the x-tracecat-api-key header" — this script does that
#      automatically when <api_key> is present below.
#
# <integration>
#   <n>custom-tracecat</n>
#   <hook_url>http://<TRACECAT_IP>/api/webhooks/<WORKFLOW_ID>/<SECRET></hook_url>
#   <api_key>tc_sk_<YOUR_KEY_HERE></api_key>
#   <level>3</level>
#   <alert_format>json</alert_format>
# </integration>
#
# -----------------------------------------------------------------------
# MULTIPLE WORKFLOWS — one <integration> block per Tracecat workflow
# -----------------------------------------------------------------------
#
# <integration>
#   <n>custom-tracecat</n>
#   <hook_url>http://192.168.250.12/api/webhooks/wf_AAA/secret_AAA</hook_url>
#   <api_key>tc_sk_KEY_FOR_WORKFLOW_AAA</api_key>
#   <level>3</level>
#   <alert_format>json</alert_format>
# </integration>
#
# <integration>
#   <n>custom-tracecat</n>
#   <hook_url>http://192.168.250.12/api/webhooks/wf_BBB/secret_BBB</hook_url>
#   <api_key>tc_sk_KEY_FOR_WORKFLOW_BBB</api_key>
#   <rule_id>5503,5551,5712,31166</rule_id>
#   <alert_format>json</alert_format>
# </integration>
#
# <integration>
#   <n>custom-tracecat</n>
#   <hook_url>http://192.168.250.12/api/webhooks/wf_CCC/secret_CCC</hook_url>
#   <api_key>tc_sk_KEY_FOR_WORKFLOW_CCC</api_key>
#   <group>authentication_failed</group>
#   <level>5</level>
#   <alert_format>json</alert_format>
# </integration>
#
# NOTE: Each Tracecat workflow has its own independent API key.
#       Each <integration> block must carry the key for its own workflow.
# =======================================================================
#
# LOGGING
# =======================================================================
# This script writes a structured JSON log for every execution to:
#   /var/ossec/logs/tracecat.log
#
# Every log entry is a single JSON object on one line (JSON Lines format),
# making it easy to parse, grep, and ingest into any log analysis tool.
#
# Log file ownership is set to wazuh:wazuh automatically on first run.
# If the script cannot create or write the log file it will print a
# warning to stderr and continue — logging failure never blocks alerts.
#
# To follow the log in real time:
#   sudo tail -f /var/ossec/logs/tracecat.log
#
# To pretty-print the last entry:
#   sudo tail -1 /var/ossec/logs/tracecat.log | python3 -m json.tool
#
# To filter only errors:
#   sudo grep '"level": "ERROR"' /var/ossec/logs/tracecat.log
#
# To filter only successful deliveries:
#   sudo grep '"event": "alert_sent"' /var/ossec/logs/tracecat.log
# =======================================================================

import json
import os
import pwd as pwd_module
import grp
import sys
import traceback
from datetime import datetime, timezone

# Exit error codes
ERR_NO_REQUEST_MODULE = 1
ERR_BAD_ARGUMENTS     = 2
ERR_FILE_NOT_FOUND    = 6
ERR_INVALID_JSON      = 7

try:
    import requests
except ModuleNotFoundError:
    print("No module 'requests' found. Install: pip install requests")
    sys.exit(ERR_NO_REQUEST_MODULE)

# ---------------------------------------------------------------------------
# Global configuration
# ---------------------------------------------------------------------------

debug_enabled = False
pwd = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

# Wazuh shared integrations log (standard — always written)
LOG_FILE          = f'{pwd}/logs/integrations.log'

# Tracecat dedicated structured JSON log
TRACECAT_LOG_FILE = f'{pwd}/logs/tracecat.log'
TRACECAT_LOG_USER  = 'wazuh'
TRACECAT_LOG_GROUP = 'wazuh'

ALERT_INDEX   = 1   # args[1] — path to alert JSON file written by Wazuh
API_KEY_INDEX = 2   # args[2] — Tracecat API key from <api_key> (optional)
WEBHOOK_INDEX = 3   # args[3] — Tracecat webhook URL from <hook_url>

# ---------------------------------------------------------------------------
# Rule IDs to suppress (recursion/noise guard)
# ---------------------------------------------------------------------------
SKIP_RULE_IDS = [
    '87924', '87900', '87901', '87902',
    '87903', '87904', '86001', '86002',
    '86003', '87932', '80710', '87929',
    '87928', '5710',
]

# ---------------------------------------------------------------------------
# Severity mapping
# ---------------------------------------------------------------------------
SEVERITY_LABELS = {
    1: 'low',
    2: 'medium',
    3: 'high',
}


# ===========================================================================
# STRUCTURED JSON LOGGER
# ===========================================================================

def _ensure_log_file():
    """
    Create /var/ossec/logs/tracecat.log if it does not exist and set
    ownership to wazuh:wazuh with permissions 660.
    Silently swallows any OS errors so logging never blocks alert delivery.
    """
    try:
        if not os.path.exists(TRACECAT_LOG_FILE):
            with open(TRACECAT_LOG_FILE, 'a'):
                pass
        # Set ownership to wazuh:wazuh
        try:
            uid = pwd_module.getpwnam(TRACECAT_LOG_USER).pw_uid
            gid = grp.getgrnam(TRACECAT_LOG_GROUP).gr_gid
            os.chown(TRACECAT_LOG_FILE, uid, gid)
        except (KeyError, PermissionError):
            pass  # User may not exist in test environments
        # Set permissions to 660 (rw-rw----)
        os.chmod(TRACECAT_LOG_FILE, 0o660)
    except Exception:
        pass


def log(level: str, event: str, **kwargs) -> None:
    """
    Write a single structured JSON log entry to tracecat.log.

    Every entry always contains:
      timestamp  — ISO-8601 UTC time of the log entry
      level      — INFO | WARNING | ERROR
      event      — short snake_case identifier of what happened
      **kwargs   — any additional context fields relevant to the event

    Parameters
    ----------
    level : str
        Log level: 'INFO', 'WARNING', or 'ERROR'
    event : str
        Short identifier, e.g. 'alert_sent', 'alert_suppressed', 'http_error'
    **kwargs
        Any additional key-value context to include in the log entry.
    """
    entry = {
        'integration': 'tracecat',   # Fixed identifier — used by Wazuh decoder
        'timestamp':   datetime.now(timezone.utc).isoformat(),
        'level':       level,
        'event':       event,
    }
    entry.update(kwargs)

    try:
        _ensure_log_file()
        with open(TRACECAT_LOG_FILE, 'a') as f:
            f.write(json.dumps(entry) + '\n')
    except Exception as e:
        # Logging must never crash the script — print to stderr and move on
        print(f'[tracecat] WARNING: Could not write to log file: {e}', file=sys.stderr)

    # Also print to stdout when debug mode is on
    if debug_enabled:
        print(json.dumps(entry, indent=2))


# Convenience wrappers
def log_info(event: str, **kwargs):
    log('INFO', event, **kwargs)

def log_warning(event: str, **kwargs):
    log('WARNING', event, **kwargs)

def log_error(event: str, **kwargs):
    log('ERROR', event, **kwargs)


# ---------------------------------------------------------------------------
# Legacy debug() — kept for internal step tracing, writes to integrations.log
# ---------------------------------------------------------------------------

def debug(msg: str) -> None:
    """Print and append msg to integrations.log only when debug is active."""
    if debug_enabled:
        print(msg)
        with open(LOG_FILE, 'a') as f:
            f.write(msg + '\n')


# ===========================================================================
# Entry point
# ===========================================================================

def main(args):
    """
    Called by Wazuh. Validates arguments, logs the invocation, then
    hands off to process_args().

    Wazuh always calls the script with these positional arguments:
      args[1] = path to the alert JSON file
      args[2] = API key from <api_key> in ossec.conf
                → present  : sent as x-tracecat-api-key header
                → absent   : Wazuh passes 'None' — no auth header is sent
      args[3] = the <hook_url> value from ossec.conf
      args[4] = 'debug' (optional — enables verbose logging)
      args[5] = path to options file (optional)
    """
    global debug_enabled

    try:
        bad_arguments = False

        if len(args) >= 4:
            msg = '{0} {1} {2} {3} {4}'.format(
                args[1],
                args[2],
                args[3],
                args[4] if len(args) > 4 else '',
                args[5] if len(args) > 5 else '',
            )
            debug_enabled = len(args) > 4 and args[4] == 'debug'
        else:
            msg = '# ERROR: Wrong arguments'
            bad_arguments = True

        # Always write to the shared Wazuh integrations log
        with open(LOG_FILE, 'a') as f:
            f.write(msg + '\n')

        if bad_arguments:
            log_error(
                'bad_arguments',
                detail='Script received fewer than 4 arguments from Wazuh.',
                received=args[1:],
            )
            debug('# ERROR: Exiting, bad arguments. Received: %s' % args)
            sys.exit(ERR_BAD_ARGUMENTS)

        log_info('script_started', webhook=args[WEBHOOK_INDEX] if len(args) > WEBHOOK_INDEX else 'unknown')
        process_args(args)

    except SystemExit:
        raise
    except Exception as e:
        log_error(
            'unhandled_exception',
            exception=type(e).__name__,
            detail=str(e),
            traceback=traceback.format_exc(),
        )
        debug(str(e))
        raise


# ===========================================================================
# Core pipeline
# ===========================================================================

def process_args(args) -> None:
    """
    Core pipeline:
      1. Extract the alert file path, api key, and webhook URL from args.
      2. Load optional options file if provided.
      3. Load the Wazuh alert from disk.
      4. Check the recursion noise filter.
      5. Build the Tracecat payload.
      6. POST it to the webhook URL.
    """
    debug('# Running Tracecat integration script')

    alert_file_location   = args[ALERT_INDEX]
    webhook               = args[WEBHOOK_INDEX]
    options_file_location = ''

    # Extract API key — Wazuh passes the literal string 'None' when
    # <api_key> is not present in ossec.conf, so we treat that as empty.
    api_key = args[API_KEY_INDEX] if args[API_KEY_INDEX] != 'None' else ''

    for idx in range(4, len(args)):
        if args[idx].endswith('options'):
            options_file_location = args[idx]
            break

    json_options = get_json_options(options_file_location)
    debug(f"# Options: '{options_file_location}' -> {json_options}")

    json_alert = get_json_alert(alert_file_location)
    debug(f"# Alert loaded from '{alert_file_location}'")

    rule    = json_alert.get('rule', {})
    rule_id = rule.get('id', '')
    level   = rule.get('level', 0)
    groups  = rule.get('groups', [])
    agent   = json_alert.get('agent', {}).get('name', 'N/A')

    # Recursion guard
    if rule_id in SKIP_RULE_IDS:
        log_info(
            'alert_suppressed',
            reason='recursion_noise_filter',
            rule_id=rule_id,
            agent=agent,
        )
        debug('# Suppressed (recursion noise) rule_id=%s' % rule_id)
        return

    debug('# Building payload')
    msg = generate_msg(json_alert, json_options)

    if not msg:
        log_warning('payload_empty', rule_id=rule_id, agent=agent)
        return

    debug('# Sending to Tracecat: %s' % webhook)
    debug('# API key authentication: %s' % ('enabled' if api_key else 'disabled'))

    log_info(
        'alert_dispatching',
        rule_id=rule_id,
        rule_level=level,
        rule_groups=groups,
        agent=agent,
        webhook=webhook,
        api_key_used=bool(api_key),
    )

    send_msg(msg, webhook, api_key, json_alert)


# ===========================================================================
# Helpers
# ===========================================================================

def generate_msg(alert: dict, options: dict) -> str:
    """
    Build a Tracecat-compatible JSON payload from a Wazuh alert.
    """
    rule  = alert.get('rule', {})
    level = rule.get('level', 0)

    if level <= 4:
        severity = 1
    elif 5 <= level <= 7:
        severity = 2
    else:
        severity = 3

    msg = {
        'source':        'wazuh',
        'severity':      severity,
        'severity_text': SEVERITY_LABELS.get(severity, 'unknown'),
        'title':         rule.get('description', 'N/A'),
        'description':   alert.get('full_log', 'N/A'),
        'rule_id':       rule.get('id', 'N/A'),
        'rule_groups':   rule.get('groups', []),
        'mitre':         rule.get('mitre', {}),
        'agent': {
            'id':   alert.get('agent', {}).get('id',   'N/A'),
            'name': alert.get('agent', {}).get('name', 'N/A'),
            'ip':   alert.get('agent', {}).get('ip',   'N/A'),
        },
        'manager': {
            'name': alert.get('manager', {}).get('name', 'N/A'),
        },
        'timestamp': alert.get('timestamp', 'N/A'),
        'alert_id':  alert.get('id', 'N/A'),
        'raw_alert': alert,
    }

    if options:
        msg['extra'] = options

    return json.dumps(msg)


def send_msg(msg: str, url: str, api_key: str = '', alert: dict = None) -> None:
    """
    HTTP POST the payload to the Tracecat webhook URL.

    API KEY AUTHENTICATION (optional):
      - If api_key is provided, it is sent in the x-tracecat-api-key header.
      - If api_key is empty, no auth header is sent.

    RESPONSE LOGGING:
      Tracecat returns a JSON response body on every webhook call. The
      response is fully parsed and logged as a nested object under the
      'tracecat_response' key in the log entry so you can trace exactly
      what Tracecat acknowledged for every alert.

      Typical Tracecat success response fields:
        status         — acknowledgment status (e.g. "ok")
        workflow_id    — the workflow that was triggered
        execution_id   — unique run ID for this specific trigger
        message        — human-readable confirmation from Tracecat

      These fields are extracted individually into the log entry so you
      can grep/filter by workflow_id or execution_id directly in the log.
    """
    headers = {
        'Content-Type':   'application/json',
        'Accept-Charset': 'UTF-8',
        'User-Agent':     'WazuhTracecatIntegration/1.0',
    }

    if api_key:
        headers['x-tracecat-api-key'] = api_key

    rule_id    = alert.get('rule', {}).get('id', 'N/A') if alert else 'N/A'
    alert_id   = alert.get('id', 'N/A') if alert else 'N/A'
    agent_name = alert.get('agent', {}).get('name', 'N/A') if alert else 'N/A'

    try:
        response = requests.post(url, data=msg, headers=headers, timeout=10)
        response.raise_for_status()

        # ------------------------------------------------------------------
        # Parse the Tracecat server response
        # Tracecat returns JSON with execution context on every successful
        # webhook call. We try to parse it fully — if it is not JSON (e.g.
        # a plain text acknowledgment) we store the raw text instead.
        # ------------------------------------------------------------------
        tracecat_response_raw  = response.text
        tracecat_response_body = {}

        try:
            tracecat_response_body = response.json()
        except Exception:
            # Response was not JSON — store as plain text
            tracecat_response_body = {'raw': tracecat_response_raw}

        # Extract key Tracecat response fields individually for easy grepping
        tc_workflow_id  = tracecat_response_body.get('workflow_id', 'N/A')
        tc_execution_id = tracecat_response_body.get('execution_id', 'N/A')
        tc_status       = tracecat_response_body.get('status', 'N/A')
        tc_message      = tracecat_response_body.get('message', 'N/A')

        log_info(
            'alert_sent',
            rule_id=rule_id,
            alert_id=alert_id,
            agent=agent_name,
            webhook=url,
            http_status=response.status_code,
            # Top-level convenience fields for quick filtering
            tc_workflow_id=tc_workflow_id,
            tc_execution_id=tc_execution_id,
            tc_status=tc_status,
            tc_message=tc_message,
            # Full response body nested for complete context
            tracecat_response=tracecat_response_body,
        )
        debug('# Tracecat responded [%d]: %s' % (response.status_code, response.text))

    except requests.exceptions.HTTPError as e:
        # Parse the error response body too — Tracecat often returns
        # a JSON error object with a 'detail' field explaining the rejection.
        error_body = {}
        try:
            error_body = response.json()
        except Exception:
            error_body = {'raw': response.text}

        log_error(
            'http_error',
            rule_id=rule_id,
            alert_id=alert_id,
            agent=agent_name,
            webhook=url,
            http_status=response.status_code,
            detail=str(e),
            tracecat_response=error_body,
        )
        debug('# HTTP error: %s' % str(e))
        raise

    except requests.exceptions.ConnectionError as e:
        log_error(
            'connection_error',
            rule_id=rule_id,
            alert_id=alert_id,
            agent=agent_name,
            webhook=url,
            detail=str(e),
        )
        debug('# Connection error - is Tracecat reachable? %s' % str(e))
        raise

    except requests.exceptions.Timeout:
        log_error(
            'timeout',
            rule_id=rule_id,
            alert_id=alert_id,
            agent=agent_name,
            webhook=url,
            detail='Request timed out after 10 seconds.',
        )
        debug('# Request timed out after 10 seconds.')
        raise


def get_json_alert(file_location: str) -> dict:
    """Read and parse the Wazuh alert JSON file from disk."""
    try:
        with open(file_location) as f:
            return json.load(f)
    except FileNotFoundError:
        log_error(
            'alert_file_not_found',
            path=file_location,
        )
        debug("# Alert file not found: '%s'" % file_location)
        sys.exit(ERR_FILE_NOT_FOUND)
    except json.decoder.JSONDecodeError as e:
        log_error(
            'alert_json_parse_error',
            path=file_location,
            detail=str(e),
        )
        debug('# Failed to parse alert JSON: %s' % e)
        sys.exit(ERR_INVALID_JSON)


def get_json_options(file_location: str) -> dict:
    """Read and parse an optional JSON options file. Non-fatal if absent."""
    if not file_location:
        return None
    try:
        with open(file_location) as f:
            return json.load(f)
    except FileNotFoundError:
        log_info(
            'options_file_not_found',
            path=file_location,
            detail='Continuing without options file.',
        )
        debug("# Options file not found: '%s' (continuing without it)" % file_location)
        return None
    except json.decoder.JSONDecodeError as e:
        log_error(
            'options_json_parse_error',
            path=file_location,
            detail=str(e),
        )
        debug('# Failed to parse options JSON: %s' % e)
        sys.exit(ERR_INVALID_JSON)


# ---------------------------------------------------------------------------
if __name__ == '__main__':
    main(sys.argv)
