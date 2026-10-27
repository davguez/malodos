'''
Created on 21 juin 2010
@author: david guez (guezdav@gmail.com)
This file is a part of the source code of the MALODOS project.
You can use and distribute it freely, but have to conform to the license
attached to this project (LICENSE.txt file)
=====================================================================
sane scanner access
'''
import sane
import gui.utilities as GUI
import data
from scannerAccess import scannerOption
class SaneAccess(object):
    # DATA MEMBERS
    sourceData = None
    dataReadyCallback = None
     
    # CONSTRUCTOR
    def __init__(self,imageContainer,dataReadyCallback=None):
        self.imageContainer = imageContainer
        self.dataReadyCallback = dataReadyCallback
        #self.tmpFileName=tempfile.NamedTemporaryFile().name
        sane.init()
        self.selected = None
        self.sourceData = None
        self.devices=None
 
    # METHODS
    def listSources(self):
        return  sane.get_devices()
    def chooseSource(self,sourceName=None):
        self.devices = sane.get_devices()
        names = [D[2] for D in self.devices]
        
        if sourceName:
            try:
                self.selected = names.index(sourceName)
            except:
                self.selected = None
        if self.selected is None: self.selected = GUI.multichoice(names)
        if self.selected<0 :
            self.selected=None
            return "None"
        else:
            return names[self.selected]
    def openScanner(self):
        """Connect to the scanner"""
        if self.selected is None: self.chooseSource()
        if self.selected is None : return
        try:
            scn = self.devices[self.selected][0]
            self.sourceData = sane.open(scn)
        except:
            self.sourceData = None

    def closeScanner(self):
        """ Close the scanner """
        if self.sourceData : self.sourceData.close()
        self.sourceData=None

    def useOptions(self,options):
        """Use the specific options."""
        if not self.sourceData:
            self.openScanner()
        if not self.sourceData: return
        for k,v in list(options.items()) :
            try:
                if hasattr(self.sourceData,k) and self.sourceData[k].is_settable():
                    if self.sourceData[k].type == sane.TYPE_BOOL:
                        self.sourceData.__setattr__(k,v.lower()=='true' or v=='1' or v.lower()=='on')
                    elif self.sourceData[k].type == sane.TYPE_FIXED:
                        self.sourceData.__setattr__(k,float(v))
                    elif self.sourceData[k].type == sane.TYPE_INT:
                        self.sourceData.__setattr__(k,int(v))
                    else:
                        self.sourceData.__setattr__(k,v)
            except:
                print(_('Option %s not settable') % k)
    def startAcquisition(self,options=None):
        """Begin the acquisition process."""
        if not self.sourceData:
            self.openScanner()
        if not self.sourceData: return
        if not options is None : self.useOptions(options)
        #L=self.get_options()
        #for i in L : print i.name,i.value
        src = self.get_options('source',False)
        if not (src is None) and (len(src)==1) and (src[0].value.lower().count('automatic')>0 or src[0].value.lower().count('adf')>0) :
            try:
                it = self.sourceData.multi_scan()
                cont = True
                while cont :
                    try:
                        img = next(it)
                        data.theData.add_image(img)
                    except:
                        cont=False
            except:
                GUI.show_message(_('Error during scanning, aborted.'))
                return
            self.sourceData=None
        else:
            try:
                img = self.sourceData.scan()
                data.theData.add_image(img)
            except:
                GUI.show_message(_('Error during scanning, aborted.'))
            self.closeScanner()
        if self.dataReadyCallback:
            self.dataReadyCallback()
    def get_options(self,optName=None,autoClose=True):
        """ Get current scanner options """
        L =list()
        try:
            if optName is None or optName.lower() == 'manual_multipage' :
                L.append(scannerOption.scannerOption(name='manual_multipage',title=_('Manual multipage'),
                 description=_('Check to manually scan a multiple page document'),
                 scan_type=scannerOption.TYPE_BOOL,value=False))
        except:
            pass
        if not self.sourceData:
            self.openScanner()
        if not self.sourceData: return L
        for k,o in list(self.sourceData.opt.items()) :
            try:
                if not optName is None and optName.lower() != k.lower() : continue 
                optValue = self.sourceData.__getattr__(k)
            except:
                optValue=None
            L.append(scannerOption.scannerOption(name=k,title=o.title,scan_type=o.type,description=o.desc,constraint=o.constraint,value=optValue))
        if autoClose : self.closeScanner()
        return L
