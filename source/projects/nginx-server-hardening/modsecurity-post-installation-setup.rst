Post Installation Setup - ModSecurity
=====================================

After successfully installing ModSecurity, the next step is to configure it for production use. 
One of the most critical configurations is enabling **audit logging**, 
which records detailed information about requests and helps with monitoring, debugging, and security analysis.

Audit logs are essential to detect malicious activity, track anomalies, and integrate with SIEM solutions.

Enable Logging for ModSecurity Events
-------------------------------------

Ensure that ModSecurity audit logging is enabled by setting the appropriate directives in the ModSecurity configuration file - ``modsecurity.conf``

To enable it the set the parameter below,

.. code-block:: nginx

   SecAuditEngine On

When ``SecAuditEngine`` is set to ``On``, ModSecurity generates an audit log entry for **every request and response** processed by the web server. 
This mode provides complete visibility into web traffic.

Configuring JSON Audit Log Format - (Optional)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

ModSecurity v3 supports JSON-based audit logging using the **serial audit log** mechanism.

Configure the audit log type and format as follows,

.. code-block:: nginx

   SecAuditLogType Serial
   SecAuditLogFormat JSON
   SecAuditLog /path/to/modsec_audit.log

Where,

- ``SecAuditLogType Serial`` writes all audit events to a single log file.
- ``SecAuditLogFormat JSON`` enables JSON-formatted audit entries.
- ``SecAuditLog`` defines the audit log file path.

Each audit event will be written as a single JSON object, making it suitable for ingestion log processing tools.

Refer to the following image to have high level view.

.. image:: ../../assets/images/projects/nginx-server-hardening/settingup-modsecurity-post-installation-1.png
   :alt: Enabling ModSecurity Audit Logs
   :align: center

.. raw:: html

   <div style="height:25px;"></div>

.. attention::

    If you want to change the default ``SecAuditLog`` path to your preferred path, then make sure the path exists first with relevant and related access permissions.
    Otherwise there changes the logs might not generate due path not being found.

Verifying JSON Log Output
-------------------------

After applying the configuration, restart the web server and updated ModSecurity configurations will be applied immediately.

Example:

.. code-block:: bash

   systemctl reload nginx

Generate a test request e.g ``http://[server-ip]/?exec=/bin/bash`` that triggers a ModSecurity rule, then verify the audit log output:

.. code-block:: bash

   tail -f /path/to/modsec_audit.log | jq

A valid JSON audit log entry should resemble the following,

.. code-block:: json

    {
        "transaction": {
                    "client_ip": "192.168.111.1",
                    "time_stamp": "Sat Dec 20 19:08:10 2025",
                    "server_id": "a0c471f54012f3a3e121348ec12c6aaab884b0d9",
                    "client_port": 60357,
                    "host_ip": "192.168.111.130",
                    "host_port": 80,
                    "unique_id": "176625769044.127496",
                    "request": {
                    "method": "GET",
                    "http_version": "1.1",
                    "hostname": "192.168.111.130",
                    "uri": "/?exec=/bin/bash",
                    "headers": {
                        "Host": "192.168.111.130",
                        "Connection": "keep-alive",
                        "Cache-Control": "max-age=0",
                        "Upgrade-Insecure-Requests": "1",
                        "Sec-GPC": "1",
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.5",
                        "Accept-Encoding": "gzip, deflate"
                    }
                },
                    "response": {
                    "body": "<html>\r\n<head><title>403 Forbidden</title></head>\r\n<body>\r\n<center><h1>403 Forbidden</h1></center>\r\n<hr><center>nginx/1.28.0</center>\r\n</body>\r\n</html>\r\n<!-- a padding to disable MSIE and Chrome friendly error page -->\r\n<!-- a padding to disable MSIE and Chrome friendly error page -->\r\n<!-- a padding to disable MSIE and Chrome friendly error page -->\r\n<!-- a padding to disable MSIE and Chrome friendly error page -->\r\n<!-- a padding to disable MSIE and Chrome friendly error page -->\r\n<!-- a padding to disable MSIE and Chrome friendly error page -->\r\n",
                    "http_code": 403,
                    "headers": {
                        "Server": "nginx/1.28.0\u0000",
                        "Date": "Sat, 20 Dec 2025 19:08:10 GMT",
                        "Content-Length": "555",
                        "Content-Type": "text/html",
                        "Connection": "keep-alive"
                    }
                },
                    "producer": {
                    "modsecurity": "ModSecurity v3.0.14 (Linux)",
                    "connector": "ModSecurity-nginx v1.0.4",
                    "secrules_engine": "Enabled",
                    "components": [
                        "OWASP_CRS/4.21.0\""
                    ]
                },
                "messages": [
                    {
                        "message": "Host header is a numeric IP address",
                        "details": {
                        "match": "Matched \"Operator `Rx' with parameter `(?:^([\\d.]+|\\[[\\da-f:]+\\]|[\\da-f:]+)(:[\\d]+)?$)' against variable `REQUEST_HEADERS:Host' (Value: `192.168.111.130' )",
                        "reference": "o0,15o0,15v36,15",
                        "ruleId": "920350",
                        "file": "/usr/local/modsecurity/modsecurity-crs/rules/REQUEST-920-PROTOCOL-ENFORCEMENT.conf",
                        "lineNumber": "712",
                        "data": "192.168.111.130",
                        "severity": "4",
                        "ver": "OWASP_CRS/4.21.0",
                        "rev": "",
                        "tags": [
                            "application-multi",
                            "language-multi",
                            "platform-multi",
                            "attack-protocol",
                            "paranoia-level/1",
                            "OWASP_CRS",
                            "OWASP_CRS/PROTOCOL-ENFORCEMENT",
                            "capec/1000/210/272"
                        ],
                        "maturity": "0",
                        "accuracy": "0"
                        }
                    },
                {
                    "message": "Remote Command Execution: Unix Shell Code Found",
                    "details": {
                    "match": "Matched \"Operator `PmFromFile' with parameter `unix-shell.data' against variable `ARGS:exec' (Value: `/bin/bash' )",
                    "reference": "o1,8v11,9t:cmdLine,t:normalizePath",
                    "ruleId": "932160",
                    "file": "/usr/local/modsecurity/modsecurity-crs/rules/REQUEST-932-APPLICATION-ATTACK-RCE.conf",
                    "lineNumber": "631",
                    "data": "Matched Data: bin/bash found within ARGS:exec: /bin/bash",
                    "severity": "2",
                    "ver": "OWASP_CRS/4.21.0",
                    "rev": "",
                    "tags": [
                        "application-multi",
                        "language-shell",
                        "platform-unix",
                        "attack-rce",
                        "paranoia-level/1",
                        "OWASP_CRS",
                        "OWASP_CRS/ATTACK-RCE",
                        "capec/1000/152/248/88"
                    ],
                    "maturity": "0",
                    "accuracy": "0"
                    }
                },
                {
                    "message": "Inbound Anomaly Score Exceeded (Total Score: 8)",
                    "details": {
                    "match": "Matched \"Operator `Ge' with parameter `5' against variable `TX:BLOCKING_INBOUND_ANOMALY_SCORE' (Value: `8' )",
                    "reference": "",
                    "ruleId": "949110",
                    "file": "/usr/local/modsecurity/modsecurity-crs/rules/REQUEST-949-BLOCKING-EVALUATION.conf",
                    "lineNumber": "222",
                    "data": "",
                    "severity": "0",
                    "ver": "OWASP_CRS/4.21.0",
                    "rev": "",
                    "tags": [
                        "anomaly-evaluation",
                        "OWASP_CRS"
                    ],
                    "maturity": "0",
                    "accuracy": "0"
                    }
                }
            ]
        }
    }

