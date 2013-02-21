Testerman Administration Guide
==============================

The Document Root
-----------------

The document root (or docroot for short) in the directory used by the
server processes to store local repository files, component updates,
built test executables and execution logs.

The document hierarchy is:

-  ``repository/``: this directory is the root directory exposed to the
   user through the Ws interface. This is the local directory that is
   mounted as / in the exposed virtual file system. It typically
   contains all user ATS and module files, unless you configured
   additional file system backends to point to other locations or
   backend types. Since it contains user data, this is a directory to
   backup.
-  ``MOTD``: the Message Of The Day optional file. If present, it is
   retrieved by QTesterman clients and displayed on startup. You may use
   it to communicate about the server administrations, updates or
   maintenance announcements, etc.
-  ``archives/``: this directory contains executed ATSes, as Test
   Executables and associated log execution files. If you need to
   troubleshoot a TE, you may need to access this folder. It can also be
   browsed through the Ws interface, and is actually interfaces by
   QTesterman, so that the user can retrieve any archived execution log.
-  ``updates.xml``: this file is used to describe available component
   updates for component that supports autoupdates (for instance,
   QTesterman (via Ws) and the PyAgent (via Xa)). This file is mandatory
   to enable updates distribution.

Additionally, when distribution updates from the servers, we suggest you
use the following convention:

-  ``updates/``: store component update packages (tar or tar.gz files).
   The complete path within the document root to the update is provided
   within the ``updates.xml``, so it is not mandatory to use this folder
   name. However, distributable packages must be located below the
   document root.

This document root is typically used by both the Testerman Server and
the Testerman Agent Controller Server (TACS). However, since the TACS
only uses it for distributing updates to agents, you may create a
document root dedicated to it, containing at least a ``updates.xml``
file, and typically a ``updates/`` folder with the agent packages
referred by the xml file.

Update Management
-----------------

Updates Metadata Format
~~~~~~~~~~~~~~~~~~~~~~~

The file ``docroot/updates.xml`` provides all the needed information to
update an agent or a client. It is a xml file whose structure is
something like:

.. code-block:: xml

    <?xml version="1.0" encoding="utf-8" ?>
    <updates>
      <update component="qtesterman" branch="stable" version="1.0.0" url="/updates/qtesterman-1.0.0.tar">
        <!-- optional properties -->
        <property name="release_notes_url" value="/updates/rn-1.0.0.txt />
        <!-- ... -->
      </update>
      <update component="qtesterman" branch="experimental" version="1.0.1" url="/updates/qtesterman-1.0.1.tar" />
      <update component="pyagent" branch="stable" version="1.0.1" url="/updates/pyagent-1.0.1.tar" />
      <update component="pyagent" branch="stable" version="1.0.0" url="/updates/pyagent-1.0.0.tar" />
    </updates>

Whenever you want to make a new update available to agents/clients, you
should update this file to declare the new update, providing the
followinf information as attributes to the ``update`` element:

-  ``component``: a name identifying the component the update refers to.
   This name depends on the client/agent. See below for details.
-  ``branch``: a branch classifies an update. By convention, it is
   either ``stable`` (well tested update), ``testing`` (should be OK in
   most cases, but the user should be aware of some remaining potential
   problems with it - early deployment), or ``experimental`` (beta or
   alpha testing, specific purposes). These branches enables you to
   deploy updates without impacting all production users (using only
   stable updates), while leaving the opportunity to some users to test
   new probes or new QTesterman features (testing or experimental, when
   testing very specific updates with one or two users). Once a version
   has been correctly tested, you may switch its branch from ``testing``
   to ``stable`` (or anything else).
-  ``version``: the version of a component. Must be formatted as
   ``A.B.C`` (for instance ``1.0.1``, ``2.10.13``). The meaning of each
   digit is your own choice for the component you developed. For
   components distributed with the project, C is a incremented on bugfix
   or small enhancement (A.B fixed), B on normal enhancement (A fixed, C
   reset to 0), A on major changes (B, C reset to 0).
-  ``url``: the location of the update archive within the document root.
   Must be a file format supported by the component.

Additional, optional properties may be defined. In this case, they are
component-dependent.

Standard Updatable Components
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Testerman provides the following standard component that can be updated
through the system above:

+----------------------+--------------------------------------------+---------------------------------+----------------------------+-------------------------------------------------------------------------------------------------+
| Component name       | Description                                | Supported archive formats       | Supported properties       | Comments                                                                                        |
+======================+============================================+=================================+============================+=================================================================================================+
| ``qtesterman``       | The QTesterman rich client                 | ``tar``, ``tar.gz``             | (none)                     | The archive file must contain files in a ``qtesterman/`` base folder. Updated through Ws.       |
+----------------------+--------------------------------------------+---------------------------------+----------------------------+-------------------------------------------------------------------------------------------------+
| ``pyagent``          | The Python Testerman Agent (with probes)   | ``tar``, ``tar.gz``             | (none)                     | The archive must contain a (single) subdir containing the file to update. Updated through Xa.   |
+----------------------+--------------------------------------------+---------------------------------+----------------------------+-------------------------------------------------------------------------------------------------+

You may develop your own components that could be distributed through
this infrastructure as well.


