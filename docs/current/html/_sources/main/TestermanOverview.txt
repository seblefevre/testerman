Testerman Overview
==================

Testerman is a project that brings most of the powerful
capabilities and concepts of TTCN-3 to the Python programming language,
both providing a set of Python libraries and a complete, multi-user,
distributed test execution environment.

TTCN-3 is a test description language standardized by the ETSI as `ES
201 873 <http://www.ttcn-3.org/StandardSuite.htm>`__. Testerman
implements most language primitives described in its part 1
(ES201-873-1: TTCN-3 Core Part) as Python functions, however it drops
all the strict typing model of TTCN-3 and privileges the weak typing of
Python, enabling to write test cases faster than in TTCN-3.

Testerman is not meant to replace or to compete with such a growing
supported standard. Instead, it tries to fill the gap between the
existing, closed-source, expensive TTCN-3 tools on the market and the
other testing tools that are dedicated to one family of protocols,
forcing the users to develop glues to synchronize them together, and
create additional scripts to test non-protocol things such as log files,
database updates, etc.

By using the same concepts as in TTCN-3, your time investment in
Testerman can be fully reusable when migrating to the standard, if
needed: the test logic implementation, objects and primitives remain the
same, only the syntax changes.

Testerman Infrastructure
------------------------

Testerman has been designed to be multi-user (client-server) with a
centralized test cases repository, adaptable to most SUT topologies and
network constraints (distributed test/system adapters), and extensible
(test/system adapters can be developed easily, in any language).

.. image:: img/architecture.png
   :align: center

Clients
~~~~~~~

Users interact with the system through a Testerman client. Any number of
clients can connect to the same server, enabling to share the same ATS
repository and the same technical resources (the agents, see below).
Currently, the following clients are available:

-  a command-line interface client, that can be used to call test suite
   executions from a shell script, a Makefile, or a continuous
   integration system
-  a multi-platform, rich client named QTesterman providing an IDE to
   design, execute, control and analyze test suites
-  a lightweigth web-based client, limited to running tests and
   get their results and logs. This client can be published as a front-end
   to your customers in a DMZ.

CLI and rich client should be installed on the user's workstation. However,
developing a full fledged web-based client (with test designs and writing
capabilities) is quite possible.

Server Components
~~~~~~~~~~~~~~~~~

The server is actually split into two components:

-  The Testerman Server, which is a front-end to the clients,
   responsible for creating, running and controlling Test Executables
   (TE) from a source ATS written by the user. It is also able to push
   updates to the clients which implemented auto-updates, such as
   QTesterman.
-  The Testerman Agent Controller Server (TACS), which is a backend
   process responsible for managing remote Agents and Probes so that TEs
   can use them when needed at runtime (see below). The TACS may be
   installed on another machine than the Testerman Server (and shared
   between multiple servers), but is typically colocated with it.

Test Executables
~~~~~~~~~~~~~~~~

They are the result of a "compilation" of the ATS into something
runnable by the operating system. In a real TTCN-3 execution system, the
ATS, written in TTCN-3, would probably be transformed into Java or C++
code before being compiled with a standard compiler, and linked to
specific libraries according to the tool vendor. These libraries then
enable the TE to access a Platform Adapter (PA) and System Adapters (SA)
modules that implement actual, technical services such as timers,
message encoders/decoders, and connections to the SUT (actual socket
management, writing and reading on the wire, etc).

In Testerman, the ATS, writing by the user in Python and calling
Testerman-provided functions, is also transformed into a special Python
program that embeds additional Testerman modules (the Python word for
"libraries") to provide an access to the Testerman environment
functions. In particular, these libraries enable the TE to access the
probes either hosted on a distant agent ("remote probes") or run from
the same location as the TE ("local probes").

Agents & Probes
~~~~~~~~~~~~~~~

A probe is the Testerman word for the implementation of what TTCN-3
would call a Test Adapter (aka a System Adapter). This is the piece of
software that can actually connects to a SUT (System Under Test) using
different protocols (such as tcp, udp, sctp, or higher level ones: http,
rtsp, Oracle, SOAP, XMLRPC, ...).

Testerman provides a collection of probes to be able to interact with
the SUT using most usual protocols but also to interact with it
simulating user actions or anything needed to automate a test you can do
manually. For instance, the probe whose type is ``watcher.file`` is able
to monitor any (text) file on a system, and sends notifications when a
new line matching some patterns was written to it. Some others enable
you to simulate command line commands, as if you were opening a local
shell on the machine and running some commands locally.

Probes can be run by the TE itself, running on the Testerman Server and
thus initiating or expecting network connections on the Testerman
Server's IP interfaces (which may not be possible in all SUT
topologies), or can be run on any distant system. In this case, they
need to be hosted on a Testerman Agent, responsible for managing the
low-level communications with the Testerman Agent Controller Server
(TACS).

Agents must be deployed (i.e. installed and started) manually by the
tester. However, once deployed, an agent may be used by any TE to deploy
(dynamically) any number of probes on it, according to its defined Test
Adapter Configuration.

This Agent-oriented architecture enables to distribute probes anywhere
in the network, either around the SUT or inside the SUT itself. This
provides several benefits:

-  You can stimulate the SUT from any IP address, not limited to the
   server's ones. Useful to simulate SIP endpoints between multiple NAT
   gateways, test an Intrusion Detection System or any security rules,
   stimulate some interfaces that are only reachable from selected SUT
   subnets, etc.
-  You may install an agent on the SUT machines themselves, even if they
   are behind a router disabling direct access to them (the agents
   tcp-connect to the TACS, so that you can NAT them), and then be able
   to execute commands on the SUT itself or observe events occurring
   inside the SUT only, such as log updates, file creations, child
   process creations or kills, etc. You are no longer limited to what
   the SUT exposes outside of it to interact with it.
-  As a side effect, you may implement probes in any language, providing
   an agent exists for it - you are not stuck to Python and free to
   choose the best implementation language for your probe according to
   your likes, skills, or available libraries in the language (for
   instance, a SOAP probe using the .NET stack, a C++ based ISUP probe
   linked with HP OpenCall TDM modules, ...). If not using Python,
   however, your probes won't be able to run locally with the TE and
   will require an agent to host them.

For now, the main (and single) Testerman agent implementation available
is written in Python (that's why it is dubbed PyAgent) and can host any
probes that can also be run locally by the TE, sharing the same plugin
interface. This PyAgent can also be updated remotely from the
TACS+Testerman Server, making Testerman administrator's and user's lives
easier when new updates are available.

Main Concepts
-------------

...


