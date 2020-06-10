# OVERVIEW:
# This EEM script provides alerting functionality to LPTS on Cisco IOS-XR. It
# does this by applying user-configured thresholds, specified as a number of
# dropped packets, to the output of the 'show lpts pifib hardware police
# location <loc>' command. Should a flow type be over-threshold, a syslog
# message will be sent.
#
# ENVIRONMENT VARIABLES:
# The operation of this policy to configured using the following environment
# variables. EEM environment variables are set using the 'event manager
# environment <variable-name> <value>' global configuration command.
#
# EEM_LPTS_CHECK_INTERVAL
# Run script every 60, 120, 180, 240, 300, 360, 600, 720, 900, 1200 or 1800 s
#
# EEM_LPTS_CHECK_FLOWTYPES
# Contains a list of LPTS "Flow Types" to monitor. Flow types are separated by
# spaces, as they cannot contain spaces themselves. It can also contain a
# wildcard (*) that will enable alerting for all flow types. The following is
# an example that explicitly configures two flow types as well as a wildcard
# value:
#
#  event manager environment EEM_LPTS_CHECK_FLOWTYPES BGP-known OSPF-mc-known *
#
# EEM_LPTS_CHECK_THRESHOLD
# Contains the threshold at which the script will generate an alert. It can
# take one of several forms. The first form is a space separated list of values
# with one value per-configured flow type. The second value form is a single
# value, which will be applied to all monitored flow types. The following
# example configures three thresholds:
#
#  event manager environment EEM_LPTS_CHECK_THRESHOLD 1200 800 900
#
# When used with the previous example for EEM_LPTS_CHECK_FLOWTYPES, the 
# following alerting thresholds will be used:
#
#   Flow Type       | Threshold
#  +----------------+-------------------------+
#   BGP-known       | 1200 drops per interval
#   OSPF-mc-known   | 800 drops per interval
#   * (wildcard)    | 900 drops per interval
#  +----------------+-------------------------+
#
# EEM_LPTS_CHECK_LOCATIONS
# Contains the line cards on which to gather the LPTS  statistics. It can 
# contain a space separated list of locations, such as 0/2/CPU0 0/3/CPU0.
#
# VERSION HISTORY:
# v20090224 Tim Sammut [tsammut@cisco.com]
# - Initial version
#
# v20161020 Tim Dorssers [tim.dorssers@vosko.nl]
# - Changed platform support to ASR 9000
# - Added command 'show lpts pifib hardware static-police location <loc>'
# - Added fix for function cli_read_pattern
# - Added debug prints enabled by setting env variable EEM_LPTS_PRINTDEBUGINFO
#
# v20161118 Tim Dorssers [tim.dorssers@vosko.nl]
# - Removed percentage based threshold calculations
# - Added support for big numbers by adding two helper functions
# - Set maxrun to script interval
# - Updated the script overview above
#
# v20170110 Tim Dorssers [tim.dorssers@vosko.nl]
# - Added option to ignore a specified flow if threshold is set to -1
#
# v20170124 Tim Dorssers [tim.dorssers@vosko.nl]
# - Fixed bug in function subtract that caused miscalculations
#
# v20170625 Tim Dorssers [tim.dorssers@vosko.nl]
# - Added script name to debug output and verbosity levels
# - Switched from watchdog to cron timer
#
# v20170628 Tim Dorssers [tim.dorssers@vosko.nl]
# - Simplified command parsing regex routine
#
# =============================================================================
#
# Use the Timer ED to execute every EEM_LPTS_CHECK_INTERVAL seconds.
#
::cisco::eem::event_register_timer cron name lptsCheckTimer cron_entry [format "*/%s * * * *" [expr int($EEM_LPTS_CHECK_INTERVAL / 60)]] maxrun $EEM_LPTS_CHECK_INTERVAL

#
# Import the cisco namespaces to gain access to the cli_* and context_* keywords.
#
#namespace import ::cisco::fm::*
namespace import ::cisco::eem::*

# errorInf gets set by namespace if any of the auto_path directories do not
# contain a valid tclIndex file.
set errorInfo ""

# Check to make sure the required environment variables exist. If not, exit
# with an error.
# In reality, we will not have gotten this far if this  variable did not exist
# (the script will fail to register), but good practice requires us to check
# for all environment variables.
#
if {![info exists EEM_LPTS_CHECK_INTERVAL]} {
  set result "Mandatory EEM_LPTS_CHECK_INTERVAL variable has not been set"
  error $result $errorInfo
} else {
  if {[lsearch {60 120 180 240 300 360 600 720 900 1200 1800} $EEM_LPTS_CHECK_INTERVAL] < 0} {
    set result "Mandatory EEM_LPTS_CHECK_INTERVAL variable is invalid"
    error $result $errorInfo
  }
}

if {![info exists EEM_LPTS_CHECK_FLOWTYPES]} {
 set result "Policy cannot be run: variable EEM_LPTS_CHECK_FLOWTYPES has not been set"
 error $result $errorInfo
}

if {![info exists EEM_LPTS_CHECK_THRESHOLD]} {
 set result "Policy cannot be run: variable EEM_LPTS_CHECK_THRESHOLD has not been set"
 error $result $errorInfo
} else {
 # The threshold has been configured. Verify that it is valid.

 # The threshold is valid if either it is one value in length (one threshold
 # for all flow types) or there is one threshold for _each_ configured flow 
 # type.

 if {[llength $EEM_LPTS_CHECK_THRESHOLD] != 1 &&
     [llength $EEM_LPTS_CHECK_THRESHOLD] != [llength $EEM_LPTS_CHECK_FLOWTYPES]} {
  error "Configured threshold not valid." ""
 }
}

if {![info exists EEM_LPTS_CHECK_LOCATIONS]} {
 set result "Policy cannot be run: variable EEM_LPTS_CHECK_LOCATIONS has not been set"
 error $result $errorInfo
}

set DEBUG_ENABLED 0
if {[info exists EEM_LPTS_PRINTDEBUGINFO]} {
  if {[string match "verbose" [string tolower $EEM_LPTS_PRINTDEBUGINFO]]} {
    set DEBUG_ENABLED 2
  } else {
    set DEBUG_ENABLED 1
  }
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
    # lets not spin forever. try for maximum 50000 times
    while {$is_end == 0 && $i<=50000} {
        set str [read $fd]
        if {$str == ""} {
            after 50
            incr i;
            continue
        } else {
            #sometimes read returns router prompt partially.
            #we hope in at least 2 read() calls we get full router prompt
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

# print debug information
proc pdbg {dbg_level line_to_print} {
  global DEBUG_ENABLED
  global scriptName
  if {$DEBUG_ENABLED >= $dbg_level} {
    puts "$scriptName: $line_to_print"
  }
}

# define two helper functions
# this procedure will compare two large numbers represented as a list of digits
proc comp {n1l n2l len} {
  set i 0
  while {$i<$len} {
    set n1i [lindex $n1l $i]
    set n2i [lindex $n2l $i]
    if {$n1i == $n2i} {
      incr i 1
      continue
    }
    if {$n1i > $n2i} {
      return 1
    } else {
      return -1
    }
  }
  return 0
}

# this procedure will subtract two big positive numbers and will 
# return the result as a string
# tim: fixed broken string zero padding
proc subtract {n1s n2s} {
  #determine len and pad front with 0
  set n1l [string length $n1s]
  set n2l [string length $n2s]
  set nlen [expr ($n2l > $n1l) ? $n2l : $n1l]
  set n1 [split [format "%0$nlen\s" $n1s] ""]
  set n2 [split [format "%0$nlen\s" $n2s] ""]
  set n ""

  set cr [comp $n1 $n2 $nlen]
  if {$cr == 0} {
    return "0"
  }

  #iterate over list and make subtraction
  set t 0
  while {$nlen>0} {
    incr nlen -1
    set d1 [lindex $n1 $nlen]
    set d2 [lindex $n2 $nlen]
    if {$cr > 0} {
      set rx [expr $d1-$d2-$t]
    } else {
      set rx [expr $d2-$d1-$t]
    }
    if {$rx < 0} {
      set rx [expr $rx+10]
      set t 1
    } else {
      set t 0
    }
    set n $rx$n
  }
  # cut all trailing zeroes from the number
  set n [string trimleft $n "0"]
  # add sign if <0
  if {$cr == -1} {
    set n "-$n"
  }
  return $n
}

# keep the time of starting the script
set startTime [clock seconds]

# script name
set scriptName [file tail $argv0]

#
# Retrieve the statistics gathered the last time the script was executed.
# These are stored in the savedDropCounts array variables. These variable is
# stored in the EEM_LPTS_CHECK_DROP context. If the context_retrieve commands
# do not return any data we do not fail; we assume this is the first 
# iteration of the script and we create the variable (later on).
#
if {![catch {context_retrieve EEM_LPTS_CHECK_DROP "savedDropCounts"} result]} {
 # context_retrieve has returned an array (as a list) in $result, 
 # copy it to the savedDropCounts array.

 array set savedDropCounts $result
}

#
# Use the Cisco provided CLI library to open a CLI session, execute the
# the 'show lpts pifib hardware police location <loc>' command placing the
# output in the commandOutput(<loc>) array variable, then close the CLI.
#
# We capture this command output for all 'locations' up front to minimize
# the time we are interacting with the CLI.
#
pdbg 1 "Opening CLI"
if [catch {cli_open} result] {
 error $result $errorInfo
} else {
 array set cli $result
}

#
# Execute the command 'show lpts pifib hardware police location <loc>' once
# for each line card in EEM_LPTS_CHECK_LOCATIONS, store the output in the
# commandOutput array variable.
#
foreach location $EEM_LPTS_CHECK_LOCATIONS {
 pdbg 1 "Executing CLI commands for $location"
 if [catch {cli_exec $cli(fd) "show lpts pifib hardware police location $location"} result] {
  error $result $errorInfo
 } else {
  set commandOutput($location) $result
 }
 #
 # Append the output of the command 'show lpts pifib hardware static-police 
 # location <loc>' to the commandOutput array variable.
 #
 if [catch {cli_exec $cli(fd) "show lpts pifib hardware static-police location $location"} result] {
  error $result $errorInfo
 } else {
  append commandOutput($location) $result
 }
}

pdbg 1 "Closing CLI"
 if [catch {cli_close $cli(fd) $cli(tty_id)} result] {
    error $result $errorInfo
}

#
# Prepare a list of patterns.
# First pattern parses 'show lpts pifib hardware police location <loc>'
# Second pattern parses 'show lpts pifib hardware static-police location <loc>'
#
set pat_list [list {^(\S+)\s+\d+\s+\S+\s+\d+\s+\d+\s+\d+\s+(\d+)} \
                   {^(\S+)\s+\S+\s+\d+\s+\d+\s+\d+\s+(\d+)}]

foreach location $EEM_LPTS_CHECK_LOCATIONS {
 #
 # Parse the output of the commands using the prepared patterns.
 #
 array unset parsedCommandOutput
 # Iterate over each line of the command output
 foreach line [split $commandOutput($location) "\n"] {
  # Iterate over each pattern in the list
  foreach pat $pat_list {
   # Parse the actual line
   if [regexp -linestop -- $pat $line -> flowType droppedPackets] {
    # Store number of dropped packets in the parsedCommandOutput array
    set parsedCommandOutput($flowType) $droppedPackets
    pdbg 2 "***$flowType $droppedPackets***"
    break
   }
  }
 }
 # If the parsedCommandOutput array is empty, then exit with an error.
 if {[array size parsedCommandOutput] == 0} {
  error "Could not parse output of location $location specified in EEM_LPTS_CHECK_LOCATIONS" ""
 }
 pdbg 1 "Parsed CLI output of $location"

 #
 # Iterate over the list variable EEM_LPTS_CHECK_FLOWTYPES. The for
 # loop below is executed once per entry in EEM_LPTS_CHECK_FLOWTYPES
 #
 for {set indexMonitoredFlowTypes 0} \
     {$indexMonitoredFlowTypes < [llength $EEM_LPTS_CHECK_FLOWTYPES]} \
     {incr indexMonitoredFlowTypes} {

  # Use an easy to remember variable name for our flow type.
  set flowType [lindex $EEM_LPTS_CHECK_FLOWTYPES $indexMonitoredFlowTypes]

  # Figure out which type of threshold we have; one threshold for all flow
  # types, or one threshold _per_ flow type.
  if {[llength $EEM_LPTS_CHECK_THRESHOLD] > 1} {
   # Get per-flow type threshold and place into $threshold.
   set threshold [lindex $EEM_LPTS_CHECK_THRESHOLD $indexMonitoredFlowTypes]
  
  } else {
   # Get single threshold for all flow types and place it into $threshold.
   set threshold $EEM_LPTS_CHECK_THRESHOLD
  }

  # Check to see if the flow type we are processing is the wildcard (*)
  if {![regexp {\*} $flowType]} {
   # The flow type in $flowType is not a wildcard
  
   # Find where in parsedCommandOutput our flow type is located. If flowType 
   # does not exist in parsedCommandOutput, exit with an error.
   if {[catch {set droppedPackets $parsedCommandOutput($flowType)}]} {
    error "Invalid Flow Type ($flowType) specified in EEM_LPTS_CHECK_FLOWTYPES" ""
   }
   
   pdbg 2 "!* Current $location: $flowType: $droppedPackets"
   #
   # The script is about to use the savedDropCounts array. These array 
   # elements will not exist on the first script iteration (they have not yet
   # been saved), so initialize any missing elements to the current values.
   # This should only happen the first time the script is run.
   #
   if {![info exists savedDropCounts($location,$flowType)]} {
    # Array elements do not exist, initialize to the seen values.
           
    set savedDropCounts($location,$flowType) $droppedPackets
    pdbg 2 "!* Initialize $location: $flowType: $droppedPackets"
    
    # Since this is first script iteration, we know that we are not going
    # to alert, so move on to the next flow type.
   } else {
  
    pdbg 2 "!* Saved $location: $flowType: $savedDropCounts($location,$flowType)"
    # Determine the number of dropped packets for this flow type since the last
    # script iteration.
    set drops [subtract $droppedPackets $savedDropCounts($location,$flowType)]
    # If threshold is set to -1 then this flow must be ignored.
    if {$threshold != -1} {
     pdbg 2 "!* Drops $location: $flowType: $drops"
     if {$threshold < $drops} {
    
      # We are over threshold, send syslog message.
      action_syslog priority notice msg "LPTS drop threshold ($threshold) exceeded for flow type $flowType on $location, $drops drops in last $EEM_LPTS_CHECK_INTERVAL seconds."
     }
    }

    # This is processed whether or not a flow type is in or out of threshold,
    # save the counters for next script iteration.
    set savedDropCounts($location,$flowType) $droppedPackets
   }
  } else {
   # This code is processed for our special wildcard flow type.
  
   foreach flowType [array names parsedCommandOutput] {
   
    # Skip over this dataset if this flowType has been specifically added to 
    # EEM_LPTS_CHECK_FLOWTYPES (i.e. do not process it as part of the wildcard)
    if {[lsearch -regexp $EEM_LPTS_CHECK_FLOWTYPES "^$flowType\$"] == -1} {  
    # flowType not found in EEM_LPTS_CHECK_FLOWTYPES
    
     set droppedPackets $parsedCommandOutput($flowType)

     pdbg 2 "Current $location: $flowType: $droppedPackets"
     #
     # The script is about to use the savedDropCounts array. These array 
     # elements will not exist on the first script iteration (they have not yet
     # been saved), so initialize any missing elements to the current values.
     # This should only happen the first time the script is run.
     #
     if {![info exists savedDropCounts($location,$flowType)]} {
      # Array elements do not exist, initialize to the seen values.

      set savedDropCounts($location,$flowType) $droppedPackets
      pdbg 2 "Initialize $location: $flowType: $droppedPackets"
      
      # Since this is first script iteration, we know that we
      # are not going to alert, so move on.
     } else {

      pdbg 2 "Saved $location: $flowType: $savedDropCounts($location,$flowType)"
      # Determine the number of dropped packets for this flow type since the
      # last script iteration.
      set drops [subtract $droppedPackets $savedDropCounts($location,$flowType)]
      pdbg 2 "Drops $location: $flowType: $drops"
      if {$threshold < $drops} {

       # We are over threshold, send syslog message.
       action_syslog priority notice msg "LPTS drop threshold ($threshold) exceeded for flow type $flowType on $location, $drops drops in last $EEM_LPTS_CHECK_INTERVAL seconds."
      }
     }

     # This is processed whether or not a flow type is in or out of threshold,
     # save the counters for next script iteration.
     set savedDropCounts($location,$flowType) $droppedPackets
    }
   }
  }
 }
}
#
# Save the number of dropped (stored in savedDropCounts in the context
# EEM_LPTS_CHECK_DROP to be accessible the next time the script runs.
#
catch {context_save EEM_LPTS_CHECK_DROP "savedDropCounts"}

set endTime [clock seconds]
set totalRunTime [expr $endTime - $startTime]
pdbg 1 "Total script runtime was: $totalRunTime seconds"

exit