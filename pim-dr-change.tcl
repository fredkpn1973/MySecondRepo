# This is a workaround for the missing HSRP aware PIM feature on IOS-XR.
# The policy configures the PIM dr-priority (inherited by all interfaces) for
# the specified VRFs based on a tracked object state. It does not use the HSRP
# state of individual interfaces, instead it assumes that all interfaces have
# the same HSRP and PIM dr-priority. The tracked object should track the 
# backbone interfaces. At router startup, the tracked object will be down.
# The first time it changes to up (within one hour uptime), the dr-priority is
# decremented. Then after the configured delay, the dr-priority is restored.
# When a core isolation occurs, the dr-priority is decremented and when the
# core isolation event is cleared, the dr-priority is restored after the 
# configured delay.
#
# Environment variables:
# EEM_PIMDR_OBJECT     : Tracked object
# EEM_PIMDR_DELAY      : Delay in seconds
# EEM_PIMDR_VRF        : List of VRFs
# [EEM_PIMDR_PRIORITY] : PIM dr-priority (optional)
# [EEM_PIMDR_DECREMENT]: IMDR_DECREMENT]: Decrement value (optional)
#
# Author Tim Dorssers (tim.dorssers@vosko.nl)
# 26-10-2016: initial script version
# 04-11-2016: added router reload sequence into this script
#             removed script pim-dr-reload.tcl
#             added fix for function cli_read_pattern
# 11-11-2016: reset errorInfo after namespace import
# 25-03-2017: added configuration commit error handling
# 05-02-2020: get uptime by snmp instead of cli method

::cisco::eem::event_register_track $EEM_PIMDR_OBJECT state any maxrun [expr {int($EEM_PIMDR_DELAY + 60)}]

namespace import ::cisco::eem::*

# errorInf gets set by namespace if any of the auto_path directories do not
# contain a valid tclIndex file.
set errorInfo ""

if {![info exists EEM_PIMDR_OBJECT]} {
 set result "Policy cannot be run: variable EEM_PIMDR_OBJECT has not been set"
 error $result $errorInfo
}

if {![info exists EEM_PIMDR_DELAY]} {
 set result "Policy cannot be run: variable EEM_PIMDR_DELAY has not been set"
 error $result $errorInfo
}^Mrror $result $errorInfo
}^M^M

if {![info exists EEM_PIMDR_VRF]} {
 set result "Policy cannot be run: variable EEM_PIMDR_VRF has not been set"
 error $result $errorInfo
}

# If not explicitly exported set default to 100
if {![info exists EEM_PIMDR_PRIORITY]} {
 set EEM_PIMDR_PRIORITY 100
}

# If not explicitly exported set default to 15
if {![info exists EEM_PIMDR_DECREMENT]} {
 set EEM_PIMDR_DECREMENT 15
}

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
    # lets not spin forever. try for maximum 500 times
    while {$is_end == 0 && $i<=500} {
        set str [read $fd]
        if {$str == ""} {
            after 50
            incr i;
            continue
        } else {
            #sometimes read returns router prompt partially.
            #we hope in attially.
            #we hope in att least 2 read() calls we get full router prompt
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

# Procedure to configure the PIM DR-priority for all specified VRFs
proc configure_dr_priority {priority} {
 global EEM_PIMDR_VRF
 global errorInfo

 # Open CLI
 if [catch {cli_open} result] {
  error $result $errorInfo
 } else {
  array set cli1 $result
 }
 # Enter configure mode
 if [catch {cli_exec $cli1(fd) "config"} result] {
  error $result $errorInfo
 }
 # For each VRF in the list
 for {set indexVrf 0} {$indexVrf < [llength $EEM_PIMDR_VRF]} {incr indexVrf} {
  set vrf [lindex $EEM_PIMDR_V} {
  set vrf [lindex $EEM_PIMDR_VVRF $indexVrf]
  # Configure new PIM dr-priority
  if [catch {cli_exec $cli1(fd) "router pim vrf $vrf address-family ipv4 dr-priority $priority"} result] {
   error $result $errorInfo
  }
  action_syslog priority notice msg "Setting PIM dr-priority to $priority for vrf $vrf"
 }
 # Commit configuration, try 10 times
 for {set i 0} {$i < 10} {incr i} {
  if [catch {cli_write $cli1(fd) "commit"} result] {
   error $result $errorInfo
  }
  if [catch {cli_read_drain $cli1(fd) } result] {
   error $result $errorInfo
  } else {
   # Other configuration sessions?
   if {[string match "*One or more commits*" $result]} {
        if [catch {cli_write $cli1(fd) "yes"} result] {
     error $result $errorInfo
    } else {
     break
        }
   }
   # Configuration locked?
   if {![string match "*% Failed to commit*" $result]} break
  }
 }
 # Close CLI
 if [catch {cli_close $cli1(fd) $cli1(tty_id)} result] {
  error $result $errorInfo
 }
}

# Retrieve previous context data
if {[catch {context_retrieve Pta
if {[catch {context_retrieve PPIM_DR initialized} result]} {
 set initialized 0
} else {
 set initialized $result
 # Save the variable for the next run
 catch {context_save PIM_DR initialized}
}

# Query the information of triggered fm event
array set track_info [event_reqinfo]
set track_state $track_info(track_state) 

# Node reload scenario
if {$initialized == 0} {
 # Get uptime in 1/100 seconds
 array set snmp_res [sys_reqinfo_snmp oid 1.3.6.1.2.1.1.3.0 get_type exact]
 if {[info exists snmp_res(value)]} {
  set snmp_val $snmp_res(value)
 } else {
  set snmp_val 0
 }
 # Check if router uptime is less than 10 minutes
 if {$snmp_val < 60000} {
  # Check for down event
  if [string equal $track_state "down"] {
   # Ignore the first down event, exit script
   exit
  } else {
   # This is the very first up event, decrement DR priority
   action_syslog priority notice msg "System startup"
   configure_dr_priority [expr {int($EEM_PIMDR_PRIORITY - $EEM_PIMDR_DECREMENT)}]
  }
 }
 # Node reload scenario finished o# Node reload scenario finished or router uptime is more than 10 minutes,
 # continue to core isolation scenario
 set initialized 1
 # Save the variable for the next run
 catch {context_save PIM_DR initialized}
}

# Core isolation scenario
if {$initialized == 1} {
 # Determine priority based on state: down -> decrement, up -> delayed restore
 if [string equal $track_state "up"] {
  action_syslog priority notice msg "Core isolation cleared. Waiting for $EEM_PIMDR_DELAY seconds" 
  # Do synchronous sleep when going up
  after [expr {int($EEM_PIMDR_DELAY * 1000)}]
  configure_dr_priority $EEM_PIMDR_PRIORITY
 } else {
  action_syslog priority notice msg "Isolated from the network core"
  configure_dr_priority [expr {int($EEM_PIMDR_PRIORITY - $EEM_PIMDR_DECREMENT)}]
 }
}

exit
NT)}]
 }
}

exit
xit
