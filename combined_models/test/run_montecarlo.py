#!/usr/bin/env python3
#------------------------------------------------------------------------------
#
# run_montecarlo.py --
#
#	Run monte carlo simulation (mismatch analysis of nFET threshold voltage)
#
#------------------------------------------------------------------------------

import re
import os
import sys
import time
import shutil
import signal
import subprocess
import faulthandler
import multiprocessing

from hist_mosfet_vth import make_mosfet_vth_hist

#------------------------------------------------------------------------------
# Generate a SPICE netlist from the template through variable substitution
#------------------------------------------------------------------------------

def genspice(templatename, devicename, variant, corner, index, pdkroot, debug):
    print('Generating simulation netlist for device ' + devicename + ', index = ' + str(index))
    with open(templatename, 'r') as ifile:
        spicelines = ifile.read()

    # Default parameters
    params = 'W=1.0 L=0.15 M=1'

    libtop = pdkroot + '/' + variant + '/libs.ref/sky130_fd_pr'
    techtop = '../../ngspice'
    includelines = ['.lib ' + techtop + '/sky130.lib.spice ' + corner]

    spicedata = spicelines.replace('INDEX', str(index))
    spicedata = spicedata.replace('DEVICENAME', devicename)
    spicedata = spicedata.replace('VARIANT', variant)
    spicedata = spicedata.replace('CORNER', corner)
    spicedata = spicedata.replace('PARAMS', params)
    spicedata = spicedata.replace('INCLUDELINES', '\n'.join(includelines))

    # Remove the '.in' from the template file name
    basename = os.path.splitext(templatename)[0]	
    outfroot = os.path.splitext(basename)[0]
    outfext = os.path.splitext(basename)[1]
    retname = outfroot + '_' + str(index) + outfext
    outfname = 'results/' + retname

    if debug:
        print('Output file is ' + retname)
    
    with open(outfname, 'w') as ofile:
        ofile.write(spicedata)

    # ngspice will run with cwd=results/ so don't include that in the
    # returned file name.
    return retname

#------------------------------------------------------------------------------
# Run ngspice on the indicated input file
#------------------------------------------------------------------------------

def runspice(scriptname, resultname, devicename, debug):
    print('Running ngspice on ' + scriptname)
    with subprocess.Popen(
            ['ngspice', scriptname],
            stdin= subprocess.DEVNULL,
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE,
	    cwd = 'results',
            universal_newlines = True) as sproc:

        try:
            stdout, stderr = sproc.communicate(timeout=300)
        except TimeoutExpired:
            sproc.kill()
            stdout, stderr = sproc.communicate()
           
        stdout = stdout.splitlines(True)
        stderr = stderr.splitlines(True)

        found = True if resultname == 'none' else False
        valueline = False
        returncode = 0
        reason = 'Success'

        for line in stdout:
            if line.strip('\n').strip() == '':
                continue
            print('Diagnostic:  ngspice output line is "' + line.strip('\n').strip() + '"')
            if valueline:
                try:
                    rvaluestring = line.split('=')[1].strip()
                except:
                    rvaluestring = line.strip('\n').strip()
                returncode = rvaluestring
                valueline = False
            elif resultname in line:
                found = True
                valueline = True

        if stderr:
            errors = False
            messages = []
            for line in stderr:
                if len(line.strip()) > 0:
                    messages.append(line)
                    if 'error' in line.lower():
                        errors = True
            if errors:
                print('Execution error:  Ngspice returned error messages:')
                # Print errors.  Also try to pull the most relevant error message.
                for message in messages:
                    print(message)
                    if 'find model' in message.lower() or 'undefined' in message.lower() or 'unknown' in message.lower() or 'valid model' in message.lower() or 'many parameters' in message.lower() or 'few parameters' in message.lower():
                        reason = message
                if reason == 'Success':
                    for message in messages:
                        if 'error' in message.lower():
                            reason = message
                if reason == 'Success':
                    reason = message[0]
                returncode = -1
            else:
                print('Ngspice warnings:')
                for message in messages:
                    print(message)
        try:
            return_code = sproc.wait(timeout=300)
        except TimeoutExpired:
            sproc.kill()
            return_code = -1
        if return_code != 0:
            print('Execution error:  Ngspice exited with error code ' + str(return_code))
            if reason == 'Success':
                reason = 'Ngspice exited with error code ' + str(return_code)
            return (-2, reason)

    if found:
        return (returncode, reason)
    else:
        print('Result error:  Expected result name ' + resultname + ' but did not receive it.')
        reason = 'Expected result name ' + resultname + ' but did not receive it.'
        return (-1, reason)

#------------------------------------------------------------------------------
# Run a spice simulation (or two) for the device specified in 'line' (obtained
# from the list of devices and expected values).
#------------------------------------------------------------------------------

def do_for_device(devicename, variant, corner, index, pdkroot, keep, debug):

    if 'nfet' in devicename:
        template = 'nfet_vth_mc.spice.in'

    filename = genspice(template, devicename, variant, corner, index, pdkroot, debug)
    (result, reason) = runspice(filename, 'threshold voltage', devicename, debug)
    if not keep:
        os.remove('results/' + filename)
    if isinstance(result, str):
        return result
    else:
        return None

#------------------------------------------------------------------------------
# Main script starts here (using multiprocessing)
#------------------------------------------------------------------------------

def run_single_process(device, variant, corner, pdkroot, keep, runs, debug):

    entries = []
    for i in range(runs):
        print('Simulating device ' + device + ', run #' + str(i))
        new_entry = do_for_device(device, variant, corner, i, pdkroot, keep, debug)
        entries.append(new_entry)

    return entries

#------------------------------------------------------------------------------
# Main script starts here (using multiprocessing)
#------------------------------------------------------------------------------

def run_multi_process(device, variant, corner, pdkroot, keep, runs, debug):
    entries = []

    # Use forkserver method for multiprocessing (otherwise processes hang)
    multiprocessing.set_start_method('forkserver')

    # Allow process to dump a trace when hit with SIGUSR2
    # ("kill -USR2 <pid>")
    faulthandler.register(signal.SIGUSR2)

    # Allow ngspice runs to happen in parallel.
    with multiprocessing.Pool() as pool:
        indexes = []
        for i in range(runs):
            indexes.append(i)

        results = []
        for index in indexes:
            results.append(pool.apply_async(do_for_device,
			(device, variant, corner, index, pdkroot, keep, debug)))

        # Method of polling all results, handling those that have finished,
        # and then waiting a few seconds and trying again.

        recycle = results
        pending = indexes
        k = 0

        while recycle:
            results = recycle
            recycle = []
            lastpending = pending
            pending = []
            for i in range(len(results)):
                r = results[i]
                index = lastpending[i]
                if r.ready():
                    new_entry = r.get()
                    entries.append(new_entry)
                else:
                    recycle.append(r)
                    pending.append(index)
            time.sleep(2)

            # For every minute of elapsed time, give a status update
            k = k + 2
            npend = len(pending)
            if npend == 0:
                print('All simulations have completed in ' + str(k) + ' seconds.')
            elif k % 60 == 0:
                print('Elapsed time in seconds: ' + str(k))
                print('Still waiting on ' + str(npend) + ' simulations.')
                if len(pending) < len(lastpending):
                    print('Pending:')
                    for index in pending:
                        print('   ' + str(index))

    return entries

#------------------------------------------------------------------------------
# Main script starts here (non-multiprocessing)
#------------------------------------------------------------------------------

if __name__ == "__main__":

    variant = 'sky130A'
    corner = 'tt_mm'
    device = 'sky130_fd_pr__nfet_01v8'
    pdkroot = '/usr/share/pdk'
    multiproc = True
    keep = False
    debug = False
    runs = 100

    if len(sys.argv) == 1:
        print('Usage:  run_montecarlo.py [-variant=<var>] [-corner=<cor>]')
        print('    [-device=<dev>] [-pdkroot=<path>] [-runs=<num>]')
        print('    [-nomulti] [-keep] [-debug]')
        print('')
        print('where:')
        print('    <var> = "sky130A" or "sky130B"')
        print('    <cor> = "mc" or "tt_mm" or "ss_mm", etc.')
        print('    <dev> = "sky130_fd_pr__nfet_01v8", etc.')
        print('    <path> defaults to "/usr/share/pdk"')
        print('    <num> defaults to 100')
        print('    "nomulti" runs in single-threaded mode') 
        print('    "keep" keeps the netlist file after simulation')
        print('    "debug" mode generates additional output')
        sys.exit(0)

    for argument in sys.argv[1:]:
        optlist = argument.split('=')
        if len(optlist) == 2:
            if optlist[0] == '-variant':
                variant = optlist[1]
            elif optlist[0] == '-corner':
                corner = optlist[1]
            elif optlist[0] == '-device':
                device = optlist[1]
            elif optlist[0] == '-runs':
                runs = int(optlist[1])
        elif optlist[0] == '-nomulti':
            multiproc = False
        elif optlist[0] == '-keep':
            keep = True
        elif optlist[0] == '-debug':
            debug = True

    print('Simulation information:')
    print('   Device name = "' + device + '"')
    print('   Corner = "' + corner + '"')

    if debug:
        print('Selected options:')
        print('   Variant = "' + variant + '"')
        print('   PDK root = "' + pdkroot + '"')
        print('   Number of runs = ' + str(runs))
        if keep:
            print('   Retain netlists after simulation')
        if multiproc:
            print('   Run in multi-threaded mode')
        else:
            print('   Run in single-threaded mode')

    print('')

    # Check for valid device.  To do:  Add other devices (need template files)
    if 'nfet' in device:
        pass
    else:
        print('Missing template SPICE file for device "' + device + '"')
        sys.exit(1)

    # Make sure that the spice initialization file is in the results directory
    if not os.path.exists('.spiceinit'):
        shutil.copyfile(pdkroot + '/' + variant + '/libs.tech/ngspice/spinit',
		'.spiceinit')

    if multiproc:
        entries = run_multi_process(device, variant, corner, pdkroot, keep, runs, debug)
    else:
        entries = run_single_process(device, variant, corner, pdkroot, keep, runs, debug)

    # Output values if any were generated

    if len(entries) > 0:
        with open('results/' + device + '_' + corner + '_' + variant[-1] + '.dat',
		'w') as ofile:
            for entry in entries:
                print(entry, file=ofile)

        if 'nfet' in device:
            make_mosfet_vth_hist(device, variant, corner)

    sys.exit(0)

