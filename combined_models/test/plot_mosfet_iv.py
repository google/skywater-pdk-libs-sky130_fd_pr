#!/usr/bin/env python3
#
# Plot MOSFET I/V curve from devicename + '.data' from running ngspice
# on 'mosfet_test.spice'

import os
import sys
import matplotlib.pyplot as plt


def make_mosfet_iv_plot(devicepath, devicename, version, corner):

    with open(devicepath + '/' + devicename + '__iv.data', 'r') as ifile:
        idata = ifile.read().split()

    # Reformat data

    nrows = int(len(idata) / 6)
    allIds = list(float(idata[p + 1]) for p in range(0, len(idata), 6))
    allVgs = list(float(idata[p + 3]) for p in range(0, len(idata), 6))
    allVds = list(float(idata[p + 5]) for p in range(0, len(idata), 6))

    # Generate X/Y plots

    fig = plt.figure()
    ax = fig.add_axes([0.1, 0.1, 0.6, 0.75])
    for i in range(0, len(allIds), 181 * 10):
        Ids = allIds[i : i + 181]
        Vgs = allVgs[i : i + 181]
        Vds = allVds[i : i + 181]
        ax.plot(Vds, Ids, label='{:.2f}'.format(Vgs[0]))
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0.,
                        title='Vgs (Volts)')

    title = 'SkyWater SKY130 PDK ' + version + '\n' + devicename + '\nI/V characteristic (Ids vs. Vds) at corner ' + corner
    plt.title(title)
    plt.xlabel('Vds (Volts)')
    plt.ylabel('Ids (Amps)')
    plt.axis('on')
    plt.grid('on')
    plt.savefig(devicepath + '/' + devicename + '_ids_v_vds.svg', bbox_inches='tight', pad_inches=0.1)

    fig = plt.figure()
    ax = fig.add_axes([0.1, 0.1, 0.6, 0.75])
    for i in range(0, 181, 18):
        Ids = allIds[i : len(allIds): 181]
        Vgs = allVgs[i : len(allVgs): 181]
        Vds = allVds[i : len(allVds): 181]
        ax.plot(Vgs, Ids, label='{:.2f}'.format(Vds[0]))
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0.,
                        title='Vds (Volts)')

    title = 'SkyWater SKY130 PDK ' + version + '\n' + devicename + '\nI/V characteristic (Ids vs. Vgs) at corner ' + corner
    plt.title(title)
    plt.xlabel('Vgs (Volts)')
    plt.ylabel('Ids (Amps)')
    plt.axis('on')
    plt.grid('on')
    plt.savefig(devicepath + '/' + devicename + '_ids_v_vgs.svg', bbox_inches='tight', pad_inches=0.1)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("No device name given to plot_mosfet_iv")
        sys.exit(1)

    devicename = sys.argv[1]
    version = '0.20.1'
    corner = 'tt'
    make_mosfet_iv_plot(os.getcwd(), devicename, version, corner)
