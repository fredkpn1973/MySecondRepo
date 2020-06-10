Wed Jun 10 15:58:22.550 CEST
# This EEM script implements the IOS style "archive log config" syslog
# notification for IOS XR.
#
# Author Tim Dorssers (tim.dorssers@vosko.nl)
# 11-11-2016: initial script version

::cisco::eem::event_register_syslog pattern "%MGBL-CONFIG-6-DB_COMMIT : Configuration committed by user" maxrun 60

namespace import ::cisco::eem::*
namespace import ::cisco::lib::*

# official cisco fix for function cli_read_pattern
# tim: moved trim_last_line out of while loop to fix duplicate lines
proc ::cisco::eem::cli_read_pattern {fd ptn} {
    set result ""
    set is_end 0
    set str2 ""
    set trim_last_line ""
    set i 1
    set last_line ""
    set line2 ""
    # lets not spin forever. try for maximum 50000 times
    while {$is_end == 0 && $i<=50000} {
        set str [read $fd]
        if {$str == ""} {
            after 50
            incr i;
            continue
        } else {
            #sometimes read returns router prompt partially.
            #we hope in at least 2 read() cwe hope in at least 2 read() calls we get full router prompt
            set last_line $line2
            append last_line $str
            set line2 $str
        }
        # double quotes (don't change to curly braces!)
        set is_end [regexp "(.*)?($ptn)" $last_line]
        append result $str
        after 60
    }
    #remove last line containing routername
    set trim_last_line [regexp "(.*)\n" $result str2]
    if {$trim_last_line} {
        set result $str2
    }
    return $result
}

#
# errorInf gets set by namespace if any of the auto_path directories do not
# contain a valid tclIndex file.  It is not an error just left over stuff.
# So we set the errorInfo value to null so that we don't have left
# over errors in it.
#
set errorInfo ""

#query the event info
array set arr_einfo [event_reqinfo]

if {$_cerrno != 0} {
    set result [format "component=%s; subsys err=%s; posix err=%s;\n%s" \
        $_cerr_sub_num $_cerr_sub_err $_cerr_posix_err $_cerr_str]
    error $result
}

#Extract the m error $result
}

#Extract the me message from the event info
set syslog_msg $arr_einfo(msg)

#Extract user ID and commit ID from syslog message
regexp {.*Configuration committed by user '(.*?)'.*} $syslog_msg result user_id
regexp {.*show configuration commit changes ([0-9]*).*} $syslog_msg result commit_id

#open a cli connection
if [catch {cli_open} result] {
    error $result $errorInfo
} else {
    array set cli1 $result
}

#execute show configuration commit changes command
if [catch {cli_exec $cli1(fd) "show configuration commit changes $commit_id"} result] {
    error $result $errorInfo
} else {
    set startOfCommands 0
    # Split into multiple syslog messages, since multi line messages are not
    # supported by all syslog deamons
    foreach line [split $result "\n"] {
        # stop when end of configuration is reached
        if {[string equal "end" $line]} {
            break
        }
        # IOS style archive config log output
        if {$startOfCommands} {
            action_syslog priority info action_syslog priority info msg "User:$user_id  logged command:$line"
        }
        # configuration commands start after !! IOS XR Configuration version
        if {[string match "!!*" $line]} {
            set startOfCommands 1
        }
    }
}

#close the cli connection
if [catch {cli_close $cli1(fd) $cli1(tty_id)} result] {
    error $result $errorInfo
}
rrorInfo
}