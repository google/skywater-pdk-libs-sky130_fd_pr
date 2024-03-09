#!/usr/bin/env python3
#------------------------------------------------------------------------------
#
# run_spice_tests.py --
#
#    Run all ngspice tests, assuming an input file "devices.txt" containing,
#    with one entry per line:
#
#    <device_name>  <device_type>  <expected_value>
#
#    where <device_type> is one of:  mosfet, bipolar, capacitor, resistor, or diode.
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

import find_all_devices

from plot_mosfet_iv import make_mosfet_iv_plot
from plot_bipolar_iv import make_bipolar_iv_plot
from plot_bipolar_beta import make_bipolar_beta_plot
from plot_diode_iv import make_diode_iv_plot

#------------------------------------------------------------------------------
# Enumerate capacitors that have additional shield pin connection
#------------------------------------------------------------------------------

four_pin_caps = [
	'sky130_fd_pr__cap_vpp_03p9x03p9_m1m2_shieldl1_floatm3',
	'sky130_fd_pr__cap_vpp_04p4x04p6_l1m1m2_shieldpo_floatm3',
	'sky130_fd_pr__cap_vpp_04p4x04p6_m1m2m3_shieldl1m5_floatm4',
	'sky130_fd_pr__cap_vpp_06p8x06p1_l1m1m2m3_shieldpom4',
	'sky130_fd_pr__cap_vpp_06p8x06p1_m1m2m3_shieldl1m4',
	'sky130_fd_pr__cap_vpp_08p6x07p8_l1m1m2_shieldpo_floatm3',
	'sky130_fd_pr__cap_vpp_08p6x07p8_m1m2m3_shieldl1m5_floatm4',
	'sky130_fd_pr__cap_vpp_11p3x11p8_l1m1m2m3m4_shieldm5_nhv',
	'sky130_fd_pr__cap_vpp_11p5x11p7_l1m1m2_shieldpom3',
	'sky130_fd_pr__cap_vpp_11p5x11p7_l1m1m2m3_shieldm4',
	'sky130_fd_pr__cap_vpp_11p5x11p7_l1m1m2m3_shieldpom4',
	'sky130_fd_pr__cap_vpp_11p5x11p7_l1m1m2m3m4_shieldm5',
	'sky130_fd_pr__cap_vpp_11p5x11p7_l1m1m2m3m4_shieldpom5',
	'sky130_fd_pr__cap_vpp_11p5x11p7_l1m1m2m3m4_shieldpom5_x',
	'sky130_fd_pr__cap_vpp_11p5x11p7_m1m2m3_shieldl1m5_floatm4',
	'sky130_fd_pr__cap_vpp_11p5x11p7_m1m2m3m4_shieldl1m5',
	'sky130_fd_pr__cap_vpp_11p5x11p7_m1m2m3m4_shieldm5',
	'sky130_fd_pr__cap_vpp_04p4x04p6_l1m1m2_shieldm3_floatpo',
	'sky130_fd_pr__cap_vpp_04p4x04p6_l1m1m2m3m4_shieldpom5',
	'sky130_fd_pr__cap_vpp_04p4x04p6_m1m2m3_shieldl1m5_floatm4_r',
	'sky130_fd_pr__cap_vpp_04p4x04p6_m1m2m3_shieldl1m5_floatm4_top',
	'sky130_fd_pr__cap_vpp_06p8x06p1_l1m1m2m3_shieldpom4_r',
	'sky130_fd_pr__cap_vpp_06p8x06p1_l1m1m2m3_shieldpom4_top',
	'sky130_fd_pr__cap_vpp_06p8x06p1_l1m1m2m3m4_shieldpo_floatm5',
	'sky130_fd_pr__cap_vpp_06p8x06p1_m1m2m3_shieldl1m4_r',
	'sky130_fd_pr__cap_vpp_06p8x06p1_m1m2m3_shieldl1m4_top',
	'sky130_fd_pr__cap_vpp_08p6x07p8_m1m2m3_shieldl1m5_floatm4_r',
	'sky130_fd_pr__cap_vpp_08p6x07p8_m1m2m3_shieldl1m5_floatm4_top',
	'sky130_fd_pr__cap_vpp_08p6x07p8_m1m2m3m4_shieldpom5',
	'sky130_fd_pr__cap_vpp_11p5x11p7_l1m1m2_shieldpom3_r',
	'sky130_fd_pr__cap_vpp_11p5x11p7_l1m1m2m3_shieldm4_top',
	'sky130_fd_pr__cap_vpp_11p5x11p7_l1m1m2m3_shieldpom4_top',
	'sky130_fd_pr__cap_vpp_11p5x11p7_l1m1m2m3m4_shieldm5_r',
	'sky130_fd_pr__cap_vpp_11p5x11p7_l1m1m2m3m4_shieldm5_top',
	'sky130_fd_pr__cap_vpp_11p5x11p7_l1m1m2m3m4_shieldpom5_m5pullin',
	'sky130_fd_pr__cap_vpp_11p5x11p7_l1m1m2m3m4_shieldpom5_r',
	'sky130_fd_pr__cap_vpp_11p5x11p7_l1m1m2m3m4_shieldpom5_top',
	'sky130_fd_pr__cap_vpp_11p5x11p7_l1m1m2m3m4_shieldpom5_x6',
	'sky130_fd_pr__cap_vpp_11p5x11p7_l1m1m2m3m4_shieldpom5_x7',
	'sky130_fd_pr__cap_vpp_11p5x11p7_l1m1m2m3m4_shieldpom5_x8',
	'sky130_fd_pr__cap_vpp_11p5x11p7_l1m1m2m3m4_shieldpom5_x9',
	'sky130_fd_pr__cap_vpp_11p5x11p7_l1m1m2m3m4_shieldpom5_xtop',
	'sky130_fd_pr__cap_vpp_11p5x11p7_m1m2m3_shieldl1m5_floatm4_top',
	'sky130_fd_pr__cap_vpp_11p5x11p7_m1m2m3m4_shieldl1m5_r',
	'sky130_fd_pr__cap_vpp_11p5x11p7_m1m2m3m4_shieldl1m5_top',
	'sky130_fd_pr__cap_vpp_11p5x11p7_m1m2m3m4_shieldm5_r'
]

five_pin_fets = [
	'sky130_fd_pr__nfet_20v0_iso',
	'sky130_fd_pr__nfet_20v0_nvt_iso',
	'sky130_fd_pr__nfet_20v0_reverse_iso'
]

two_pin_resistors = [
	'sky130_fd_pr__res_generic_po'
]

#------------------------------------------------------------------------------
# Run ngspice on the indicated input file in the "results" directory.
#------------------------------------------------------------------------------

def runspice(scriptname, resultname, devicename, expectedval):
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
                if rvaluestring != expectedval:
                    if expectedval == 'none':
                        returncode = rvaluestring
                    else:
                        print('Result error:  Expected "' + resultname + '" with value "' + expectedval + '" but got ' + rvaluestring)
                        reason = 'Expected "' + resultname + '" with value "' + expectedval + '" but got ' + rvaluestring
                        returncode = -1
                valueline = False

            elif resultname != 'none' and resultname in line:
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
# Read ".spice.in" file, replace DEVICENAME string with the device name,
# PDKVERSION with the variant (sky130A), and CORNER with the simulation
# corner (tt), and write out as ".spice" file in "results" directory.
#------------------------------------------------------------------------------

def genspice(scriptname, devicename, variant, corner):
    print('Generating simulation netlist for device ' + devicename)
    with open(scriptname + '.in', 'r') as ifile:
        spicelines = ifile.read().splitlines()

    # Some parameters to pass to the output
    # Default works for low-voltage FET devices

    params = 'W=3.0 L=0.15 M=1'

    if '_cM' in devicename or '_bM' in devicename or '_aM' in devicename:
        params = ''
    elif '_aF' in devicename:
        params = ''
    elif 'esd_nfet_g5v0d10v5' in devicename:
        params = 'W=17.5 L=0.55 M=1'
    elif 'esd_pfet_g5v0d10v5' in devicename:
        params = 'W=14.5 L=0.55 M=1'
    elif 'pfet_01v8_lvt' in devicename:
        params = 'W=3.0 L=0.35 M=1'
    elif 'g5v0d10v5' in devicename:
        params = 'W=3.0 L=0.5 M=1'
    elif 'pfet_g5v0d16v0' in devicename:
        params = 'W=5.0 L=0.66 M=1'
    elif 'nfet_g5v0d16v0' in devicename:
        params = 'W=5.0 L=0.7 M=1'
    elif 'sky130_fd_pr__nfet_01v8_esd' in devicename:
        params = 'W=10 L=0.17 M=1'
    elif 'sky130_fd_pr__esd_nfet_05v0_nvt' in devicename:
        params = 'W=10 L=2 M=1'
    elif 'sky130_fd_pr__nfet_03v3_nvt' in devicename:
        params = 'W=10 L=0.55 M=1'
    elif 'sky130_fd_pr__nfet_05v0_nvt' in devicename:
        params = 'W=10 L=2 M=1'
    elif 'sky130_fd_pr__nfet_05v0_nvt' in devicename:
        params = 'W=10 L=2 M=1'
    elif 'sky130_fd_pr__pfet_01v8_mvt' in devicename:
        params = 'W=1.68 L=0.15 M=1'
    elif 'sky130_fd_pr__esd_' in devicename: 
        params = 'W=20.35 L=0.165 M=1'
    elif 'sky130_fd_pr__special_pfet_latch' in devicename:
        params = 'W=0.14 L=0.15 M=1'
    elif 'sky130_fd_pr__special_nfet_pass_flash' in devicename:
        params = 'W=0.45 L=0.15 M=1'
    elif 'sky130_fd_pr__special_nfet_pass_lvt' in devicename:
        params = 'W=0.3 L=0.15 M=1'
    elif 'sky130_fd_pr__special_nfet_pass' in devicename:
        params = 'W=0.14 L=0.15 M=1'
    elif 'sky130_fd_pr__special_nfet_latch' in devicename:
        params = 'W=0.21 L=0.15 M=1'
    elif 'sky130_fd_pr__nfet_20v0_zvt' in devicename:
        params = 'W=60.0 L=0.5 M=1'
    elif 'sky130_fd_pr__nfet_20v0' in devicename:
        params = 'W=40.35 L=1.0 M=1'
    elif 'sky130_fd_pr__pfet_20v0' in devicename:
        params = 'W=60.0 L=0.5 M=1'

    libtop = '/usr/share/pdk/' + variant + '/libs.ref/sky130_fd_pr'
    # techtop = '/usr/share/pdk/' + variant + '/libs.tech/ngspice'
    # Directory containing new continuous models.
    techtop = '../..'
    includelines = ['.lib ' + techtop + '/sky130.lib.spice ' + corner]

    outlines = []
    for line in spicelines:
        newline = line.replace('INCLUDELINES', '\n'.join(includelines))
        newline = newline.replace('DEVICENAME', devicename)
        newline = newline.replace('PDKVERSION', variant)
        newline = newline.replace('CORNER', corner)
        newline = newline.replace('PARAMS', params)
        outlines.append(newline)

    with open('results/' + devicename + '.spice', 'w') as ofile:
        for line in outlines:
            print(line, file=ofile)

#------------------------------------------------------------------------------
# Run a spice simulation (or two) for the device specified in 'line' (obtained
# from the list of devices and expected values).
#------------------------------------------------------------------------------

def do_for_device(line, variant, corner):
    passes = []
    fails = []
    baseline_run = False
    baseline_entries = []
    reasons = {}

    devvals = line.split()

    # Capacitors
    cap1rex = re.compile('sky130_fd_pr__cap_mim.*')
    cap2rex = re.compile('sky130_fd_pr__cap.*')
    cap3rex = re.compile('sky130_fd_pr__model__parasitic__cap.*')
    # Diodes (as subcircuits)
    diode1rex = re.compile('sky130_fd_pr__esd_rf_diode.*')
    diode2rex = re.compile('sky130_fd_pr__diode.*')
    diode3rex = re.compile('sky130_fd_pr__photodiode.*')
    diode4rex = re.compile('sky130_fd_pr__model__parasitic__diode.*')
    # Inductors
    indrex = re.compile('sky130_fd_pr__ind.*')
    # Resistors
    resrex = re.compile('sky130_fd_pr__res.*')
    # MOSFETs (p-type)
    pfet1rex = re.compile('sky130_fd_pr__esd_pfet.*')
    pfet2rex = re.compile('sky130_fd_pr__pfet.*')
    pfet3rex = re.compile('sky130_fd_pr__rf_pfet.*')
    pfet4rex = re.compile('sky130_fd_pr__special_pfet.*')
    # MOSFETs (n-type)
    nfet1rex = re.compile('sky130_fd_pr__esd_nfet.*')
    nfet2rex = re.compile('sky130_fd_pr__nfet.*')
    nfet3rex = re.compile('sky130_fd_pr__rf_nfet.*')
    nfet4rex = re.compile('sky130_fd_pr__special_nfet.*')
    # Bipolars (PNP)
    pnp1rex = re.compile('sky130_fd_pr__pnp.*')
    pnp2rex = re.compile('sky130_fd_pr__rf_pnp.*')
    # Bipolars (NPN)
    npn1rex = re.compile('sky130_fd_pr__rf_npn.*')
    npn2rex = re.compile('sky130_fd_pr__npn.*')

    devicename = devvals[0]

    # NOTE:  When a line in the device list does not have an entry
    # for expected value, then this is a baseline run, and will
    # dump the device name and output measured to a file
    # 'devices_baseline.txt'

    try:
        expectedval = devvals[1]
    except:
        baseline_run = True
    else:
        baseline_run = False

    # Determine the device type from the name
    # (to do:  Pull additional information about the device from the name)
    # (also to do:  separate nmos/pmos testbenches and pnp/npn testbenches)

    if indrex.match(devicename):
        devicetype = 'inductor'
    elif cap1rex.match(devicename):
        devicetype = 'mimcap'
    elif cap2rex.match(devicename):
        if devicename in four_pin_caps:
            devicetype = 'capacitor4pin'
        else:
            devicetype = 'capacitor'
    elif cap3rex.match(devicename):
        devicetype = 'capacitor2pin'
    elif diode1rex.match(devicename):
        devicetype = 'diode'
    elif diode2rex.match(devicename):
        devicetype = 'diode'
    elif diode3rex.match(devicename):
        devicetype = 'diode'
    elif diode4rex.match(devicename):
        devicetype = 'diode'
    elif nfet1rex.match(devicename):
        devicetype = 'nfet'
    elif nfet2rex.match(devicename):
        devicetype = 'nfet'
    elif nfet3rex.match(devicename):
        devicetype = 'nfet'
    elif nfet4rex.match(devicename):
        devicetype = 'nfet'
    elif pfet1rex.match(devicename):
        devicetype = 'pfet'
    elif pfet2rex.match(devicename):
        devicetype = 'pfet'
    elif pfet3rex.match(devicename):
        devicetype = 'pfet'
    elif pfet4rex.match(devicename):
        devicetype = 'pfet'
    elif pnp1rex.match(devicename):
        devicetype = 'pnp'
    elif pnp2rex.match(devicename):
        devicetype = 'pnp'
    elif npn1rex.match(devicename):
        devicetype = 'npn'
    elif npn2rex.match(devicename):
        devicetype = 'npn'
    elif resrex.match(devicename):
        if devicename in two_pin_resistors:
            devicetype = 'res2pin'
        else:
            devicetype = 'resistor'
    else:
        devicetype = 'unknown'

    if devicetype == 'nfet':
        if devicename in five_pin_fets:
            devicetype = 'nfet5term'

    if devicetype != 'unknown':
        print('Diagnostic:  Determined device ' + devicename + ' to be type ' + devicetype)
    else:
        print('Unknown device type for device name ' + devicename + '.  Cannot simulate.')
        reasons[devicename] = 'Unknown device type for device name ' + devicename + '.  Cannot simulate.'
        fails.append(devicename)
        return (passes, fails, baseline_entries, reasons)

    if baseline_run:
        expectedval = 'none'

    if devicetype == 'nfet' or devicetype == 'nfet5term' or devicetype == 'pfet':
        genspice(devicetype + '_vth.spice', devicename, variant, corner)
        (result, reason) = runspice(devicename + '.spice', 'threshold voltage', devicename, expectedval)
        reasons[devicename] = reason
        if baseline_run and isinstance(result, str):
            baseline_entries.append(devicename + '    ' + result)
            passes.append(devicename)
        elif result != 0:
            fails.append(devicename)
        else:
            passes.append(devicename)
        if result != -2:
            make_mosfet_iv_plot('results', devicename, variant, corner)

    elif devicetype == 'npn' or devicetype == 'pnp':
        genspice(devicetype + '.spice', devicename, variant, corner)
        (result, reason) = runspice(devicename + '.spice', 'maximum beta', devicename, expectedval)
        reasons[devicename] = reason
        if baseline_run and isinstance(result, str):
            baseline_entries.append(devicename + '    ' + result)
            passes.append(devicename)
        elif result != 0:
            fails.append(devicename)
        else:
            passes.append(devicename)
        if result != -2:
            make_bipolar_iv_plot('results', devicename, variant, corner)
            make_bipolar_beta_plot('results', devicename, variant, corner)

    elif devicetype == 'mimcap':
        genspice('mimcap_test.spice', devicename, variant, corner)
        (result, reason) = runspice(devicename + '.spice', 'capacitance', devicename, expectedval)
        reasons[devicename] = reason
        if baseline_run and isinstance(result, str):
            baseline_entries.append(devicename + '    ' + result)
            passes.append(devicename)
        elif result != 0:
            fails.append(devicename)
        else:
            passes.append(devicename)

    elif devicetype == 'capacitor':
        genspice('capval_test.spice', devicename, variant, corner)
        (result, reason) = runspice(devicename + '.spice', 'capacitance', devicename, expectedval)
        reasons[devicename] = reason
        if baseline_run and isinstance(result, str):
            baseline_entries.append(devicename + '    ' + result)
            passes.append(devicename)
        elif result != 0:
            fails.append(devicename)
        else:
            passes.append(devicename)

    elif devicetype == 'capacitor4pin':
        genspice('cap4termval_test.spice', devicename, variant, corner)
        (result, reason) = runspice(devicename + '.spice', 'capacitance', devicename, expectedval)
        reasons[devicename] = reason
        if baseline_run and isinstance(result, str):
            baseline_entries.append(devicename + '    ' + result)
            passes.append(devicename)
        elif result != 0:
            fails.append(devicename)
        else:
            passes.append(devicename)

    elif devicetype == 'capacitor2pin':
        genspice('cap2termval_test.spice', devicename, variant, corner)
        (result, reason) = runspice(devicename + '.spice', 'capacitance', devicename, expectedval)
        reasons[devicename] = reason
        if baseline_run and isinstance(result, str):
            baseline_entries.append(devicename + '    ' + result)
            passes.append(devicename)
        elif result != 0:
            fails.append(devicename)
        else:
            passes.append(devicename)

    elif devicetype == 'resistor':
        genspice('resval_test.spice', devicename, variant, corner)
        (result, reason) = runspice(devicename + '.spice', 'resistance', devicename, expectedval)
        reasons[devicename] = reason
        if baseline_run and isinstance(result, str):
            baseline_entries.append(devicename + '    ' + result)
            passes.append(devicename)
        elif result != 0:
            fails.append(devicename)
        else:
            passes.append(devicename)

    elif devicetype == 'res2pin':
        genspice('res2pin_test.spice', devicename, variant, corner)
        (result, reason) = runspice(devicename + '.spice', 'resistance', devicename, expectedval)
        reasons[devicename] = reason
        if baseline_run and isinstance(result, str):
            baseline_entries.append(devicename + '    ' + result)
            passes.append(devicename)
        elif result != 0:
            fails.append(devicename)
        else:
            passes.append(devicename)


    elif devicetype == 'inductor':
        genspice('inductor_test.spice', devicename, variant, corner)
        (result, reason) = runspice(devicename + '.spice', 'inductance', devicename, expectedval)
        reasons[devicename] = reason
        if baseline_run and isinstance(result, str):
            baseline_entries.append(devicename + '    ' + result)
            passes.append(devicename)
        elif result != 0:
            fails.append(devicename)
        else:
            passes.append(devicename)

    elif devicetype == 'diode' or devicetype == 'diode_dev':
        genspice(devicetype + '_vth.spice', devicename, variant, corner)
        (result, reason) = runspice(devicename + '.spice', 'threshold voltage', devicename, expectedval)
        reasons[devicename] = reason
        if baseline_run and isinstance(result, str):
            baseline_entries.append(devicename + '    ' + result)
            passes.append(devicename)
        elif result != 0:
            fails.append(devicename)
        else:
            passes.append(devicename)
        if result != -2:
            make_diode_iv_plot('results', devicename, variant, corner)

    return (passes, fails, baseline_entries, reasons)

#------------------------------------------------------------------------------
# Main script starts here (non-multiprocessing)
#------------------------------------------------------------------------------

if __name__ == "__main__":
    if not os.path.exists('results'):
        os.makedirs('results')

    # To do:  Loop through variant and corner.  For now, fixed.
    variant = 'sky130A'
    corner = 'tt'

    # Original method:  List of devices was in file devices.txt.  If an argument
    # is passed to the program, then use it as the list of devices to process.
    # To get the original behavior, use "run_spice_tests.py devices.txt".

    devicelist = []
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as ifile:
            ilines = ifile.read().splitlines()
        for line in ilines:
            if not line.strip().startswith('#'):
                devicelist.append(line.strip())
    else:
        # Prepare list of devices by scanning the model and cell directories.
        libtop = '/usr/share/pdk/' + variant + '/libs.ref/sky130_fd_pr'
        # techtop = '/usr/share/pdk/' + variant + '/libs.tech/ngspice'
        # Directory containing new continuous models.
        techtop = '..'
        (filesdict, subcktdict, includedict, modfilesdict) = find_all_devices.find_everything(libtop, techtop)
        for key in subcktdict:
            devicelist.append(key)

    # Make sure that the spice initialization file is in the results directory
    if not os.path.exists('results/.spiceinit'):
        techtop = '/usr/share/pdk/' + variant + '/libs.tech/ngspice'
        shutil.copyfile(techtop + '/spinit', 'results/.spiceinit')

    passes = []
    fails = []
    baseline_entries = []
    reasons = {}

    for device in devicelist:
        print('Simulating device ' + device)
        (newpasses, newfails, new_baseline_entries, new_reasons) = do_for_device(device, variant, corner)
        passes.extend(newpasses)
        fails.extend(newfails)
        baseline_entries.extend(new_baseline_entries)
        reasons.update(new_reasons)

    # Output which devices passed and failed

    print()
    print('Simulation summary:')

    print()
    print('Passing devices:')
    for passing in passes:
        print(passing)

    print()
    print('Failing devices:')
    for failing in fails:
        print(failing)
        print('   Reason: ' + reasons[failing])

    # Output pass / fail summary

    print()
    print('Final results:')
    print('Passes: ' + str(len(passes)))
    print('Fails:  ' + str(len(fails)))

    # Repeat the summary in a file "output.log"

    with open('output.log', 'w') as ofile:
        print('Simulation summary:', file=ofile)

        print('', file=ofile)
        print('Passing devices:', file=ofile)
        for passing in passes:
            print(passing, file=ofile)

        print('', file=ofile)
        print('Failing devices:', file=ofile)
        for failing in fails:
            print(failing, file=ofile)
            print('   Reason: ' + reasons[failing], file=ofile)

        # Output pass / fail summary

        print('', file=ofile)
        print('Final results:', file=ofile)
        print('Passes: ' + str(len(passes)), file=ofile)
        print('Fails:  ' + str(len(fails)), file=ofile)

    # Output baseline values if any were generated

    if len(baseline_entries) > 0:
        with open('baseline_results.txt', 'w') as ofile:
            for entry in baseline_entries:
                print(entry, file=ofile)

    if len(fails) > 0:
        sys.exit(1)
    else:
        sys.exit(0)

#------------------------------------------------------------------------------
# Main script starts here (using multiprocessing)
#------------------------------------------------------------------------------

if False:
    # Use forkserver method for multiprocessing (otherwise processes hang)
    multiprocessing.set_start_method('forkserver')

    # Allow process to dump a trace when hit with SIGUSR2
    # ("kill -USR2 <pid>")
    faulthandler.register(signal.SIGUSR2)

    if not os.path.exists('results'):
        os.makedirs('results')

    # To do:  Loop through variant and corner.  For now, fixed.
    variant = 'sky130A'
    corner = 'tt'

    # Original method:  List of devices was in file devices.txt.  If an argument
    # is passed to the program, then use it as the list of devices to process.
    # To get the original behavior, use "run_spice_tests.py devices.txt".

    devicelist = []
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as ifile:
            ilines = ifile.read().splitlines()
        for line in ilines:
            if not line.strip().startswith('#'):
                devicelist.append(line.strip())
    else:
        # Prepare list of devices by scanning the model and cell directories.
        libtop = '/usr/share/pdk/' + variant + '/libs.ref/sky130_fd_pr'
        # techtop = '/usr/share/pdk/' + variant + '/libs.tech/ngspice'
        # Directory containing new continuous models.
        techtop = '..'
        (filesdict, subcktdict, includedict, modfilesdict) = find_all_devices.find_everything(libtop, techtop)
        for key in subcktdict:
            devicelist.append(key)

        # Make sure that the spice initialization file is in the results directory
        if not os.path.exists('results/.spiceinit'):
            # techtop = '/usr/share/pdk/' + variant + '/libs.tech/ngspice'
            techtop = '..'
            shutil.copyfile(techtop + '/spinit', 'results/.spiceinit')

    passes = []
    fails = []
    baseline_entries = []
    reasons = {}

    # Allow ngspice runs to happen in parallel.
    with multiprocessing.Pool() as pool:
        results = []

        for device in devicelist:
            print('Queueing simulation of device ' + device)
            results.append(pool.apply_async(do_for_device, (device,variant,corner)))

        # Method of polling all results, handling those that have finished,
        # and then waiting a few seconds and trying again.

        recycle = results
        pending = devicelist
        k = 0

        while recycle:
            results = recycle
            recycle = []
            lastpending = pending
            pending = []
            for i in range(len(results)):
                r = results[i]
                device = lastpending[i]
                if r.ready():
                    (newpasses, newfails, new_baseline_entries, new_reasons) = r.get()
                    passes.extend(newpasses)
                    fails.extend(newfails)
                    baseline_entries.extend(new_baseline_entries)
                    reasons.update(new_reasons)
                else:
                    recycle.append(r)
                    pending.append(device)
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
                    for device in pending:
                        print('   ' + device)

    # Output which devices passed and failed

    print()
    print('Simulation summary:')

    print()
    print('Passing devices:')
    for passing in passes:
        print(passing)

    print()
    print('Failing devices:')
    for failing in fails:
        print(failing)
        print('   Reason: ' + reasons[failing])

    # Output pass / fail summary

    print()
    print('Final results:')
    print('Passes: ' + str(len(passes)))
    print('Fails:  ' + str(len(fails)))

    # Repeat the summary in a file "output.log"

    with open('output.log', 'w') as ofile:
        print('Simulation summary:', file=ofile)

        print('', file=ofile)
        print('Passing devices:', file=ofile)
        for passing in passes:
            print(passing, file=ofile)

        print('', file=ofile)
        print('Failing devices:', file=ofile)
        for failing in fails:
            print(failing, file=ofile)
            print('   Reason: ' + reasons[failing], file=ofile)

        # Output pass / fail summary

        print('', file=ofile)
        print('Final results:', file=ofile)
        print('Passes: ' + str(len(passes)), file=ofile)
        print('Fails:  ' + str(len(fails)), file=ofile)

    # Output baseline values if any were generated

    if len(baseline_entries) > 0:
        with open('baseline_results.txt', 'w') as ofile:
            for entry in baseline_entries:
                print(entry, file=ofile)

    if len(fails) > 0:
        sys.exit(1)
    else:
        sys.exit(0)
