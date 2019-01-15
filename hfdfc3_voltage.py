#!/usr/bin/env python2.7
"""
For testing & calibration of higher voltages per acturator up to 15V
"""
import glob
import os
import time
import datetime
import ast
import h5py
import numpy as np
import astropy.io.fits as pyfits
import cv2
#import matplotlib.pyplot as plt
import config
import wfs
import axroElectronics as ax
import connect_client as intcom

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
#When measuring IFs, you would call [measureIF_ WFS(c,100...) for c in goodcell]

#Influence functions with the WFS
def measureIF_WFS(cellnum, N=1, filebase='', volt=0, ftype=None):
    """
    Measure the influence function using the WFS of piezo cell cellnum.
    Measure using 100 averages per measurement, and do this N times.
    Save the results in a 3D fits file of shape (N,128,128).
    These results may then be postprocessed into an influence function
    fits or h5 file.

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
        sy[i] = wfs.processHAS(act_file, ref=ref_file, ptype='Y')
        sx[i] = wfs.processHAS(act_file, ref=ref_file, ptype='X')
        p[i] = wfs.processHAS(act_file, ref=ref_file, ptype='P')

    # Save compiled array to defined filetype
    save_dataset_wfs(sx, sy, p, cellnum, filebase=filebase, ftype=ftype)


#Influence functions with the WFS
def measureIF_4D(cellnum, N=1, filebase='', volt=0, ftype='h5'):
    """
    Measure the influence function using the WFS of piezo cell cellnum.
    Measure using 100 averages per measurement, and do this N times.
    Save the results in a h5 file of shape (N,128,128).
    These results may then be postprocessed into an influence function
    fits or h5 file.

    """
    num = 32  # num frames avg

    for i in range(N):
        #Ensure all cells are grounded
        ax.ground()

        #Take WFS reference measurement
        ref_file = os.path.join(fdir, 'Ref_CellNum' + str(cellnum) + '_Meas' + str(i) + '.h5')
        intcom.takeWavefront(num, filename=ref_file)

        #Set cell voltage
        ax.setVoltChan(cellnum, volt)
        print(volt)

        print('\nTaking a nap.........\n')
        time.sleep(2)
        #Take actuated WFS measurement
        act_file = os.path.join(fdir, 'Act_CellNum' + str(cellnum) + '_Meas' + str(i) + '.h5')
        intcom.takeWavefront(num, filename=act_file)#filename='Act_CellNum_' + str(cellnum) + '_Meas' + str(i) + '.has')
        time.sleep(1)
        #Ensure all cells are grounded
        ax.ground()
        refdata, _, _ = load_h5(ref_file)
        actdata, _, _ = load_h5(act_file)

        # Save to a composite h5 file of the reference subtracted data
        save_dataset_4d(actdata-refdata, cellnum=cellnum, filebase=filebase, ftype=ftype)

        #Process influence function measurement
def save_dataset_4d(data, cellnum, filebase='', ftype='h5'):
    day = datetime.date.today().strftime('%y%m%d')  # capture date for filename encoding
    # Write h5 file
    if ftype == 'h5':
        with h5py.File(os.path.join(filebase, day + '_IFdata'), 'a') as fin:
            group = fin.create_group('Actuator %s' % cellnum)
            group.create_dataset('wfe', data=data)
            group.attr['actuator'] = cellnum

    #Write fits file
    elif ftype == 'fits':
        pyfits.writeto('%s_WFE_%03i.fits' % (filebase, cellnum), data, overwrite=True)


    # Save compiled array to defined filetype
    #save_dataset(sx, sy, p, cellnum, filebase=filebase, ftype=ftype)

def load_h5(fname, surfmap=True):
    """ Loads a 4D .h5 interferogram file from a file location (local or network drive)"""
    filenames = glob.glob(fname)
    print("Files found: {}".format(filenames))
    fin = h5py.File(filenames[0])
    meas = fin['measurement0']  # Wavefront data located in 'measurement0'
    opdsets = meas['genraw']
    wvl = opdsets.attrs['wavelength'][:]
    wvl = float(wvl[:-3])
    # Get the x pixel spacing
    try:
        iscale = float(opdsets.attrs['xpix'][:-3])
    except TypeError:
        iscale = 0.0
        print("No Calibration Dimensioning Found in H5 file")
    # Return either surface map or fringe map
    if surfmap is True:
        data = np.asarray(opdsets['data'])
        data[data > 1e10] = np.nan  # Eliminates "bad" data sets to NAN
        data *= wvl * mask_data(filenames[0])
    else:
        data = np.asarray(meas['reserve_interferogram']['frame4']['data'])
    return data, wvl, iscale

def center_circle_mask(points, arrayshape=(480, 640), maskinside=True):
    """creates a boolean masking array of a circle"""
    mask = np.zeros(arrayshape)
    points = [float(ii) for ii in points.split(', ')]
    center_col = round(points[0] + (points[2]/2))
    center_row = round(points[1] + (points[3]/2))
    Y, X = np.ogrid[:arrayshape[0], :arrayshape[1]]

    dist = np.sqrt((X - center_col)**2 + (Y - center_row)**2)
    if maskinside is False:
        mask = dist <= points[2]/2
    else:
        mask = dist >= points[2]/2
    return mask * 1

def rect_mask(points, arrayshape=(480, 640), maskinside=True):
    mask = np.zeros(arrayshape)

    points = ast.literal_eval(points)
    polygon = np.array(points[:-1], dtype=np.int32)

    mask = (cv2.fillPoly(mask, [polygon], 1)).astype(np.int8)

    if maskinside is True:
        mask ^= 1
    return mask

def mask_data(fname):
    """find Interferometer masks"""
    filenames = glob.glob(fname)
    h5file = h5py.File(filenames[0])
    masklist = h5file['measurement0']['maskshapes']
    maskshape = np.asarray(h5file['measurement0']['genraw']['data']).shape
    mask = np.ones(maskshape)

    if 'Analysis' in masklist:
        print('Analysis Masks found: {}'.format(list(masklist['Analysis'].attrs)))
        for maskitem in masklist['Analysis'].attrs.values():
            maskitem = maskitem.decode().split('|')
            if maskitem[0] == 'circle':
                if 'Mask Inside' in maskitem[2]:
                    mask *= center_circle_mask(maskitem[1], maskshape, maskinside=True)
                elif 'Mask Outside' in maskitem[2]:
                    mask *= center_circle_mask(maskitem[1], maskshape, maskinside=False)
                elif 'Pass Inside' in maskitem[2]:
                    mask += center_circle_mask(maskitem[1], maskshape, maskinside=False)
            elif maskitem[0] == 'rect':
                if 'Mask Inside' in maskitem[2]:
                    mask *= rect_mask(maskitem[1], maskshape, maskinside=True)
                elif 'Mask Outside' in maskitem[2]:
                    mask *= rect_mask(maskitem[1], maskshape, maskinside=False)
                elif 'Pass Inside' in maskitem[2]:
                    mask += rect_mask(maskitem[1], maskshape, maskinside=False)
    mask = mask.astype(np.bool)*1.0
    mask[mask == 0] = np.nan
    return mask

def save_dataset_wfs(sx, sy, p, cellnum, filebase='', ftype='h5'):
    day = datetime.date.today().strftime('%y%m%d')  # capture date for filename encoding
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

def compileIF_WFS(filebase='', vmax=10.0, ftype='h5'):
    """
    Runs through and applied voltage to each actuator in the AXRO board saving
    all WFS data into one big file
    """
    for idx in ax.cellmap:
        measureIF_WFS(idx, N=1, volt=vmax, filebase=filebase, ftype=ftype)

def compileIF_INT(filebase='', vmax=10.0, ftype='h5'):
    """
    Runs through and applied voltage to each actuator in the AXRO board saving
    all 4D Interferometer Wavefront data into one big file.
    """
    for idx in ax.cellmap:
        measureIF_WFS(idx, N=1, volt=vmax, filebase=filebase, ftype=ftype)

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

    for volt in voltages:
        measureIF_WFS(cellnum, N, filebase + '_' + "{:2.1f}".format(volt).replace('.', 'p') + 'V', volt=volt)


def collectHysteresisData(filebase, cellnums=range(3, 112, 10), N=10):
    for cellnum in cellnums:
        measureHysteresisCurve(cellnum, N, filebase)


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
    rel_change = wfs.processHAS(act_file, ref=ref_file, ptype='P')

    # And saving the measurement at the specified file path location.
    figure_filepath = filebase + '_MeasChange_Iter' + str(n) + '.fits'
    hdu = pyfits.PrimaryHDU(rel_change)
    hdu.writeto(figure_filepath, overwrite=True)

    np.savetxt(filebase + '_MeasVoltApplied_Iter' + str(n) + '.txt', actual_volts)

    # Returning the file path location for easy reading with the metrology suite.
    return figure_filepath
