'''
Created on 15 aout 2010. Copyright 2010, David GUEZ
@author: david guez (guezdav@gmail.com)
This file is a part of the source code of the MALODOS project.
You can use and distribute it freely, but have to conform to the license
attached to this project (LICENSE.txt file)
=====================================================================
GUI dialog to define general user preferences

'''
import wx
import gui.utilities
class CreatorFrame(wx.Panel):
    '''
    classdocs
    '''


    def __init__(self,parent,iid=-1):
        '''
        Constructor
        '''
        wx.Panel.__init__(self,parent,iid)
        self.filename = None
        self.password = None

        self.fcFile = wx.FilePickerCtrl(self,wildcard='*.db',style=wx.FLP_OVERWRITE_PROMPT|wx.FLP_SAVE|wx.FLP_USE_TEXTCTRL)
        self.cbEncrypted = wx.CheckBox(self,label=_('Encrypted database'))
        self.lbPasswd = wx.TextCtrl(self,style=wx.TE_PASSWORD)
        self.lbPasswdConfirm = wx.TextCtrl(self,style=wx.TE_PASSWORD)
        
        self.totalWin = wx.BoxSizer(wx.VERTICAL)
        self.pssSizer = wx.FlexGridSizer(2,2)
        
        self.totalWin.Add(self.fcFile,0,wx.EXPAND)
        self.totalWin.Add(self.cbEncrypted,0,wx.EXPAND)
        self.pssSizer.Add(wx.StaticText(self,label=_('Password')),0,wx.EXPAND)
        self.pssSizer.Add(self.lbPasswd,0,wx.EXPAND)
        self.pssSizer.Add(wx.StaticText(self,label=_('Confirmation')),0,wx.EXPAND)
        self.pssSizer.Add(self.lbPasswdConfirm,0,wx.EXPAND)
        self.pssSizer.AddGrowableCol(1)
        self.totalWin.Add(self.pssSizer,0,wx.EXPAND)
        
        self.SetSizerAndFit(self.totalWin)
        
        self.Bind(wx.EVT_CHECKBOX,self.changeShow,self.cbEncrypted)
        self.Bind(wx.EVT_FILEPICKER_CHANGED,self.checkFileName,self.fcFile)
        
        self.changeShow(None)
    def changeShow(self,event):
        for i in self.pssSizer.GetChildren(): i.GetWindow().Enable(self.cbEncrypted.Value)
    def checkFileName(self,event):
        s = self.fcFile.GetPath()
        if not s.endswith('.db'):
            s=s+'.db'
            self.fcFile.SetPath(s)
    def Validate(self):
        if self.cbEncrypted.Value and self.lbPasswd.Value != self.lbPasswdConfirm.Value:
            gui.utilities.show_message(_('The two password confirmation is invalid, please check it.'))
            return False
        if self.fcFile.GetPath()=='':
            gui.utilities.show_message(_('The filename cannot be empty.'))
            return False
        if self.cbEncrypted.Value:
            self.password=self.lbPasswd.Value
        else:
            self.password=None
        self.filename=self.fcFile.GetPath()
        return True
class CreatorDialog(wx.Dialog):
    def __init__(self,parent,iid=-1):
        wx.Dialog.__init__(self,parent,iid,title=_('Defining a new database'))
        self.filename = None
        self.password = None
        self.panel = wx.Panel(self)
        self.sizer = wx.GridBagSizer()
        self.creatorFrame = CreatorFrame(self.panel)
        self.btOk= wx.Button(self.panel,label=_('ok'))
        self.btCancel= wx.Button(self.panel,label=_('cancel'))
        self.sizer.Add(self.creatorFrame,(0,0),span=(1,3),flag=wx.EXPAND|wx.GROW)
        self.sizer.Add(self.btOk,(1,0),flag=wx.EXPAND)
        self.sizer.Add(self.btCancel,(1,1),flag=wx.EXPAND)
        self.sizer.AddGrowableCol(2)
        self.panel.SetSizerAndFit(self.sizer)
        self.SetSize(self.sizer.GetMinSize())
        self.Bind(wx.EVT_BUTTON,self.Validate,self.btOk)
        self.Bind(wx.EVT_BUTTON,lambda x:self.Close(),self.btCancel)
    def Validate(self,event):
        if not self.creatorFrame.Validate(): return
        self.filename = self.creatorFrame.filename
        self.password = self.creatorFrame.password
        self.Close()
        return
