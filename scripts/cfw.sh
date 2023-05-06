# cfw.sh: wrapper script for Clash-for-windows.
#
# Copyright 2022 Eric Zhuo Chen

# CFW (Clash-for-windows) is my proxy tool of choice now.  It provides binary
# for GNU/Linux, but there is no standard way to install it.  For me, I always
# put the binary in a consistent location (see $CFW_BIN below).

CFW_BIN="$HOME/Applications/Clash-for-windows/cfw"

# However, it's not easy to launch CFW at startup properlly.  The app itself has
# a "Start with Linux" toggle, and it works most of time.  But after an user
# re-login, CFW will not function normally because the old clash-linux process
# is not killed and will block the port CFW is supposed to use.  To solve that,
# turn off the "Start with Linux" toggle, and launch CFW with this script.

# If CFW is installed, kill all related processes and launch CFW.
if [ -f $CFW_BIN ]; then
    # Kill all existing CFW-related processes.
    CLASH_PROCS=$(pgrep clash-linux)
    if [ ! -z $CLASH_PROCS ]; then
        kill $CLASH_PROCS
    fi
    CFW_PROCS=$(pgrep clash-linux)
    if [ ! -z $CFW_PROCS ]; then
        kill $CFW_PROCS
    fi
    # Run CFW.
    nohup $CFW_BIN > /dev/null 2>&1 &
else
    # Echo a warning message.
    echo 'Clash-for-windows is not installed to the expected location!'
fi
