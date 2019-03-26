#!/usr/bin/env python

# Interface to FLIR AX8 camera

import urllib2 # Python2
import urllib # Python 2
import argparse
import time
import datetime
from time import strftime

import flir_image_extractor

parser = argparse.ArgumentParser(description='Functionality to control/read data from the FLIR AX8 camera.')

parser.add_argument('--url', action="store", help="the url of the camera, including http://", required=True)
parser.add_argument('--type', action="store", help="the type of image", choices = ['msx','ir','visual'])
parser.add_argument('--snap', action="store", help="take a snapshot with the given filename")
parser.add_argument('--interval', action="store", type=float, help="tries to take snapshots at given interval")
parser.add_argument('--csv', action="store", help="take a snapshot and export to csv-file")
parser.add_argument('--plot', action="store_true", help="shows the images")
parser.add_argument('--range', action="store", type=float, nargs=2, help="temperature range")
parser.add_argument('--autorange', action="store_true", help="use auto scale")
parser.add_argument('--nooverlay', action="store_true", help="hide the overlay")
parser.add_argument('--light', action="store", help="activate the torchlight", choices = ['on','off'])
parser.add_argument('--debug', action="store_true", help="prints extra debug information")

debug = False

def CtoK(temp):
    return temp+273.15

class Flir:
    def __init__(self, baseURL='http://192.168.11.47/'):
        self.baseURL = baseURL

    def setResource(self,resource,value):
        message = urllib2.urlopen(self.baseURL+'res.php',urllib.urlencode({'action':'set','resource':resource,'value':value})).read() # Python 2
        #message = urlopen(self.baseURL+'res.php', urlencode({'action':'set','resource':resource,'value':value})).read()

        if (debug and message != "\"\""):
            print(" Return message when setting " + resource + " to " + str(value) + ":\r\n" +message)
        
        return (message)

    def getResource(self,resource):
        return urllib2.urlopen(self.baseURL+'res.php',urllib.urlencode({'action':'get','resource':resource})).read()

    def setVisualMode(self):
        f.setResource('.image.sysimg.fusion.fusionData.fusionMode',1)
        f.setResource('.image.sysimg.fusion.fusionData.useLevelSpan',0)

    def setIRMode(self):
        f.setResource('.image.sysimg.fusion.fusionData.fusionMode',1)
        f.setResource('.image.sysimg.fusion.fusionData.useLevelSpan',1)

    def setMSXMode(self):
        f.setResource('.image.sysimg.fusion.fusionData.fusionMode',3)

    def setPeriodicMode(self):
        f.setResource('.resmon.schedule.active','true')
        f.setResource('.resmon.schedule.config.ftp', '192.168.11.18')
        f.setResource('.resmon.schedule.config.imageFormat', 'JPEG')
        f.setResource('.resmon.schedule.actions.sendImage', 'true')
        f.setResource('.resmon.schedule.results.1.active', 'true')
        f.setResource('.resmon.schedule.wednesday.active', 'true')
        f.setResource('.resmon.schedule.wednesday.mode', 'repeat')
        f.setResource('.resmon.schedule.wednesday.start', '10:00')
        f.setResource('.resmon.schedule.wednesday.stop', '22:00')
        f.setResource('.resmon.schedule.wednesday.interval', '00:01')
        f.setResource('.resmon.schedule.reinit','true')

    def getTemperatureValue(self, x, y):
        f.setResource('.image.sysimg.measureFuncs.spot.1.active','true')
        f.setResource('.image.sysimg.measureFuncs.spot.1.x',x)
        f.setResource('.image.sysimg.measureFuncs.spot.1.y',y)
        value = f.getResource('.image.sysimg.measureFuncs.spot.1.valueT')
        return float(value[1:-2])

    def setTemperatureRange(self,minTemp, maxTemp):
        f.setResource('.image.contadj.adjMode', 'manual')
        f.setResource('.image.sysimg.basicImgData.extraInfo.lowT',CtoK(minTemp))
        f.setResource('.image.sysimg.basicImgData.extraInfo.highT',CtoK(maxTemp))

    def setAutoTemperatureRange(self):
        f.setResource('.image.contadj.adjMode', 'auto')
    
    def showOverlay(self,show=True):
        if show:
            f.setResource('.resmon.config.hideGraphics','false')
        else:
            f.setResource('.resmon.config.hideGraphics','true')

    def light(self,on=True):
        if on:
            f.setResource('.system.vcam.torch','true')
        else:
            f.setResource('.system.vcam.torch','false')

    def setPalette(self, palette):
        # iron.pal, bw.pal, rainbow.pal
        f.setResource('.image.sysimage.palette.readFile',palette)

    def getSnapshot(self, jpgfile):

        start = time.time()

        dt = datetime.datetime.now()
        filename = 'ax8' + str(dt.hour) + "-" + str(dt.minute) + "-" + str(dt.second) + ".jpg"

        f.setResource('.image.services.store.format','JPEG')
        f.setResource('.image.services.store.overlay','true')
        f.setResource('.image.services.store.owerwrite','true')
        f.setResource('.image.services.store.fileNameW','/FLIR/images/' + filename)
        f.setResource('.image.services.store.commit','true')
        fh = open(jpgfile, "wb")

        ready = False

        while not(ready):
            try:
                response = urllib2.urlopen('http://192.168.11.47/download.php?file=/FLIR/images/' + filename)
                ready = True
                fh.write(response.read())
            except urllib2.HTTPError as e:
                time.sleep(0.05)
        fh.close()

        end = time.time()

        print("Downloaded image " + jpgfile + " from camera in " + str(end-start) + " s.")
    
    def getCsvData(self, jpgfile, csvfile, plot = False):

        start = time.time()
                    
        fie = flir_image_extractor.FlirImageExtractor()
        fie.process_image(jpgfile)

        fie.export_thermal_to_csv(csvfile)

        end = time.time()
                    
        print("Thermal data in picture " + jpgfile + " written to " + csvfile + " in " + str(end-start) + " s.")
        
        if (plot):
            fie.plot()

    #def getBox(self,boxNumber):
    #    ret = {}
    #    bns = str(boxNumber)
    #    ret['boxNumber']=boxNumber
    #    #for field in ('active','avgT','avgValid','x','y','width','height','medianT','medianValid','minT','minValid','minX','minY','maxT','maxValid','maxX','maxY'):
    #    for field in ('active','avgT','minT','maxT'):
    #        ret[field] =self.getResource('.image.sysimg.measureFuncs.mbox.'+bns+'.'+field)
    #        if field == 'active' and ret[field] == '"false"':
    #            break
    #    return ret

    #def getBoxes(self):
    #    ret = []
    #    for i in range(1,7):
    #        ret.append(self.getBox(i))
    #    return ret

if __name__ == '__main__':
    import sys

    args = parser.parse_args()

    if (args.debug):
        debug = True

    if (not(args.url.startswith('http://'))):
        args.url = 'http://' + args.url

    if (not(args.url.endswith('/'))):
        args.url = args.url + '/'

    f = Flir(baseURL=args.url)

    if (args.type == 'visual'):
        f.setVisualMode()
        print("Setting visual mode")
    elif (args.type == 'ir'):
        f.setIRMode()
        print("Setting IR mode")
    elif (args.type == 'msx'):
        f.setMSXMode()
        print("Setting MSX mode")
    else:
        print("Wrong argument given to parameter 'type'")

    if (args.nooverlay):
        f.showOverlay(False)
        print("Hiding the overlay")
    else:
        f.showOverlay(True)
        print("Showing the overlay")

    if (args.light == 'off'):
        f.light(False)
        print("Torchlight deactivated")
    elif (args.light == 'on'):
        f.light(True)
        print("Torchlight activated")
    
    if (args.autorange):
        f.setAutoTemperatureRange()
        print("Auto range set")

    if (args.range):
        f.setTemperatureRange(args.range[0],args.range[1])
        print("Range set to [" + str(args.range[0]) + "," + str(args.range[1]) + "]")
    
    if (args.interval):
        if (args.snap):
          
            while True:
                timestamp = strftime("%H%M%S")
                filename = args.snap.strip('.jpg') + '_' + timestamp + '.jpg'
                f.getSnapshot(filename)

                if (args.csv):
                    filenamecsv = filename.strip('.jpg') + '.csv'
                    f.getCsvData(filename, filenamecsv, False)

                if (args.interval > 0):
                    time.sleep(args.interval)

    elif (args.snap):
        f.getSnapshot(args.snap)

    if (args.csv):
        if (not args.snap):
            f.getSnapshot('snap.jpg')
            f.getCsvData('snap.jpg',args.csv, args.plot)
        else:
            f.getCsvData(args.snap, args.csv, args.plot)
    

    # if len(sys.argv) > 1:
    #     res = sys.argv[1]
    #     if len(sys.argv) == 2:
    #         if sys.argv[1] == '-b':
    #             print f.getBox(1)
    #         else:
    #             print f.getResource(res)
    #     elif len(sys.argv) == 3:
    #         print f.setResource(res,sys.argv[2])
    #     elif sys.argv[1] == '-t':
    #         f.setTemperatureRange(float(sys.argv[2]),float(sys.argv[3]))
    # else:
    #     f.setMSXMode()
    #     f.setTemperatureRange(20,45)
    #     f.showOverlay(True)
    #     #f.setPeriodicMode()
        
        #for i in range(1,80):
        #    for j in range(1,60):
        #        print("value in " + str(i) + "," + str(j) + " is " + str(f.getTemperatureValue(i,j)))
            
        #f.setPalette('bw.pal')

    
