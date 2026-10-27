'''
Created on 21 juin 2010. Copyright 2010, David GUEZ
@author: david guez (guezdav@gmail.com)
This file is a part of the source code of the MALODOS project.
You can use and distribute it freely, but have to conform to the license
attached to this project (LICENSE.txt file)
=====================================================================
GUI dialog for addition of a file into the database
'''
import wx
import os
from . import RecordWidget
from database import theConfig
from algorithms.general import str_to_bool
from . import docWindow
import data

class AddFileWindow(wx.Dialog):
    '''
    GUI dialog for addition of a file into the database
    '''


    #===========================================================================
    # constructor (building gui)
    #===========================================================================
    def __init__(self,parent, title,filename=None):
        '''
        Constructor
        '''
        wx.Dialog.__init__(self, parent, -1, _('Adding a documents to the database'),style=wx.CLOSE_BOX | wx.SYSTEM_MENU | wx.CAPTION | wx.RESIZE_BORDER | 0 | 0 | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX)
        self.panel = wx.Panel(self, -1)
        if not filename:
            dlg = wx.FileDialog(self,style=wx.FD_OPEN,message=_('filename of the document to add'))
            
            if dlg.ShowModal():
                filename = os.path.join(dlg.Directory,dlg.Filename)
        if not filename : return
        try:
            data.theData.load_file(filename, do_clear=False)
        except:
            pass
        
        self.totSizer = wx.BoxSizer(wx.VERTICAL)
        self.horSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.docWin = docWindow.docWindow(self.panel,-1)
        self.recordPart = RecordWidget.RecordWidget(self.panel,filename)
        self.recordPart.cbOCR.SetValue(str_to_bool(theConfig.get_param('OCR', 'autoStart','1')))
        self.btSizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.btOk = wx.Button(self.panel,-1,_('Ok'))
        self.btCancel = wx.Button(self.panel,-1,_('Cancel'))

        self.btSizer.Add(self.btOk,1,wx.EXPAND)
        self.btSizer.Add(self.btCancel,1,wx.EXPAND)
        
        self.horSizer.Add(self.recordPart,1,wx.EXPAND)
        self.horSizer.Add(self.docWin,1,wx.EXPAND)
        self.totSizer.Add(self.horSizer,1,wx.EXPAND)
        self.totSizer.Add(self.btSizer,0,wx.EXPAND)

        self.panel.SetSizerAndFit(self.totSizer)
        self.totSizer.Fit(self)
        
        self.Bind(wx.EVT_BUTTON, self.actionDoAdd, self.btOk)
        self.Bind(wx.EVT_BUTTON, self.actionClose, self.btCancel)
    #===========================================================================
    # when closing the window
    #===========================================================================
    def actionClose(self,event):
        self.Close()
    #===========================================================================
    # Click on Add document button
    #===========================================================================
    def actionDoAdd(self,event):
        if len(self.recordPart.lbFileName.GetPath()) == 0 :
            dlg = wx.FileDialog(self,style=wx.FD_OPEN,message=_('filename of the document to add'))
            
            if dlg.ShowModal():
                fname = os.path.join(dlg.Directory,dlg.Filename)
            if fname :
                self.recordPart.SetFields(filename=fname)
            else:
                self.Close()
                return
        if not self.recordPart.do_save_record():
            wx.MessageBox(_('Unable to add the file to the database'))
        else:
            # close the dialog
            self.Close()