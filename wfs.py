import numpy.ctypeslib as npct
import ctypes
import numpy as np
import matplotlib.pyplot as plt
import os,glob
import astropy.io.fits as pyfits
import pdb

#Load in DLL
dlldir = 'C:\\Users\\WFS\\Documents\\Visual Studio 2015\\Projects\\WFS3\\Debug'
cwd = os.getcwd()
os.chdir(dlldir)
lib = npct.load_library('WFS3','.')
os.chdir(cwd)

#Ctypes (for convenience)
array_1d_double = npct.ndpointer(dtype=np.double, ndim=1, flags='CONTIGUOUS')
cpoint = ctypes.c_char_p
cbool = ctypes.c_bool
cchar = ctypes.c_char
cint = ctypes.c_int
cll = ctypes.c_longlong
cdoub = ctypes.c_double

#Set up functions
lib.processFile.restype=None
lib.processFile.argtypes = [array_1d_double,cpoint,cpoint,cbool,cbool,\
                            cbool,cbool,cchar]
lib.takeWavefront.restype=cdoub
lib.takeWavefront.argtypes = [cint,cint,cpoint,cbool,cpoint,cbool,cpoint,cbool]
lib.takeImage.restype=cdoub
lib.takeImage.argtypes = [cint,cint,cpoint,cbool,cpoint,cbool]
lib.saturationLevel.restype=cdoub
lib.saturationLevel.argtypes = [cpoint]

#Create a global exposure time variable
exptime = 3600 #3.6 msec default exposure time

def init():
    """Initialize the connection to the WFS
    Call this before trying to use it to take images
    or wavefronts
    """
    lib.init()
    return

def close():
    """Close the connection to the WFS
    Good practice to call this after a session, though
    it won't break anything not to
    """
    lib.close()
    return

def getSat(filename):
    return lib.saturationLevel(filename)

def processHAS(filename,ref=None,dbl=True,nb=True,notilt=True,type='P'):
    """
    Load a .has file and apply the desired processing
    If ref is not none, the .has file pointed to will be
    subtracted from the main .has file.
    dbl indicates double path
    nb indicates neighborhood extension
    notilt removes tip and tilt
    type='P' returns phase
    type='X' returns X slopes
    type='Y' returns Y slopes
    """
    slopes = np.zeros((128*128))
    if ref is None:
        ref,flag='',False
    else:
        flag=True
    lib.processFile(slopes,filename,ref,flag,dbl,nb,notilt,type)
    return slopes.reshape((128,128))

def takeWavefront(num,filename=None,bg=None,img=None):
    """
    Takes a wavefront measurement and saves the result to a .has file.
    For optional BG subtraction, set bg to a .hmg filename
    num is the number of images to average
    exp is the exposure time in microseconds
    img is the filename to save the himg file to
    Saturation level needs to be below 70% in order to be sure
    images are not saturated and degrading measurement noise
    If returned saturation level is out of bounds, call a routine
    to adjust exposure time
    """
    global exptime
    if bg is None:
        flag=False
    else:
        flag=True
    if img is None:
        iflag=False
    else:
        iflag=True
    if filename is None:
        flag2 = False
    else:
        flag2 = True
    print exptime
    cursat =  lib.takeWavefront(int(num),int(exptime),filename,flag2,\
                                bg,flag,img,iflag)
    print cursat

    if (cursat < .6) or (cursat > .7):
        print 'Setting exposure'
        setExposure(bg=bg)
        cursat = takeWavefront(num,filename=filename,bg=bg,img=img)

    return cursat

def takeImage(num,exp=exptime,filename=None,bg=None):
    """
    Takes a wavefront image and saves the result to a .hmg file.
    For optional BG subtraction, set bg to a .hmg filename
    num is the number of images to average
    exp is the exposure time in microseconds
    This function will return the saturation fraction
    """
    global exptime
    if bg is None:
        flag=False
    else:
        flag=True
    if filename is None:
        flag2=False
    else:
        flag2=True
    print exp
    return lib.takeImage(int(num),int(exp),filename,flag2,bg,flag)

def setExposure(bg=None):
    """
    Adjust exposure time to reach 65-70%.
    If camera is oversaturated, reduce exposure time by half
    If camera is undersaturated, multiply exposure time
    by .7/currentSat
    Call recursively until saturation level is corrected
    Set global exptime variable to required exposure time.
    """
    global exptime
    #Get current saturation level
    cursat = takeImage(1,exptime,'',bg=bg)
    print cursat, exptime
    #Determine course of action
    if (cursat > .6) & (cursat < .7):
        return exptime
    elif cursat >= 1:
        exptime = exptime / 2.
        return setExposure(bg=bg)
    else:
        exptime = exptime * .675/cursat
        return setExposure(bg=bg)

def testRepeatability(nb,N):
    filenames = ['Repeatability%04i.has' % i for i in range(N)]
    #Take the data!
    sat = [takeWavefront(nb,filename=f,\
                         img=f.split('.')[0]+'.himg') for f in filenames]
    return sat

def convertRepeatability():
    filenames = glob.glob('*.has')
    filenames.sort()

    for i in range(np.size(filenames)-1):
        slopesx = processHAS(filenames[i+1],ref=filenames[i],type='X')
        slopesy = processHAS(filenames[i+1],ref=filenames[i],type='Y')
        pyfits.writeto('SlopesY%04i.fits' % i,slopesy,clobber=True)
        pyfits.writeto('SlopesX%04i.fits' % i,slopesx,clobber=True)
    return
        
def repeatability(nb,N):
    sat = testRepeatability(nb,N)
    convertRepeatability()
    fn = glob.glob('SlopesX*')
    fn.sort()
    slopesx = [getdata(f) for f in fn]
    rmsx = [rms(s) for s in slopesx]
    return rmsx,sat

def getdata(f):
    fl = pyfits.open(f)
    d = fl[0].data
    fl.close()
    return d

def rms(x):
    return np.sqrt(np.nanmean((x-np.nanmean(x))**2))
        

#Test script
if __name__ == "__main__":
##    lib.init()
##    lib.close()
##    filename="c:/DoubleSled/151218_PreVibe01.has"
    slopes = np.zeros(128*128)
##    lib.manipulateDouble.restype=None
##    lib.manipulateDouble.argtypes = [array_1d_double]
##    lib.manipulateDouble(slopes)
##    print slopes[60]
##    m = input('')


    #Try reference
##    lib.processFile(slopes,"c:/DoubleSled/151215_DoubleSledFigure.has",\
##                    "c:/DoubleSled/151215_Ref.has",False,False,False,True,'X')
##    #Reshape slopes array and plot
##    plt.ion()
##    plt.figure()
##    plt.imshow(slopes.reshape((128,128)))
##    plt.colorbar()
##    plt.title('Reference')
##    slopes2 = np.zeros(128*128)
##    lib.processFile(slopes2,"c:/DoubleSled/151215_DoubleSledFigure.has",\
##                    "c:/DoubleSled/151215_Ref.has",False,False,False,False,'X')
##    plt.figure()
##    plt.imshow(slopes2.reshape((128,128)))
##    plt.colorbar()
##    plt.title('No Ref')

    #Try shooting a wavefront
##    lib.init()
##    lib.takeWavefront(1,1000,"DLLTest.has","",False)
##    lib.close()
    
