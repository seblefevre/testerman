Getting Testerman
=================

Testerman is made of several components that are designed to work
together:

- server: the Testerman core server
- tacs: the Testerman Agent Controller Server,
- cliclient: a command-line interface Testerman client,
- qtesterman: a multi-platform rich client, used as an IDE to
  develop, run and monitor tests
- pyagent: a python-based remote agent used to run probes on the SUT machines
- webclientserver: a web front-end that can be used to monitor and trigger test suites and can be
  deployed in a DMZ.

While each component evolves at its own rate, baseline kits, containing
a reference version for all of them, are released from time to time.

Releases
--------

Testerman is currently hosted on http://testerman.fr, and
releases are available from http://testerman.fr/testerman/wiki/GetTesterman.

Development versions
--------------------

If you want the latest probes or component enhancement, you may download the current Testerman version using anonymous git
access:

::

    git clone http://testerman.fr/git/testerman.git

The anonymous git access is read-only. If you want to contribute and get
a read-write access, feel free to `contact me <About>`__.

