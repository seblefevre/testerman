Quick Start
-----------

Before installing Testerman, make sure you had a look to
TestermanOverview, in particular to understand its client/server
architecture.

The following procedure will help you install and start the server
components, set up a repository with some sample scripts, and deploy the
QTesterman client.

Server Installation
~~~~~~~~~~~~~~~~~~~

Requirements
^^^^^^^^^^^^

The Testerman server components currently run on Linux (may also run
on Solaris 10) with Python 2.6 or better (however, Python 3 is not yet
supported).

Installation (current development snapshot)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This procedure assumes that you have installed the subversion client on
your machine, named in this sample ``testermanserver``.

0. You may create a dedicated user to run the Testerman server
components, or run it as a normal user. It is usually a bad idea to run
it as root.

#. Get the current development snapshot using subversion (here
   "installed" to ``testerman-svn``):

::

    git clone http://testerman.fr/git/testerman.git testerman-git
    cd testerman-git

2. Set up a document root (in this example, we are using the default, as
configured in ``conf/testerman.conf``: ``~/testerman``) and a repository
that will contain your shared test cases; we also fill it with some
samples (WARNING: existing samples will be replaced with the one from
the SVN tree):

::

    bin/testerman-admin setup document-root

3. Publish the current (SVN version) QTesterman client and PyAgent on
this server, advertising them as stable versions:

::

    bin/testerman-admin -c testerman/components source-publish component qtesterman branch stable
    bin/testerman-admin -c testerman/components source-publish component pyagent branch stable

4. You may check the published components with:

::

    user@testermanserver$ bin/testerman-admin -c testerman/components show
    Component  | Version | Branch | Archive File                  | Status
    -----------------------------------------------------------------------
    pyagent    | 1.1.3   | stable | /updates/pyagent-1.1.3.tgz    | OK
    qtesterman | 1.2.0   | stable | /updates/qtesterman-1.2.0.tgz | OK

Starting the Server Components
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Assuming you are using ``~/testerman`` as the document root, go to the
directory where you installed or checked out Testerman (in the procedure
above, into ``~/testerman-svn``), and start the Testerman components,
i.e. the Testerman Agent Controller Server (TACS) and the Testerman
Server, with:

::

    user@testermanserver$ bin/testerman-admin start all

You may check that both processes are running with:

::

    user@testermanserver$ bin/testerman-admin status
     Component | Management Address    | Status  | PID  
    -----------------------------------------------------
     server    | http://localhost:8080 | running | 6625 
     tacs      | 127.0.0.1:8087        | running | 6670 

By default, the Testerman Server listens on ``tcp/8080`` (Ws interface,
XML-RPC based Web Services), ``tcp/8082`` (Xc interface, a text-based
event subscription service), ``tcp/127.0.0.1:8081`` (Ei interface). You
may set Ws and Xc IP addresses explicitly in the ``conf/testerman.conf``
file if needed.

The TACS listens on ``tcp/40000`` (Xa interface, used by the agents to
connect to their controller) and ``tcp/127.0.0.1:8087`` (Ia interface).
Those are configurable in the same configuration file as well.

Installing the QTesterman Client
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can now proceed with the `QTesterman client
installation <QTesterman#Installation>`__, pointing to
``http://testermanserver:8080`` were ``testermanserver`` is the name or
the IP of the machine where you just installed and started the Testerman
Server component.

Deploying and Starting a PyAgent
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You may need to deploy some Testerman agents to host probes remotely.

You may directly start a Python-based agent, dubbed PyAgent, from the
installation root:

::

    bin/testerman-agent --name localagent --log-filename myagent.log -d

where ``localagent`` is a friendly identifier that will be used as the
domain part in probe URIs when defining test adapter configurations. The
``-d`` flag indicates that the agent should deamonize. By default, it
will try to connect to a controller on ``localhost:40000``.

But starting an agent locally is not very useful, as it main interest is
its capability to be distributed over the network. Several options exit
to install such an agent on another machine, on which it has the
following requirements:

-  Any system with Python 2.4 or better (won't work/untested with python
   3.x)
-  according to the probes you plan to use on this agent, additional
   requirements may appear. Please see CodecsAndProbes.

The Easiest Way
^^^^^^^^^^^^^^^

Assuming ``wget`` is installed on your target machine, you can retrieve
a pre-configured pyagent installer from the Testerman server with:

::

    wget http://<server>:8080/pyagentinstaller

where ``<server>`` is your Testerman server hostname or IP address.

This fetches a Python script that is pre-configured to download and
install the latest stable pyagent package from the server you provided
in this url. Just execute it with:

::

    python ./pyagentinstaller

(for other options, in particular to install a specific pyagent version
or a testing version, see the inline help with
``python ./pyagentinstaller --help``)

Once done, your pyagent is ready to be executed from your current
directory with:

::

    ./testerman-agent.py -c testermanserver --name remoteagent [-d] [--log-filename remoteagent.log]

where ``testermanserver`` is the Testerman server hostname or IP
address, and ``remoteagent`` the name that will identify this agent on
the Testerman system. Use the ``-d`` flag to daemonize the agent, if
needed, and ``--log-filename`` to add an optional log file if you want
one.

Manual PyAgent Installation
^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you don't want to use the ``pyagentinstaller`` script, you may copy
the pyagent component package that was deployed into
~/testerman/updates/pyagent-X.X.X.tgz to a target machine that will run
the agent (you can also fetch this file from
``http://<testermanserver>:8080/components.vm``).

Once ``pyagent-X.X.X.tgz`` has been copied, just untar it (it will
create a directory named ``pyagent``) and execute the agent:

::

    cd pyagent
    python ./testerman-agent.py -c testermanserver --name remoteagent --log-filename remoteagent.log -d 

where ``testermanserver`` is the hostname or IP address of the server
the TACS is running on and ``remoteagent`` the name you want to assign
to this agent instance (using the machine hostname can be a good start).
The agent will connect to the TACS on startup (and keeps reconnecting in
case of a connection failure) and will show up in QTesterman's probe
manager when available.

Alternatively, you may check the correct agent deployment from the
server's installation root with:

::

    user@testermanserver$ bin/testerman-admin -c testerman/probes show all
    URI                    | Type    | Location      | Version
    --------------------------------------------------------------------------
    agent:remoteagent      | pyagent | 192.168.13.17 | PyTestermanAgent/1.1.3
    agent:localagent       | pyagent | 127.0.0.1     | PyTestermanAgent/1.1.3

And voila ! You are now ready to play with some samples from the
QTesterman interface.

External Resources
------------------

TTCN-3
~~~~~~

If you are new to TTCN-3, you may find the following links useful:

-  `The official TTCN-3 site <http://www.ttcn-3.org>`__, in particular
   the core language reference to download (and use it in conjunction
   with TestermanTTCN3 for feature comparisons) and the `tutorials
   page <http://www.ttcn-3.org/CoursesAndTutorials.htm>`__ (don't miss
   `C Willcock's introduction to
   TTCN-3 <http://www.ttcn-3.org/TTCN3UC2005/program/TTCN-3%20Introduction%20version%20T3UC05.pdf>`__)
-  `TTCN-3 Basics <http://www.ttcn3basics.com/Day1/siframes.html>`__, a
   very clear introduction (courses ?) to TTCN-3 by Vesa-Matti Puro,
   from OpenTTCN
-  `Research in
   TTCN-3 <http://www.site.uottawa.ca/~bernard/ttcn.html>`__ is a
   collection of very useful links, including multiple tutorials and
   real world use cases

Python
~~~~~~

New to Python ? try these:

-  `The official Python site <http://www.python.org>`__ - at least one
   thing to read: `the Python
   tutorial <http://docs.python.org/tutorial/>`__. However, since it is
   based on the most recent Python version at date, some features may be
   not available on most Testerman deployments, running Python 2.4 or
   2.5 as provided with your distribution
-  `Dive into Python <http://diveintopython.org/toc/index.html>`__ is a
   book by Mark Pilgrim that is freely available online. A good reading,
   too.


