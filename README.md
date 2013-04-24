Lending Club Auto Investor
=======================

A daemon written in python that will automatically invest available cash in your LendingClub account.

Disclaimer
--------------------
I have tested this tool to the best of my ability but understand that it may have bugs. Use at your own risk!

Why?
--------------------
The trouble I've had when investing money in LendingClub is that not all the loans get funded, so it becomes a back-and-forth dance of investing all available cash and reinvesting as some of it becomes available again. Two steps forward, one step back. This means that investing large sum of money can take quite awhile to get fully into the system.

How it works
--------------------
This is a background daemon (or can be run in the foreground) that checks your account every 30 minutes. If the available cash meets or exceeds a threshold you set (see Minimum cash section), it's automatically invested in a portfolio with an average return within your specified bounds.

To put it simply, the tool does the same thing as if you were to:
 * Log into your account
 * Click Invest
 * Click More Options
 * Select an average return you want
 * Now click Continue and to through the following two pages to invest in that portfolio.


Flexibility
--------------------
Through easy to use command prompts, you can set the minimum cash to invest and the min/max *average* interest portfolio you want to invest in. 

Current Limitations
--------------------
You **CANNOT** set filters or exclude specific loans or loan rate classes.

Help
--------------------
Please help me by forking and committing enhancements!

Install
--------------------
As long as the requirements are met, you can run the script right from where it is on your system (see Running).

### Requirements
Currently there is no installer, so you have to install the following packages manually or with [pip](https://pypi.python.org/pypi/pip).
 * python-daemon
 * requests
 * beautifulsoup4
 * html5lib

Running
--------------------

### Foreground
To start the tool in the foreground:

    python ./investor.py

The script will run in a loop and print all the output to the screen until you exit it with CTRL+C.

### Background (daemon)
To run it as a background daemon

    python ./investor.py start

All output will be sent to `daemon.log` which is located in the same directory as investor.py.

To stop the daemon run:

    python ./investor.py stop

### Usage
To see the useage info

    python ./investor.py -h


Options
--------------------
When you run the tool, it will take you though a series of prompts to define how to invest for you.

### Email / Password
This is the email and password you use to sign into LendingClub. Your password will be kept in memory but never saved to file.

### Minimum cash
When the auto investor runs it will attempt to invest **ALL** available cash in your account into a investment portfolio. However, you will probably want it to wait until your account has a certain amount of cash before investing. For example, $25 will only invest in a single note, whereas $1000 could be invested across up to 40 notes.

### Min/Max Percent interest rate
When the minimum available cash option is met, the auto investor will query the LendingClub API and get a list of possible investment portfolios available at that moment. To pick the appropriate one for you, it needs to know what the minimum and maximum *AVERAGE* interest rate value you will accept. The investment option closest to the maximum value will be chosen and all your available cash will be invested in it.

This value relates to finding a investment portfolio using the slider on the Invest page of www.LendingClub.com. It's not possible, at any given time, to define an absolute interest rate value, so we need to know the range that you will accept.

**Note** This does *NOT* filter out individual notes of a different interest rate.

### Named portfolio
After the auto investor puts in an investment order, it can assign all the new notes to a specific portfolio. This option lets you choose from existing portfolios in your account or create a new one.

### Review
After all the options are set, you will be given a review screen to verify those values. If you approve, type Y + Enter to start the program. It will now check your account every 30 minutes to see if there is enough available cash in your account to invest.



