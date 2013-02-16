.. Plugin index
   Includes 'manual' documentation, but also
   the various plugin docs automatically extracted by regenerate_plugins_docs.py
   from the source code.

Codecs and Probes Overview
--------------------------

Testerman comes with a collection of codecs and probes to interact with
your SUTs.

A *probe* (a.k.a. a Test Adapter or SUT Adapter in TTCN-3
terminology) is the entity that is responsible for actually implementing
the interaction with the SUT.

It could be reading and writing packets on the wire, reading/writing a
file somewhere, etc, and is usually configurable to provision actual SUT
IP addresses or port or other SUT-dependent and test logic-independent
parameters.

The probe is what is behind a test system interface port, and both are
associated through what Testerman calls a *binding*. The binding is also
the moment when you can set those SUT-dependent parameters for the
probe: they are called probe *properties*.

A *codec* is something different.

It does not perform any SUT adaptation, but only provides a way to
encode/decode high level, structured userland messages to/from a lower
level payload. Codecs can be stacked so that it is trivial to build
things such as transporting a MAP message encoded in base64 in a XML
element sent over UDP to a remote target; in this dummy example, we
would stack MAP, base64, and XML codecs to build a full payload that
would be sent through a UDP probe, actually injecting raw data over the
network to a SUT address that could be defined as a probe property (when
not test-dependent).

*Note: codec and probe documentations are currently missing. However,
all codecs and probes referenced below are readily available in
Testerman. Additional documentation is available in their source code,
too.*

Codecs
------

IT Oriented Codecs
~~~~~~~~~~~~~~~~~~

+-----------------+-----------------------------------------------------------------------------------------------------------------------+
| Codec ID        | Description                                                                                                           |
+=================+=======================================================================================================================+
| ``xml``         | :doc:`a simple XML coder/decoder <autogen/CodecXml>` - you may also have a look to CodecXerLite                       |
+-----------------+-----------------------------------------------------------------------------------------------------------------------+
| ``xer.lite``    | CodecXerLite, a XER (XML Encoding Rules)-like codec that only uses a subset of XML capabilities (no attributes)       |
+-----------------+-----------------------------------------------------------------------------------------------------------------------+
| ``http``        | CodecHttp, HTTP request/response codecs                                                                               |
+-----------------+-----------------------------------------------------------------------------------------------------------------------+
| ``soap11.ds``   | CodecSoapDs, a codec that enables to sign (and verify signatures of) SOAP 1.1 message, using Ws-Security standards.   |
+-----------------+-----------------------------------------------------------------------------------------------------------------------+

Multimedia and VoIP Oriented Codecs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

+----------------+----------------------------------------------------------------+
| Codec ID       | Description                                                    |
+================+================================================================+
| ``rtsp.*``     | :doc:`a RTSP codecs <autogen/CodecsRtsp>`                      |
+----------------+----------------------------------------------------------------+
| ``sdp``        | CodecSdp, a RFC4566 SDP (Session Description Protocol) codec   |
+----------------+----------------------------------------------------------------+

Telecom Oriented Codecs
~~~~~~~~~~~~~~~~~~~~~~~

+-------------------+------------------------------------------------------------------------------+
| Codec ID          | Description                                                                  |
+===================+==============================================================================+
| ``sua``           | CodecSua, a RFC3868 SUA (SCCP User Adaptation) codec                         |
+-------------------+------------------------------------------------------------------------------+
| ``tcap``          | CodecTcap, a TCAP (ITU) codec                                                |
+-------------------+------------------------------------------------------------------------------+
| ``map.*``         | CodecMap, a collection of codecs for MAP Phase 2+ PDUs                       |
+-------------------+------------------------------------------------------------------------------+
| ``sms.tpdu.*``    | CodecSmsTpdu, a collection of codecs for SMS TPDU SM-TL layer (GSM 030.40)   |
+-------------------+------------------------------------------------------------------------------+
| ``tbcd``          | A telephony BCD codec                                                        |
+-------------------+------------------------------------------------------------------------------+
| ``packed.7bit``   | A codec for 7-bit packed strings (useful for SMS encoding)                   |
+-------------------+------------------------------------------------------------------------------+


Test Adapters (Probes)
----------------------

Protocol Oriented Probes
~~~~~~~~~~~~~~~~~~~~~~~~

These probes are useful to test a SUT at protocol level.

-  General purpose probes: transport over IP probes: :doc:`TCP <autogen/ProbeTcp>`,
   :doc:`UCP <autogen/ProbeUdp>`, :doc:`STCP <autogen/ProbeSctp>` (could be used as
   a base for implementing SIP testing, SUA, HTTP, ... most protocols)
-  ProbeHttpClient, a simple, dummy HTTP client probe without any
   automated behaviours (no redirect following, etc)
-  ProbeRtspClient, a simple RTSP client probe
-  ProbeRtp, a RTP stream sender/listener

Tools Probes
~~~~~~~~~~~~

These probes are mainly useful to interfact with a SUT at high-level.
They are mainly convenience tools to develop the glue between several
domain testing, and are meant to integrate usual actions associated
with testing: connecting to remote machines, checking files, running
commands, changing configuration files, checking an SQL database, etc.

-  ProbeSsh, a probe to execute non-interactive commands remotely
   through SSH, ProbeExec to execute them locally, ProbeExecInteractive
   to execute them locally, but interactively
-  SQL connector probes: [ProbeSqlMysql MySQL], [ProbeSqlOracle Oracle]
-  ProbeDirWatcher, a probe that monitors a directory and notifies you
   when an entry has been added/removed (useful to check if a lock file
   was created/removed, ...)
-  ProbeFileWatcher, a probe that monitors an ascii file and notifies
   you of new lines (think of it as a combination of ``tail -f`` and
   ``grep``, useful to check log files for instance)
-  ProbeConfigurationFile, a probe that can access in read-write to
   configuration files, supporting most used configuration formats and
   extensible to match your needs (useful to prepare a SUT for testing
   in particular configuration conditions)
-  ProbeXmlRpc, a probe to invoke remote operations via XML-RPC
-  ProbeLdap, a probe to access a LDAP directory
-  ProbeSelenium, a probe to execute web-oriented tests through Selenium
   RC
-  ProbeFileManager, a probe to create, move, delete files dynamically
   (convenient to create temporary files, to inject resources into the
   SUT that are kept embedded in the ATS that you don't have to manage
   additional dependencies at runtime)
-  (more to come)

Codecs and Probes References
----------------------------

This section provides the reference documentation for each codec and probes.

.. toctree::
   :maxdepth: 1

   autogen/toc.rst

Developing New Codecs and Probes
--------------------------------

TODO.

Notice that the internal APIs are stable and can be safely used to develop new codecs/probes plugins.


