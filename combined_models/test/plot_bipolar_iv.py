#!/usr/bin/env python3
#
# Plot Bipolar I/V curve from devicename + '.data' from running ngspice
# on 'bipolar_test.spice'

import os
import sys
import matplotlib.pyplot as plt

def make_bipolar_iv_plot(devicepath, devicename, version, corner):

    with open(devicepath + '/' + devicename + '__iv.data', 'r') as ifile:
        idata = ifile.read().split()

    # Reformat data

    nrows = int(len(idata) / 6)
    allIce = list(float(idata[p + 1]) for p in range(0, len(idata), 6))
    allVbe = list(float(idata[p + 3]) for p in range(0, len(idata), 6))
    allVce = list(float(idata[p + 5]) for p in range(0, len(idata), 6))

    # Generate X/Y plots

    fig = plt.figure()
    ax = fig.add_axes([0.1, 0.1, 0.6, 0.75])
    for i in range(0, len(allIce), 181 * 10):
        Ice = allIce[i : i + 181]
        Vbe = allVbe[i : i + 181]
        Vce = allVce[i : i + 181]
        ax.plot(Vce, Ice, label='{:.2f}'.format(Vbe[0]))
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0.,
                    title='Vbe (Volts)')

    title = 'SkyWater SKY130 PDK ' + version + '\n' + devicename + '\nI/V characteristic (Ice vs. Vce) at corner ' + corner
    plt.title(title)
    plt.xlabel('Vce (Volts)')
    plt.ylabel('Ice (Amps)')
    plt.axis('on')
    plt.grid('on')
    plt.savefig(devicepath + '/' + devicename + '_ice_v_vce.svg', bbox_inches='tight', pad_inches=0.1)

    fig = plt.figure()
    ax = fig.add_axes([0.1, 0.1, 0.6, 0.75])
    for i in range(0, 181, 18):
        Ice = allIce[i : len(allIce): 181]
        Vbe = allVbe[i : len(allVbe): 181]
        Vce = allVce[i : len(allVce): 181]
        ax.plot(Vbe, Ice, label='{:.2f}'.format(Vce[0]))
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0.,
                    title='Vce (Volts)')

    title = 'SkyWater SKY130 PDK ' + version + '\n' + devicename + '\nI/V characteristic (Ice vs. Vbe) at corner ' + corner
    plt.title(title)
    plt.xlabel('Vbe (Volts)')
    plt.ylabel('Ice (Amps)')
    plt.axis('on')
    plt.grid('on')
    plt.savefig(devicepath + '/' + devicename + '_ice_v_vbe.svg', bbox_inches='tight', pad_inches=0.1)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("No device name given to plot_bipolar_iv")
        sys.exit(1)

    devicename = sys.argv[1]
    version='0.20.1'
    corner='tt'
    make_bipolar_iv_plot(os.getcwd(), devicename, version, corner)
