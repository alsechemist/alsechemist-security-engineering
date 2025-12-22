Conclusion
==========

This documentation demonstrated a complete and practical approach to **integrating ModSecurity audit logs into Wazuh** for 
centralized monitoring, detection, and analysis. By leveraging **ModSecurity v3**, **OWASP Core Rule Set (CRS) 4.21.0**, and 
**Wazuh’s JSON decoding and rule engine**, raw web application firewall events were transformed into structured and actionable security alerts.

The implementation covered the full detection lifecycle, including:

- Configuring ModSecurity to generate **JSON-formatted audit logs**
- Designing a **custom JSON-based decoder** for reliable log normalization
- Creating **custom Wazuh rules** to detect common web attacks such as SQL injection, remote command execution, and path traversal
- Ingesting audit logs into Wazuh using the **agent log collection mechanism**
- Validating log ingestion by **actively triggering ModSecurity alerts**

This approach provides Security Operations Centers (SOCs) with improved visibility into web application attacks while maintaining flexibility for 
rule tuning and expansion. The modular design of the decoders and rules allows security teams to gradually extend detection coverage without 
disrupting existing monitoring workflows.

While the current ruleset establishes a foundational detection framework, it also serves as a starting point for **continuous detection engineering**. 
As attack patterns evolve and new ModSecurity rules are introduced, additional Wazuh rules can be developed to enhance accuracy, reduce noise, and 
improve contextual awareness.

Ultimately, integrating ModSecurity with Wazuh strengthens web application defense by bridging **real-time request inspection** with **centralized security analytics**, 
enabling faster detection, better triage, and more informed incident response.

