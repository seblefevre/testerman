Generate Testerman test cases with Selenium IDE
-----------------------------------------------

Summary
~~~~~~~

`Selenium IDE <http://seleniumhq.org/projects/ide/>`__ is a Firefox
plugin which records user interaction with a web site. The plugin can
then export the list (of user actions) to different formats. The plugin
enabling Selenium IDE to export is called a formatter.

The Selenium team provides bindings for several `programming
languages <http://seleniumhq.org/about/platforms.html#programming-languages>`__.
You can write a test in one of these languages and use the provided
libraries to remote control a browser. Selenium IDE formatters do
exactly that: convert the recorded list into source code for a specific
language.

The Testerman ATS Formatter let's you export your recorded interactions
directly to a Testerman test script (\*.ats). The generated code will
use the ProbeSelenium to control the browser.

Install
~~~~~~~

The formatter is a Firefox plugin, you have to install it on top of the
Selenium IDE plugin. It is attached at the bottom of this page (you can
get it from the svn tree, too). Install it via Firefox: Select File ->
Open File ... and select the \*.xpi file.

Installing a newer versions of the formatter
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Before installing a newer version, make sure to reset the options
(Selenium IDE -> Options -> Options -> Formats -> Testerman ATS
Formatter -> Reset Options) in order to follow the latest changes.
Please be carefully though, as this will erase all your personal
configurations.

How To, Best Practises and Information
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Please read the following instructions carefully (yes, it is long
\*sigh\*). There are a lot of hidden tricks in SeleniumIDE/Testerman one
has to know to efficiently generate ats files.

You should be familiar with writing Testerman ats files manually (and
thus you are familiar with the send/receive concept, alt statements,
verdicts, ...) and know Selenium IDE a little bit (record test cases,
exporting), too. You will find a lot of documentation for Selenium IDE
`here <http://seleniumhq.org/docs/02_selenium_ide.html>`__.

Understanding Selenium
^^^^^^^^^^^^^^^^^^^^^^

Selenium is a suite of different tools. We will use Selenium IDE
(recording user interactions with a web interface) and Selenium RC
(remote executing of "simulated" user actions on a web interface,
acutally, this is done by the ProbeSelenium).

Selenium RC has a set of different type of commands. There are commands
like click(myButton), type(myInput, blablub), getText(myElement),
isEditable(myInput).

Selenium IDE uses these commands but in a slightly changed way. Some
commands are the same (click, open, type), but some others are not
available in Selenium IDE, at least not in their orinigal form. Selenium
IDE uses generated commands from the Selenium RC accessors (getText,
isEditable, ... every command where you would expect a result). Instead
of getXXX, one can use assertXXX, verifyXXX, storeXXX, and/or
waitForXXX. These generated commandes are ultimately translated into
their source command (= the command Selenium RC expects). It will note
change anything for Selenium RC whether you use assertText(id=myElement,
42) or verifyText(id=myElement, 42); the actual command in both cases
will be getText(id=myElement). To see which Selenium RC command will be
produced, have a look at the reference tab in the lower bar of the
Selenium IDE gui. When adding a command, you will see it's argument and
it's base command appear. It is up to the formatter (e.g. the source
code generator) to handle the different command types while still
sending the base command to Selenium RC. Selenium IDE is of course not
able to "record" these generated commands. It knows where you clicked,
but it doesn't know your expectations concering returned results.

Selenium commands are often refered to as "selenese".

Using Selenium IDE generated commands
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

As an example consider you want to fill in a form and expect a certain
text after clicking on the submit button. During recording, you would
type your text into the form and click the button. Selenium will list
something like this:

::

    commands        target      value
    type            id=input_pw     1234
    click           id=login

Now, to check whether your expected text appears on the following page,
right-click on the element where the text should appear (or select the
text, ...). The context menu will propose you a range of commands to
check the elements content. After selecting one command, Selenium IDE
will list something like this:

::

    verifyText      id=header   Login successful

The command will become "getText(id=header)" for Selenium RC. If you had
used assertText() instead, the outcoming Selenium RC commands would have
been the same. The difference lies in the handling of the returned
result (see below for a differentiation of assert and verify). The
target argument is often a "locator", i.e. the element on the web
interface you address. To get an element's locator, you could check the
HTML source (Firebug!) for id or name attributes. However, it is a
probably a good idea to let Selenium IDE choose the locator: "Record" a
dummy click (or something) action on that element to get it's locator
listed and delete the dummy action then.

See http://release.seleniumhq.org/selenium-core/1.0.1/reference.html for
more details

Using Testerman's parameter system
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The Testerman ats formatter supports Testerman's parameter system
(global variables, often called PX\_PASSWORD or PX\_HOST\_IP). There is
a support for "static" and "dynamic" parameters. We call theme "static",
when they are defined in the meta data block at the beginning of the
generated code regardless of the content. You can setup these static
parameters in the formatter's option (Selenium IDE -> Options -> Options
-> Formats). Define here the parameter name, default value and type
("string" or "integer"). Every parameter listed here will always be
dumped. Remember that the parameter's value can be overwritten by the
campaign configuration (when launching a campaing in Testerman).

The Format is "name:value:type\\n". The name has to match
**/!^PX\_[\_A-Z0-9]+$/**. Examples:

::

    PX_DB_SERVER:string:127.0.0.1
    PX_DB_PASSWORD:string:1234
    PX_MAX_CONNECT:integer:10

On the other hand, "dynamic" parameters are set up within the actual
selenese. After recording your actions with Selenium IDE and before
formatting (exporting), you could change some command arguments in order
to make the test more flexible. By replacing a "real" value with it's
parameter name (and it's default value), the test can be adapted to
another test environment. To define a dynamic parameter, replace the
original value by ${PX\_PARA\_NAME:orginalValue}.

Example:

::

    commands        target      value
    type            id=input_pw     1234

The above command generates:

.. code-block:: python

    sel.send(["type", "id=input_pw", "1234"])

Now consider the following

::

    commands        target      value
    type            id=input_pw     ${PX_PASSWORD:1234} ** define parameter name and default value before export **

generates:

.. code-block:: python

    # <parameter name="PX_PASSWORD" default="1234" type="integer"><![CDATA[]]></parameter>
    ...
    sel.send(["type", "id=input_pw", str(PX_PASSWORD)])

As you can see, a new parameter is defined and during the selenium
command, this parameter is used. The parameter definition is to be found
in the meta data block, the value can be overwritten by external
campaing config as mentioned before. Of course, you do/can not redefine
the same parameter several times. Once, your PX\_XXX is defined you can
use in later commands:

old:

::

    commands        target      value
    type            id=input_pw     1234
    assertValue     id=blub     1234

generates:

.. code-block:: python

    sel.send(["type", "id=input_pw", "1234"])
    sel.send(["getValue", "id=blub"])
    alt([
        [ sel.RECEIVE(template = "1234"),
    ...

new:

::

    commands        target      value
    type            id=input_pw     ${PX_PASSWORD:1234}
    assertValue     id=blub     ${PX_PASSWORD}

generates:

.. code-block:: python

    # <parameter name="PX_PASSWORD" default="1234" type="integer"><![CDATA[]]></parameter>
    ...
    sel.send(["type", "id=input_pw", str(PX_PASSWORD)])
    sel.send(["getValue", "id=blub"])
    alt([
        [ sel.RECEIVE(template = str(PX_PASSWORD)),
    ...

The parameter can easily be referred to. This enables you to use static
parameters as well. You do not have to define a default value because
they are defined anyway. Remember that you have to adapt the selenese
\*before\* exporting. Their is one disadvantage: Once you changed your
values to 'PX\_SOMETHING' you won't be able to replay your test case
with Selenium IDE any more.

The rule of thumb is:

``${PX_XXX}`` --> replace this by a variable called ``PX_XXX``

``${PX_XXX:1234}`` --> replace this by a variable called ``PX_XXX``, which
has been set to 1234 in the meta data block

``PX_XXX`` --> take this literally (do not replace anything, used for
``storeXXX()``, see later)

The replace mechanism generally applies to the last argument of a
command (often called "pattern" in Selenium IDE).

The px parameters can be used in conjunction with regular expressions.
The value field is ``regexp:${PX_VAR_NAME:the_actual_expression}``.
Fur further details see the section for regular expressions.

::

    commands        target      value
    assertValue     id=blub     regexp:${PX_PASSWORD:[a-z]?}

Store Commands
^^^^^^^^^^^^^^

Seleniums provides the possiblity to store values in variables. You will
find a lot of storeXXX() fonctions (storeText(), storeAlert(),
storeChecked(), ...). Whenever you use a store command, the Testerman
Formatter will print a send and a receive command (to the port). When
using storeXXX(), the second argument of the command is the name of the
variable to which the value will be assigned. There are two
possibilities to store values. Either you use a "normal" variable name
or you use a name like PX\_XXX (matching the abouve regexp).

::

    commands        target      value
    storeText       link=home   myvari
    storeText       link=home   PX_MYVAR

The generated code will be as follows:

.. code-block:: python

    # store (selinium): myvari = getText(link=home)
    sel.send(["getText", "link=home"])
    sel.receive(value = 'myvari')
    myvari = value('myvari')
    log('myvari = %s' % myvari)
    # store (selinium): PX_MYVAR = getText(link=home)
    sel.send(["getText", "link=home"])
    sel.receive(value = 'PX_MYVAR')
    PX_MYVAR = value('PX_MYVAR'))
    log('PX_MYVAR = %s' % str(PX_MYVAR))

To refer to the stored variables, use the **${nameOfTheVariable}**
syntax as mentioned above. If you used a PX\_XXX variable you could even
store a value and define a default value in the metadata block:

::

    commands        target      value
    storeText       link=home   ${PX_MYVAR:42}

The generated code will be as follows:

.. code-block:: python

    # <parameter name="PX_MY_VAR" default="42" type="integer"><![CDATA[]]></parameter>
    ...
    # store (selinium): PX_MYVAR = getText(link=home)
    sel.send(["getText", "link=home"])
    sel.receive(value = 'PX_MYVAR')
    PX_MYVAR = value('PX_MYVAR'))
    log('PX_MYVAR = %s' % str(PX_MYVAR))

This would enable you to use PX\_MYVAR (with it's default value) even
before storing it. Of course, it's pretty hard to find a use case ;)

Let's take another example. Imagine you want to change a value on the
web interface, check that the settings are saved correctly and then
reset the original value. The naive command list would be:

::

    commands        target            value
    type            name=port         12345
    clickAndWait    id=submit_button 
    assertValue     name=port         12345
    type            name=port         1234 (supposing the original value was 1234)
    clickAndWait    id=submit_button 

While this is pretty forward (and easily recordable), it is not very
flexible. When you are not sure of the system's state before test
execution, it will be hard to reset the "right" default value (in this
case, the original value was 9999 or so). Use storeXXX() to copy and
paste. After recording your test with Selenium IDE and before exporting
to an ats file, change the following:

::

    commands        target      value
    storeValue      name=port   PX_DEFAULT_PORT
    type            name=port   ${PX_NEW_PORT:12345}
    clickAndWait        id=submit_button 
    assertValue     name=port   ${PX_NEW_PORT}
    type            name=port   ${PX_DEFAULT_PORT}
    clickAndWait        id=submit_button 

Just save the value before changing it, then, during "cleanup" reuse the
given name. The above example will produce the following code:

.. code-block:: python

    # <parameter name="PX_NEW_PORT" default="12345" type="integer"><![CDATA[]]></parameter>
    ...
    # store (selinium): PX_DEFAULT_PORT = getValue(name=port)
    sel.send(["getValue", "name=port"])
    sel.receive(value = 'PX_DEFAULT_PORT')
    PX_DEFAULT_PORT = value('PX_DEFAULT_PORT'))
    log('PX_DEFAULT_PORT = %s' % str(PX_DEFAULT_PORT))

    #change to new port
    sel.send(["type", "name=port", str(PX_NEW_PORT)])
    sel.send(["click", "id=submit_button"])
    sel.send(["waitForPageToLoad", "30000"])

    #verify changings
    sel.send(["getValue", "name=port"])
    alt([
        [ sel.RECEIVE(template = str(PX_NEW_PORT)),
            lambda: self.setverdict(PASS),
            lambda: log('getValue(name=port) == ' + str(PX_NEW_PORT) + ' [using PX_NEW_PORT] -> Good!'),
        ],
        [ sel.RECEIVE(template = any_or_none()),
            lambda: self.setverdict(FAIL),
            lambda: log('getValue(name=port) != ' + str(PX_NEW_PORT) + ' [using PX_NEW_PORT] -> Bad!'),
            lambda: stop(),
        ],
    ])

    #clean up
    sel.send(["type", "name=port", str(PX_DEFAULT_PORT)])
    sel.send(["click", "id=submit_button"])
    sel.send(["waitForPageToLoad", "30000"])

Regular Expression
^^^^^^^^^^^^^^^^^^

Sometime you need to check a certain value, but you know only the
expected pattern. Selenium IDE has build-in support for regular
expression (in fact, it says [in our case] to the formatter, that the
user wants to use a regexp). The following example should answer all
questions:

::

    commands        target      value
    assertValue     name=search blub
    assertValue     name=search regexp:^[A-Z]?$
    assertValue     name=search regexp:${PX_MYPATTERN}
    assertTextPresent   regexp:[a-z].?

generates:

.. code-block:: python

    sel.send(["getValue", "name=search"])
    alt([
        [ sel.RECEIVE(template = "blub"), 
    ...
    sel.send(["getValue", "name=search"])
    alt([
        [ sel.RECEIVE(template = pattern(r"^[A-Z]?$")), 
    ...
    sel.send(["getValue", "name=search"])
    alt([
        [ sel.RECEIVE(template = pattern(str(PX_MYPATTERN))),
    ...
    sel.send(["isTextPresent", "regexp:[a-z].?"])
    alt([
        [ sel.RECEIVE(template = True),
    ...

You can combine px parameter definitions with regexp:

::

    commands        target      value
    assertValue     name=search regexp:${PX_REGEXP:[a-e]?}  ** define new px parameter (with default value) and it use it as regexp **

Regular expression are a bit tricky though. In fact, Selenium RC
supports regexp by itself and Testerman does so (vie Python's
re.search()), too. The "problem" is that sometimes Selenium RC has to
use it to determine the result of a command and sometimes Testerman can
just wait for the result and then check it against the regular
expression. Whenever you use a selenese generated from getXXX() (like
assertText(), verifyConfirmation(), ...) the Testerman's (=Python's)
regular expressions will be used. You can see them in the output
(Testerman's function pattern()). On the other hand, commands like
assertTextPresent() (e.g. commands where you expect a boolean response)
will use Selenium RC's regexp. When dumping these commands, you will the
that the literal "regexp:" is still present because it will be send to
Selenium RC. There doesn't seem to be a way to unify the two regular
expression systems, although it probably won't be a problem.

Note: You can not use a variable stored previously via storeXXX() in an
regexp if the variable is **not** a PX\_XXX parameter. By the way,
Selenium IDE doesn't implement variable translation (with
${variableName}) in regular expressions at all. It's the Testerman
Formatter which adds this feature only for PX\_XXX parameters.

See also:
http://release.seleniumhq.org/selenium-core/1.0.1/reference.html#patterns

Assert vs. Verify
^^^^^^^^^^^^^^^^^

assertXXX() and verifyXXX() produce nearly the same code. In both cases,
an alt statement checks whether the returned response matches the
expected result. The difference is that assert() will stop the test case
if the check failed, verify will not (-> assert() generates an extra
"lambda: stop()" for the failing template). Most of the time, you would
probably want to use assert(), but verify() can be handy for debugging
purpose or small and unimportant checks.

Adding comments
^^^^^^^^^^^^^^^

There are to types of comments possible. The first one is inserted via
Selenium IDE -> Edit -> Insert new comment. This will generate a simply
python comment. Or, use the command echo(), which will use Testerman's
log() method.

setverdict()
^^^^^^^^^^^^

The formatter will dump a setverdict(FAIL) during every alt step for the
branch with the not-matching template (no setverdict() in storXXX(),
though). A setverdict(PASS) is only printed in the very last alt branch.
In fact, before dumping the code, the formatter counts all accessors (=
all commands generated from isXXX() or getXXX() = every command where a
result is returned). This enables him to print the setverdict(PASS) only
at the very end.

Best Practices
^^^^^^^^^^^^^^

If Selenium IDE is not recording your actions (although the red button
is pressed), the base url is most likely wrong. Selenium IDE will only
record user interaction with the site given in the base url. You can
change it in the upper "address bar" in Selenium IDE gui.

When using stuff like waitForCondition (e.g. functions with a timeout),
you could consider to set up a high timeout and use a Testerman timer as
watchdog with a lower timeout instead. If the selenium call fails
(=condition didn't become true until the given timeout), the
ProbeSelenium will throw an exception; whereas if the Testerman timer
times out, the test can "fail correctly"

Make sure you use [assert\|verify\|storte]Value() when checking the text
of an input and not [assert\|verify\|store]Text(). Inputs do not have
text, they have values. Applying getText() on an input will return an
empty string.

Once you did your assertions etc (e.g. your test verdict is set), reset
the system to the state before the test.

Wherever you want in the command list in Selenium IDE, you can use "Edit
-> Insert new comment" to add a comment in the generated source coude.
For example, before resetting the system to the former state you could
add a comment saying "clean up"

Import ats files to Selenium IDE
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It is possible to revert the process, e.g. import a generated ats file
to Selenium IDE. It does not work with every ats file, though. In fact,
the generated ats files contain the list of selenese and the import
mechanism exploits this list. Thus, ats without this list cannot be
imported. To open an ats file with Selenium IDE, you have to change the
expected format: Selenium IDE -> Options -> Format -> Testerman Anevia
ATS Formatter. If this option is not available, enable it via Options ->
Options -> Enable experimental features.

Note that the formatter is NOT able to import ats scripts containing
several test cases.

ATTENTION: Make backups of your original ats file. The formatter will
try to warn you if the thinks the file has been touched by hand

Known Issues
~~~~~~~~~~~~

Selenese returning an array
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Some commands return an array (typically commands with
[assert\|verify\|waitFor]All[Buttons\|Links\|...](), like
assertAllLinks()). They are handled by the formatter now in a
experimental version. The generated code may not be what you expected.
The formatter will warn you.


