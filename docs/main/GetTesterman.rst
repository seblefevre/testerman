Getting Testerman
=================

Testerman is made of several components that are designed to work
together:

- server: the Testerman core server - tacs: the Testerman
  Agent Controller Server ,
- cliclient: a command-line interface Testerman
  client ,
- qtesterman: a multi-platform rich client, used as an IDE to
  develop, run and monitor tests - pyagent: a python-based remote agent
  used to run probes on the SUT machines - webclientserver: a web
  front-end that can be used to monitor and trigger test suites and can be
  deployed in a DMZ.

While each component evolves at its own rate, baseline kits, containing
a reference version for all of them, are released from time to time.

Releases
--------

Latest stable release: Baseline 1.4.

+-------------------------------------------------------------------+----------------+--------------------------------------------------------------------------------------------------------+------------------------------------------------------------------------------------+
| Version                                                           | Release date   | Description                                                                                            | Repository access                                                                  |
+===================================================================+================+========================================================================================================+====================================================================================+
| [/chrome/site/pub/testerman-baseline-1.4.tar.gz baseline-1.4.0]   | 20111016       | The first packaged release after several years of internal use in selected telco software companies.   | `` git clone http://testerman.fr/git/testerman.git --branch tags/baseline-1.4 ``   |
+-------------------------------------------------------------------+----------------+--------------------------------------------------------------------------------------------------------+------------------------------------------------------------------------------------+

Components Versions Matrix
~~~~~~~~~~~~~~~~~~~~~~~~~~

+-------------------+----------+---------+-------------+--------------+-----------+-------------------+
| Release version   | server   | tacs    | cliclient   | qtesterman   | pyagent   | webclientserver   |
+===================+==========+=========+=============+==============+===========+===================+
| baseline-1.4.0    | 1.4.0    | 1.4.0   | 1.4.0       | 1.4.0        | 1.4.0     | 1.4.0             |
+-------------------+----------+---------+-------------+--------------+-----------+-------------------+

Development versions
--------------------

You may download the current Testerman version using anonymous git
access:

::

    git clone http://testerman.fr/git/testerman.git

or just browse the [source:/ git repository].

The anonymous git access is read-only. If you want to contribute and get
a read-write access, feel free to `contact me <About>`__.


