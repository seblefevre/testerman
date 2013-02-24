Testerman Reference Guide
=========================

This chapter describes features that are not related to the
Testerman core librairies, implementing the TTCN-3 concepts,
but instead the Testerman infrastructure and environment features.

Main Concepts
-------------

Note: all concepts that from TTCN-3 are indicated with a \* in this
chapter.

-  ATS (Abstract Test Suite)\*: The script containing the automated
   testcases. It is normally written in TTCN-3. In Testerman, it is
   written in Python, using the Testerman-provided modules (libs) to
   provide TTCN-3 features and an access to a complete Test System\*
   implementation.
-  Test System\*. An implementation framework to compile TTCN-3 scripts
   to TEs\*, execute them, control them, analyse their logs, etc. A
   typical TSE system is described below. Testerman is one example of a
   Test system, though not TTCN-3 compliant.
-  TE (Test Executable)\*: the executable generated from an ATS that can
   be actually executed on a real machine to perform the tests. In
   Testerman, the TE is built as a python script from the user-written
   ATS\*, slightly modified, and linked to Testerman-provided modules to
   connect to the execution environment, providing system, platform, and
   test adapters implementations.
-  Campaign: a hierarchical collection of ATSes (or other campaigns) to
   execute conditionally in a row. Gathers your ATSes from multiple
   sources in a single campaign, and run all your tests in one click.
-  ...
-  SUT (System Under Test): the system to test. Identifying the SUT is
   essential to correct automated tests implementation in Testerman (and
   TTCN-3), especially because you'll have to identify the different
   stimulation and observation interfaces between the Test System and
   the SUT. These interfaces are then viewed in TTCN-3 as Test System
   Interface Ports\*, or TSI Ports for short.
-  userland: the "TTCN-3" or "Testerman" world, where the testcase is
   executed and designed by a writer, i.e. the abstract part where
   testcases, test components, messages, templates live without being
   bothered by low-level consideration such as encoding/decoding,
   physical transports, physical connections, etc. The userland is test
   logic-oriented, not test implementation-oriented.

Logical Architectures
~~~~~~~~~~~~~~~~~~~~~

TTCN-3 Test System
^^^^^^^^^^^^^^^^^^

...

-  *TCI* (Test Control Interface) and *TRI* (Test Runtime Interface)
   are two interfaces standardized in TTCN-3, with specific operations
   and call flows.

Testerman does not implement them directly nor completely, but tries to
follow them as often as possible to keep the clean, flexible model of a
TTCN-3 implementation.

Testerman System
^^^^^^^^^^^^^^^^

...

Physical Architecture
~~~~~~~~~~~~~~~~~~~~~

Testerman implements these logical view as a distributed system, at
different levels:

-  the SA is made of distributable entities: agents. Agents are
   containers that can be deployed on any physical machine providing it
   has an access to an agent controller (and, not to be useless, to the
   SUT). This controller, dubbed the TACS (Testerman Agent Controller
   Server), is typically co-hosted with the Testerman Server (the main
   test system executor front-end), and exposes the connected agents to
   TACS clients:

[little diagram]

All TEs are clients to the TACS, enabling them an access to all the
probes hosted on the agents. The Testerman Server itself is also a TACS
client, for administration and control purposes.

On the front-end side, Testerman uses a client/server model, enabling
multiple users to control and executes ATSes at the same time, sharing
the same Testerman installation and repository.

[another little diagram]

Interfaces
^^^^^^^^^^

Testerman names the following interfaces:

-  **Ws** (Web Service): client/server control interface. Job control,
   repository access (read/write), agent/probe management, and some
   server administration. Implemented in XML-RPC, and documented
   `here <TestermanInternals>`__ - useful if you plan to integrate Testerman in
   a SOA.
-  **Xc** (eXternal interface, Client): subscription-based notification
   interface. Clients can subscribe to get job, probe, agent
   control-related events or real-time execution logs. Implemented using
   TestermanProtocol.
-  **Xa** (eXternal interface, Agent): the interface between the TACS
   and the agents (TACS southbound interface). Implemented using
   TestermanProtocol.
-  **Ia** (Internal interface, Agent): the protocol used internally by
   the TEs to access the remote probes through the TACS (TACS northbound
   interface). Also used for basic TACS management. Implemented using
   TestermanProtocol.
-  **Il** (Internal interface, Logging): the interface between the TEs
   and the Test Logging (TL) module embedded within the Testerman
   Server. Whenever the TE needs to log something, it sends it to the TL
   through this interface. The TL is responsible for writing it to the
   proper log file. Will enable distributed PTCs over multiple TEs on
   different machine (but not yet). You can identify this interface as
   being a part of the TTCN-3 TCI. Implemented using TestermanProtocol.

Core Concepts
-------------

Most concepts at use for an ATS writers are described in `TTCN-3: Core
Language (ES 201 873-1, version
3.4.1) <http://www.ttcn-3.org/StandardSuite.htm>`__. However, Testerman
adds some new ones to fill the gap between the standard, dealing with
abstractions only, and a real implementation.

Test Adapter Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~

TTCN-3 does not provide a standard way to assign a test system interface
port with an actual test adapter implementation, implementing
on-the-wire sending and receiving operations.

Testerman introduces a way to bind these ports to test adapters, i.e. to
probes, and calls this relationship a "binding". When defining a (named)
Test Adapter Configuration (for now, programmatically in your ATS only),
you defines the different bindings (i.e. what probe instance will be
used to implement a test system interface port), including the binding
configuration, i.e. the probe parameters, if any.

You may define multiple test adapter configurations and switch from
one to another one depending on the test environment you're about to run
your tests against.

The test adapter configuration is supposed to be the only thing that
change from one test environment to another one. It usually defines:

-  real SUT IP addresses, ports
-  some low level variables such as ssh login/password (likely to change
   from one system to another one)
-  etc

Application-oriented variables may still vary from one test environment
to another one, but if your testcase is carefully designed, including
with correct [#PreambleandPostamble Preambles], you should be able to
minimize the amount of efforts needed to run your test on another
instance of your SUT.

Codec Aliasing
~~~~~~~~~~~~~~

The TTCN-3 code language does not completely ignore this, though.

Basic, General Purpose SUT Adapters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once introduced to TTCN-3, you may wonder "OK, that's nice and powerful,
but now, how do I connect to a tcp server, send and receive some data
?". Protocols in use are not a (direct) concern for the standard, you
are right. We're dealing with application- and test-oriented message
structures, but physical transport (such as tcp/udp/sctp or even ip) is
not adressed. TTCN-3 has the concept of SUT addresses, but how do we
control (perform and verify) actual connections, disconnections,
stream-oriented data reception, and so on ?

Antti Hyrkkanen, from the Tampere University of Technology, defended his
`master thesis <http://www.ttcn-3.org/doc/GeneralPurposeTTCN3SA.pdf>`__
about a general purpose SUT Adapter for TTCN-3, bringing socket-like
structures and associated functions to TTCN-3. While this approach
cannot be more flexible and complete, it renders ATSes harder to write
for non-programmers, forced to take into account low level details in
most cases (of course, if your tests are about testing the SUT's ability
to handle tcp connections, disconnect them when expected, etc, this is
fully adapted and even required).

[WARNING: feel free to correct me if I misunderstood Antti's work]

Testerman tries to find an intermediate solution to this problem by
providing a collection of transport-related probes, interfaced in
userland using the same kind of templates - quite similar to Antti's
solution, but just less generic as the very low level (socket
parameters) are embedded within the probe, and partially controllable
through test adapter configurations.

(TODO: transport interface: to document)

Preamble and Postamble
~~~~~~~~~~~~~~~~~~~~~~

Testcases may require some SUT preparation in order to be executed,
typically data provisioning, configuration files settings, maybe some
processes or applications restarts.

Once the test is over (independently from its verdict), the SUT needs
to be restored in an "original" state so that, in particular, we can
replay the testcase without any additional manipulations.

These SUT preparation and clean up phases are called "Preamble" and
"Postamble" (P&P), respectively, in Testerman terminology.

Testerman provides a way to use its core features to implement an
automated preamble (you may call it "automated test bed setup",
"automated prerequisites set up", ...) at least for what Testerman can
automate using its available probes and the available SUT provisioning
interfaces - manual prerequisites may still be needed.

You may design campaign-level P&P, suitable for multiple ATSes (i.e.
starting the Preamble at the beginning of a campaign, starting the
Postamble when finished), or ATS-level P&P, where a Preamble/postable
may be used for multiple testcases in a row, or testcase-level P&P, i.e.
only valid for a particular testcase (in this case, they are typically
embedded within the testcase definition itself).

Testerman Applications
~~~~~~~~~~~~~~~~~~~~~~

**The Testerman application framework is currently not available.**

The idea is to provide a way to run "in the background" applications
built using Testerman features to act as simulators either to help
manual testing or to simulate/prototype new applications.

Basically, you can already develop such simulators in a testcase, but a
testcase is not designed to run forever and not to return a verdict. A
Testerman application will.

Campaigns
~~~~~~~~~

A campaign is a structured collection of ATSes that can be executed
conditionally.

It is basically a black and white tree (each node has two branches: one
to follow if the current node is successful, the other one in case of an
error) enabling to chain ATSes (or other campaigns), executing specific
ATSes or campaign depending on the execution status of the current job.

Campaign Definition
^^^^^^^^^^^^^^^^^^^

A campaign is defined in clear text, declaring a job tree based on
indentation:

::

    job
     job
     job
      job
    job

The indentation is defined by the number of indent characters. Valid
indent characters are ``\t`` and ``' '``.

A job line is formatted as:

::

    [<branch> ]<type> <path> [groups <groups>] [with <mapping>]

where:

-  ``<branch>`` indicates the execution branch the job belongs too. Must
   be a keyword in 'on\_success', 'on\_error', '\*', or left empty. If
   not provided or set to 'on\_success', it indicates that the job is in
   the *success* branch, and that it should be executed only if its
   parent job returns a 0-result. If set to 'on\_error' or '\*', this is
   the 'error' branch, and the job is executed only if its parent job
   returns a non-0 result.
-  ``<type>`` is a keyword in 'ats', 'campaign', indicating the type of
   the job
-  ``<path>`` is a relative (not starting with a /) or and absolute path
   (/-starting) within the repository refering to the ATS or the
   campaign to execute.
-  ``<groups>`` is an optional string formatted as
   ``GX_GROUP_NAME[,GX_ANOTHER_GROUP]*`` enabling to select
   the groups to run in the ATS. This option is only valid for an ATS job.
   By default, all groups are selected.
-  ``<mapping>`` is an optional string formatted as
   ``key=value[,key=value]*`` enabling to map or set job's parameters
   from the current context's parameters. See
   `below <#SessionParametersFlowsinCampaigns>`_ for more details.

Comments are indicated with a #.

Example:

::

    # Sample campaign
    ats class5/call_forward_unconditional.ats # job1
     ats class5/call_forward_busy.ats         # job2
     ats class5/call_forward_no_answer.ats    # job3
    ats clip/clip_base.ats                    # job4
    ats clip/clir_base.ats                    # job5

reads:

-  first start executing ``call_forward_unconditional.ats``. If it's OK
   (retcode = 0), then execute ``call_forward_busy.ats``, and
   (regardless of its retcode) ``call_forward_no_answer.ats``
-  always execute ``clip_base.ats`` then ``clir_base.ats``

Session Parameters Flows in Campaigns
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Additionally, session parameters are transmitted to the executed
children. In the example above:

-  job1 will be started with the campaign's initial session parameters
   (a merge from the user provided values, if any, and the default
   values)
-  job2, if executed, will be started with the session output from job1
-  job3, if executed (same condition as for job2), will be executed with
   the session output from job1, too (its parent)
-  job4 will be executed with the campaign's initial session parameters
-  job5 will be executed with the campaign's initial session parameters

You can also define some local mappings to adjust the parameters to
pass to a child job.

Let's assume the script ``class5/call_forward_unconditional.ats``
takes two parameters: ``PX_SUT_IP``, defaulted to 127.0.0.1,
``PX_SUT_PORT``, defaulted to 5060, and ``PX_SOURCE_URI``, defaulted to
``'sip:john@testerman.fr'``.
In a campaign defined as:

::

    ats class5/call_forward_unconditional.ats with PX_SUT_IP=192.168.1.1,PX_SOURCE_URI=sip:campaign@somewhere.com

the ATS will be executed with explicitly provided ``PX_SUT_IP`` and
``PX_SOURCE_URI`` values, but keeping the default ATS value for
``PX_SUT_PORT`` (5060).

However, hardcoding SUT-dependent values is probably not a good idea.
Instead, we'd probably define the ``PX_SUT_IP`` parameter at campaign
level, and set it on run or via its default value.

::

    ats class5/call_forward_unconditional.ats with PX_SOURCE_URI=sip:campaign@somewhere.com

with a ``PX_SUT_IP`` defined as a parameter for the campaign.

**Note**: this is equivalent to:

::

    ats class5/call_forward_unconditional.ats with PX_SUT_IP=${PX_SUT_IP},PX_SOURCE_URI=sip:campaign@somewhere.com

Now, if you have several ATSes using the same parameter names for
different purposes, for instance PX\_SUT\_IP, used to defined a SIP
server in one ATS, and used to defined a LDAP interface in another ATS,
you can design different parameters at campaign levels and map them to
their local names when needed:

::

    ats class5/sip_test.ats with PX_SUT_IP=${PX_SIP_SUT_IP}
    ats class5/ldap_provisioning_test.ats with PX_SUT_IP=${PX_LDAP_SUT_IP}

and defining ``PX_SIP_SUT_IP`` and ``PX_LDAP_SUT_IP`` as parameters for
the campaign.

You got it, ``'${NAME}'`` is the way to reference a session parameter
named ``NAME``. If such a parameter is not defined when requested, no
substitution occurs (``'${UNKNOWN_PARAM}'`` will be expanded to
``'${UNKNOW_PARAM}'``).

As it is a mere string substitution, you may design campaigns whose
parameterization is more user-friendly than the ATSes (or campaigns)
they embed:

::

    ats another_test.ats with PX_PROBE_URI=probe:_@${PX_AGENT}

The ATS ``another_test.ats`` was designed to make the whole probe URI
configurable. In the campaign, only the agent is, indirectly reducing
the amount of information to set.

Jobs
----

ATSes and campaigns are executed as "jobs" created internally by the
server.

Job Control
~~~~~~~~~~~

Some clients, for instance QTesterman, provides a user interface to
control the scheduled or running testerman jobs.

Jobs are controlled sending *signals* to them, through the Ws
interface using the ``sendSignal(jobId, signal)`` API. The job reacts
differently according to its state when receiving the signal.

+--------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------+-------------------+
| Signal       | Description                                                                                                                                                                                                                                                                         | **Acceptable states**      | **Final state**   |
+==============+=====================================================================================================================================================================================================================================================================================+============================+===================+
| pause        | pause the job                                                                                                                                                                                                                                                                       | running                    | paused            |
+--------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------+-------------------+
| resume       | resume a paused job                                                                                                                                                                                                                                                                 | paused                     | running           |
+--------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------+-------------------+
| cancel       | cancel a waiting job (preventing it from being executed), or stop a running job after its current ATS is over (for a campaign), or gracefully stop the current testcase (for an ATS) then stop the ATS. This automatically resumes the job if it was paused before cancelling it.   | waiting, running, paused   | cancelled         |
+--------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------+-------------------+
| kill         | kill a running job, not waiting for any pending testcase completion. This should only be used if the cancel operation does not work, as it may leave remote probe resources unfreed.                                                                                                | running, cancelling        | killed            |
+--------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------+-------------------+

Job Lifecycle
~~~~~~~~~~~~~

The following diagram exposes the basic job state machine, from its
birth to its multiple death possibilities:

.. image:: img/job-state-machine.png

Some state explanations:

-  **initializing**: the job is being prepared and dependencies scanned:
   campaigns are parsed and missing ATSes or children are reported,
   leading to an error; imported modules in ATSes are checked.
-  **waiting**: the job is now in the server's queue, waiting for its
   start according to its scheduled start time.
-  **running**: the job is now running, either executing testcases for
   ATSes, or ATSes for campaigns
-  **paused**: the job has been paused. Only meaningful for an ATS job.
   Running timers, if any, are not frozen during the pause. As a
   consequence, when resuming the job, several timers may expire
   immediately.
-  **complete**: the job completes its execution "successfully", i.e. no
   technical errors (TTCN3-, Testerman- or Python-related
   errors/exceptions) occurred, and the job return code is 0 (you may
   alter it with the stop(retcode) statement in the control part).
   However, it does not mean that all testcases were OK.
-  **cancelling**: the job is being cancelled, i.e. it waits for the
   pending testcase to finish, then stops.
-  **cancelled**: the job has been cancelled, i.e. probably did not
   complete all its testcases (unless the cancel signal arrived during
   the last testcase execution). The associated log file is still valid
   and consistent to analyze testcases till the cancellation.
-  **killing**: the job is being killed, i.e. stopped without waiting
   for a possible pending testcase to finish. This state typically lasts
   less than one second. Anyway, you can't do anything more to kill the
   job now.
-  **killed**: the job has been killed. The associated log file may be
   inconsistent, especially regarding the running testcase when killed.
-  **error**: a problem occurred either while preparing the job
   (campaign parsing error, temporary files creation problems, TE syntax
   error, ...) or a technical error occurred preventing the ATS
   continuation, typically a Python exception in the control part
   (incorrect testcase identifier, ...). In the first case, you should
   have a look to the server's logs to know what was wrong; in the
   second case, take a look at the log file in raw mode: the exception
   is probably logged. Additionally, the job's return code could help
   you diagnose the problem:

+-------------------+-----------------------------------------------------------------------+------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Return code       | Description                                                           | **Associated state**   | **Comments**                                                                                                                                                                                                                                                            |
+===================+=======================================================================+========================+=========================================================================================================================================================================================================================================================================+
| 0                 | No error                                                              | complete               |                                                                                                                                                                                                                                                                         |
+-------------------+-----------------------------------------------------------------------+------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| 1                 | Cancelled (by the user)                                               | cancelled              |                                                                                                                                                                                                                                                                         |
+-------------------+-----------------------------------------------------------------------+------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| 2                 | Killed (by the user)                                                  | killed                 |                                                                                                                                                                                                                                                                         |
+-------------------+-----------------------------------------------------------------------+------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| 3                 | Killed by the OS                                                      | error                  | Could be a segfault, out of memory, ... check the server's logs for the exact signal.                                                                                                                                                                                   |
+-------------------+-----------------------------------------------------------------------+------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| 4                 | Complete, but some testcases were not executed successfully           | complete               | This status enables to quickly identify that at least one testcase was not passed, and the ATS may require your attention.                                                                                                                                              |
+-------------------+-----------------------------------------------------------------------+------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| 10                | TE/Runtime: Unable to initialize the logger                           | error                  | Check the server's log for a possible additional trace. Check Il interface settings and local firewall settings.                                                                                                                                                        |
+-------------------+-----------------------------------------------------------------------+------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| 11                | TE/Runtime: Unable to initialize core libraries                       | error                  | Check the ATS log file for more details, in raw mode.                                                                                                                                                                                                                   |
+-------------------+-----------------------------------------------------------------------+------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| 12                | TE/Runtime: TTCN-3 related error                                      | error                  | You did something not compliant with the TTCN-3 logic in the control part. Check the ATS log file for more details, in raw mode.                                                                                                                                        |
+-------------------+-----------------------------------------------------------------------+------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| 13                | TE/Runtime: Generic TE error                                          | error                  | An exception occurred in the control part, probably a missing or invalid identifier. Check the ATS log file for more details, in raw mode.                                                                                                                              |
+-------------------+-----------------------------------------------------------------------+------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| 20                | Preparation: Unable to write the TE                                   | error                  | Check disk space and rights to create a file in the document\_root/archives folder.                                                                                                                                                                                     |
+-------------------+-----------------------------------------------------------------------+------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| 21                | Preparation: Python Syntax error                                      | error                  | Look at the server's logs for the error line in the TE.                                                                                                                                                                                                                 |
+-------------------+-----------------------------------------------------------------------+------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| 22                | Preparation: Unable to check the TE                                   | error                  | Look at the server's logs for more details.                                                                                                                                                                                                                             |
+-------------------+-----------------------------------------------------------------------+------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| 23                | Preparation: Unable to extract ATS parameters from its metadata       | error                  | Look at the server's logs for more details.                                                                                                                                                                                                                             |
+-------------------+-----------------------------------------------------------------------+------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| 24                | Preparation: Unable to create input session file or TE dependencies   | error                  | Check disk space and rights to create a file in the tmp\_root.                                                                                                                                                                                                          |
+-------------------+-----------------------------------------------------------------------+------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| 25                | Preparation: Unable to locate all module dependencies                 | error                  | Check ``import`` statements in ATS and imported modules (you can only import modules that are in the repository or Python system modules). The missing dependencies are reported to some client such as QTesterman. Alternatively, you may look at the server's logs.   |
+-------------------+-----------------------------------------------------------------------+------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| 26                | Preparation: Unable to create the TE                                  | error                  | The exact error is provided to the caller when submitting the job for an standalone run (i.e. outside a campaign). Typical errors include unsupported language APIs, or internal (but specified) errors.                                                                |
+-------------------+-----------------------------------------------------------------------+------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| >= 100            | user defined, via stop(retcode) in control part                       | error                  |                                                                                                                                                                                                                                                                         |
+-------------------+-----------------------------------------------------------------------+------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

Documentation System
--------------------

Testerman provides a highly flexible framework to create documentation
from ATS scripts, based on Python’s docstring capabilities.

A docstring is a character string (usually multi-line) that is inserted
just after defining a Python object, in particular a class or a
function. Testerman re-uses this model to offer the ability to document
user-created functions as well as test cases through the use of
documentation plugins that extract these information to create a test
specification document, or to export to a test management system, etc.

Raw Documentation
~~~~~~~~~~~~~~~~~

Basically, if you need to document a test case named ``TC_MY_TESTCASE``:

.. code-block:: python

    class TC_MY_TESTCASE(TestCase):
      """
      This is the test case documentation.
      
      This test verifies that an SNMP trap
      is actually sent when rebooting the server.
      We first listen for a trap,
      then we reboot a machine using ssh reboot.
      We then should get our trap within 30 seconds.
      
      Created by John Smith on 2009-05-05.
      """
      def body(self, ...):
        """
        A documentation can also apply here
        """
        ...

Documentation Tags
~~~~~~~~~~~~~~~~~~

It is usually convenient to structure your test case documentation into
something more formal. A test case specification, for instance, may
contain a purpose, the description of the steps to perform, some
prerequisites, an author, a creation date, and so on.

The documentation may be left as is, using a plain English text, or
turned into something more formal and still human-readable using tags.
Tags are special markers in the plain text that indicates the different
parts of the documentation. If you are familiar with code documentation
system such as Epydoc, Javadoc, Doxygen, there is nothing new here – the
syntax is (almost) the same:

.. code-block:: python

    class TC_MY_TESTCASE(TestCase):
      """
      This is the test case documentation.
     
      @purpose: This test verifies that an SNMP trap
      is actually sent when rebooting the server.
      @steps:
      We first listen for a trap,
      then we reboot a machine using ssh reboot.
     
      We then should get our trap within 30 seconds.
     
      @author: John Smith
      @date: 2009-05-05
      """
      def body(self, ...):
        """
        A documentation can also apply here
        """
        ...

``@purposes``, ``@steps``, ``@author``, ``@date`` are used to tag
different parts of the raw documentation. In this sample, however, we
left what could be a test case overview untagged, as the "natural",
basic test case documentation.

Documentation plugins, for instance, can then access tag values directly
to create some more formal test specification (or any other kind of
documentation).

Any tags can be created at any time, anywhere in docstrings. However,
they are mainly interpreted by plugins and you should match their
expectations, according to the documentation strategy defined by your
Testerman administrator and test managers. Testerman only provides a
framework, regardless of the way you plan to use it.

Tag Format
~~~~~~~~~~

A tag is defined as an identifier (``[a-zA-Z0-9_-]+``) following a ``@``
character, starting a new line. Its value starts just after the
following ``:`` character.

Tags are case-insensitive: for instance, ``@purpose`` and ``@Purpose``
define the same tag ``purpose``.

Tag Value Format
~~~~~~~~~~~~~~~~

A tag value can be written over multiple lines. Actually, the current
tags value only stops when another tag is started or when the docstring
ends:

::

      @purpose: This test verifies that an SNMP trap
      is actually sent when rebooting the server.

Resulting in a tag value:

::

    This test verifies that an SNMP trap is actually sent when rebooting the server.

Notice that leading and trailing spaces are stripped, so that this is
equivalent to:

::

      @purpose:
      This test verifies that an SNMP trap
      is actually sent when rebooting the server.

If you need to create a value that contains carriage returns, you must
either leave an empty line or starts a new line with at least one blank
character (space(s), tab(s)):

::

      @steps:
      We first listen for a trap,
      then we reboot a machine using ssh reboot.
      We then should get our trap within 30 seconds.

Resulting in the following tag value:

::

    We first listen for a trap, then we reboot a machine using ssh reboot. We then should get our trap within 30 seconds.

Which is not really readable. So let’s use:

::

      @steps:
      We first listen for a trap,
      then we reboot a machine using ssh reboot.
     
      We then should get our trap within 30 seconds.

Or

::

     @steps:
     We first listen for a trap, then we reboot a machine using ssh reboot.
     We then should get our trap within 30 seconds.

Leading to:

::

    We first listen for a trap, then we reboot a machine using ssh reboot.
    We then should get our trap within 30 seconds.


