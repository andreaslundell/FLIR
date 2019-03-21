#!/usr/bin/env python

# Interface to FLIR AX8 camera

import urllib2
import urllib

Reverse_engineering_notes = '''

wget --post-data 'action=set&resource=.resmon.action.snapshot&value=true'  http://192.168.15.6/res.php

wget --post-data 'action=get&resource=.image.services.store.filename' http://192.168.15.6/res.php

//Set to MSX:
.image.sysimg.fusion.fusionData.fusionMode 3

//Set to IR:
.image.sysimg.fusion.fusionData.fusionMode 1
.image.sysimg.fusion.fusionData.useLevelSpan 1

//Set to Visual:
.image.sysimg.fusion.fusionData.fusionMode 1
.image.sysimg.fusion.fusionData.useLevelSpan 0



The variable that controls the Lamp is .system.vcam.torch



In order to enable or disable a given alarm the following Boolean registers should be changed. These registers are accessible via Pass Through Object (EtherNet/IP).

.resmon.items.<alarm#>.active

.image.sysimg.alarms.measfunc.<alarm#>.active


Enabling alarm 1

.resmon.items.1.active TRUE

16 2e 72 65 73 6d 6f 6e 2e 69 74 65 6d 73 2e 31 2e 61 63 74 69 76 65 01

.image.sysimg.alarms.measfunc.1.active TRUE

26 2e 69 6d 61 67 65 2e 73 79 73 69 6d 67 2e 61 6c 61 72 6d 73 2e 6d 65 61 73 66 75 6e 63 2e 31 2e 61 63 74 69 76 65 01

 

Disabling alarm 3

.resmon.items.3.active FALSE

16 2e 72 65 73 6d 6f 6e 2e 69 74 65 6d 73 2e 33 2e 61 63 74 69 76 65 00

.image.sysimg.alarms.measfunc.3.active FALSE

26 2e 69 6d 61 67 65 2e 73 79 73 69 6d 67 2e 61 6c 61 72 6d 73 2e 6d 65 61 73 66 75 6e 63 2e 33 2e 61 63 74 69 76 65 00


See also: BasicICD.pdf


''' 

def CtoK(temp):
    return temp+273.15

class Flir:
    def __init__(self, baseURL='http://192.168.11.47/'):
        self.baseURL = baseURL

    def setResource(self,resource,value):
        return urllib2.urlopen(self.baseURL+'res.php',urllib.urlencode({'action':'set','resource':resource,'value':value})).read()

    def getResource(self,resource):
        return urllib2.urlopen(self.baseURL+'res.php',urllib.urlencode({'action':'get','resource':resource})).read()

    def setIRMode(self):
        f.setResource('.image.sysimg.fusion.fusionData.fusionMode',1)
        f.setResource('.image.sysimg.fusion.fusionData.useLevelSpan',1)

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
        #f.setResource('.image.sysimg.measureFuncs.spot.1.active','true')
        f.setResource('.image.sysimg.measureFuncs.spot.1.x',x)
        f.setResource('.image.sysimg.measureFuncs.spot.1.y',y)
        value = f.getResource('.image.sysimg.measureFuncs.spot.1.valueT')
        return float(value[1:-2])

    def setVisualMode(self):
        f.setResource('.image.sysimg.fusion.fusionData.fusionMode',1)
        f.setResource('.image.sysimg.fusion.fusionData.useLevelSpan',0)

    def setMSXMode(self):
        f.setResource('.image.sysimg.fusion.fusionData.fusionMode',3)

    def setTemperatureRange(self,minTemp, maxTemp):
        f.setResource('.image.contadj.adjMode', 'manual')
        f.setResource('.image.sysimg.basicImgData.extraInfo.lowT',CtoK(minTemp))
        f.setResource('.image.sysimg.basicImgData.extraInfo.highT',CtoK(maxTemp))
    
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

    def getBox(self,boxNumber):
        ret = {}
        bns = str(boxNumber)
        ret['boxNumber']=boxNumber
        #for field in ('active','avgT','avgValid','x','y','width','height','medianT','medianValid','minT','minValid','minX','minY','maxT','maxValid','maxX','maxY'):
        for field in ('active','avgT','minT','maxT'):
            ret[field] =self.getResource('.image.sysimg.measureFuncs.mbox.'+bns+'.'+field)
            if field == 'active' and ret[field] == '"false"':
                break
        return ret

    def getBoxes(self):
        ret = []
        for i in range(1,7):
            ret.append(self.getBox(i))
        return ret

if __name__ == '__main__':
    import sys
    f = Flir()
    if len(sys.argv) > 1:
        res = sys.argv[1]
        if len(sys.argv) == 2:
            if sys.argv[1] == '-b':
                print f.getBox(1)
            else:
                print f.getResource(res)
        elif len(sys.argv) == 3:
            print f.setResource(res,sys.argv[2])
        elif sys.argv[1] == '-t':
            f.setTemperatureRange(float(sys.argv[2]),float(sys.argv[3]))
    else:
        f.setIRMode()
        f.setTemperatureRange(20,45)
        #f.showOverlay(False)
        #f.setPeriodicMode()
        
        for i in range(1,80):
            for j in range(1,60):
                print("value in " + str(i) + "," + str(j) + " is " + str(f.getTemperatureValue(i,j)))
            
        #f.setPalette('bw.pal')

    
