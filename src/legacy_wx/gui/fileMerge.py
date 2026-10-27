'''
Created on 21 juin 2010. Copyright 2010, David GUEZ
@author: david guez (guezdav@gmail.com)
This file is a part of the source code of the MALODOS project.
You can use and distribute it freely, but have to conform to the license
attached to this project (LICENSE.txt file)
=====================================================================

GUI to be embedded into a frame, that contains a canvas and buttons
for navigating between the  images managed by the data singleton

'''
import data
import database
import wx
from algorithms.general import str_to_bool
import os
from . import RecordWidget
from . import utilities
import logging

class FileMerger(wx.Dialog):
    '''
    classdocs
    '''

    ID_UP=1
    ID_DOWN=2
    def __init__(self,parent,rowList):
        '''
        Constructor
        '''
        wx.Dialog.__init__(self,parent,style=wx.CLOSE_BOX | wx.SYSTEM_MENU | wx.CAPTION | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX)
        self.rowList = rowList
        self.docOrder = list(range(len(rowList)))
        self.panel = wx.Panel(self, -1)
        self.totSizer = wx.GridBagSizer(7,5)
        
        self.lstFiles = wx.ListBox(self.panel,style=wx.LB_ALWAYS_SB)
        self.btUp=wx.Button(self.panel,self.ID_UP,label=_('Move up'))
        self.btDown=wx.Button(self.panel,self.ID_DOWN,label=_('Move down'))
        
        self.rbSuppressOlds = wx.RadioBox(self.panel,label=_('What do you want to do with the previous documents'),choices=[_('Keep them on database'),_('Remove from database only'),_('Remove from the database and delete the file contents')])
        self.recordPart = RecordWidget.RecordWidget(self.panel,file_style=wx.FLP_SAVE | wx.FLP_OVERWRITE_PROMPT | wx.FLP_USE_TEXTCTRL)

        self.rbWhereToSave = wx.RadioBox(self.panel,label=_('Where do you want to save the merged content'),choices=[_('As a new file'),_('Instead one of the older files')])
        self.lbFileChoice = wx.ComboBox(self.panel,choices=[row[database.theBase.IDX_FILENAME] for row in self.rowList])
        self.lbFileChoice.Disable()
        
        self.btOk=wx.Button(self.panel,label=_('Ok'))
        self.btCancel=wx.Button(self.panel,label=_('Cancel'))
        
        self.totSizer.Add(wx.StaticText(self.panel,label=_('Define in which order the files will be merged into the new document')),pos=(0,0),span=(1,5),flag=wx.EXPAND)
        self.totSizer.Add(self.lstFiles,pos=(1,0),span=(1,5),flag=wx.EXPAND)
        self.totSizer.Add(self.btUp,pos=(2,0),span=(1,1),flag=wx.EXPAND)
        self.totSizer.Add(self.btDown,pos=(2,1),span=(1,1),flag=wx.EXPAND)
        
        self.totSizer.Add(self.rbSuppressOlds,pos=(3,0),span=(1,5),flag=wx.EXPAND)
        self.totSizer.Add(self.rbWhereToSave,pos=(4,0),span=(1,5),flag=wx.EXPAND)
        self.totSizer.Add(self.lbFileChoice,pos=(5,0),span=(1,5),flag=wx.EXPAND)
        self.totSizer.Add(self.recordPart,pos=(6,0),span=(1,5),flag=wx.EXPAND)
        
        self.totSizer.Add(self.btOk,pos=(7,0),span=(1,1),flag=wx.ALIGN_RIGHT)
        self.totSizer.Add(self.btCancel,pos=(7,1),span=(1,1),flag=wx.ALIGN_LEFT)

        self.totSizer.AddGrowableRow(1)
        self.totSizer.AddGrowableCol(2)

        self.panel.SetSizerAndFit(self.totSizer)
        self.totSizer.Fit(self)
        self.SetSize((800,650))
        
        list_tags = []
        for row in self.rowList :
            list_tags.append(row[database.theBase.IDX_TAGS])
            self.lstFiles.Append(row[database.theBase.IDX_TITLE])
        list_tags = ','.join(list_tags)
        list_tags.replace(',,', ',')
        list_tags = ','.join(set(list_tags.split(',')))
        list_tags = list_tags.strip(',')
        
        
        self.recordPart.SetFields(tags=list_tags)
        
        self.rbWhereToSave.Bind(wx.EVT_RADIOBOX,self.action_change_save_location )
        self.Bind(wx.EVT_COMBOBOX,self.action_change_save_location,self.lbFileChoice)
        self.Bind(wx.EVT_BUTTON,self.action_up_down,self.btUp)
        self.Bind(wx.EVT_BUTTON,self.action_up_down,self.btDown)
        self.Bind(wx.EVT_BUTTON,self.action_save,self.btOk)
        self.Bind(wx.EVT_BUTTON,lambda e : self.Destroy(),self.btCancel)
        self.Bind(wx.EVT_RADIOBOX,self.action_choice_suppress_old,self.rbSuppressOlds)
        
        self.rbSuppressOlds.Selection=0
        self.action_choice_suppress_old(None)


    def action_save(self,event):
        data.theData.clear_all()
        for idx in self.docOrder:
            row = self.rowList[idx]
            data.theData.load_file(row[database.theBase.IDX_FILENAME], None, False)
        data.theData.rescale_all()
        fname = self.recordPart.lbFileName.GetPath()
        if fname == '' :
            wx.MessageBox(_('You must give a valid filename to record the document'))
            return
        direct = os.path.dirname(fname)
        if not os.path.exists(direct) :
            if utilities.ask(_('The directory {dname} does not exists. Should it be created ?'.format(dname=direct))) :
                try:
                    os.makedirs(direct)
                except Exception as E:
                    logging.exception('Unable to create directory '+direct + ':' + str(E))
                    #raise Exception('Unable to add the file to the disk')
                    return
            else:
                #raise Exception('Unable to add the file to the disk')
                return
        try:
            #if not data.theData.save_file(fname,self.recordPart.lbTitle.Value,self.recordPart.lbDescription.Value,self.recordPart.lbTags.Value) : raise _('Unable to add the file to the disk')
            if not data.theData.save_file(fname,self.recordPart.lbTitle.Value,self.recordPart.lbDescription.Value,self.recordPart.lbTags.Value) :
                logging.exception('Unable to save '+fname + ':' + str(E))
                return
        except Exception as E:
            logging.debug('Saving file ' + str(E))
            wx.MessageBox(_('Unable to add the file to the disk'))
            return
        if not self.recordPart.do_save_record():
            wx.MessageBox(_('Unable to add the file to the database'))
            return
        # test if one should remove / delete old documents
        if self.rbSuppressOlds.Selection == 1 :
            # just remove from the database
            database.theBase.delete_documents(self.rowList,database.theBase.ID_DEL_DB)
        elif self.rbSuppressOlds.Selection == 2 :
            # remove from the database and delete the files
            database.theBase.delete_documents(self.rowList,database.theBase.ID_DEL_DB_AND_FS,exclusion=[fname])
        # close the dialog
        database.theConfig.set_param('scanner', 'lastDir',os.path.dirname(fname),True)
        database.theConfig.commit_config()
        self.Destroy()
    def fill_list(self):
        self.lstFiles.Clear()
        for idx in self.docOrder:
            row = self.rowList[idx]
            self.lstFiles.Append(row[database.theBase.IDX_TITLE])
    def action_choice_suppress_old(self,event):
        if self.rbSuppressOlds.GetSelection() == 0 :
            self.rbWhereToSave.SetSelection(0)
            self.rbWhereToSave.Disable()
        else:
            self.rbWhereToSave.Enable()
        self.action_change_save_location(None)
        
    def action_up_down(self,event):
        i = self.lstFiles.GetSelection()
        if i is None or i == wx.NOT_FOUND: return
        if event.GetId() == self.ID_UP:
            if i==0 : return
            t = self.docOrder[i-1]
            self.docOrder[i-1] = self.docOrder[i]
            self.docOrder[i] = t
            i=i-1
        elif event.GetId() == self.ID_DOWN:
            if i==len(self.docOrder)-1 : return
            t = self.docOrder[i+1]
            self.docOrder[i+1] = self.docOrder[i]
            self.docOrder[i] = t
            i=i+1
        self.fill_list()
        self.lstFiles.SetSelection(i)
            
    def action_change_save_location(self,event):
        if self.rbWhereToSave.GetSelection()==0:
            self.recordPart.lbFileName.Enable()
            self.lbFileChoice.Disable()
            self.recordPart.lbFileName.SetPath('')
        else:
            self.recordPart.lbFileName.Disable()
            i = self.lbFileChoice.GetSelection()
            if i is not None  and i != wx.NOT_FOUND:
                self.recordPart.lbFileName.SetPath(self.rowList[i][database.theBase.IDX_FILENAME])
            self.lbFileChoice.Enable()
        
    def defaultNameDir(self):
        defDir = database.theConfig.get_param('scanner', 'defaultDir',os.path.join(os.path.expanduser('~'),'MALODOS','Images'),False)
        if str_to_bool(database.theConfig.get_param('scanner', 'useLastDir','False',True)) : 
            defNameDir = database.theConfig.get_param('scanner', 'lastDir',defDir,False)
        else:
            defNameDir = defDir
        return defNameDir
