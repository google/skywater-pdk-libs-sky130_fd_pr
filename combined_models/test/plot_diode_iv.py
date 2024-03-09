#!/usr/bin/env python3
#
# Plot DIODE I/V curve from devicename + '.data' from running ngspice
# on 'diode_iv.spice'

import os
import sys
import matplotlib.pyplot as plt


def make_diode_iv_plot(devicepath, devicename, version, corner):

    with open(devicepath + '/' + devicename + '__iv.data', 'r') as ifile:
        idata = ifile.read().split()

    # Reformat data

    nrows = int(len(idata) / 4)
    allId = list(float(idata[p + 1]) for p in range(0, len(idata), 4))
    allVd = list(float(idata[p + 3]) for p in range(0, len(idata), 4))

    # Generate X/Y plot

    plt.figure()
    for i in range(0, len(allId), 181 * 10):
        Id = allId[i : i + 181]
        Vd = allVd[i : i + 181]
        plt.plot(Vd, Id)

    title = 'SkyWater SKY130 PDK ' + version + '\n' + devicename + '\nI/V characteristic (Id vs. Vd) at corner ' + corner
    plt.title(title)
    plt.xlabel('Vd (Volts)')
    plt.ylabel('Id (Amps)')
    plt.axis('on')
    plt.grid('on')
    plt.savefig(devicepath + '/' + devicename + '_id_v_vd.svg', bbox_inches='tight', pad_inches=0.1)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("No device name given to plot_diode_iv")
        sys.exit(1)

    devicename = sys.argv[1]
    version='0.20.1'
    corner='tt'
    make_diode_iv_plot(os.getcwd(), devicename, version, corner)
