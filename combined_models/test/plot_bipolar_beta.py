#!/usr/bin/env python3
#
# Plot Bipolar beta curve from devicename + '__beta.data' from running ngspice
# on 'bipolar_test.spice'

import os
import sys
import matplotlib.pyplot as plt

def make_bipolar_beta_plot(devicepath, devicename, version, corner):

    with open(devicepath + '/' + devicename + '__beta.data', 'r') as ifile:
        idata = ifile.read().split()

    # Reformat data

    nrows = int(len(idata) / 6)
    allBeta = list(float(idata[p + 1]) for p in range(0, len(idata), 6))
    allVbe = list(float(idata[p + 3]) for p in range(0, len(idata), 6))
    allVce = list(float(idata[p + 5]) for p in range(0, len(idata), 6))

    # Generate X/Y plots

    fig = plt.figure()
    ax = fig.add_axes([0.1, 0.1, 0.6, 0.75])
    for i in range(0, len(allBeta), 166 * 10):
        Beta = allBeta[i : i + 166]
        Vbe = allVbe[i : i + 166]
        Vce = allVce[i : i + 166]
        ax.plot(Vce, Beta, label='{:.2f}'.format(Vbe[0]))
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0.,
                title='Vbe (Volts)')

    title = 'SkyWater SKY130 PDK ' + version + '\n' + devicename + '\nBeta vs. Vce at corner ' + corner
    plt.title(title)
    plt.xlabel('Vce (Volts)')
    plt.ylabel('Beta')
    plt.axis('on')
    plt.grid('on')
    plt.savefig(devicepath + '/' + devicename + '_beta_v_vce.svg', bbox_inches='tight', pad_inches=0.1)

    fig = plt.figure()
    ax = fig.add_axes([0.1, 0.1, 0.6, 0.75])
    for i in range(0, 166, 18):
        Beta = allBeta[i : len(allBeta): 166]
        Vbe = allVbe[i : len(allVbe): 166]
        Vce = allVce[i : len(allVce): 166]
        ax.plot(Vbe, Beta, label='{:.2f}'.format(Vce[0]))
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0.,
                title='Vce (Volts)')

    title = 'SkyWater SKY130 PDK ' + version + '\n' + devicename + '\nBeta vs. Vbe at corner ' + corner
    plt.title(title)
    plt.xlabel('Vbe (Volts)')
    plt.ylabel('Beta')
    plt.axis('on')
    plt.grid('on')
    plt.savefig(devicepath + '/' + devicename + '_beta_v_vbe.svg', bbox_inches='tight', pad_inches=0.1)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("No device name given to plot_bipolar_beta")
        sys.exit(1)

    devicename = sys.argv[1]
    version = '0.20.1'
    corner = 'tt'
    make_bipolar_beta_plot(os.getcwd(), devicename, version, corner)
