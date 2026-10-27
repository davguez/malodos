'''
Created on 21 juin 2010. Copyright 2010, David GUEZ
@author: david guez (guezdav@gmail.com)
This file is a part of the source code of the MALODOS project.
You can use and distribute it freely, but have to conform to the license
attached to this project (LICENSE.txt file)
=====================================================================
class related to the document to go wizard
'''

import wx
try:
    import wx.adv as wx_wizard
except ImportError:
    import wx.wizard as wx_wizard
from . import dbGui
from . import utilities
import os
import database
from . import virtualFolder
if os.name == 'posix' :
    from scannerAccess import saneAccess
else:
    from scannerAccess import twainAccess
from algorithms.words import get_available_languages
from algorithms.general import str_to_bool
import gui.utilities

class StartupWizard(wx_wizard.Wizard):
    '''
    wizard helping user to configure the preferences
    '''


    def __init__(self,parent,params=None):
        '''
        Constructor
        '''
        wx_wizard.Wizard.__init__(self,parent,-1,_('Startup wizard'))
        
        dlg=utilities.ProgressDialog(_('Getting scanner list'),_('The list of acquisition device is being retrieved. Please wait a moment.'))
        dlg.set_current_step_to(0.5)
        wx.GetApp().ProcessPendingEvents()
        self.pageDatabase = PageDatabaseChoice(self)
        self.pageScanner  = PageScannerChoice(self)
        self.pageOCR      = PageOCRChoice(self)
        self.pageSurvey   = PageSurveyChoice(self)
        #self.pageFolders  = PageFoldersChoice(self)
        self.Bind(wx_wizard.EVT_WIZARD_FINISHED, self.on_finished)
        self.Bind(wx_wizard.EVT_WIZARD_CANCEL, self.on_cancel)
        self.GetPageAreaSizer().Add(self.pageDatabase)
        self.params=params
        dlg.destroy()
    def on_cancel(self,event):
        if not utilities.ask(_('Are you sure you want to cancel the startup wizard ?')) : event.Veto()
    def on_finished(self,event):
        if not self.pageDatabase.actionSave() : return
        self.pageScanner.actionSave()
        self.pageOCR.actionSave()
        self.pageSurvey.actionSave()
        #self.pageFolders.actionSave()
        database.theConfig.commit_config()
 
class PageDatabaseChoice (wx_wizard.PyWizardPage):
    def __init__(self,parent):
        wx_wizard.PyWizardPage.__init__(self,parent)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        s=_('Please choose a name for your database.\n Check the box if you want to define an encryption password for the database.')
        self.dbFrame = dbGui.CreatorFrame(self)
        self.cbEncryptData=wx.CheckBox(self,-1,_('Encrypt the scanned files'))
        self.cbSamePasswd = wx.CheckBox(self,-1,_('Use the same password for the scanned files and for the database'))
        self.lbPasswd = wx.TextCtrl(self,style=wx.TE_PASSWORD)
        self.lbPasswdConfirm = wx.TextCtrl(self,style=wx.TE_PASSWORD)
        self.sizer.Add(wx.StaticText(self,-1,s),wx.EXPAND)
        self.sizer.Add(self.dbFrame,0,flag=wx.EXPAND)
        self.sizer.Add(self.cbEncryptData,0,flag=wx.EXPAND)
        self.sizer.Add(self.cbSamePasswd,0,flag=wx.EXPAND)
        self.sizer.Add(self.lbPasswd,0,flag=wx.EXPAND)
        self.sizer.Add(self.lbPasswdConfirm,0,flag=wx.EXPAND)
        self.SetSizer(self.sizer)
        
        self.Bind(wx.EVT_CHECKBOX,self.adaptEncryptShow,self.cbEncryptData)
        self.Bind(wx.EVT_CHECKBOX,self.adaptEncryptShow,self.cbSamePasswd)
        self.dbFrame.Bind(wx.EVT_CHECKBOX,self.adaptEncryptShow,self.dbFrame.cbEncrypted)
        self.adaptEncryptShow(None)
    def adaptEncryptShow(self,event):
        self.cbSamePasswd.Enable(self.cbEncryptData.Value and self.dbFrame.cbEncrypted.Value)
        showingPassFields = self.cbEncryptData.Value and (not self.dbFrame.cbEncrypted.Value or (self.dbFrame.cbEncrypted.Value and not self.cbSamePasswd.Value))
        self.lbPasswd.Enable(showingPassFields)
        self.lbPasswdConfirm.Enable(showingPassFields)
        self.dbFrame.lbPasswd.Enable(self.dbFrame.cbEncrypted.Value)
        self.dbFrame.lbPasswdConfirm.Enable(self.dbFrame.cbEncrypted.Value)
    def GetNext(self):
        #if not self.dbFrame.Validate() :
        #    return self
        return self.Parent.pageScanner
    def GetPrev(self):
        return None
    def actionSave(self):
        self.dbFrame.Validate()
        database.theBase.create_and_use(self.dbFrame.filename,self.dbFrame.password)
        if not database.theBase.buildDB() :
            utilities.show_message(_('Unable to build the database'))
            return False
        database.theConfig.set_database_name(self.dbFrame.filename)
        database.theConfig.set_param('encryption', 'encryptData', str(self.cbEncryptData.Value), True)
        database.theConfig.set_param('encryption', 'encryptDatabase', str(self.dbFrame.cbEncrypted.Value), True)
        if self.cbEncryptData.Value:
            if self.cbSamePasswd.Value :
                data_psw =self.dbFrame.password
            else:
                if self.lbPasswd.Value != self.lbPasswdConfirm.Value:
                    gui.utilities.show_message(_('The two data password confirmation mismatches, please check them.'))
                    return False
                data_psw =self.lbPasswd
             
            database.record_current_password(data_psw)
        return True

class PageScannerChoice (wx_wizard.PyWizardPage):
    def __init__(self,parent):
        wx_wizard.PyWizardPage.__init__(self,parent)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        
        if os.name == 'posix' :
            self.scanner = saneAccess.SaneAccess(self.GetHandle())
        else:
            self.scanner = twainAccess.TwainAccess(self.GetHandle())
        names = self.scanner.listSources()
        names=[D[2] for D in names]
        self.lstScanners = wx.ListBox(self,choices=names)
        self.sizer.Add(wx.StaticText(self,-1,_('Choose the scanner to use')),0,flag=wx.EXPAND)
        self.sizer.Add(self.lstScanners,0,flag=wx.EXPAND)
        self.sizer.Add(wx.StaticText(self,-1,_('Go to preference screen in order to setup specific scanner options.')),0,flag=wx.EXPAND)
        
        self.SetSizer(self.sizer)
        
    def GetNext(self):
        return self.Parent.pageOCR
    def GetPrev(self):
        return self.Parent.pageDatabase
    def actionSave(self):
        s=self.lstScanners.GetStringSelection()
        if s!='' : database.theConfig.set_current_scanner(s)

class PageOCRChoice (wx_wizard.PyWizardPage):
    def __init__(self,parent):
        wx_wizard.PyWizardPage.__init__(self,parent)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer = wx.GridBagSizer(1,1)
        self.cbAutoOCR = wx.CheckBox(self,-1,_('Automatically proceed to OCR when a new document is added to the database'))
        self.clOcrProgs = wx.CheckListBox(self,-1,style=wx.LB_EXTENDED)
        self.clSpellProgs = wx.CheckListBox(self,-1,style=wx.LB_EXTENDED)
        
        ocrConf = database.theConfig.get_ocr_configuration()
        self.clOcrProgs.AppendItems(ocrConf.get_available_ocr_programs())
        self.clSpellProgs.AppendItems(get_available_languages())

        self.sizer.Add(self.cbAutoOCR,(0,0),span=(1,6),flag=wx.ALL|wx.EXPAND)
        self.sizer.Add(wx.StaticText(self,-1,_("OCR programs to use")),(1,0),span=(1,3),flag=wx.ALL|wx.EXPAND)
        self.sizer.Add(wx.StaticText(self,-1,_("OCR Checking languages")),(1,3),span=(1,3),flag=wx.ALL|wx.EXPAND)
        self.sizer.Add(self.clOcrProgs,(2,0),span=(1,3),flag=wx.ALL|wx.EXPAND)
        self.sizer.Add(self.clSpellProgs,(2,3),span=(1,3),flag=wx.ALL|wx.EXPAND)

        self.sizer.AddGrowableCol(0)
        self.sizer.AddGrowableCol(5)
        self.sizer.AddGrowableRow(2)
        
        self.actionLoad()
        
        self.SetSizer(self.sizer)
        
    def actionLoad(self):
        for i in range(self.clOcrProgs.Count) :
            opt = 'use' + self.clOcrProgs.GetItems()[i]
            chk = database.theConfig.get_param('OCR', opt,'0').lower()
            chk = str_to_bool(chk)
            self.clOcrProgs.Check(i,chk)
        lngs = database.theConfig.get_param('OCR', 'languages','').split(',')
        for i in range(self.clSpellProgs.Count):
            l = self.clSpellProgs.GetString(i)
            try:
                lngs.index(l)
                self.clSpellProgs.Check(i)
            except:
                self.clSpellProgs.Check(i,False)
        self.cbAutoOCR.Value = str_to_bool( database.theConfig.get_param('OCR', 'autoStart','1') )
    def GetNext(self):
        return self.Parent.pageSurvey
    def GetPrev(self):
        return self.Parent.pageScanner
    def actionSave(self):
        for i in range(self.clOcrProgs.Count) :
            opt = 'use' + self.clOcrProgs.GetItems()[i]
            chk = self.clOcrProgs.IsChecked(i)
            database.theConfig.set_param('OCR', opt, str(chk),True)
        database.theConfig.set_param('OCR', 'languages', ','.join(self.clSpellProgs.GetCheckedStrings()),True)
        database.theConfig.set_param('OCR', 'autoStart', str(self.cbAutoOCR.Value),True)
        

class PageSurveyChoice (wx_wizard.PyWizardPage):
    def __init__(self,parent):
        wx_wizard.PyWizardPage.__init__(self,parent)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)
        self.dirSurveySizer = wx.GridBagSizer(1,1)
        self.lstSurveyDirs = wx.CheckListBox(self,-1,style=wx.LB_EXTENDED)
        self.txtSurveyExt = wx.TextCtrl(self,-1)
        self.btAddDir = wx.Button(self,-1,_("Add"))
        self.btRemDir = wx.Button(self,-1,_("Remove"))

        self.dirSurveySizer.Add(wx.StaticText(self,-1,_("Survey directories")) , (0,0),flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL )
        self.dirSurveySizer.Add(self.btAddDir,(0,1),flag=wx.ALL)
        self.dirSurveySizer.Add(self.btRemDir,(0,2),flag=wx.ALL)
        self.dirSurveySizer.Add(wx.StaticText(self,-1,_("(check directories which have to be recursively surveyed)")) , (1,0),span=(1,3),flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL )
        self.dirSurveySizer.Add(self.lstSurveyDirs,(2,0),span=(1,4),flag=wx.ALL | wx.EXPAND)
        self.dirSurveySizer.Add(wx.StaticText(self,-1,_("Survey extensions") ),(3,0),flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL)
        self.dirSurveySizer.Add(self.txtSurveyExt,(3,1),span=(1,3),flag=wx.EXPAND|wx.ALL)

        self.dirSurveySizer.AddGrowableCol(3)
        self.dirSurveySizer.AddGrowableRow(2)
        
        
        (item_list,checked) = database.theConfig.get_survey_directory_list()
        self.lstSurveyDirs.SetItems(item_list)
        self.lstSurveyDirs.SetChecked(checked)
        S = database.theConfig.get_survey_extension_list()
        self.txtSurveyExt.SetValue(S)
        self.SetSizerAndFit(self.dirSurveySizer)
        # BINDING
        self.Bind(wx.EVT_BUTTON, self.actionAddDir, self.btAddDir)
        self.Bind(wx.EVT_BUTTON, self.actionRemDir, self.btRemDir)
    def actionAddDir(self,event):
        dir_name = wx.DirSelector()
        if len(dir_name)>0 :  self.lstSurveyDirs.Append(dir_name)
    def actionRemDir(self,event):
        elems = list(self.lstSurveyDirs.GetSelections())
        elems.sort(reverse=True)
        for e in elems : self.lstSurveyDirs.Delete(e)
    def actionSave(self):
        dir_list = self.lstSurveyDirs.GetItems()
        recursiveIndex = self.lstSurveyDirs.GetChecked()
        database.theConfig.set_survey_directory_list(dir_list, recursiveIndex)
        database.theConfig.set_survey_extension_list(self.txtSurveyExt.GetValue())
        
    def GetNext(self):
        return None# self.Parent.pageFolders
    def GetPrev(self):
        return self.Parent.pageOCR

class PageFoldersChoice (wx_wizard.PyWizardPage):
    def __init__(self,parent):
        wx_wizard.PyWizardPage.__init__(self,parent)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.vFold = virtualFolder.FolderView(self,False,True)
        self.sizer.Add(self.vFold,1,flag=wx.ALL|wx.EXPAND)
        

        self.SetSizer(self.sizer)
        
    def GetNext(self):
        return None
    def GetPrev(self):
        return self.Parent.pageSurvey