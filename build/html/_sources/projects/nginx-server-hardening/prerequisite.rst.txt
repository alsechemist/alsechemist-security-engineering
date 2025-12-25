Prerequisites
=============

Before building **ModSecurity v3 (libModSecurity)** from the official GitHub repository, ensure that the required system packages and development tools are installed. 
These dependencies are necessary to compile the core ModSecurity engine and enable support for common features such as 
JSON parsing, regular expressions, compression, and HTTP communication.

The following prerequisites have been validated on **Ubuntu Server 24.04 LTS** as well.

Install the required packages using the package manager:

.. code-block:: bash

    sudo apt update
    sudo apt install git g++ apt-utils autoconf automake build-essential libcurl4-openssl-dev libgeoip-dev liblmdb-dev libpcre2-dev libtool libxml2-dev libyajl-dev pkgconf zlib1g-dev

These packages provide the necessary build tools and libraries required by libModSecurity during compilation and runtime.

System Dependencies - `(Reference) <https://github.com/owasp-modsecurity/ModSecurity?tab=readme-ov-file#dependencies>`_
------------------------------------------------------------------------------------------------------------------------

ModSecurity is written in C++ using the C++17 standards. It also uses Flex and Yacc to produce the “Sec Rules Language” parser. 
Other, mandatory dependencies include YAJL, as ModSecurity uses JSON for producing logs and its testing framework, libpcre (not yet mandatory) 
for processing regular expressions in SecRules, and libXML2 (not yet mandatory) which is used for parsing XML requests.

All others dependencies are related to operators specified within SecRules or configuration directives and may not be required for compilation. 
A short list of such dependencies is as follows:

- libinjection is needed for the operator @detectXSS and @detectSQL
- curl is needed for the directive SecRemoteRules.

If those libraries are missing ModSecurity will be compiled without the support for the operator @detectXSS and the configuration directive SecRemoteRules.

Setting Up SSDEEP (Fuzzy Hashing Library)
-----------------------------------------

For this project, **ssdeep** is installed to enable **fuzzy hashing** capabilities within ModSecurity. Fuzzy hashing allows the comparison of files or payloads
based on similarity rather than exact matches. This is particularly useful in detecting **variants of known attacks**, malware, or suspicious payloads that
may evade exact signature-based detection.

By integrating ssdeep, ModSecurity can:

- Compare incoming HTTP requests or file uploads against previously recorded attack patterns using **fuzzy hash matching**.
- Identify **mutated or obfuscated attacks** that share similarity with known malicious payloads.
- Improve detection of **zero-day or polymorphic attacks** that do not match exact signatures but exhibit recognizable patterns.
- Complement the OWASP Core Rule Set (CRS) by adding an extra layer of similarity-based detection.

On **Ubuntu 24.04 LTS**, ssdeep can be installed using:

.. code-block:: bash

   sudo apt install -y ssdeep libfuzzy2 libfuzzy-dev

.. note::

   While ssdeep is optional, enabling it enhances ModSecurity's capability to detect variants of malicious content, thereby increasing overall WAF effectiveness.

Setting Up NGINX
----------------

To setup NGINX refer to their official `Installation Documentation <https://nginx.org/en/linux_packages.html#Ubuntu>`_ for Ubuntu distributions.
At Alsechemist, we always promote to stay updated, adapt the changes that new technologies bring and make new innovations along with changes that
come from time to time.

.. tip::
   
   Always make sure to setup or install the ``latest stable`` versions that vendors usually recommend regarding any package or tools.
   A ``latest`` without ``stable`` isn't always suitable for production environments. So choose your versions wisely.

