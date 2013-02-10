General Concepts
----------------

Test Cases
~~~~~~~~~~

...

Control Part
~~~~~~~~~~~~

You may think of control part of an ATS as the main function in a
program: this is where test cases are instantiated and executed in the
order that fits your needs, with additional conditions or loops or the
usual programming control primitives.

The control code is usually located at the end of the ATS, and it is a
good practice to stick to this structure, defining all test cases
classes before it, leading to the following advised ATS layout:

1. ATS header, comments
2. ``import`` directives
3. ATS-wide function definitions, including templates (non-shared functions or templates are better kept within their test cases)
4. Test Case and Behaviour definitions as Python classes
5. Control part

For instance:

.. code-block:: python

    ##
    # Some comments here
    ##


    # Let's import some stuff shared with our colleages
    from myteam.SharedFunctions_2_3 as CommonTeam
    import mysite.utils as Utils


    # We define some templates and functions
    def mw_myTemplate(text, minsize = 10, author = any()):
      return { 'text': text, 'size': greater_than(minsize), 'author': author }

    def f_sleep(duration):
      t_sleep = Timer(duration)
      t_sleep.start()
      t_sleep.timeout()


    # Now, let's define some test cases
    class TC_MY_TESTCASE(TestCase):
      """
      A first test case.
      """
      def body(self):
        ...

    # Another one
    class TC_MY_SECOND_TESTCASE(TestCase):
      """
      Don't forget to document me.
      """
      def body(self, loopCount = 10):
        ...


    # Finally, the control part
    TC_MY_TESTCASE().execute()
    TC_MY_SECOND_TESTCASE().execute(loopCount = 20)

In the ATS control section, TTCN-3 allows several basic operations, and
so does Testerman:

-  Logging, using the [#ThelogStatement ``log()`` statement]
-  Stopping the ATS explicitly, using the [#ThestopStatement ``stop()``
   statement]
-  [#ExecutingaTestCase Executing a test case], optionally modifying
   some test case information on the fly (such as its ID)

In addition, TTCN-3 provides a way to create and start timers from the
control part. Testerman does not, however it offers several facilities
to:

-  [#ControllingLogLevel Control log level]
-  [#TestAdapterConfiguration Define and use test adapter
   configurations]
-  [#ControllingTestCasesExecution Control ATS autostop after a testcase
   failure]

Executing a Test Case
^^^^^^^^^^^^^^^^^^^^^

To execute a test case, you first have to instantiate its class, then
call its ``execute()`` method. In practice, this translates to:

.. code-block:: python

    TC_MY_TESTCASE().execute()

The ``execute()`` method may take any optional or mandatory arguments,
depending on how you defined the test case body. Naming the argument
before assigning it a value is mandatory.
Let's imagine you defined a test case this way:


.. code-block:: python

    class TC_MY_TESTCASE(TestCase):
      def body(self, clip, clir, cnip = False, cnir = False):
        ...

This defines a test case with 4 parameters: two of them are mandatory
(``clip`` and ``clir``), while the two last (``cnip`` and ``cnir``) are
optional, as they have a default value. You may then execute such a test
case with:

.. code-block:: python

    # Minimal case: we only provide the mandatory parameters
    TC_MY_TESTCASE().execute(clir = False, clip = True)
    # We provide an additional, optional parameter value
    TC_MY_TESTCASE().execute(clir = False, clip = True, cnir = True)
    # Or all of them (notice that the argument order does not matter):
    TC_MY_TESTCASE().execute(cnip = True, clir = False, clip = True, cnir = True)

The following cases would lead to a runtime error, as the mandatory
paraemeters won't be set:

.. code-block:: python

    # Missing mandatory parameters
    TC_MY_TESTCASE().execute()
    # Missing argument name - not a syntax error, but won't fill clip/clir
    TC_MY_TESTCASE().execute(False, True)
    # Missing mandatory parameter
    TC_MY_TESTCASE().execute(clir = True, cnir = False)

A call to ``execute()`` returns the test case verdict, as a character
string in ``"pass", "inconc", "fail", "none", "error"``. You may use
this result to execute additional tests or stop the ATS conditionally
(see [#ThestopStatement below] for some examples).

Test Case Instantiation
^^^^^^^^^^^^^^^^^^^^^^^

Upon test case instantiation, you also have the possibility to alter
some of its static attributes to adapt them to the execution context:

.. code-block:: python

    TC_MY_TESTCASE(title = "Sample test case", id_suffix = "001").execute()

Both ``title`` and ``id_suffix`` are optional.

-  ``title`` is a way to label your test case with a friendly short
   description. Such a title can then be used in log analyzers and
   reporters to create more clear and readable test execution reports.
-  ``id_suffix`` enables to alter the test case ID, which is its class
   name (in this sample, ``TC_MY_TESTCASE``) with an additional suffix.
   When such a suffix is present, an underscore character is
   automatically added before adding it to the native ID. In this case,
   for instance, the executed test case would have a final ID equals to
   ``TC_MY_TESTCASE_001``.

These parameters may prove useful when looping over the same test case
with different parameters:

.. code-block:: python

    i = 0
    for clir in [ True, False ]:
      for clip in [ True, False ]:
        i += 1
        TC_MY_TESTCASE(id_prefix = "%3.3d" % i, title = "Call with clip=%s, clir=%s" % (clip, clir)).execute(clip = clip, clir = clir)

will result in the four following test cases:

+-------------------------+-----------------------------------+
| ID                      | Title                             |
+=========================+===================================+
| TC\_MY\_TESTCASE\_001   | Call with clip=True, clir=True    |
+-------------------------+-----------------------------------+
| TC\_MY\_TESTCASE\_002   | Call with clip=False, clir=True   |
+-------------------------+-----------------------------------+
| TC\_MY\_TESTCASE\_003   | Call with clip=True, clir=False   |
+-------------------------+-----------------------------------+
| TC\_MY\_TESTCASE\_004   | Call with clip=True, clir=False   |
+-------------------------+-----------------------------------+

In particular, their IDs are now unique.

Controlling Log Level
^^^^^^^^^^^^^^^^^^^^^

Several functions are provided to control the logs that the execution
may generate.

Generally, you don't need to use these functions, as the default log
levels provide all that is necessary to construct acceptable log files
for functional testing analysis. However, in several conditions, you may
need to add additional internal traces, using:

.. code-block:: python

    enable_debug_logs()

or disable them later in your ATS, using:

.. code-block:: python

    disable_debug_logs()

Finally, if you don't care analysing your test cases (known to work
already) and you need to boost test execution performances (for minimal
load testing, for instance), you may use:

.. code-block:: python

    disable_logs()

to disable all traces except the core ones that will be used to identify
ATSes and test cases executions.

A fine-grain log control is also available, using
``enable_log_levels(*levels)`` and ``disable_log_levels(*levels)``.

Controlling Test Cases Execution
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``execute()`` method of a Test Case returns its verdict. It enables
to stop your ATS conditionally:

.. code-block:: python

    if TC_MY_TESTCASE().execute() != PASS:
      stop() # explicit ATS stop, this is a critical testcase
    TC_MY_SECOND_TESTCASE().execute()  # we don't care about its verdict
    if TC_MY_THIRD_TESTCASE().execute() != PASS:
      stop() # another important testcase

While this method offers a precise control over which testcase may be
considered critical enough to justify the ATS abortion, it is not
convenient when you want any testcase failure to stop the ATS.

In this case, you may use the ``stop_ats_on_testcase_failure()``
directive:

.. code-block:: python

    # auto stop on failure
    stop_ats_on_testcase_failure()

    TC_MY_TESTCASE().execute()
    TC_MY_THIRD_TESTCASE().execute()

Test Adapter Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^

A test adapter configuration is a Testerman context that enables to
define a set of bindings, i.e. the mapping between test system interface
ports and probes, with their location on the network and particular
properties, to use when executing your test cases.

In the mid term, such configurations will be taken outside the ATS, as
they can be different from one site (or user) to another one. This deals
with ATS portability, and running an ATS to another site should not make
the operator modify the source at all.

However, for now, the test adapter configuration can be done only
programmatically, using the ``TestAdapterConfiguration`` Testerman
class:

.. code-block:: python

    myconfig = TestAdapterConfiguration('myconfig')
    myconfig.bind('ldapServer', 'probe:ldap', 'ldap')
    myconfig.bind('hlr', 'probe:sctp@remoteagent', 'sctp', listening_port = 14001)

This will create a test adapter configuration labelled/named
``default``, binding a ldap probe to the test system interface port name
``ldapServer`` and a remote SCTP probe bound to ``hlr``. This probe is
also pre-configured to listen on port 14001.

Then, to activate a test adapter configuration, use:

.. code-block:: python

    use_test_adapter_configuration('myconfig')

where ``name`` is the name of your defined configuration, for instance
``'myconfig'`` in the example above.

Activating a configuration automatically deactivates the previous one,
if any.

However, it is not mandatory to create a test adapter configuration
explicitely. You may also use the ``bind`` instruction directly, and it
will use a built-in, default test adapter configuration:

.. code-block:: python

    bind('ldapServer', 'probe:ldap', 'ldap')
    bind('hlr', 'probe:sctp@remoteagent', 'sctp', listening_port = 14001)

is actually enough to be able to use the tsiPort ``'ldapServer'`` and
``'hlr'`` in your testcases.

Basic Statements
~~~~~~~~~~~~~~~~

The ``stop()`` Statement
^^^^^^^^^^^^^^^^^^^^^^^^

This statement can be used in multiple locations, leading to different
effects according to the calling context.

-  When called from a (running) PTC (either from its Behaviour body or
   any of the functions called from it, including in alternative
   actions), it stops the PTC whose final local verdict will then be its
   last known local verdict.
-  When called from the MTC, i.e. from the test case body or any of the
   functions called from it, it stops the test case itself, requesting
   all running PTC to stop, merging all current local verdicts at the
   time of the stop action as the final test case verdict.

A typical usage pattern can be:

.. code-block:: python

    setverdict('fail')
    stop()

used when something went wrong and you don't need to continue your
test case anymore. Notice that you don't need to stop whenever you set
the verdict to ``fail`` to fail your test case since this verdict value
can't be overriden.

In case of explicit test case stop, beware that you may skip the
postamble part of your test case that is supposed to restore the SUT
state to what it was before the test case started. You should use this
statement carefully.

-  In addition, you may call ``stop()`` from anywhere in the ATS control
   part to stop the ATS explicitly. In this case, Testerman provides an
   additional, optional integer argument to this function so that you
   can control the ATS return code - useful to control a campaign
   continuation, or simply state that the ATS was "failed" or "passed".
   This code is also returned by the Testerman CLIclient in synchronous
   execution mode, enabling to check an ATS status from shell scripts,
   Makefile, continuous integration engines or the likes.
-  An ATS is considered complete if its return code is 0 - this is
   the default behaviour. This status is independent from the
   executed test cases results: it just indicates that the ATS was
   run up to its end.
-  An ATS is considered not complete if its return code is greather
   or equals to 1. Return codes from 1 to 99 (included) are reserved
   for runtime errors and ATS control (abnormal terminations, either
   system or user-triggered). Return codes >= 100 (and <= 255) are
   for your own use, and you should only pass return codes in this
   range to ``stop()``.

You may control this return code with:

.. code-block:: python

    # Don't continue if this test case is not passed, 
    # and consider the ATS should report an error to the ATS executor
    # (a campaign, or a Makefile, ...)
    if TC_VERY_IMPORTANT_TESTCASE().execute() != PASS:
      stop(100) 

    # In this case, we stop the ATS for optimization reasons:
    # if the first TC fails, we assume that all others will fail too.
    # Since they lasts a very long time, we don't want to waste our time waiting
    # for their completion.
    if TC_FIRST_OF_A_SERIES_OF_SAME_KIND_OF_TC().execute(param = value1) != PASS:
      stop()
    TC_FIRST_OF_A_SERIES_OF_SAME_KIND_OF_TC().execute(param = value2)
    TC_FIRST_OF_A_SERIES_OF_SAME_KIND_OF_TC().execute(param = value3)
    TC_FIRST_OF_A_SERIES_OF_SAME_KIND_OF_TC().execute(param = value4)

Setting a return code in a ``stop()`` called from a test case (i.e. not
from the control part) has no effect.

The ``log()`` Statement
^^^^^^^^^^^^^^^^^^^^^^^

You may log a user message at any time, anywhere in your ATS, using the
following function:

.. code-block:: python

    log("This is a user message")

This produces a user log element in the logger system that can be
analyzed and displayed in the various log viewers available for
Testerman. Such a logged message is automatically attached to a logging
entity depending on the calling context:

-  when called from the control part, the logged message is not attached
   to any test case.
-  when called from the test case body or any function called from here,
   the logged message is attached to the main test component (MTC). The
   QTesterman visual log viewer, for instance, is able to make this
   association visible to the end-user.
-  when called from a behaviour body or any function called from here,
   the logged message is attached to the parallel test component (PTC)
   running the behaviour. The QTesterman visual log viewer is able to
   make this association visible to the end-user, too.

``log()`` only takes a single string or unicode string argument. The
usual Python formatting methods apply, such as:

.. code-block:: python

    log("Current verdict: %s ; based on parameter p1=%s" % (getverdict(), p1))

Test Components
~~~~~~~~~~~~~~~

...

Timers
~~~~~~

Timers can be defined at any time as soon as a test case is running
(TTCN-3 allows the use of timers in the control part, this is not the
case for Testerman). They can be declared and manipulated in the MTC,
PTC, or any functions called from them.

Once started, a timer emits a timeout event on expiry. It can be
restarted at any time (while running, stopped or expired), stopped
before its timeout, and provides a way to measure the elapsed time since
its start.

To declare a timer, use:

.. code-block:: python

    t_myTimer = Timer()

Alternatively, you may assign a default duration to it, expressed in
seconds (as a non-negative float), and a name to track it in execution
logs:

.. code-block:: python

    t_myTimer = Timer(2.0, "my timer") # defines a 2-second timer labeled "my timer"

Both arguments are optional, and you may use named arguments as well:

.. code-block:: python

    t_myTimer = Timer(duration = 2.0, name = "my timer") # defines a 2-second timer labeled "my timer"

If no name is provided, an identifier is automatically generated. It is
unique for each timer. If no duration is provided, you will have to
provide one when starting it. Consider this is a default duration.

To start a timer, use:

.. code-block:: python

    t_myTimer.start() # raise a runtime error (exception) if no duration was provided on declaration

or

.. code-block:: python

    t_myTimer.start(5.0) # start the timer with a 5 second duration, overriding the default duration, if any.

If you start an already running timer, it is restarted with the new
duration, or, if not provided, the default duration provided during the
timer declaration.

At any time you may stop it:

.. code-block:: python

    t_myTimer.stop()

This has no effect if the timer was not running (already stopped,
expired, or never started).

While the timer is running, you may use:

.. code-block:: python

    elapsed = t_myTimer.read()

which returns the number of seconds, as a float, since the timer start.
Returns ``0.0`` if the timer is not running; and

.. code-block:: python

    if t_myTimer.running():
      ...

which returns a boolean value indicating if the timer is running.
Returns False only if the timer is stopped, expired, or never started.

To catch the timeout event, you may use, in a ``alt`` statement:

.. code-block:: python

    alt([
      [ t_myTimer.TIMEOUT, # timer timeout
        lambda: log("Do something on timer expiry"),
        lambda: ...
      ],
      ...
    ])

or the shortcut:

.. code-block:: python

    t_myTimer.timeout()

if you don't have any other events or messages to match in parallel.
This is equivalent to ``alt([[t_myTimer.TIMEOUT]])``.

In particular, this is used to implement a sleep/wait function:

.. code-block:: python

    # Sleep of 1.5s, the TTCN-3/Testerman way
    t_myTimer = Timer(1.5)
    t_myTimer.start()
    t_myTimer.timeout()

It is important to use this pattern for a sleep/wait implementation
instead of the standard Python library ``time.sleep()`` to ensure that
your code is interruptible by a ``ptc.stop()`` or equivalent.

Notes:

-  ``t_myTimer.timeout()`` blocks until the timeout event for this timer
   is detected. However, it will returns immediately if the timer is not
   running.
-  ``t_myTimer.TIMEOUT`` event can be matched only once. It will me
   matchable again once the timer has been restarted.

Template Matching
~~~~~~~~~~~~~~~~~

Matching Mechanisms
^^^^^^^^^^^^^^^^^^^

Template matching is one of the most interesting feature of TTCN-3. It
enables to detect if we receive a quite precise message without any
manual checks or conditional value traversal. In addition to constant
matching, several matching mechanisms are available to act as wildcards
or conditions. These mechanisms are used in place of a constant in a
template.

Testerman implements the following template matching mechanisms:

+------------------------------+--------------------------------------+-----------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| mechanism                    | arguments                            | applies to\*          | description                                                                                                                                                        |
+==============================+======================================+=======================+====================================================================================================================================================================+
| ``any()``                    |                                      | any type of values    | matches any but non-empty value. May be used as a single element wildcard in a list, too.                                                                          |
+------------------------------+--------------------------------------+-----------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``any_or_none()``            |                                      | any type of values    | matches any values, including empty values (lists, dicts, strings) or absent values (in a dict). May be used as "any number of elements" wildcard in a list, too   |
+------------------------------+--------------------------------------+-----------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``greater_than(value)``      | integer, float                       | integer or float      | matches values v as ``value`` <= ``v``                                                                                                                             |
+------------------------------+--------------------------------------+-----------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``lower_than(value)``        | integer, float                       | integer or float      | matches values v as ``v`` <= ``value``                                                                                                                             |
+------------------------------+--------------------------------------+-----------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``between(a, b)``            | integer, float                       | integer or float      | matches values v as ``a`` <= ``v`` <= ``b``                                                                                                                        |
+------------------------------+--------------------------------------+-----------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``empty()``                  |                                      | list, dict, string    | matches empty lists, dicts, or strings                                                                                                                             |
+------------------------------+--------------------------------------+-----------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``pattern(pattern)``         | Python regular expression            | string                | matches strings that matches the regular expression ``pattern``                                                                                                    |
+------------------------------+--------------------------------------+-----------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``omit()``                   |                                      | any value in a dict   | enables to match a dict only if the associated field is not present in the dict (i.e. the entry has been omitted)                                                  |
+------------------------------+--------------------------------------+-----------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``ifpresent(template)``      | a Testerman template                 | any value in a dict   | enables to apply the ``template`` to the value if the field present in a received dict, or still accept to match the dict if the field is not present              |
+------------------------------+--------------------------------------+-----------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``superset(*templates)``     | any number of elements of any type   | lists                 | matches any list that contains at least one time each of the given elements, in any order                                                                          |
+------------------------------+--------------------------------------+-----------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``subset(*templates)``       | any number of elements of any type   | lists                 | matches any list that contains only elements in the given elements, 0 or more times, in any order                                                                  |
+------------------------------+--------------------------------------+-----------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``complement(*templates)``   | any number of elements of any type   | lists                 | matches any list that does not contain any of the given elements                                                                                                   |
+------------------------------+--------------------------------------+-----------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``length(template)``         | a Testerman (scalar) template        | list, string, dict    | extracts the length of the received message, and matches it against the provided template                                                                          |
+------------------------------+--------------------------------------+-----------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------+

\* "applies to" means "can be used to match"

Mechanisms can be combined together. See the examples below.

**Examples**

+--------------------------------------------+---------------------------------------------------------------------+-----------------+--------------------------------------------------------------------+
| message                                    | template                                                            | **matched ?**   | **comments**                                                       |
+============================================+=====================================================================+=================+====================================================================+
| ``1.0``                                    | ``any()``                                                           | yes             |                                                                    |
+--------------------------------------------+---------------------------------------------------------------------+-----------------+--------------------------------------------------------------------+
| ``0``                                      | ``any()``                                                           | yes             |                                                                    |
+--------------------------------------------+---------------------------------------------------------------------+-----------------+--------------------------------------------------------------------+
| ``[]``                                     | ``any()``                                                           | no              |                                                                    |
+--------------------------------------------+---------------------------------------------------------------------+-----------------+--------------------------------------------------------------------+
| ``[]``                                     | ``any_or_none()``                                                   | yes             |                                                                    |
+--------------------------------------------+---------------------------------------------------------------------+-----------------+--------------------------------------------------------------------+
| ``hello``                                  | ``pattern(r'^hell.*')``                                             | yes             |                                                                    |
+--------------------------------------------+---------------------------------------------------------------------+-----------------+--------------------------------------------------------------------+
| ``{ 'key': 123, 'password': 'secret' }``   | ``{ 'key': between(100, 200) }``                                    | yes             |                                                                    |
+--------------------------------------------+---------------------------------------------------------------------+-----------------+--------------------------------------------------------------------+
| ``{ 'key': 123, 'password': 'secret' }``   | ``{ 'key': lower_than(200), 'password': omit() }``                  | no              | the field ``password`` should not be present                       |
+--------------------------------------------+---------------------------------------------------------------------+-----------------+--------------------------------------------------------------------+
| ``{ 'key': 123 }``                         | ``{ 'key': any(), 'password': any_or_none() }``                     | yes             |                                                                    |
+--------------------------------------------+---------------------------------------------------------------------+-----------------+--------------------------------------------------------------------+
| ``{ 'password': 'secret' }``               | ``{ 'key': any(), 'password': any_or_none() }``                     | no              | the ``key`` field must be present (but may have any value)         |
+--------------------------------------------+---------------------------------------------------------------------+-----------------+--------------------------------------------------------------------+
| ``{ 'key': 123 }``                         | ``{ 'key': any(), 'password': ifpresent('secret') }``               | yes             | ``password`` was made optional                                     |
+--------------------------------------------+---------------------------------------------------------------------+-----------------+--------------------------------------------------------------------+
| ``{ 'key': 123, 'password': 'hello' }``    | ``{ 'key': any(), 'password': ifpresent(pattern(r'secret.*')) }``   | no              | ``password`` is now present, but does not match the sub-template   |
+--------------------------------------------+---------------------------------------------------------------------+-----------------+--------------------------------------------------------------------+
| ``'verylongpassword'``                     | ``length(greater_than(16))``                                        | yes             |                                                                    |
+--------------------------------------------+---------------------------------------------------------------------+-----------------+--------------------------------------------------------------------+
| ``[1, 2, 3]``                              | ``subset(3, 2, 4, 1, 5, 6)``                                        | yes             |                                                                    |
+--------------------------------------------+---------------------------------------------------------------------+-----------------+--------------------------------------------------------------------+
| ``[1, 2, 3, 1]``                           | ``superset(2, 1)``                                                  | yes             |                                                                    |
+--------------------------------------------+---------------------------------------------------------------------+-----------------+--------------------------------------------------------------------+
| ``[1, 2, 3, 2]``                           | ``superset(1, 2, 3, 4)``                                            | no              |                                                                    |
+--------------------------------------------+---------------------------------------------------------------------+-----------------+--------------------------------------------------------------------+
| ``[1, 1, 2, 2]``                           | ``complement(3, 4, 5, 6, 7)``                                       | yes             |                                                                    |
+--------------------------------------------+---------------------------------------------------------------------+-----------------+--------------------------------------------------------------------+

**List matching**

List matching may be tricky because ordered. Several mechanisms,
however, can help you matching exactly what you need, even if you don't
know the complete list you may receive (optional elements, etc). In
particular, you can use ``any()`` and ``any_or_none()`` as ``?`` and
``*`` wildcards, respectively:

+----------------------------+-------------------------------------------+-----------------+-------------------------------------------------------------+
| message                    | template                                  | matched ?       | comments                                                    |
+============================+===========================================+=================+=============================================================+
| ``[ 1, 2, 3, 4, 5, 6 ]``   | ``[]``                                    | no              |                                                             |
+----------------------------+-------------------------------------------+-----------------+-------------------------------------------------------------+
| ``[ 1, 2, 3, 4, 5, 6 ]``   | ``[ 1, 2, 3, 4, 5, 6, 7 ]``               | no              |                                                             |
+----------------------------+-------------------------------------------+-----------------+-------------------------------------------------------------+
| ``[ 1, 2, 3, 4, 5, 6 ]``   | ``[ 6, 5, 4, 3, 2, 1 ]``                  | no              | not in the correct order                                    |
+----------------------------+-------------------------------------------+-----------------+-------------------------------------------------------------+
| ``[ 1, 2, 3, 4, 5, 6 ]``   | ``[ 1, 2, 3, 4, 5, 6 ]``                  | yes             |                                                             |
+----------------------------+-------------------------------------------+-----------------+-------------------------------------------------------------+
| ``[ 1, 2, 3, 4, 5, 6 ]``   | ``[ 1, 2, any(), 4, 5, 6 ]``              | yes             | ``any()`` can replace any single element...                 |
+----------------------------+-------------------------------------------+-----------------+-------------------------------------------------------------+
| ``[ 1, 2, 3, 4, 5, 6 ]``   | ``[ 1, 2, 3, any(), 4, 5, 6 ]``           | no              | ...but this element must be present                         |
+----------------------------+-------------------------------------------+-----------------+-------------------------------------------------------------+
| ``[ 1, 2, 3, 4, 5, 6 ]``   | ``[ 1, 2, any_or_none(), 5, 6 ]``         | yes             | ``any_or_none()`` can replace any number of elements...     |
+----------------------------+-------------------------------------------+-----------------+-------------------------------------------------------------+
| ``[ 1, 2, 3, 4, 5, 6 ]``   | ``[ 1, 2, 3, any_or_none(), 4, 5, 6 ]``   | yes             | ...even zero                                                |
+----------------------------+-------------------------------------------+-----------------+-------------------------------------------------------------+
| ``[ 1, 2, 3, 4, 5, 6 ]``   | ``[ any_or_none(), 3, any(), 5, 6 ]``     | yes             | you may combine ``any()`` and ``any_or_none()``             |
+----------------------------+-------------------------------------------+-----------------+-------------------------------------------------------------+
| ``[ 1, 2, 3, 4, 5, 6 ]``   | ``[ any_or_none(), 3, any_or_none() ]``   | yes             | equivalent to ``superset(3)``, which may be more readable   |
+----------------------------+-------------------------------------------+-----------------+-------------------------------------------------------------+

And you may combine any other matching mechanism as well:

+----------------------------+-----------------------------------------------------------------------+-----------------+----------------+
| message                    | template                                                              | matched ?       | comments       |
+============================+=======================================================================+=================+================+
| ``[ 1, 2, 3, 4, 5, 6 ]``   | ``[ lower_than(10), 2, 3, any_or_none() ]``                           | yes             |                |
+----------------------------+-----------------------------------------------------------------------+-----------------+----------------+
| ``[ 1, 2, 3, 4, 5, 6 ]``   | ``[ any_or_none(), lower_than(2), any_or_none(), 3, 4, 5, any() ]``   | yes             |                |
+----------------------------+-----------------------------------------------------------------------+-----------------+----------------+
| ``[ 1, 2, 3, 4, 5, 6 ]``   | ``superset(greater_than(5))``                                         | yes             |                |
+----------------------------+-----------------------------------------------------------------------+-----------------+----------------+

Matching Mechanisms Valuation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To avoid writing different templates for both sending and receiving
purposes, Testerman proposes an extension to TTCN-3 to valuate some
matching mechanisms.

For instance, if you defined the following template:

.. code-block:: python

    mw_received_message = { 'location': 'Grenoble, France', 'weatherForecast': { 'temperature': between(0, 30) } }

You may also send it though it does not contain only fully qualified
values due to the ``between`` matching condition. In this example, the
sent value will use a ``temperature`` field valuated to a random integer
between 0 and 30 (inclusive).

The following table provides the possible valuations for the matching
mechanisms that implement one:

+-------------------------------+------------------+-----------------------------+------------+
| template matching mechanism   | valuation type   | valuation value             | comments   |
+===============================+==================+=============================+============+
| ``between(a, b)``             | integer          | random integer >= a, <= b   |            |
+-------------------------------+------------------+-----------------------------+------------+
| ``lower_than(a)``             | a's type         | value of a                  |            |
+-------------------------------+------------------+-----------------------------+------------+
| ``greater_than(a)``           | a's type         | value of a                  |            |
+-------------------------------+------------------+-----------------------------+------------+
| ``any()``                     | ``None``         | ``None``                    |            |
+-------------------------------+------------------+-----------------------------+------------+

All valuations are implemented so that they lead to a value that matches
the corresponding matching mechanisms. When trying to send a message
that contains non-value-able matching mechanisms, a Testerman exception
occurs.

Alternatives
~~~~~~~~~~~~

Alternatives are a way to express the branching of a test behaviour upon
the reception of messages on selected ports, timer events, or
termination of (parallel) test components. Basically, you can see them
as a kind of ``switch..case`` operating asynchronously and
self-reevaluating in an infinite loop, until one branch is selected.
This is a pooling loop where we wait for SUT (or Timer or PTC) events.

The event is called a "branch condition", and is associated to some code
to execute if the condition is met, i.e. when the branch is selected.
Branches can be of five different types:

-  *receiving-branch*: such a branch is selected when a message matching
   a template has been receiving on a port. The associated condition is
   expressed, in Testerman, using ``port.RECEIVE(template)``, as
   detailed below.
-  *timeout-branch*: this kind of branch is selected when a timer
   expires. The associated condition is expressed using
   ``timer.TIMEOUT``.
-  *done-branch*: the associated branch is selected when a PTC is
   complete; it is denoted ``ptc.DONE`` in Testerman.
-  *killed-branch*: the associated branch is selected when a PTC is
   killed; denoted ``ptc.KILLED`` in testerman.
-  TTCN-3 also specifies an *altstep-branch*, which is currently not
   supported in Testerman.

Notice that all branch conditions syntaxes use methods or members in
uppercase. It helps differentiate them from the operations
``port.receive(template)``, ``timer.timeout()``, ``ptc.done()``,
``ptc.killed()`` respectively, which are basically shortcuts to a
``alt()`` statement containing only a single branch condition.

Additionally, a branch condition can be optionally guarded, i.e. only
considered if an additional condition evaluates to true. If not
provided, the guard is assumed to be always fulfilled, and the branch
condition is always taken into account.

Finally, the branch contains some code to execute if its branch
condition is matched. In Testerman, this code is written as a list of
``lambda`` functions (aka anonymous functions).

*Note for the curious readers*: lambda functions are used to prevent
evaluating their contained statements when calling the ``alt()``
function - since we basically write Python code in the Testerman ATS,
Python naturally evaluates all arguments to a function before being able
to call it. In our case, this is not what we want, since we want to
execute code conditionally. As an alternative (no pun intended), you may
call a single function that contains all your code for the branch. This
is, by the way, your only choice if you need multiple-line lambda
functions (containing control structures such as ``if/else``, ``while``,
...).

These complete branches (optional guard, branch condition, code) are
technically written as a list, and all these branches are gathered into
another, ordered list which is passed as the single argument to the
``alt()`` function, leading to the following kind of construct:

.. code-block:: python

    alt([
      [ port01.RECEIVE(mw_myTemplate),
        lambda: log("This is a receiving-branch"),
      ],
      [ port02.RECEIVE(mw_mySecondTemplate),
        lambda: log("This is another receiving-branch, on an other port"),
      ],
      [ port01.RECEIVE(),
        lambda: log("Still a receiving-branch, matching all messages on port01"),
        lambda: log("You can use several lambda in the 'code block'"),
        lambda: setverdict('fail'),
      ],
      [ lambda: a >= 1, port02.RECEIVE(mw_myThirdTemplate),
        lambda: log("This is another receiving-branch, guarded only considered if a >= 1"),
      ],
      [ t_timer.TIMEOUT,
        lambda: log("This is a timeout-branch"),
      ],
      [ ptc.DONE,
        lambda: log("This is a done-branch"),
      ],
      [ ptc.KILLED,
        lambda: log("This is a killed-branch"),
      ],
    ])

The order branches are written does matter, due to the following rules
when entering an ``alt()``:

-  whenever we enter a alt or loop over it (once all conditions have
   been checked and mismatched, or due to an explicit repeat using
   ``REPEAT``), a "snapshot" of the current system is taken, memorizing
   all message queues states on all ports that are involved in the alt
   (actually, this snapshot is not implemented for now - ticket:20 -
   just consider it should be the expected behaviour, however) - in our
   example, ``port01`` and ``port02`` - as well as the current known PTC
   and timer event,
-  we try to match the snapshot messages/events against the different
   branch conditions ``in their order of appearance`` - providing their
   guards are fulfilled (they are re-evaluated at each loop)
-  if the branch condition is matched, then the associated code is
   executed. If the last executed statement evaluates to ``REPEAT``, we
   restart the loop from scratch, with the matched message consumed,
   re-snapshooting the current system state. If the last executed
   statement evaluates to anything else, we exit the ``alt()`` call,
   with the matched message consumed, but all other messages on other
   ports unchanged. Matching a condition is the only way to exit a
   ``alt()`` call.
-  if the branch condition is mismatched, we continue with the next
   branch condition
-  once we mismatched all conditions in the alt, we discard the
   mismatched message, and restart our pass with the next message.

Since matching is "first-match" and not "best-match" based, the order
does matter. In particular, in something like:

.. code-block:: python

    alt([
      [ port01.RECEIVE(),
        lambda: log("This condition hides the next one"),
      ],
      [ port01.RECEIVE(mw_myTemplate),
        lambda: log("This log will never be displayed"),
      ],
    ])

both conditions are expecting a message on the same port, but even if we
receive a message that matches ``mw_myTemplate``, it will first match
the default template implicitly provided in ``port01.RECEIVE()``,
keeping the second branch from being selected.

Branch Conditions
^^^^^^^^^^^^^^^^^

...

Code Block
^^^^^^^^^^

A code "block" is typically a list of lambda functions to call in this
order. While this is quite convenient for small actions, such as sending
a message back, setting a verdict, logging something, or event stop the
current test component or test case, this is sufficient.

However, if you need to execute more complex statements, in particular
control statements such as ``if/elif/else``, ``for..in``, or even
variable assignment, you won't be able to do it from a lambda. In this
case, you'll need to implement a function external to the ``alt`` call,
or, if you just want to assign a variable, use something like a
``StateManager`` instance, which has been designed for this kind of
case.

Examples: If you need an additional condition or loop in a branch:

.. code-block:: python

    def f_messageHandler(message):
      if message['method'] == 'POST':
        action1()
      elif message['method'] == 'PUT':
        action2()

    def f_doSomeLoop():
      for i in range(10):
        port02.send(m_response(count = i))

    alt([
      [ port01.RECEIVE(mw_request(), value = 'msg'),
        lambda: f_messageHandler(value('msg')),
      ],
      [ port02.RECEIVE(),
        lambda: f_doSomeLoop(),
      ],
      ...
    ])

Notice that most conditions could be embedded into the matching
template too. In the example above, we may have just use 2 branch
conditions, one on ``port01.RECEIVE(mw_postRequest())``, another one on
``port01.RECEIVE(mw_putRequest())``.

Loops, to a certain extent, can also be collapsed to a single line
instruction using Python list comprehensions:
``lambda: [ port02.send(m_response(count = i)) for i in range(10) ]``
would have been equivalent to the ``f_doSomeLoop()`` code above, but may
be less readable.

In case of variable assignation, something like ``lambda: a = 1``,
you'll simply get a syntax error. You can't assign a variable directly
from a lambda, but you can assign a member variable, or use a
``StateManager``:

.. code-block:: python

    # This sample counts the number of requests received on a port
    count = StateManager(0)

    alt([
      [ port01.RECEIVE(mw_request()),
        lambda: count.set(count.get() + 1), # increment a
        lambda: REPEAT, # repeat the alt
      ],
      [ port02.RECEIVE(),
        # no action - just exit the alt when something has been received on port02
      ]
    ])

    log("OK, we received %d requests on port01" % count.get())

``StateManager`` objects can be quite convenient to implement state
machines (hence their names), as we will see below.

Repeating a Alt
^^^^^^^^^^^^^^^

By default, when a branch is selected, its code block is executed and
the alt returns. If you need to re-enter the loop, waiting for another
event, you may use the special "Testerman keyword" ``REPEAT`` as the
(usually last) action in your code block:

.. code-block:: python

    alt([
      [ port01.RECEIVE(mw_interestingMessage()),
        lambda: log("Got it !") # then exit the alt
      ],
      [ port01.RECEIVE(mw_keepAlive()),
        lambda: log("KA message received, sending response")
        lambda: port01.send(m_keepAliveResponse()),
        lambda: REPEAT, # repeat the alt
      ],
    ])

Repeating the alt is the default behaviour when receiving a message that
does not match your templates. So it's not use adding an alternative
branch if you don't need to perform any particular action on this
message.

``REPEAT`` can also be returned by the function called in your code
block. Combined with the fact that if ``REPEAT`` is not the last action
of your code block, it breaks your action sequence to restart the alt,
discarding the remaining actions, this can lead to interesting things:

.. code-block:: python

    count = 0

    def f_conditionalLoop():
      count += 1
      if count < 10:
        return REPEAT
      return False # or anything != REPEAT

    alt([
      [ port.RECEIVE(),
        lambda: action1(),
        lambda: f_conditionalLoop(), # if it returns REPEAT, action2 won't be executed this time.
        lambda: action2()
      ]
    ])

    # action2 will be executed only in the last loop, before leaving the alt

However, this example would rather be implemented with two alternative
guarded branches (more readable).

Returning from a Alt
^^^^^^^^^^^^^^^^^^^^

By default, when a branch is selected, its code block is executed and
the alt returns, so you don't need to return explicitly. However, you
may implement conditional return in your list of actions via external
functions:

.. code-block:: python

    def f_shouldWeContinue():
      if count > 10 and timer.read() < 10.0:
        return RETURN # don't continue
      return True # or anything != RETURN

    alt([
      ...
      [ port.RECEIVE(),
        lambda: action1(),
        lambda: f_shouldWeContinue(), # if it returns RETURN, action2 won't be executed
        lambda: action2()
      ]
    ])

Returning the "Testerman keyword" ``RETURN`` immediately returns from
the alt, discarding the subsequent actions. Writing it statically is
also possible, but would have exactly the same effect as commenting out
the subsequent actions:

.. code-block:: python

    alt([
      [ port.RECEIVE(),
        lambda: action1(),
        lambda: RETURN,
        lambda: action2(),
        lambda: action3()
      ]
    ])
    # equivalent to:
    alt([
      [ port.RECEIVE(),
        lambda: action1(),
      ]
    ])

Guards
^^^^^^

Guards are defined as callable/0 Python objects, that is functions that
do not take any argument. If the first element of a branch declaration
list is such a callable object, Testerman assumes this is a guard. If
not, the first element of the list is assumed to be the branch condition
- this is the way the guard can be optional.

The most usual way to implement such guards is, once again, ``lambda``
functions:

.. code-block:: python

    class TC_GUARD(TestCase):
      def body(self):
        a = StateManager(0)

        alt([
          [ port01.RECEIVE(m_something()),
            lambda: log("let's increment a"),
            lambda: a.set(a.get() + 1),
            lambda: REPEAT,
          ],
          [ lambda: a.get() >= 1,
            port01.RECEIVE(),
            lambda: log("ok, now we are sure that we received at least once m_something() on port01"),
          ],
        ])

...

Alt Execution
^^^^^^^^^^^^^

You can execute one ``alt()`` per test component "thread". An alt is
interruptible via ``ptc.kill()`` or ``ptc.stop()`` from any other test
component, or only by a matching event. So be careful when entering the
function, be sure to have a watchdog timer or a way to stop the polling
loop gracefully.

Default Behaviours may help you with setting such watchdog timers for
all ``alt()`` at once.

Default Behaviours
~~~~~~~~~~~~~~~~~~

It is not unusual to have one or several events to catch systematically
in a ``alt`` to execute some default actions, such as stopping the test
case on error due to receiving a non-explicitly handled message, a
global watchdog timeout keeping your test case from running
indefinitely, or dealing with "background", uninteresting messages such
as keep-alive probes.

In these case, you may appreciate to implement one or several default
behaviours.

Basically, a default behaviour is a set of alternative branches that are
automatically appended to any ``alt()`` defined branches. This set can
be activated and deactivated at any time. It is also possible to
activate multiple default behaviours - however they will be handled in
the order or their activation.

Activating a Default Behaviour
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To activate, i.e. register, a default behaviour, use:

.. code-block:: python

    myDefaultBehaviour = activate([
      [ t_watchdog.TIMEOUT,
        lambda: log("Global watchdog expiry - stopping testcase"),
        lambda: setverdict("fail"),
        lambda: stop()
      ],
      [ port.RECEIVE(),
        lambda: log("Unknown message received. Strict mode: stopping testcase"),
        lambda: setverdict("inconc"),
        lambda: stop()
      ],
    ])

You noticed that ``activate`` takes only one argument that is exactly
constructed the same as for a ``alt()``. It may contain as many branches
as needed. ``activate`` returns an identifier that is suitable for a
call to ``deactivate`` (see below), in case of you need to deactivate
thisdeault behaviour.

Since you can activate multiple default behaviours in a row, it may be
convenient to separate the branches sets according to their functions.
For instance, one set for a global watchdog, one set for background
error management:

.. code-block:: python

    defaultWatchdog = activate([[t_watchog.TIMEOUT, lambda: setverdict('fail'), lambda: stop()]])
    defaultError = activate([[port.RECEIVE(mw_errorMessage()), lambda: setverdict('fail'), lambda: stop()]])

An activation is only valid within a single test component, depending on
where you activated it from. As a consequence, if you want to use a
default behaviour in the MTC and in each PTC you create, you have to
activate it from each PTC in addition to the MTC.

Notes:

-  a default behaviour activated from within an alternative branch will
   only be taken into account in the next ``alt`` call and not in the
   current one, if it is repeated.

Deactivating a Default Behaviour
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Once a default behaviour has been activated using ``activate()``, it is
taken into account in all subsequent calls to ``alt()`` (or functions
that embeds an alt, such as ``timer.timeout()``, ``port.receive()``,
etc) for the current test component. At any time, however, you may
deactivate it using the identifier returned during its activation:

.. code-block:: python

    defaultWatchog = activate([ ... ])

    ...

    deactivate(defaultWachdog)
    # From now on, no more default watchdog handling in alt()

You can only deactivate a default behaviour that was activated in the
same test component. Deactivating an already-deactivated behaviour has
no effect.

Notes:

-  a default behaviour deactivated from within an alternative branch
   will only be discarded in the next ``alt`` call and not in the
   current one, if it is repeated.

Template Value Extraction
~~~~~~~~~~~~~~~~~~~~~~~~~

Full Extraction
^^^^^^^^^^^^^^^

TTCN-3 defines a single way to extract a value from a message that
matched a template, using the ``->`` syntax and ``value`` (and
``sender``) keywords.
For instance:

.. code-block:: ttcn3

    port.receive(my_template) -> value m, sender s;

will store the received message that matched the template
``my_template`` to the local variable ``m``, and the address of the
sender (either a test component reference or a SUT address) to the local
variable ``s``.
Once stored, you may traverse the received message as any other
structured value to find the field of interest. For instance, if we
assumed we received a SIP request to which we should reply with a
response using the same call-id, we may use:

.. code-block:: ttcn3

    type record SipRequestType {
      charstring method,
      ...
      charstring callId,
      ...
    }

    template SipRequestType mw_sipRequest()
    {
      method := ?,
      ...
      callId := ?,
      ...
    }

    // ...

    charstring callId;

    port.receive(nw_sipRequest) -> value request;
    callId := request.callId

    // Now reinject the callId into a response

    resp = m_sipResponse(callId)
    // ...

Testerman offers a similar mechanism to match the complete received
message (and the associated sender, if needed). The syntax, however, is
different:

.. code-block:: python

    port.receive(m_myTemplate, value = 'm', sender = 's')

This will store the received message matching the template
``my_template`` to an internal structure whose value can be retrieve
later within the same test component "thread" (i.e. within the
behaviour/PTC "thread" or the main/MTC "thread") using:

.. code-block:: python

    matchedMessage = value('m')

The sender (either a reference to a test component (``TestComponent``
instance) or the SUT address (Python built-in ``string``) can be
retrieved a similar way within the current test component "thread" with:

.. code-block:: python

    messageSender = value('s')

Of course, it is not mandatory to store the matched value to a variable;
however you are advised to do so, as the matched value may be overriden
on the next template match if you use the same value/sender name.

The above SIP example then translates to:

.. code-block:: python

    def mw_sipRequest():
      return { 'method': any(), 'callId': any() }

    port.receive(sip_request(), value = 'request')
    callId = value('request')['callId']

    resp = m_sipResponse(callId)
    ...

Selective Extraction
^^^^^^^^^^^^^^^^^^^^

The mechanism above is quite convenient to get a whole message.
Sometimes, however, you may prefer get only a part of the matched
message to avoid a structure traversal, especially when this structure
is not as trivial as in the example above or when wildcards and lists
are involved.

For example, if your template is something like:

.. code-block:: python

    # In SUA protocol, we may get an undefined list of parameters that contain a tag and a value.
    # We are only interested in one of these parameters, but we cannot control the order
    # we received them.
    mw_myTemplate = [ any_or_none(), { 'tag': 0x06, 'value': any() }, any_or_none() ]
    # This is equivalent to my_template = superset({ 'tag': 0x06, 'value': any() })

Once we matched it, we have to find the interesting parameter manually,
checking the tag value in each entry of the matched list (provided all
these entries contains a\ ``tag`` field, which may be not mandatory
depending on the message structure / involved codec). Instead of
traversing the list manually, Testerman proposes a selective extraction
mechanism that is tightly bound to the template:

.. code-block:: python

    mw_myTemplate = [ any_or_none(), { 'tag': 0x06, 'value': extract(any(), 'my_val') }, any_or_none() ]

Using the ``extract(<matching mechanism>, <name>)`` feature, you can
directly get the value you want to extract without requiring a full
message traversal. The matched value, if the template has matched, is
then available through the ``value(<name>)`` syntax as for full message
extraction.

Full example:

.. code-block:: python

    mw_myTemplate = [ any_or_none(), { 'tag': 0x06, 'value': extract(any(), 'my_val') }, any_or_none() ]

    alt([
      [ port.RECEIVE(mw_myTemplate),
        lambda: log("parameter 0x06 value: %s" % value('my_val'),
      ]
    ])

Notice that you can freely use ``extract`` in sending templates
providing the wrapped template matching condition has a tangible
valuation (typically ``between``, ``greater_than``, ``lower_than``, ...
- selective extraction is meaningless, but fully usable, to extract
constants).

**Limitations**:

-  This selective extraction mechanism does not work with
   ``any_or_none()`` (TTCN-3 ``*``) wildcard.
-  Calls to ``value(name)`` where ``name`` is a string referring to a
   selected extraction in a template that did not match is undefined
   (may or may not return a value, depending on when the mismatch was
   detected).

Verdict Management
~~~~~~~~~~~~~~~~~~

Each test component has a local verdict that can be set and retrieved
at any moment, from anywhere during the test component execution.

This verdict is said to be local as it is only valid for the running
test component: this is the PTC verdict in a behaviour body or any
functions called from it, or the MTC verdict in the test case body or
any functions called from it.

You can only manipulate (get or set) the local verdict of your current
context. The test case verdict is automatically computed from merging
the different local verdicts.

In Testerman, verdict values are string literals instead (while they are
keywords in TTCN-3). However, the full verdict values are available, and
some Testerman constants are provided for convenience to avoid using
string values:

+------------------+--------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| TTCN-3 verdict   | Testerman verdict value        | description                                                                                                                                                                                                                                                            |
+==================+================================+========================================================================================================================================================================================================================================================================+
| ``none``         | ``NONE`` (or ``'none'``)       | default verdict, unset                                                                                                                                                                                                                                                 |
+------------------+--------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``pass``         | ``PASS`` (or ``'pass'``)       | the test component logic considers the SUT reactions it observed were what it expected. Test case passed successfully.                                                                                                                                                 |
+------------------+--------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``fail``         | ``FAIL`` (or ``'fail'``)       | the test component logic considers the SUT reactions it observed were not the expected ones. Due to the verdict values precedence rules, if at least one local verdict is set to ``fail``, it implies that the Test case verdict will be ``fail``, too.                |
+------------------+--------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``inconc``       | ``INCONC`` (or ``'inconc'``)   | inconclusive: not enough elements have been observed to tell if the SUT reactions were correct or not. We can't tell that the test case failed because what we planned to test was not tested actually. Useful when some prerequisites cannot be set up or verified.   |
+------------------+--------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``error``        | ``ERROR`` (or ``'error'``)     | an execution error occurred. Automatically set by the test execution system on runtime exception; cannot be set by the user.                                                                                                                                           |
+------------------+--------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

Local verdicts are automatically merged to create a "test case" verdict
using the following rules:

-  the test case verdict is initialized to ``none``
-  whenever a test component is over (either done or killed), the test
   case verdict is updated with its local verdict,
-  when updating a verdict (including the test case verdict), the
   following precedence rules apply: ``none`` < ``pass`` < ``inconc`` <
   ``fail`` < ``error``, which can also be visualized as indicated in
   the table below, indicating the resulting verdict after an update:

+-------------------+----------------------------------------------+
| current verdict   |                  new verdict                 |
|                   +---------------+----------+--------+----------+
|                   | pass          | inconc   | fail   | none     |
+===================+===============+==========+========+==========+
| none              | pass          | inconc   | fail   | none     |
+-------------------+---------------+----------+--------+----------+
| pass              | pass          | inconc   | fail   | pass     |
+-------------------+---------------+----------+--------+----------+
| inconc            | inconc        | inconc   | fail   | inconc   |
+-------------------+---------------+----------+--------+----------+
| fail              | fail          | fail     | fail   | fail     |
+-------------------+---------------+----------+--------+----------+

The ``error`` value overwrites all others.

Notice that the order of verdict merges does not affect the final test
case verdict (when we wait for N PTCs to complete, for instance).

Setting a Verdict
~~~~~~~~~~~~~~~~~

You can only set a local verdict; the test case verdict is automatically
computed by the system according to the different local ones.

To update the current local verdict, use the Testerman function
``setverdict`` anywhere in your test case or behaviour body or in a
called function, for instance:

.. code-block:: python

    setverdict(PASS) # you may use setverdict('pass') if not using the pre-defined constant

Setting a verdict that is not in
``[ 'error', 'none', 'pass', 'fail', 'inconc' ]`` leads to a runtime
exception.

However, as a best practice to make your code more readable and more
reusable, you should only set verdicts from behaviour an test case
``body`` methods, while functions you call should never decide for such
a verdict: only the caller should know how to interpret a function
result.

Getting a Verdict
~~~~~~~~~~~~~~~~~

Local Verdict (Test Component)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can get a verdict at any time during a test component execution
using the Testerman function ``getverdict``:

.. code-block:: python

    v = getverdict()

The returned value is the current local verdict, as a string in
``[ 'error', 'none', 'pass', 'fail', 'inconc' ]`` (i.e. in
`` [ ERROR, NONE, PASS, FAIL, INCONC ]``).

Additionally, when a test component is over (either done or killed), you
may retrieve their local verdict with the ``getverdict()`` method:

.. code-block:: python

    ptc = create()
    ptc.start(MyBehaviour())
    ptc.done()
    v_ptcVerdict = ptc.getverdict()

Test Case Verdict
^^^^^^^^^^^^^^^^^

The test case verdict is returned as a result to its execution; if you
don't store it in a variable, it is lost. For instance:

.. code-block:: python

    TC_SAMPLE_01().execute()
    v = TC_SAMPLE_02().execute()
    if v != 'pass':
      stop()

could be a way to stop an ATS when a particular test case fails (or more
precisely - does not succeed), avoiding executing additional test cases
whose outcomes would already be known since this basic test case failed.

Reference: Testerman API
------------------------

This API may evolve, but its backward compatibility is guaranteed, so
that your ATSes can still work in next Testerman versions.

The whole API is made accessible directly in the ATS namespace. You
should NOT import any Testerman modules in your ATS, as their names and
contents may evolve without notice.

Timer Objects
~~~~~~~~~~~~~

Constructor:

.. code-block:: python

    Timer(duration = None, name = None)

Methods:

.. code-block:: python

    start(duration = None)
    stop()
    running()
    timeout()
    read()

TestComponent Objects
~~~~~~~~~~~~~~~~~~~~~

Constructor: N/A (constructed from a testcase only)

Methods (meaningless on MTC):

.. code-block:: python

    alive()
    running()
    start(behaviour, **kwargs)
    stop()
    kill()
    done()

Members (meaningless on MTC):

.. code-block:: python

    DONE
    KILLED

Specials:

.. code-block:: python

    get_item[name] # provides a reference to a TC port - creates it dynamically if needed

Port Objects
~~~~~~~~~~~~

Constructor: N/A (constructed dynamically when calling
``tc['portname']``)

Methods:

.. code-block:: python

    send(message, to = None)
    receive(template = None, value = None, sender = None, from_ = None)
    start()
    stop()
    clear()
    RECEIVE(template = None, value = None, sender = None, from_ = None)

Behaviour Objects
~~~~~~~~~~~~~~~~~

Constructor:

.. code-block:: python

    Behaviour()

TestCase Objects
~~~~~~~~~~~~~~~~

Constructor:

.. code-block:: python

    TestCase(title = None, id_suffix = None)

Methods:

.. code-block:: python

    set_description(description)
    create(name = None, alive = False)
    execute(**kwargs)
    stop_testcase_on_failure(stop = True)

Functions Callable while a Testcase is Running
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Can be used anywhere (functions, altsteps, behaviour, testcases):

.. code-block:: python

    stop()
    log(msg)
    getverdict(verdict)
    alt(alternatives)
    get_variable(name, default_value = None)
    set_variable(name, value)
    value(name)
    sender(name)
    match(message, template)
    action(message, timeout = 5.0)

Should be used in behaviours and testcases only (avoid setting the local
verdict from anywhere):

.. code-block:: python

    setverdict(verdict)

Should be used in testcases only (avoid dynamic test reconfiguration):

.. code-block:: python

    connect(portA, portB)
    disconnect(portA, portB)
    port_map(port, tsiPort)
    port_unmap(port, tsiPort)

Default alternatives management:

.. code-block:: python

    activate(altstep)
    deactivate(id_)

Templates matching mechanisms:

.. code-block:: python

    greater_than(value)
    lower_than(value)
    between(a, b)
    any()
    any_or_none()
    empty()
    pattern(pattern)
    omit()
    ifpresent(template)
    length(template)
    superset(*templates)
    subset(*templates)
    complement(*templates)

Selective message value extraction:

.. code-block:: python

    extract(template, value)

Codec :

.. code-block:: python

    with_(codec, template)

Control Part
~~~~~~~~~~~~

Functions:

.. code-block:: python

    enable_debug_logs()
    disable_debug_logs()
    disable_logs()
    enable_logs()
    get_variable(name, default_value = None)
    set_variable(name)
    with_test_adapter_configuration(name)
    bind(tsiPort, uri, type_, **kwargs)
    stop_ats_on_testcase_failure(stop = True)

TestAdapterConfiguration Objects
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Constructor:

.. code-block:: python

    TestAdapterConfiguration(name)

Methods:

.. code-block:: python

    bind(tsiPort, uri, type_, **kwargs)

Test-unrelated
~~~~~~~~~~~~~~

Functions:

.. code-block:: python

    octetstring(s)

StateManager Objects
^^^^^^^^^^^^^^^^^^^^

Constructor:

.. code-block:: python

    StateManager(self, state = None)

Methods:

.. code-block:: python

    get()
    set(state)


