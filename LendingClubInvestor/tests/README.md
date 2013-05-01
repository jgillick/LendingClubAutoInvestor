Unit Testing
=======================
This directory contains all the unit tests for the LendingClub Auto Investor tool.

Requirements
--------------------
To emulate the LendingClub API, the test suite will run a simple [nodejs](http://nodejs.org/) server. Be sure you have nodejs [installed](http://nodejs.org/) on your system before running any of the tests, or they will fail.

The nodejs server will be running on port 7357. You can change this in `node/server.js`.

Running
--------------------
From the test directory, run this command:

    python ./test_investor.py

It will take between 13 - 25 seconds to run.

Interpreting results
--------------------
Any test failure will be reported at the end of the output and will start with `FAIL:` and followed by a message and traceback.

If no failures were found, the test script will end with the text `OK`.

You can largely ignore output that starts with `INVESTOR ERROR:` -- which are send from the investor tool itself during the tests. The tests try to intentionally break parts of the investing flow to verify that the tool gracefully handles them. These errors are normal during testing.

Troubleshooting
--------------------
In the unlikely event that the nodejs webserver is not properly shutdown by the test script after the last time it was run, you'll get many errors that look like this:

    events.js:71
            throw arguments[1]; // Unhandled 'error' event
                           ^
    Error: listen EADDRINUSE
        at errnoException (net.js:770:11)
        at Server._listen2 (net.js:910:14)
        at listen (net.js:937:10)
        at Server.listen (net.js:994:9)
        at dns.js:72:18
        at process.startup.processNextTick.process._tickCallback (node.js:244:9)

If this is the case, manually search for the server and kill it using `ps` and `kill`:

    $ ps -A | grep node
    28393 ttys007    0:00.08 node node/server.js

    $ kill 28393


