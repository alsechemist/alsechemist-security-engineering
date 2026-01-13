Manipulating JSON Decoders - Wazuh
==================================

Before creating any custom decoder for JSON logs, it is crucial to understand how ``JSON Decoders`` actually work. We know that Wazuh already has its prebuilt JSON Decoder known as
``0006-json_decoders.xml``. Inside, if you inspect the decoder, the built-in generic json decoder has this prematch:

.. image:: ../../assets/images/knowledge-base/manipulating-json-decoders-wazuh/decoder-manipulation-1.png
   :alt: Observing 0006-json_decoders.xml Decoder
   :align: center

.. raw:: html

   <div style="height:25px;"></div>

This matches any JSON starting with ``{"``, so it captures logs before our custom decoder can process them. Since ruleset decoders load before 
custom decoders in ``/var/ossec/etc/decoders/``, the generic decoder always wins. So basically what this means, no matter what ``decoder name`` we give, the prebuilt
JSON Decoder will override the custom JSON decoders' name. For example, observe the image below:

.. image:: ../../assets/images/knowledge-base/manipulating-json-decoders-wazuh/decoder-manipulation-2.png
   :alt: JSON Decoder Behavior
   :align: center

.. raw:: html

   <div style="height:25px;"></div>

To address this issue from the root cause, we are going to use the ``<decoder_exclude>[decoder_name]</decoder_exclude>`` tag, to exclude the decoder that's causing it. 

Solution - Decoder Name Override Problem
----------------------------------------

To solve this problem it is required to exclude the prebuilt ``0006-json_decoders.xml`` decoder. Dont't worry we are not fully excluding it. 
Obviously, we care about the thing that come with the defaults. We are basically going to make it or represent it as **not the inbuilt decoder itself**.

- **Step - 1:** Copy the content of ``0006-json_decoders.xml`` and paste it in ``local_decoder.xml``
- **Step - 2:** Exclude ``0006-json_decoders.xml`` decoder from executing in the Wazuh Manager.

    .. image:: ../../assets/images/knowledge-base/manipulating-json-decoders-wazuh/decoder-manipulation-3.png
       :alt: Excluding 0006-json_decoders.xml Decoder
       :align: center

    .. raw:: html

        <div style="height:25px;"></div>

    Save it, then restart the manager.

This method actually preserves the built-in features of ``0006-json_decoders.xml`` decoder while also making it usable for customization purposes. 

To further see it into action and how it works, checkout the :doc:`Decoder Creation of ModSecurity JSON Logs <../../research/modsecurity-log-detection-wazuh/decoder-creation>`,
there the concept will be utilized for Detection Engineering.

.. important::

    Order matters! Custom JSON Decoders must be defined ``BEFORE`` the generic json decoder. Other it won't work as decoders are prioritized by order.
