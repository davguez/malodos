'''
Created on 21 juin 2010. Copyright 2010, David GUEZ
@author: david guez (guezdav@gmail.com)
This file is a part of the source code of the MALODOS project.
You can use and distribute it freely, but have to conform to the license
attached to this project (LICENSE.txt file)
=====================================================================
GUI part to show/modify a record data
'''
import wx
import ast
try:
    import wx.adv as wx_adv
except ImportError:
    wx_adv = wx
from  .TextCtrlAutoComplete import TextCtrlAutoComplete
import database
import datetime
from data import theData
import data.imageData
from  algorithms.general import str_to_bool
import os.path
import gui.utilities
import gui.virtualFolder
import logging
import algorithms.stringFunctions
#try:
#    import gfx
#except:
#    pass

#import pyPdf


class RecordWidget(wx.Window):
    @staticmethod
    def _normalize_filename(value):
        if value is None:
            return None
        if isinstance(value, bytes):
            return value.decode('utf-8', 'replace')
        if isinstance(value, str) and value.startswith(("b'", 'b\"')):
            try:
                parsed = ast.literal_eval(value)
                if isinstance(parsed, bytes):
                    return parsed.decode('utf-8', 'replace')
            except Exception:
                pass
        return value

    def __init__(self,parent,filename='',file_style = wx.FLP_OPEN | wx.FLP_FILE_MUST_EXIST | wx.FLP_USE_TEXTCTRL):
        '''
        Constructor
        '''
        self.row=None
        wx.Window.__init__(self, parent)
        self.panel = wx.Panel(self, -1)
        
        self.totSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.txtFieldSizer = wx.FlexGridSizer(cols=2,vgap=2,hgap=2)
        self.txtFieldSizer.SetFlexibleDirection(wx.HORIZONTAL)
        self.txtFieldSizer.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)
        self.txtFieldSizer.AddGrowableCol(1)
        
        self.txtFileName = wx.StaticText(self.panel , -1 , _('Filename'))
        self.lbFileName = wx.FilePickerCtrl(self.panel,-1,path=filename,style=file_style)
        self.txtFieldSizer.Add(self.txtFileName,0)
        self.txtFieldSizer.Add(self.lbFileName,1,wx.EXPAND)
        
        self.txtTitle = wx.StaticText(self.panel , -1 , _('Title'))
        #self.lbTitle = wx.TextCtrl(self.panel , -1 , '')
        self.lbTitle = TextCtrlAutoComplete(self.panel , choices=(' '),
                                           entryCallback=self.action_autoCompleteTitle,
                                           showHead=True)
        self.txtFieldSizer.Add(self.txtTitle,0)
        self.txtFieldSizer.Add(self.lbTitle,1,wx.EXPAND)
        
        self.txtDescription = wx.StaticText(self.panel , -1 , _('Description'))
        self.lbDescription = wx.TextCtrl(self.panel , -1 , '')
        self.txtFieldSizer.Add(self.txtDescription,0)
        self.txtFieldSizer.Add(self.lbDescription,1,wx.EXPAND)

        self.txtTags = wx.StaticText(self.panel , -1 , _('Tags'))
        #self.lbTags = wx.TextCtrl(self.panel , -1 , '' , style=wx.TE_HT_ON_TEXT)
        self.lbTags = TextCtrlAutoComplete(self.panel , choices=(' '),
                                           entryCallback=self.action_autoCompleteTags,
                                           getWorkingString=self.defineWorkingString,
                                           applyItem=self.changeWorkingString,
                                           showHead=True)
        self.txtFieldSizer.Add(self.txtTags,0)
        self.txtFieldSizer.Add(self.lbTags,1,wx.EXPAND)
        
        self.txtDate = wx.StaticText(self.panel , -1 , _('document date'))
        self.lbDate = wx_adv.DatePickerCtrl(self.panel , -1,style=wx_adv.DP_DROPDOWN)
        self.txtFieldSizer.Add(self.txtDate,0)
        self.txtFieldSizer.Add(self.lbDate,1)
              
#        self.txtOCR = wx.StaticText(self.panel , -1 , _('do OCR'))
        self.cbOCR = wx.CheckBox(self.panel , -1,label=_('rescan for OCR'))
        self.btEncryptDecrypt = wx.Button(self.panel,-1,_('Add password'))
#        self.txtFieldSizer.Add(self.txtOCR,0)
        self.txtFieldSizer.Add(self.cbOCR,1)
        self.txtFieldSizer.Add(self.btEncryptDecrypt,0)
        
        self.totSizer.Add(self.txtFieldSizer,proportion=2,flag=wx.EXPAND)
        
        self.virtFolderSizer = wx.GridBagSizer(5)
        self.vFold = gui.virtualFolder.FolderView(self.panel,True,False,[],self.updateSelection)
        self.lbFolders = wx.ListBox(self.panel,-1)
        self.virtFolderSizer.Add(wx.StaticText(self.panel,-1,_('Folder selection')),(0,0),flag=wx.EXPAND)
        self.virtFolderSizer.Add(self.vFold,(1,0),flag=wx.EXPAND)
        self.virtFolderSizer.Add(self.lbFolders,(2,0),flag=wx.EXPAND)
        self.virtFolderSizer.AddGrowableRow(1)
        self.virtFolderSizer.AddGrowableCol(0)
        self.totSizer.Add(self.virtFolderSizer,proportion=1,flag=wx.EXPAND)
        
        self.panel.SetSizerAndFit(self.totSizer)
        self.Bind(wx.EVT_SIZE,self.onResize)
        self.lbTitle.Bind(wx.EVT_TEXT,self.notifyModification)
        self.lbDescription.Bind(wx.EVT_TEXT,self.notifyModification)
        self.lbDate.Bind(wx_adv.EVT_DATE_CHANGED,self.notifyModification)
        self.lbFileName.Bind(wx.EVT_FILEPICKER_CHANGED,self.notifyModification)
        self.lbFolders.Bind(wx.EVT_LIST_DELETE_ITEM,self.notifyModification)
        self.lbFolders.Bind(wx.EVT_LIST_INSERT_ITEM,self.notifyModification)
        #self.Bind(wx.EVT_FILEPICKER_CHANGED,self.checkFileName,self.lbFileName)
        #self.lbFileName.Bind(wx.EVT_FILEPICKER_CHANGED, self.checkFileName)
        self.modificationCallback=None
    
    def setModificationCallback(self,callback_function=None):
        self.modificationCallback=callback_function
    def notifyModification(self,event=None):
        if self.modificationCallback is not None : self.modificationCallback()
    def updateSelection(self,selection):
        self.notifyModification()
        self.lbFolders.Clear()
        for folderID in selection:
            genealogy = database.theBase.folders_genealogy_of(folderID)
            S = '/'.join(genealogy)
            self.lbFolders.Append(S)
            
    def checkFileName(self,event):
        filename = self.lbFileName.GetPath()
        if len(filename) == 0:
            return
        (name,ext)=os.path.splitext(filename)
        if ext.lower()=='':
            filename = name  + '.pdf'
            self.lbFileName.SetPath(filename)

    def getCurrentPart(self,pos,text): 
        pos1 = text.rfind(',',0,pos+1)
        pos2 = text.find(',',pos+1)
        return [pos1,pos2]
    def defineWorkingString(self): 
        text = self.lbTags.Value
        if len(text)==0 or text.isspace() : return ''
        pos = self.lbTags.GetInsertionPoint()
        if pos>=len(text) : return ''
        if text[pos]==',' : return ''
        [pos1,_] = self.getCurrentPart(pos,text)
        if pos1<0 or pos1>=len(text)-1: pos1=0
        if text[pos1]==',' and pos1+1 < len(text) : pos1=pos1+1
        return text[pos1:pos]
    def changeWorkingString(self,newText):
        text = self.lbTags.Value
        if len(text)==0 or text.isspace() :
            self.lbTags.SetValue(newText)
            self.lbTags.SetInsertionPointEnd()
            return
        pos = self.lbTags.GetInsertionPoint()
        [pos1,pos2] = self.getCurrentPart(pos,text)
        if pos1==pos2 :
            self.lbTags.SetValue(newText)
            self.lbTags.SetInsertionPointEnd()
            return
        if pos1<0 or pos1>=len(text)-1: pos1=0
        if text[pos1]==',' :
            P1 = text[:(pos1+1)]
        else:
            P1 = ''
        if pos2<0:
            P2=',' + text[pos:]
        elif text[pos2]==',' :
            P2 = text[pos2:]
        else:
            P2 = ''
        text = P1 + newText + P2
        self.lbTags.SetValue(text)
        newPos = len(P1)+len(newText)
        if len(P2)>0 : newPos=newPos+1
        self.lbTags.SetInsertionPoint(newPos)
    def action_autoCompleteTags(self):
        self.notifyModification()
        s = self.defineWorkingString().lower()
        possibilities = database.theBase.find_keywords_by_prefix(s, database.theBase.ID_TAG)
        if possibilities and len(possibilities)>0 :
            self.lbTags.SetChoices(possibilities)
        else:
            self.lbTags.SetChoices([])
    def action_autoCompleteTitle(self):
        self.notifyModification()
        s = self.lbTitle.Value.lower()
        possibilities = database.theBase.find_field_by_prefix(s, 'title')
        if possibilities and len(possibilities)>0:
            self.lbTitle.SetChoices(possibilities)
        else:
            self.lbTitle.SetChoices([])
    def clear_all(self):
        self.notifyModification()
        self.lbFileName.SetPath('')
        self.lbTitle.SetValue('')
        self.lbDescription.SetValue('')
        self.lbTags.SetValue('')
        self.vFold.setSelectedList(set())
    def setRow(self,row):
        self.row=[r for r in row if r is not None] 
    def getRow(self):
        return self.row
    def SetFields(self,filename=None,title=None,description=None,date=None,tags=None,doOCR=None,selectedList=None):
        self.notifyModification()
        filename = self._normalize_filename(filename)
        if not filename is None: self.lbFileName.SetPath(filename)
        if not title is None : self.lbTitle.SetValue(title)
        if not description is None : self.lbDescription.SetValue(description)
        if not tags is None : self.lbTags.SetValue(tags)
        if not date is None :
            try:
                dt = wx.DateTime.Today()
                dt.SetDay(date.day)
                dt.SetMonth(date.month-1)
                dt.SetYear(date.year)
                self.lbDate.SetValue(dt)
            except Exception as E:
                logging.exception('Unable to set the date to the date' + str(date) + '->'+str(E))
        if not doOCR is None : self.cbOCR.SetValue(doOCR)
        if not selectedList is None :
            self.vFold.setSelectedList(selectedList)
            self.updateSelection(selectedList)
        if filename and os.path.exists(filename) and algorithms.stringFunctions.is_encrypted(filename) :
            self.btEncryptDecrypt.SetLabel(_('Remove password'))
        else:
            self.btEncryptDecrypt.SetLabel(_('Add password'))
    def onResize(self,event):
        self.panel.Size = self.Size
    def do_save_record(self):
        self.checkFileName(None)
        filename = self.lbFileName.GetPath()
        if not os.path.exists(filename):
            gui.utilities.show_message(_('A valid filename is required'))
            return False
        title = self.lbTitle.Value
        tags = self.lbTags.Value
        description = self.lbDescription.Value
        documentDate = self.lbDate.Value
        documentDate=datetime.date(year=documentDate.GetYear(),month=documentDate.GetMonth()+1,day=documentDate.GetDay())
        try:
            if theData.current_image == filename :
                fullText = theData.get_content()
            else:  
                imData = data.imageData.imageData()
                imData.load_file(filename)
                doOCR = self.cbOCR.GetValue()#str_to_bool( database.theConfig.get_param('OCR', 'autoStart','1') )
                if doOCR :
                    fullText = imData.get_content()
                else:
                    fullText = None
        except Exception as E:
            logging.debug('Saving record error ' + str(E))
            fullText=None
        if fullText is None or len(fullText)==0 : fullText = {'NOTHING FOUND':1}
        # add the document to the database
        keywordsGroups = database.theBase.get_keywordsGroups_from(title, description, filename , tags, fullText)
        return database.theBase.add_document(filename, title, description, None, documentDate, keywordsGroups,tags,self.vFold.getSelectedList())
    def update_record(self,docID,redoOCR=None):
        filename = self.lbFileName.GetPath()
        title = self.lbTitle.Value
        tags = self.lbTags.Value
        description = self.lbDescription.Value
        documentDate = self.lbDate.Value
        documentDate=datetime.date(year=documentDate.GetYear(),month=documentDate.GetMonth()+1,day=documentDate.GetDay())
        folderIDList = self.vFold.getSelectedList()
        fullText=None
        if redoOCR is None : redoOCR = self.cbOCR.GetValue()
        if redoOCR:
            try:
                if theData.current_image == filename :
                    fullText = theData.get_content()
                else:  
                    imData = data.imageData.imageData()
                    imData.load_file(filename)
                    doOCR = str_to_bool( database.theConfig.get_param('OCR', 'autoStart','1') )
                    if doOCR :
                        fullText = imData.get_content()
                    else:
                        fullText = None
                    if fullText is None or len(fullText)==0 : fullText = {'NOTHING FOUND':1}
            except:
                pass
        # add the document to the database
        #keywordsGroups = database.theBase.get_keywordsGroups_from(title, description, filename , tags, fullText)
        if not database.theBase.update_doc(docID, title, description, documentDate, filename,tags,fullText,folderIDList):
            wx.MessageBox(_('Unable to update the database'))
            return False
        return True
