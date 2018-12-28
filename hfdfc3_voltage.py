#!/usr/bin/env python2.7

import numpy as np
import glob
import os
import time
import wfs
import matplotlib.pyplot as plt
import axroElectronics as ax
import astropy.io.fits as pyfits
import config

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
def measureIF(cellnum, N, filebase, volt):
    """
    Measure the influence function of piezo cell cellnum.
    Measure using 100 averages per measurement, and do this N times.
    Save the results in a 3D fits file of shape (N,128,128).
    These results may then be postprocessed into an influence function
    fits file.
    Resulting fits files will be saved as:
    filebase+'_%03i.fits'
    """
    num = 100
    sy = np.zeros((N, 128, 128))
    sx = np.zeros((N, 128, 128))
    p = np.zeros((N, 128, 128))
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

    #Write fits file
    pyfits.writeto('%s_SY_%03i.fits' % (filebase, cellnum), sy, clobber=True)
    pyfits.writeto('%s_SX_%03i.fits' % (filebase, output_verify='exception'cellnum), sx, clobber=True)
    pyfits.writeto('%s_P_%03i.fits' % (filebase, cellnum), p, clobber=True)

    return sy, sx, p

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
        measureHysteresisCurve(cellnum,N,filebase)


########################
def measChangeFromVolts(opt_volts, n, filebase=''):
    # First grounding everything on HFDFC3.
    ax.ground()

    # Now taking the grounded reference measurement.
    ref_file = 'C:\\Users\\rallured\\Documents\\HFDFC3_IterativeCorrection\\RefMeas' + str(n) + '.has'
    wfs.takeWavefront(100, filename = ref_file)

    #Set optimal cell voltages
    ax.setVoltArr(opt_volts)

    # Waiting to let the cells reach equilibrium -- probably not needed.
    print('\nWaiting for Cells To Stabilize....\n')
    time.sleep(2)

    actual_volts = ax.readVoltArr()

    time.sleep(2)

    # Now taking the activated measurement.
    act_file = 'C:\\Users\\rallured\\Documents\\HFDFC3_IterativeCorrection\\OptVolt_Meas' + str(n) + '.has'
    wfs.takeWavefront(100, filename=act_file)

    # And returning to the grounded state for safety.
    ax.ground()

    # Computing the relative change from the activated state to the ground state.
    rel_change = wfs.processHAS(act_file, ref = ref_file, type = 'P')

    # And saving the measurement at the specified file path location.
    figure_filepath = filebase + '_MeasChange_Iter' + str(n) + '.fits'
    hdu = pyfits.PrimaryHDU(rel_change)
    hdu.writeto(figure_filepath,clobber = True)

    np.savetxt(filebase + '_MeasVoltApplied_Iter' + str(n) + '.txt', actual_volts)

    # Returning the file path location for easy reading with the metrology suite.
    return figure_filepath

def readCylWFSRaw(fn):
    """
    Load in data from WFS measurement of cylindrical mirror.
    Assumes that data was processed using processHAS, and loaded into
    a .fits file.
    Scale to microns, remove misalignments,
    strip NaNs.
    If rotate is set to an array of angles, the rotation angle
    which minimizes the number of NaNs in the image after
    stripping perimeter nans is selected.
    Distortion is bump positive looking at concave surface.
    Imshow will present distortion in proper orientation as if
    viewing the concave surface.
    """
    #Remove NaNs and rescale
    d = pyfits.getdata(fn)
    d = man.stripnans(d)

    # Negate to make bump positive.
    d = -d

    return d
