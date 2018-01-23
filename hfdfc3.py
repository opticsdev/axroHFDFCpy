import numpy as np
import matplotlib.pyplot as plt
import time
import wfs
import axroElectronics as ax
import astropy.io.fits as pyfits

import pdb

import axroOptimization.evaluateMirrors as eva
import utilities.imaging.man as man

#Hardware connection functions
def axInit():
    """
    Run initialization for AXRO electronics. This does not need
    to be done every time this module is reloaded.
    """
    ax.init()
    return None

def wfsInit():
    """
    Run initialization for WFS. This does not need to be done
    every time this module is reloaded.
    Also sets the WFS exposure time for proper saturation levels.
    """
    wfs.init()
    wfs.setExposure()
    return None

def close():
    """
    Close connections to WFS and AXRO electronics
    """
    wfs.close()
    ax.close()
    return None

#Good cell map, list of good cells, where each element is cellnum
#When measuring IFs, you would call [measureIF(c,100) for c in goodcell]

#Influence functions
def measureIF(cellnum,N,filebase,volt = 10.):
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
    sy = np.zeros((N,128,128))
    sx = np.zeros((N,128,128))
    p = np.zeros((N,128,128))
    for i in range(N):
        #Ensure all cells are grounded
        ax.ground()
        
        #Take WFS reference measurement
        ref_file = 'C:\\Users\\rallured\\Documents\\HFDFC3_Measurements\\Ref_CellNum' + str(cellnum) + '_Meas' + str(i) + '.has'
        wfs.takeWavefront(num, filename = ref_file) #filename='Ref_CellNum_' + str(cellnum) + '_Meas' + str(i) + '.has')

        #Set cell voltage
        ax.setVoltChan(cellnum,volt)
        print volt
        
        print '\nTaking a nap.........\n'
        time.sleep(10)
        #Take actuated WFS measurement
        act_file = 'C:\\Users\\rallured\\Documents\\HFDFC3_Measurements\\Act_CellNum' + str(cellnum) + '_Meas' + str(i) + '.has'
        wfs.takeWavefront(num,filename = act_file)#filename='Act_CellNum_' + str(cellnum) + '_Meas' + str(i) + '.has')
        #time.sleep(1)

        #Ensure all cells are grounded
        ax.ground()

        #Process influence function measurement
        sy[i] = wfs.processHAS(act_file,ref=ref_file,type='Y')
        sx[i] = wfs.processHAS(act_file,ref=ref_file,type='X')
        p[i] = wfs.processHAS(act_file,ref=ref_file,type='P')

    #Write fits file
    pyfits.writeto('%s_SY_%03i.fits' % (filebase,cellnum),sy, clobber = True)
    pyfits.writeto('%s_SX_%03i.fits' % (filebase,cellnum),sx, clobber = True)
    pyfits.writeto('%s_P_%03i.fits' % (filebase,cellnum),p, clobber = True)

    return sy,sx,p

def meanIF(filebase):
    """
    Convert an IF measurement file into a single (128,128) image
    by taking the pixel-by-pixel mean.
    Do this for all IF files that start with filebase.
    Ex. ifs = meanIF('170601_IFs')
    """
    files = glob.glob(filebase+'*')
    res = np.zeros((len(files),128,128))
    for i in range(len(files)):
        d = pyfits.getdata(files[i])
        res[i] = np.mean(d,axis=0)
    return res

def measureHysteresisCurve(cellnum,N,filebase):
    voltages = np.arange(0.5,10.5,1)
    #voltages = np.array([1.0,3.0,5.0])
    for volt in voltages:
        measureIF(cellnum,N,filebase + '_' + "{:2.1f}".format(volt).replace('.','p') + 'V',volt = volt)
        
def collectHysteresisData(filebase,cellnums = range(3,112,10),N = 10):
    for cellnum in cellnums:
        measureHysteresisCurve(cellnum,N,filebase)


########################
def measChangeFromVolts(opt_volts,n,filebase = ''):
    # First grounding everything on HFDFC3.
    ax.ground()
    
    # Now taking the grounded reference measurement.
    ref_file = 'C:\\Users\\rallured\\Documents\\HFDFC3_IterativeCorrection\\RefMeas' + str(n) + '.has'
    wfs.takeWavefront(100, filename = ref_file)

    #Set optimal cell voltages
    ax.setVoltArr(opt_volts)
    
    # Waiting to let the cells reach equilibrium.
    print '\nWaiting for Cells To Stabilize....\n'
    time.sleep(10)
    
    # Now taking the activated measurement.
    act_file = 'C:\\Users\\rallured\\Documents\\HFDFC3_IterativeCorrection\\OptVolt_Meas' + str(n) + '.has'
    wfs.takeWavefront(100, filename = act_file)
    
    # And returning to the grounded state for safety.
    ax.ground()
    
    # Computing the relative change from the activated state to the ground state.
    rel_change = wfs.processHAS(act_file,ref = ref_file,type = 'P')
    
    # And saving the measurement at the specified file path location.
    figure_filepath = filebase + '_MeasChange_Iter' + str(n) + '.fits'
    hdu = pyfits.PrimaryHDU(rel_change)
    hdu.writeto(figure_filepath,clobber = True)
    
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

def reshapeMeasToDistMap(figure_filepath,dist_map,mask_fraction):
    # Loading the as-measured correction and processing it appropriately to be stripped of
    # exterior NaNs, bump positive, and have best fit cylinder removed (like dist_map and the ifs).
    # This raw correction has its own distinct shape of order 120 by 100.
    raw_correction = readCylWFSRaw(figure_filepath)
    
    # Creating a perimeter shademask consistent with the size of the measured change.
    meas_shade = eva.slv.createShadePerimeter(np.shape(raw_correction),axialFraction = mask_fraction,azFraction = mask_fraction)
    
    # Now making the measured relative change directly comparable to the area of the
    # distortion map we are trying to correct by putting the shade mask in place, and
    # then interpolating to the size of dist_map.
    rel_change = np.copy(raw_correction)
    rel_change[meas_shade == 0] = np.NaN
    rel_change = eva.man.newGridSize(rel_change,np.shape(dist_map))
    return rel_change

def iterCorr(dist_map,ifs,perimeter,dx, \
             filebase = '',max_volts = 10.0):
    '''
    Performs an iterative correction to the HFDFC3 mirror to converge on the best correction available to the
    distortion map provided in dist_map.
    Inputs:
    dist_map - the distortion to be corrected. Assumed to be the same shape as shape(ifs[i]), the shape of the measured
    HFDFC3 influence functions - may not need to be?
    ifs - the measured influence functions of HFDFC at 5.0 V. These have been processed so as not to have NaNs in the
    center so that the optimizer will work.
    perimeter - the outer perimeter we'd like to exclude from correction considerations.
    Outputs:
    '''
    n = 0
    
    def make_bounds(cur_volts):
        bounds = []
        for i in range(np.shape(ifs)[0]):
            bounds.append((0 - cur_volts[i],1 - cur_volts[i]))
        return bounds
    
    # Defining the shade mask for the area we wish to iteratively correct.
    mask_fraction = perimeter*2/101.6
    shademask = eva.slv.createShadePerimeter(np.shape(ifs[0]),axialFraction=mask_fraction,azFraction=mask_fraction)

    # Saving the distortion map at the same format as the correction.
    dist_map_resized = man.newGridSize(dist_map,np.shape(ifs[0]))
    hdu = pyfits.PrimaryHDU(dist_map_resized)
    hdu.writeto(filebase + '_DistortionToCorrect_Iter' + str(n) + '.fits',clobber = True)

    # Performing the first computation of the correction to the distortion map,
    # and saving the first set of optimal voltages. "correction" will be masked,
    # not have best fit cylinder removed, be masked by the shademask, and have
    # shape equal to dist_map.
    correction,opt_volts = eva.correctHFDFC3(dist_map,ifs,shade = shademask,dx = dx,smax = 1.0)
    orig_volts = np.copy(opt_volts)

    # Saving the optimal voltages.
    np.savetxt(filebase + '_OptVolts_Iter' + str(n) + '.txt',opt_volts)
    
    # Saving the computed correction.
    hdu = pyfits.PrimaryHDU(correction)
    hdu.writeto(filebase + '_Correction_Iter' + str(n) + '.fits',clobber = True)
    print 'CORRECTION CALCULATED'
    
    # Measuring the relative change induced by applying the calculated set of optimal voltages.
    figure_filepath = measChangeFromVolts(opt_volts*max_volts,n,filebase)
    
    # Reading the measured change resulting from that voltage application, processing the measurement,
    # and scaling it to the size of dist_map.
    rel_change = reshapeMeasToDistMap(figure_filepath,dist_map,mask_fraction)
    first_meas_change = np.copy(rel_change)
    
    print 'RELATIVE CHANGE MEASURED'
    # Entering the iterative state while the criteria are unfulfilled. 
    while n < 5:
        n = n + 1
        residual = dist_map + rel_change
        
        hdu = pyfits.PrimaryHDU(residual)
        hdu.writeto(filebase + '_DistortionToCorrect_Iter' + str(n) + '.fits',clobber = True)
    
        iter_corr, volt_adjust = eva.correctHFDFC3(residual,ifs,shade = shademask,dx = dx,bounds = make_bounds(opt_volts))
    
        hdu = pyfits.PrimaryHDU(iter_corr)
        hdu.writeto(filebase + '_Correction_Iter' + str(n) + '.fits',clobber = True)    

        opt_volts = opt_volts + volt_adjust
        np.savetxt(filebase + '_OptVolts_Iter' + str(n) + '.txt',opt_volts)
        
        # Computing the first set of optimal voltages:        
        iter_figure_filepath = measChangeFromVolts(opt_volts*max_volts,n,filebase)
        rel_change = reshapeMeasToDistMap(iter_figure_filepath,dist_map,mask_fraction)
        
    best_fit_distortion = np.copy(rel_change)
    
    return dist_map,correction,orig_volts,first_meas_change,residual,iter_corr,volt_adjust,rel_change

    
#Need to perform iterative correction
