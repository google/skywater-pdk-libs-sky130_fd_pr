#!/usr/bin/env python3
#
# Plot MOSFET Vth histogram from file 'results.txt' from running ngspice
# on 'nfet_vth.spice'

import os
import sys
import matplotlib.pyplot as plt

def make_mosfet_vth_hist(devicename, variant, corner):

    rootname = devicename + '_' + corner + '_' + variant[-1]
    datafile = 'results/' + rootname + '.dat'
    if not os.path.isfile(datafile):
        print('No such data file ' + datafile)
        return

    with open(datafile, 'r') as ifile:
        sdata = ifile.read().split()

    idata = []
    for value in sdata:
        idata.append(float(value))

    # Generate histogram

    fig = plt.figure()
    ax = fig.add_axes([0.1, 0.1, 0.6, 0.75])
    ax.hist(idata, bins=10)

    title = 'SkyWater PDK ' + variant + '\n' + devicename + '\nVth histogram at corner ' + corner
    plt.title(title)
    plt.xlabel('Vth (Volts)')
    plt.ylabel('bins')
    plt.axis('on')
    plt.grid('on')
    plotfile = 'results/' + rootname + '.svg'
    plt.savefig(plotfile, bbox_inches='tight', pad_inches=0.1)

    print('Histogram saved in file ' + plotfile)

if __name__ == '__main__':

    variant = 'sky130A'
    corner = 'tt_mm'
    device = 'sky130_fd_pr__nfet_01v8'

    for argument in sys.argv[1:]:
        optlist = argument.split('=')
        if len(optlist) == 2:
            if optlist[0] == 'variant':
                variant = optlist[1]
            elif optlist[0] == 'corner':
                corner = optlist[1]
            elif optlist[0] == 'device':
                device = optlist[1]

    make_mosfet_vth_hist(device, variant, corner)
