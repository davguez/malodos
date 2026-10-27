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
import database
from . import utilities
import os.path
class DocToGoWizard (wx_wizard.Wizard):
    selectBasket=False
    def __init__(self,parent,doc_list,row_list,selectBasket=False):
        wx_wizard.Wizard.__init__(self,parent,-1,_('Document to go wizard'))
        self.selectBasket=selectBasket
        self.page_chooser = PageActionChooser(self)
        self.page_database_export = PageActionDatabaseExport(self)
        self.page_archive_export = PageActionArchiveCreation(self)
        self.page_archive_import = PageActionArchiveOpening(self)
        self.row_list=row_list
        self.doc_list=doc_list
        self.Bind(wx_wizard.EVT_WIZARD_FINISHED, self.on_finished)
        self.Bind(wx_wizard.EVT_WIZARD_CANCEL, self.on_cancel)
        self.GetPageAreaSizer().Add(self.page_chooser)
    def on_cancel(self,event):
        if not utilities.ask(_('Are you sure you want to cancel the document to go wizard ?')) : event.Veto()
    def on_finished(self,event):
        sel = self.page_chooser.rbContent.GetSelection()
        sel = list(self.page_chooser.choice_list.keys())[sel]
        what = self.page_chooser.rbDocToSave.GetSelection()
        what =  list(self.page_chooser.sel_list.keys())[what]
        if what==self.page_chooser.ALL_DOCUMENTS:
            cur = database.theBase.find_sql()
            if cur is None :
                rowL=[]
            else:
                rowL = [row for row in cur] 
        elif what == self.page_chooser.SELECTED_DOCS:
            rowL = self.row_list
        elif what == self.page_chooser.FILTER_RESULT:
            rowL = self.doc_list
        elif what == self.page_chooser.BASKET_DOCS:
            rowL = self.GetParent().basket
        if sel == self.page_chooser.EXPORT_DATABASE:
            filename = self.page_database_export.fcFileChooser.GetPath()
            if os.path.splitext(filename)[1]=='':
                filename=filename+'.zip'
            if filename=='' : 
                utilities.show_message(_("The filename can't be empty"))
                event.Veto()
            elif os.path.exists(filename):
                if utilities.ask(_('The filename already exists. Overwrite it ?')):
                    os.remove(filename)
                    database.theBase.export_database(filename, rowL)
                else:
                    event.Veto()
            else:
                database.theBase.export_database(filename, rowL)
        elif sel==self.page_chooser.EXPORT_ARCHIVE:
            filename = self.page_archive_export.fcFileChooser.GetPath()
            if os.path.splitext(filename)[1]=='':
                filename=filename+'.zip'
            if filename=='' : 
                utilities.show_message(_("The filename can't be empty"))
                event.Veto()
            elif os.path.exists(filename):
                if utilities.ask(_('The filename already exists. Overwrite it ?')):
                    os.remove(filename)
                    database.theBase.export_archive(filename, rowL)
                else:
                    event.Veto()
            else:
                database.theBase.export_archive(filename, rowL)
        elif sel==self.page_chooser.IMPORT_ARCHIVE :
            filename = self.page_archive_import.fcFileChooser.GetPath()
            dirname = self.page_archive_import.dcDirChooser.GetPath()
            if filename=='' or dirname=='': 
                utilities.show_message(_("The filename and dirname can't be empty"))
                event.Veto()
            else:
                database.theBase.import_archive(filename, dirname)
                dbname=os.path.join(dirname,'database.db')
                database.theConfig.set_database_name(dbname)
                database.theBase.use_base(dbname)
                database.theConfig.commit_config()

class PageActionChooser (wx_wizard.PyWizardPage):
    EXPORT_DATABASE=1
    EXPORT_ARCHIVE=2
    IMPORT_ARCHIVE=3
    
    ALL_DOCUMENTS=1
    FILTER_RESULT=2
    SELECTED_DOCS=3
    BASKET_DOCS=4
    def __init__(self,parent):
        wx_wizard.PyWizardPage.__init__(self,parent)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.choice_list = { self.EXPORT_DATABASE:_('Export all of part of the database.') ,
                             self.EXPORT_ARCHIVE :_('Create an archive with some or all of your documents, along with a database to browse into.'),
                             self.IMPORT_ARCHIVE :_('Open an existing archive.')   }
        self.rbContent =  wx.RadioBox(self,label=_('What action do you want to take'),choices=list(self.choice_list.values()),style=wx.RA_VERTICAL)
        self.sel_list = { self.ALL_DOCUMENTS:_('Export all the documents') ,
                             self.FILTER_RESULT :_('Export only the result of the current search.'),
                             self.SELECTED_DOCS :_('Export only the result of the current selection.'),
                             self.BASKET_DOCS :_('Export all the documents in the basket')    }
        self.rbDocToSave =  wx.RadioBox(self,label=_('Which documents would you like to save'),choices=list(self.sel_list.values()),style=wx.RA_VERTICAL)
        if self.Parent.selectBasket :
            self.rbDocToSave.SetSelection(3)
        self.sizer.Add(self.rbContent,0,flag=wx.EXPAND)
        self.sizer.Add(self.rbDocToSave,0,flag=wx.EXPAND)
        self.SetSizer(self.sizer)
        self.Bind(wx.EVT_RADIOBOX, self.on_choose_content , self.rbContent)
    def on_choose_content(self,event):
        sel = self.rbContent.GetSelection()
        sel = list(self.choice_list.keys())[sel]
        if sel == self.EXPORT_DATABASE or sel==self.EXPORT_ARCHIVE:
            self.rbDocToSave.Show()
        else:
            self.rbDocToSave.Hide()
        
    def GetNext(self):
        sel = self.rbContent.GetSelection()
        sel = list(self.choice_list.keys())[sel]
        if sel == self.EXPORT_DATABASE:
            return self.Parent.page_database_export
        elif sel==self.EXPORT_ARCHIVE:
            return self.Parent.page_archive_export
        elif sel==self.IMPORT_ARCHIVE :
            return self.Parent.page_archive_import
    def GetPrev(self):
        return None


class PageActionDatabaseExport (wx_wizard.PyWizardPage):
    def __init__(self,parent):
        wx_wizard.PyWizardPage.__init__(self,parent)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        s = _('Path of exported database')
        self.sizer.Add(wx.StaticText(self,label=s))
        self.fcFileChooser =  wx.FilePickerCtrl(self,message=s,wildcard='*.db',style=wx.FLP_SAVE|wx.FLP_OVERWRITE_PROMPT|wx.FLP_USE_TEXTCTRL)
        self.sizer.Add(self.fcFileChooser,0,flag=wx.EXPAND|wx.CENTER|wx.ALIGN_CENTER_VERTICAL)
        self.SetSizer(self.sizer)
    def GetNext(self):
        return None
    def GetPrev(self):
        return self.Parent.page_chooser

class PageActionArchiveCreation (wx_wizard.PyWizardPage):
    def __init__(self,parent):
        wx_wizard.PyWizardPage.__init__(self,parent)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        s = _('Path of exported archive')
        self.sizer.Add(wx.StaticText(self,label=s))
        self.fcFileChooser =  wx.FilePickerCtrl(self,message=s,wildcard='*.zip',style=wx.FLP_SAVE|wx.FLP_OVERWRITE_PROMPT|wx.FLP_USE_TEXTCTRL)
        self.sizer.Add(self.fcFileChooser,0,flag=wx.EXPAND|wx.CENTER|wx.ALIGN_CENTER_VERTICAL)
        self.SetSizer(self.sizer)
    def GetNext(self):
        return None
    def GetPrev(self):
        return self.Parent.page_chooser
class PageActionArchiveOpening (wx_wizard.PyWizardPage):
    def __init__(self,parent):
        wx_wizard.PyWizardPage.__init__(self,parent)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        s = _('Path of archive to import')
        self.sizer.Add(wx.StaticText(self,label=s))
        self.fcFileChooser =  wx.FilePickerCtrl(self,message=s,wildcard='*.zip',style=wx.FLP_OPEN|wx.FLP_FILE_MUST_EXIST|wx.FLP_USE_TEXTCTRL)
        self.sizer.Add(self.fcFileChooser,0,flag=wx.EXPAND|wx.CENTER|wx.ALIGN_CENTER_VERTICAL)
        s = _('Path of directory into which the archive will be extracted')
        self.sizer.Add(wx.StaticText(self,label=s))
        self.dcDirChooser =  wx.DirPickerCtrl(self,message=s,style=wx.DIRP_DIR_MUST_EXIST|wx.DIRP_USE_TEXTCTRL)
        self.sizer.Add(self.dcDirChooser,0,flag=wx.EXPAND|wx.CENTER|wx.ALIGN_CENTER_VERTICAL)
        self.SetSizer(self.sizer)
    def GetNext(self):
        return None
    def GetPrev(self):
        return self.Parent.page_chooser