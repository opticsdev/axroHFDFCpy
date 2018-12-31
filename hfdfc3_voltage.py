#!/usr/bin/env python2.7
"""
For testing & calibration of higher voltages per acturator up to 15V
"""
import glob
import os
import time
import datetime
import h5py
#import matplotlib.pyplot as plt
import numpy as np
import astropy.io.fits as pyfits
import config
import wfs
import axroElectronics as ax
#import pdb

# import axroOptimization.evaluateMirrors as eva
# import utilities.imaging.man as man

fdir = config.fdir

#Hardware connection functions
def axInit():
    """
    Run initialization for AXRO electronics. This does not need
    to be done every time this module is reloaded.
    """
    ax.init()


def wfsInit():
    """
    Run initialization for WFS. This does not need to be done
    every time this module is reloaded.
    Also sets the WFS exposure time for proper saturation levels.
    """
    wfs.init()
    wfs.setExposure()

def close():
    """
    Close connections to WFS and AXRO electronics
    """
    wfs.close()
    ax.close()

#Good cell map, list of good cells, where each element is cellnum
#When measuring IFs, you would call [measureIF(c,100) for c in goodcell]

#Influence functions
def measureIF(cellnum, N=1, filebase='', volt=0, ftype=None):
    """
    Measure the influence function of piezo cell cellnum.
    Measure using 100 averages per measurement, and do this N times.
    Save the results in a 3D fits file of shape (N,128,128).
    These results may then be postprocessed into an influence function
    fits or h5 file.

    """
    num = 100
    sy = np.zeros((N, 128, 128))
    sx = np.zeros((N, 128, 128))
    p = np.zeros((N, 128, 128))

    day = datetime.date.today().strftime('%y%m%d')  # capture date for filename encoding
    for i in range(N):
        #Ensure all cells are grounded
        ax.ground()

        #Take WFS reference measurement
        ref_file = os.path.join(fdir, 'Ref_CellNum' + str(cellnum) + '_Meas' + str(i) + '.has')
        wfs.takeWavefront(num, filename=ref_file)

        #Set cell voltage
        ax.setVoltChan(cellnum, volt)
        print(volt)

        print('\nTaking a nap.........\n')
        time.sleep(10)
        #Take actuated WFS measurement
        act_file = os.path.join(fdir, 'Act_CellNum' + str(cellnum) + '_Meas' + str(i) + '.has')
        wfs.takeWavefront(num, filename=act_file)#filename='Act_CellNum_' + str(cellnum) + '_Meas' + str(i) + '.has')
        #time.sleep(1)

        #Ensure all cells are grounded
        ax.ground()

        #Process influence function measurement
        sy[i] = wfs.processHAS(act_file, ref=ref_file, type='Y')
        sx[i] = wfs.processHAS(act_file, ref=ref_file, type='X')
        p[i] = wfs.processHAS(act_file, ref=ref_file, type='P')

    # Write h5 file
    if ftype == 'h5':
        with h5py.File(os.path.join(filebase, day + '_IFdata'), 'a') as fin:
            group = fin.create_group('Actuator %s' % cellnum)
            group.create_dataset('SY', data=sy)
            group.create_dataset('SX', data=sx)
            group.create_dataset('P', data=p)
            group.attr['actuator'] = cellnum

    #Write fits file
    elif ftype == 'fits':
        pyfits.writeto('%s_SY_%03i.fits' % (filebase, cellnum), sy, overwrite=True)
        pyfits.writeto('%s_SX_%03i.fits' % (filebase, cellnum), sx, output_verify='exception', overwrite=True)
        pyfits.writeto('%s_P_%03i.fits' % (filebase, cellnum), p, overwrite=True)

    return sy, sx, p

def compileIF(filebase='', vmax=10.0, ftype='h5'):
    """
    Runs through and applied voltage to each actuator in the AXRO board saving all data into one big file
    """
    for idx in ax.cellmap:
        sy, sx, p = measureIF(idx, N=1, volt=vmax, filebase=filebase, ftype=ftype)



def meanIF(filebase):
    """
    Convert an IF measurement file into a single (128,128) image
    by taking the pixel-by-pixel mean.
    Do this for all IF files that start with filebase.
    Ex. ifs = meanIF('170601_IFs')
    """
    files = glob.glob(filebase + '*')
    res = np.zeros((len(files), 128, 128))
    for i in range(len(files)):
        data = pyfits.getdata(files[i])
        res[i] = np.mean(data, axis=0)
    return res

def measureHysteresisCurve(cellnum, N, filebase):
    voltages = np.arange(0.5, 10.5, 1)
    #voltages = np.array([1.0,3.0,5.0])
    for volt in voltages:
        measureIF(cellnum, N, filebase + '_' + "{:2.1f}".format(volt).replace('.', 'p') + 'V', volt=volt)

def collectHysteresisData(filebase, cellnums=range(3, 112, 10), N=10):
    for cellnum in cellnums:
        measureHysteresisCurve(cellnum, N, filebase)


########################
def measChangeFromVolts(opt_volts, n, filebase=''):
    # First grounding everything on HFDFC3.
    ax.ground()

    # Now taking the grounded reference measurement.
    ref_file = os.path.join(fdir, 'RefCells_Meas' + str(n) + '.has')
    wfs.takeWavefront(100, filename=ref_file)

    #Set optimal cell voltages
    ax.setVoltArr(opt_volts)

    # Waiting to let the cells reach equilibrium -- probably not needed.
    print('\nWaiting for Cells To Stabilize....\n')
    time.sleep(2)

    actual_volts = ax.readVoltArr()

    time.sleep(2)

    # Now taking the activated measurement.
    act_file = os.path.join(fdir, 'ActCells_Meas' + str(n) + '.has')
    wfs.takeWavefront(100, filename=act_file)

    # And returning to the grounded state for safety.
    ax.ground()

    # Computing the relative change from the activated state to the ground state.
    rel_change = wfs.processHAS(act_file, ref=ref_file, type='P')

    # And saving the measurement at the specified file path location.
    figure_filepath = filebase + '_MeasChange_Iter' + str(n) + '.fits'
    hdu = pyfits.PrimaryHDU(rel_change)
    hdu.writeto(figure_filepath, overwrite=True)

    np.savetxt(filebase + '_MeasVoltApplied_Iter' + str(n) + '.txt', actual_volts)

    # Returning the file path location for easy reading with the metrology suite.
    return figure_filepath
