'''
Created on 21 juin 2010. Copyright 2010, David GUEZ
@author: david guez (guezdav@gmail.com)
This file is a part of the source code of the MALODOS project.
You can use and distribute it freely, but have to conform to the license
attached to this project (LICENSE.txt file)
=====================================================================
GUI frame of the main application board
'''
import wx
import ast
from . import addFileWindow
from . import RecordWidget
from . import docWindow
import database
import os
import subprocess
from . import docPrinter
from data import theData
from . import fileMerge

from . import scanWindow
from . import survey
from gui import utilities
import hashlib
from gui import Preferences
from database import Resources
import algorithms.stringFunctions as SF
import data
from . import documentToGo
import webbrowser
import logging
from . import requestBuilder
from . import startupWizard
from homeDocs import __version__

class bugReportWindow(wx.Dialog):
    def __init__(self,parent):
        wx.Dialog.__init__(self, parent, -1, _('Details of the bug report'))
        self.panel = wx.Panel(self, -1)
        self.totalWin = wx.BoxSizer(wx.VERTICAL)
        msg ="""Below is a form that you can fill to describe any bug you have found. The normal and best way to 
        report a bug should be to use the bug report system of the google code page of the project
        at this address : http://code.google.com/p/malodos/issues/entry
        However, some people do not feel sufficiently comfortable with this kind of tools, and for
        those people the following fields could be used in order to prepare an e-mail for
        reporting a bug.
        
        Please, before reporting any bug, verify at least that it is not already known by looking at
        the existing bugs in this page :  http://code.google.com/p/malodos/issues
        """
        self.totalWin.Add(wx.StaticText(self.panel,-1,_(msg)),0,wx.ALL | wx.EXPAND)
        self.totalWin.Add(wx.StaticText(self.panel,-1,_('Your name')),0,wx.ALL | wx.EXPAND)
        self.lbName  =  wx.TextCtrl(self.panel, -1)
        self.totalWin.Add(self.lbName,0,wx.ALL | wx.EXPAND)
         
        self.totalWin.Add(wx.StaticText(self.panel,-1,_('Description of the bug')),0,wx.ALL | wx.EXPAND)
        self.lbDescription  =  wx.TextCtrl(self.panel, -1,style=wx.TE_MULTILINE | wx.TE_WORDWRAP | wx.TE_AUTO_URL | wx.TE_RICH2)
        self.totalWin.Add(self.lbDescription,1,wx.ALL | wx.EXPAND)
        
        self.buttons = wx.BoxSizer(wx.HORIZONTAL)
        self.btOk = wx.Button(self.panel,-1,_('Ok'))
        self.btCancel = wx.Button(self.panel,-1,_('Cancel'))
        self.buttons.Add(self.btOk,0,wx.ALL | wx.EXPAND)
        self.buttons.Add(self.btCancel,0,wx.ALL | wx.EXPAND)
        self.totalWin.Add(self.buttons,0,wx.ALL | wx.EXPAND)

        self.panel.SetSizerAndFit(self.totalWin)
        self.SetClientSize((700,400))
        
        self.Bind(wx.EVT_BUTTON,self.actionSend,self.btOk)
        self.Bind(wx.EVT_BUTTON,self.actionCancel,self.btCancel)
    def actionCancel(self,event):
        self.Close()
    def actionSend(self,event):
        subject = 'BUG report for MALODOS version ' + __version__
        body ='Hello, my name is ' + self.lbName.Value +'\n'
        body += 'I found a bug described here :\n'
        body += self.lbDescription.Value
        body +='\n'
        body +='\n Content of the log file below \n ---------- \n'
        if os.name == 'nt' : body = body.replace('\n','%0D')
        logfilename=os.path.join(database.theConfig.conf_dir ,'messages.log')
        f = open(logfilename,'r')
        body += f.read()
        f.close()
        webbrowser.open('mailto:guezdav@gmail.com?subject={0}&body={1}'.format(subject,body ))
        self.Close()


class FlatView(wx.NotebookPage):
    ID_ALPHABETICAL=(1,_('Alphabetical'))
    ID_CHRONO_DOC=(2,_('Chronological (document)'))
    ID_CHRONO_REG=(3,_('Chronological (registering date)'))
    ID_PERTINENCE=(4,_('Relevance'))
    CHOICES=[ID_ALPHABETICAL,ID_CHRONO_DOC,ID_CHRONO_REG,]#ID_PERTINENCE]#
    def __init__(self,parent,idt,name,board):
        wx.NotebookPage.__init__(self,parent,idt,name=name)
        self.board = board
        self.totSizer = wx.GridBagSizer()
        self.panel = wx.Panel(self, -1)
        self.panel.SetLabel(_('Ascending order'))
        #self.lbDocuments = wx.ListBox(self.panel, -1,style=wx.LB_EXTENDED )
        self.lbDocuments = wx.ListCtrl(self.panel, -1,style=wx.LC_REPORT)
        self.lbDocuments.InsertColumn(0,'Document name',width=800)
        self.idDict = dict()
        listChoices = [c[1] for c in self.CHOICES]
        self.cbOrder = wx.ComboBox(self.panel,-1,choices=listChoices)
        self.cbOrder.SetSelection(0)
        self.chkInvertOrder = wx.CheckBox(self.panel,-1)
        self.chkInvertOrder.SetValue(True)
        self.totSizer.Add(wx.StaticText(self.panel,label=_('Classification')),(0,0),flag=wx.EXPAND)
        self.totSizer.Add(self.cbOrder,(0,1),flag=wx.EXPAND)
        self.totSizer.Add(self.chkInvertOrder,(0,2),flag=wx.EXPAND)
        self.totSizer.Add(wx.StaticText(self.panel,label=_('Ascending order')),(0,3),flag=wx.EXPAND)
        self.totSizer.Add(self.lbDocuments,(1,0),span=(1,4),flag=wx.EXPAND)
        self.totSizer.AddGrowableRow(1)
        self.totSizer.AddGrowableCol(1)
        self.panel.SetSizerAndFit(self.totSizer)
        #self.Bind(wx.EVT_LISTBOX,self.action_select,self.lbDocuments)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED,self.action_select,self.lbDocuments)
        self.Bind(wx.EVT_COMBOBOX,self.show_content,self.cbOrder)
        self.Bind(wx.EVT_CHECKBOX,self.show_content,self.chkInvertOrder)
        self.lbDocuments.Bind(wx.EVT_CONTEXT_MENU,self.contextualMenu)
        self.lbDocuments.Bind(wx.EVT_LEFT_DCLICK,self.action_add_to_basket)
        self.lbDocuments.Bind(wx.EVT_MENU,self.action_menu)
        self.docList=None
    def action_menu(self,event):
        self.board.action_menu(self.get_selection(),event.GetId())
    def action_add_to_basket(self,event):
        idt = self.lbDocuments.GetItemData(self.lbDocuments.GetFocusedItem())
        rowList = [self.idDict[idt]]
        self.board.basket_add_remove(rowList)
        
    def contextualMenu(self,event):
        row = self.get_selection()
        if len(row)>0: self.lbDocuments.PopupMenu(self.board.create_menu(row))
    def fillWith(self,docList):
        self.docList = docList
        self.show_content()
    def show_content(self,event=None):
        #self.lbDocuments.Clear()
        self.lbDocuments.DeleteAllItems()
        if self.docList is None or len(self.docList)==0: return
        sel = self.cbOrder.GetSelection()
        if sel is None : return
        sel = self.CHOICES[sel][0]
        if sel == self.ID_ALPHABETICAL[0]:
            self.docList.sort(key=lambda row: SF.no_accent(row[database.theBase.IDX_TITLE].lower()),reverse=self.chkInvertOrder.Value)
        elif sel == self.ID_CHRONO_DOC[0]:
            self.docList.sort(key=lambda row:row[database.theBase.IDX_DOCUMENT_DATE],reverse=self.chkInvertOrder.Value)
        elif sel == self.ID_CHRONO_REG[0]:
            self.docList.sort(key=lambda row:row[database.theBase.IDX_REGISTER_DATE],reverse=self.chkInvertOrder.Value)
        elif sel == self.ID_PERTINENCE[0] and database.theBase.IDX_COUNT<len(self.docList[0]):
            self.docList.sort(key=lambda row:row[database.theBase.IDX_COUNT],reverse=self.chkInvertOrder.Value)
        for row in self.docList:
            title= row[database.theBase.IDX_TITLE]
            #if row[database.theBase.IDX_ROWID] in self.board.basket : title='---  ' + title + '   ---' 
            #self.lbDocuments.Append( title , row)
            #n_it = self.lbDocuments.GetItemCount()

            idt = wx.NewId()
            self.idDict[idt] = row
            item_index = self.lbDocuments.InsertItem(self.lbDocuments.GetItemCount(), title)
            self.lbDocuments.SetItemData(item_index, idt)
            #if row[database.theBase.IDX_ROWID] in self.board.basket_idList() : self.lbDocuments.SetItemTextColour(n_it,wx.RED)
            #self.lbDocuments.SetItemData(n_it,row)
            #item = self.lbDocuments.FindString(title)
            #if row[database.theBase.IDX_ROWID] in self.board.basket : self.lbDocuments.SetItemForegroundColour(item,(255,0,0))
            #self.lbDocuments.SetItemBackgroundColour(item,'#990000')
        self.draw_content()
    def draw_content(self):
        for i in range(self.lbDocuments.ItemCount):
            row = self.idDict[self.lbDocuments.GetItemData(i)]
            if row[database.theBase.IDX_ROWID] in self.board.basket_idList() : 
                self.lbDocuments.SetItemTextColour(i,wx.RED)
            else:
                self.lbDocuments.SetItemTextColour(i,wx.BLACK)
    def get_selection(self):
        #sel = self.lbDocuments.GetSelections()
        #if sel == wx.NOT_FOUND: return
        #row = [self.lbDocuments.GetClientData(s) for s in sel]
        sel=[]
        for i in range(self.lbDocuments.ItemCount) :
            if  self.lbDocuments.IsSelected(i)  : sel.append(i)
        row = [self.idDict[self.lbDocuments.GetItemData(s)] for s in sel]
        return row
    def action_select(self,event):
        row = self.get_selection()
        self.board.actionDocSelect(row)


class BasketView(wx.NotebookPage):
    ID_ALPHABETICAL=(1,_('Alphabetical'))
    ID_CHRONO_DOC=(2,_('Chronological (document)'))
    ID_CHRONO_REG=(3,_('Chronological (registering date)'))
    ID_PERTINENCE=(4,_('Relevance'))
    CHOICES=[ID_ALPHABETICAL,ID_CHRONO_DOC,ID_CHRONO_REG,]#ID_PERTINENCE]#
    
    ID_REMOVE=1
    ID_MERGE=2
    ID_TOGO=3
    def __init__(self,parent,idt,name,board):
        wx.NotebookPage.__init__(self,parent,idt,name=name)
        self.board = board
        self.totSizer = wx.GridBagSizer()
        self.panel = wx.Panel(self, -1)
        self.panel.SetLabel(_('Ascending order'))
#        self.icBar=wx.ToolBar(self.panel)
#        self.icBar.SetToolBitmapSize((32,32))
#        self.icBar.AddLabelTool(self.ID_REMOVE,'',wx.Bitmap(Resources.get_icon_filename('REMOVE_SELECTION32')),shortHelp=_('Remove/delete all documents in the basket'))
#        self.icBar.AddLabelTool(self.ID_MERGE,'',wx.Bitmap(Resources.get_icon_filename('MERGE_SELECTION32')),shortHelp=_('Merge together all documents in the basket'))
#        self.icBar.AddLabelTool(self.ID_TOGO,'',wx.Bitmap(Resources.get_icon_filename('DOC_ZIP32')),shortHelp=_('Make a portable zip of all the documents in the basket'))
        self.bxSizer=wx.BoxSizer(wx.HORIZONTAL)
        self.btUpdateRemove = wx.BitmapButton(self.panel,-1,wx.Bitmap(Resources.get_icon_filename('REMOVE_SELECTION32')))
        self.btUpdateRemove.SetToolTipString(_('Remove/delete all documents in the basket'))

        self.btMerge = wx.BitmapButton(self.panel,-1,wx.Bitmap(Resources.get_icon_filename('MERGE_SELECTION32')))
        self.btMerge.SetToolTipString(_('Merge together all documents in the basket'))

        self.btToGo = wx.BitmapButton(self.panel,-1,wx.Bitmap(Resources.get_icon_filename('DOC_ZIP32')))
        self.btToGo.SetToolTipString(_('Make a portable zip of all the documents in the basket'))


        self.lbDocuments = wx.ListBox(self.panel, -1,style=wx.LB_EXTENDED )
        listChoices = [c[1] for c in self.CHOICES]
        self.cbOrder = wx.ComboBox(self.panel,-1,choices=listChoices)
        self.cbOrder.SetSelection(0)
        self.chkInvertOrder = wx.CheckBox(self.panel,-1)
        self.chkInvertOrder.SetValue(True)
#        self.totSizer.Add(self.icBar,(0,0),flag=wx.EXPAND)
        self.bxSizer.Add(self.btUpdateRemove,flag=wx.ALIGN_LEFT)
        self.bxSizer.Add(self.btMerge,flag=wx.ALIGN_LEFT)
        self.bxSizer.Add(self.btToGo,flag=wx.ALIGN_LEFT)
        self.totSizer.Add(self.bxSizer,(0,0),flag=wx.EXPAND)
        self.totSizer.Add(wx.StaticText(self.panel,label=_('Classification')),(1,0),flag=wx.EXPAND)
        self.totSizer.Add(self.cbOrder,(1,1),flag=wx.EXPAND)
        self.totSizer.Add(self.chkInvertOrder,(1,2),flag=wx.EXPAND)
        self.totSizer.Add(wx.StaticText(self.panel,label=_('Ascending order')),(1,3),flag=wx.EXPAND)
        self.totSizer.Add(self.lbDocuments,(2,0),span=(1,4),flag=wx.EXPAND)
        self.totSizer.AddGrowableRow(2)
        self.totSizer.AddGrowableCol(1)
        self.panel.SetSizerAndFit(self.totSizer)
        self.Bind(wx.EVT_LISTBOX,self.action_select,self.lbDocuments)
        self.Bind(wx.EVT_COMBOBOX,self.show_content,self.cbOrder)
        self.Bind(wx.EVT_CHECKBOX,self.show_content,self.chkInvertOrder)
        self.lbDocuments.Bind(wx.EVT_CONTEXT_MENU,self.contextualMenu)
        self.lbDocuments.Bind(wx.EVT_MENU,self.action_menu)
        self.docList=None
#        self.Bind(wx.EVT_TOOL,self.actionRemove,id=self.ID_REMOVE)
#        self.Bind(wx.EVT_TOOL,self.actionMerge,id=self.ID_MERGE)
#        self.Bind(wx.EVT_TOOL,self.actionToGo,id=self.ID_TOGO)
        self.Bind(wx.EVT_BUTTON,self.actionRemove,self.btUpdateRemove)
        self.Bind(wx.EVT_BUTTON,self.actionMerge,self.btMerge)
        self.Bind(wx.EVT_BUTTON,self.actionToGo,self.btToGo)

        
    def actionRemove(self,event):
        self.board.actionRemoveRecord(self.board.basket)
    def action_menu(self,event):
        self.board.action_menu(self.get_selection(),event.GetId())
    def actionMerge(self,event):
        self.board.merge_documents(self.board.basket)
    def actionToGo(self,event):
        self.board.actionDocToGo(self.board.basket)
    def contextualMenu(self,event):
        row = self.get_selection()
        if len(row)>0: self.lbDocuments.PopupMenu(self.board.create_menu(row))
    def fillWith(self,docList):
        self.docList = docList
        self.show_content()
    def show_content(self,event=None):
        self.lbDocuments.Clear()
        if self.docList is None or len(self.docList)==0: return
        sel = self.cbOrder.GetSelection()
        if sel is None : return
        sel = self.CHOICES[sel][0]
        if sel == self.ID_ALPHABETICAL[0]:
            self.docList.sort(key=lambda row:SF.no_accent(row[database.theBase.IDX_TITLE].lower()),reverse=self.chkInvertOrder.Value)
        elif sel == self.ID_CHRONO_DOC[0]:
            self.docList.sort(key=lambda row:row[database.theBase.IDX_DOCUMENT_DATE],reverse=self.chkInvertOrder.Value)
        elif sel == self.ID_CHRONO_REG[0]:
            self.docList.sort(key=lambda row:row[database.theBase.IDX_REGISTER_DATE],reverse=self.chkInvertOrder.Value)
        elif sel == self.ID_PERTINENCE[0] and database.theBase.IDX_COUNT<len(self.docList[0]):
            self.docList.sort(key=lambda row:row[database.theBase.IDX_COUNT],reverse=self.chkInvertOrder.Value)
        for row in self.docList:
            title= row[database.theBase.IDX_TITLE]
            self.lbDocuments.Append( title , row)
    def draw_content(self):
        pass
    def get_selection(self):
        sel = self.lbDocuments.GetSelections()
        if sel == wx.NOT_FOUND: return
        row = [self.lbDocuments.GetClientData(s) for s in sel]
        return row
    def action_select(self,event):
        row = self.get_selection()
        self.board.actionDocSelect(row)



class FolderView(wx.NotebookPage):
    def __init__(self,parent,idt,name,board):
        wx.NotebookPage.__init__(self,parent,idt,name=name)
        self.board = board
        self.totSizer = wx.BoxSizer(wx.VERTICAL)
        self.panel = wx.Panel(self, -1)
        self.trFolders = wx.TreeCtrl(self.panel, -1,style=wx.TR_DEFAULT_STYLE|wx.TR_FULL_ROW_HIGHLIGHT|wx.TR_HIDE_ROOT|wx.TR_MULTIPLE )
        self.totSizer.Add(self.trFolders,1,wx.EXPAND)
        self.panel.SetSizerAndFit(self.totSizer)
        self.Bind(wx.EVT_TREE_SEL_CHANGED,self.action_select,self.trFolders)
        self.trFolders.Bind(wx.EVT_TREE_ITEM_MENU,self.contextualMenu)
        self.trFolders.Bind(wx.EVT_LEFT_DCLICK,self.action_add_to_basket)
        self.trFolders.Bind(wx.EVT_MENU,self.action_menu)
    def action_menu(self,event):
        self.board.action_menu(self.get_selection(),event.GetId())
    def action_add_to_basket(self,event):
        idt = self.trFolders.GetPyData(self.trFolders.GetSelection())
        if (idt is not None) and (idt != 0):
            self.board.basket_add_remove([idt])
    def contextualMenu(self,event):
        row = self.get_selection()
        if len(row)>0: self.trFolders.PopupMenu(self.board.create_menu(row))
    def fillWith(self,docList):
        self.trFolders.DeleteAllItems()
        if docList is None : return
        rootItem=self.trFolders.AddRoot(_('ROOT'),data=wx.TreeItemData(0))
        unclassified = self.trFolders.AppendItem(rootItem,_('Unclassified'))
        itemDict={}
        for row in docList:
            title=row[database.theBase.IDX_TITLE]
            docID = row[database.theBase.IDX_ROWID]
            folderID_list = database.theBase.folders_list_for(docID)
            if len(folderID_list)<1:
                item=self.trFolders.AppendItem(unclassified,title,data=wx.TreeItemData(row))
                if docID in self.board.basket_idList() : self.trFolders.SetItemTextColour(item,wx.RED)
            for folderID in folderID_list:
                genealogy = database.theBase.folders_genealogy_of(folderID, False)
                item = self.trFolders.GetRootItem()
                for (fID,fName) in genealogy:
                    if fID in itemDict:
                        item = itemDict[fID]
                    else:
                        item = self.trFolders.AppendItem(item,fName)
                        itemDict[fID] = item
                item=self.trFolders.AppendItem(item,title,data=wx.TreeItemData(row))
                if docID in self.board.basket_idList() : self.trFolders.SetItemTextColour(item,wx.RED)
        #self.trFolders.Expand(rootItem)
    def draw_content(self):
        def show_under(item):
            row = self.trFolders.GetPyData(item)
            if (row is not None and row!=0) and row[database.theBase.IDX_ROWID] in self.board.basket_idList() :
                self.trFolders.SetItemTextColour(item,wx.RED)
            else:
                self.trFolders.SetItemTextColour(item,wx.BLACK)
            child , cookie = self.trFolders.GetFirstChild(item)
            while child.IsOk() :
                show_under(child)
                child , cookie = self.trFolders.GetNextChild(item,cookie)
        show_under(self.trFolders.GetRootItem())
    def get_selection(self):
        items = self.trFolders.GetSelections()
        return [self.trFolders.GetPyData(item) for item in items]
    def action_select(self,event):
        row=self.get_selection()
        self.board.actionDocSelect(row)



class TagFolderView(FolderView):
    def __init__(self,parent,idt,name,board):
        FolderView.__init__(self,parent,idt,name,board)
        self.trFolders.Bind(wx.EVT_LEFT_DCLICK,self.action_add_to_basket)
    def action_add_to_basket(self,event):
        idt = self.trFolders.GetPyData(self.trFolders.GetSelection())
        if (idt is not None) and (idt != 0):
            self.board.basket_add_remove([idt])
    def recursiveFill(self,baseItem,docList,refusedKeys,onlyTags):
        usedDoc=[]
        while len(docList)>0:
            currentKeys = refusedKeys[:]
            tags = database.theBase.get_list_of_tags_for(docList,currentKeys,onlyTags)
            if tags is not None:
                tag=tag=tags.fetchone()
            else:
                tag=None
            docList2 = docList[:]
            toShow = docList[:]
            item = baseItem
            if tag is not None:
                title=tag[0]
                nb   =tag[1]
                key  =tag[2]
                if nb>5:
                    #item = self.trFolders.AppendItem(baseItem,'{0} ({1} occurences)'.format(title,nb))
                    item = self.trFolders.AppendItem(baseItem,title)
                    currentKeys.append(key)
                    #print title,currentKeys
                    docList2 = database.theBase.get_list_of_docs_with_all_keys(currentKeys,onlyTags)
                    docList2 = list(set.intersection(set(docList),set(docList2)))
                    if docList2 is None : docList2=[]
                    if len(docList2)>5:
                        docListUnder = self.recursiveFill(item, docList2, currentKeys, onlyTags)
                        toShow = list(set.difference(set(docList2),set(docListUnder)))
                    else:
                        toShow = docList2[:]
            cur = database.theBase.get_by_doc_id(toShow)
            if cur is None : cur=[]
            for row in cur:
                itm = self.trFolders.AppendItem(item,row[database.theBase.IDX_TITLE],data=wx.TreeItemData(row))
                if row[database.theBase.IDX_ROWID] in self.board.basket_idList() : self.trFolders.SetItemTextColour(itm,wx.RED)
                usedDoc.append(row[database.theBase.IDX_ROWID])
            docList3 = list(set.difference(set(docList),set(docList2)))
            if len(docList3)==len(docList) :
                return usedDoc
            docList=docList3[:]
        return usedDoc
    def fillWith(self,docList):
        self.trFolders.DeleteAllItems()
        if docList is None : return
        rootItem=self.trFolders.AddRoot(_('ROOT'),data=wx.TreeItemData(0))
        self.recursiveFill(rootItem, [row[database.theBase.IDX_ROWID] for row in docList],[],True)
    def draw_content(self):
        def show_under(item):
            row = self.trFolders.GetPyData(item)
            if (row is not None and row!=0) and row[database.theBase.IDX_ROWID] in self.board.basket_idList() :
                self.trFolders.SetItemTextColour(item,wx.RED)
            else:
                self.trFolders.SetItemTextColour(item,wx.BLACK)
            child , cookie = self.trFolders.GetFirstChild(item)
            while child.IsOk() :
                show_under(child)
                child , cookie = self.trFolders.GetNextChild(item,cookie)
        show_under(self.trFolders.GetRootItem())


class MainFrame(wx.Frame):
    ID_ADD_FILE=1
    ID_ADD_SCAN=2
    ID_REMOVE_SEL=3
    ID_PRINT_DOC=4
    ID_DOCTOGO=5
    ID_SURVEY=6
    ID_PREFS=7
    ID_CREDITS=8
    ID_SUPPORT=9
    ID_BUGREPORT=10
    ID_DOCBASKET=11

    ID_MENU_REMOVE=1
    ID_MENU_ADD_BASKET=2
    ID_MENU_REMOVE_BASKET=3
    ID_MENU_CONCATENATE_FILE=4
    ID_MENU_CONCATENATE_SCAN=5
    ID_MENU_CONCATENATE_ITEMS=6
    
    
    modified=False
    basket=[]

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

    #===========================================================================
    # constructor (GUI building)
    #===========================================================================
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, -1, _('MALODOS Main panel'), wx.DefaultPosition, (576, 721), style=wx.CLOSE_BOX | wx.SYSTEM_MENU | wx.CAPTION | wx.RESIZE_BORDER | 0 | 0 | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX)
    def initialize(self):
        fname = Resources.get_icon_filename('APPLICATION')
        appIcon = wx.Icon(fname,wx.BITMAP_TYPE_ANY)
        #appIcon.LoadFile(Resources.get_icon_filename('APPLICATION'),wx.BITMAP_TYPE_ANY)
        self.SetIcon(appIcon)
        self.panel = wx.Panel(self, -1)
        
        self.docPart = wx.SplitterWindow(self.panel,-1,style=wx.SP_3D | wx.SP_LIVE_UPDATE)
        self.docPart.SetSashGravity(0.5)
        
        self.docViewPanel = wx.Panel(self.docPart)
        self.docViewSizer = wx.BoxSizer(wx.VERTICAL)
        self.recordSizer =  wx.BoxSizer(wx.HORIZONTAL)

        self.docWin = docWindow.docWindow(self.docViewPanel,-1)
        self.docViewSizer.Add(self.docWin,1,wx.EXPAND)
        
        self.tbMainBar = self.CreateToolBar()
        self.tbMainBar.AddLabelTool(self.ID_ADD_FILE,'',wx.Bitmap(Resources.get_icon_filename('ADD_FILE')),shortHelp=_('Add an existing file'))
        self.tbMainBar.AddLabelTool(self.ID_ADD_SCAN,'',wx.Bitmap(Resources.get_icon_filename('ADD_SCAN')),shortHelp=_('Scanning a new document'))
        self.tbMainBar.AddLabelTool(self.ID_REMOVE_SEL,'',wx.Bitmap(Resources.get_icon_filename('REMOVE_SELECTION')),shortHelp=_('Remove the current selection from the database'))
        self.tbMainBar.AddLabelTool(self.ID_PRINT_DOC,'',wx.Bitmap(Resources.get_icon_filename('DOC_PRINT')),shortHelp=_('Print the selected document'))
        self.tbMainBar.AddLabelTool(self.ID_DOCBASKET,'',wx.Bitmap(Resources.get_icon_filename('DOC_BASKET')),shortHelp=Resources.get_message('DOC_BASKET'))
        self.tbMainBar.AddLabelTool(self.ID_DOCTOGO,'',wx.Bitmap(Resources.get_icon_filename('DOC_ZIP')),shortHelp=Resources.get_message('DOC_ZIP'))
        self.tbMainBar.AddLabelTool(self.ID_SURVEY,'',wx.Bitmap(Resources.get_icon_filename('SURVEY_WIN')),shortHelp=_('Open the directory survey window'))
        self.tbMainBar.AddLabelTool(self.ID_PREFS,'',wx.Bitmap(Resources.get_icon_filename('PREFS')),shortHelp=_('Set preferences'))
        self.tbMainBar.AddLabelTool(self.ID_CREDITS,'',wx.Bitmap(Resources.get_icon_filename('CREDITS')),shortHelp=_('Credits'))
        self.tbMainBar.AddLabelTool(self.ID_BUGREPORT,'',wx.Bitmap(Resources.get_icon_filename('BUGREPORT')),shortHelp=_('Report a bug'))
        self.tbMainBar.AddLabelTool(self.ID_SUPPORT,'',wx.Bitmap(Resources.get_icon_filename('SUPPORT')),shortHelp=_('Support MALODOS'))
        self.tbMainBar.Realize()
        
        self.recordPart = RecordWidget.RecordWidget(self.docViewPanel)
        self.recordPart.setModificationCallback(self.actionRecordModified)
        self.recordPart.lbFileName.Disable()
        self.recordSizer.Add(self.recordPart,1,wx.EXPAND)
        self.btUpdateRecord = wx.BitmapButton(self.docViewPanel,-1,wx.Bitmap(Resources.get_icon_filename('REFRESH')))
        self.btUpdateRecord.SetToolTipString(_('Update'))
        self.btShowExternal = wx.BitmapButton(self.docViewPanel,-1,wx.Bitmap(Resources.get_icon_filename('SYSTEM_SHOW')))
        self.btShowExternal.SetToolTipString(_('System show'))

        #self.btDoOCR = wx.BitmapButton(self.docViewPanel,-1,wx.Bitmap(Resources.get_icon_filename('SYSTEM_SHOW')))
        #self.btDoOCR.SetToolTipString(_('Do OCR'))

        self.docViewSizer.Add(self.recordSizer,0,wx.EXPAND)
        self.recordButtonSizer = wx.BoxSizer(wx.VERTICAL)
        self.recordButtonSizer.Add(self.btUpdateRecord,1,wx.EXPAND)
        self.recordButtonSizer.Add(self.btShowExternal,1,wx.EXPAND)
        #self.recordButtonSizer.Add(self.btDoOCR,1,wx.EXPAND)
        self.recordSizer.Add(self.recordButtonSizer)
        self.docViewPanel.SetSizerAndFit(self.docViewSizer)

        #self.lbDocuments = wx.ListBox(self.docPart, -1,size= (387, 124),style=wx.LB_SORT | wx.LB_EXTENDED )
        self.leftPane = wx.Notebook(self.docPart,-1)
        self.flatViewFrame = FlatView(self.leftPane,-1,_("Flat view"),self)       
        self.leftPane.AddPage(self.flatViewFrame,self.flatViewFrame.GetName())
        self.folderViewFrame = FolderView(self.leftPane,-1,_("Folder view"),self)       
        self.leftPane.AddPage(self.folderViewFrame,self.folderViewFrame.GetName())
        self.tagFolderViewFrame = TagFolderView(self.leftPane,-1,_("Tag Folder view"),self)       
        self.leftPane.AddPage(self.tagFolderViewFrame,self.tagFolderViewFrame.GetName())
        self.basketViewFrame = BasketView(self.leftPane,-1,_("Basket view"),self)       
        self.leftPane.AddPage(self.basketViewFrame,self.basketViewFrame.GetName())
        
        self.label2 = wx.StaticText(self.panel, -1, _('filter :'))
        self.tbFilter = wx.TextCtrl(self.panel, -1, '',style=wx.TE_PROCESS_ENTER)
        self.btBuildFilter = wx.Button(self.panel, -1, _('advanced'))
        #self.btBuildFilter.Hide()
        

        # sizers
        self.totalWin = wx.BoxSizer(wx.VERTICAL)
        self.upPart = wx.BoxSizer(wx.HORIZONTAL)
        self.searchPart = wx.BoxSizer(wx.HORIZONTAL)
        self.docPart.SplitVertically(self.leftPane,self.docViewPanel)

        # adding widgets into sizers (--> creating layout)
        self.searchPart.Add(self.label2,0,wx.ALIGN_LEFT)
        self.searchPart.Add(self.tbFilter,1,wx.EXPAND)
        self.searchPart.Add(self.btBuildFilter,0,wx.EXPAND)
        self.searchPart.Layout()
        
        self.upPart.Add(self.searchPart,3,wx.ALIGN_LEFT)
        self.upPart.Layout()
        
        self.totalWin.Add(self.upPart,0,wx.EXPAND)
        self.totalWin.Add(self.docPart,1,wx.EXPAND)
        self.totalWin.Layout()

        self.Bind(wx.EVT_TEXT_ENTER, self.actionSearch, self.tbFilter)
        self.Bind(wx.EVT_TOOL, self.actionAddFile, id=self.ID_ADD_FILE)
        self.Bind(wx.EVT_TOOL, self.actionAddScan, id=self.ID_ADD_SCAN)
        self.Bind(wx.EVT_TOOL, self.actionDoPrint, id=self.ID_PRINT_DOC)
        self.Bind(wx.EVT_TOOL,self.actionStartSurvey,id=self.ID_SURVEY)
        self.Bind(wx.EVT_TOOL,self.actionShowPrefs,id=self.ID_PREFS)
        self.Bind(wx.EVT_TOOL,self.actionDocToGo,id=self.ID_DOCTOGO)
        self.Bind(wx.EVT_TOOL,self.actionRemoveRecord,id=self.ID_REMOVE_SEL)
        self.Bind(wx.EVT_TOOL,self.actionAbout,id=self.ID_CREDITS)
        self.Bind(wx.EVT_TOOL,self.actionSupport,id=self.ID_SUPPORT)
        self.Bind(wx.EVT_TOOL,self.actionReport,id=self.ID_BUGREPORT)
        self.Bind(wx.EVT_TOOL,self.actionBasket,id=self.ID_DOCBASKET)
        self.Bind(wx.EVT_BUTTON,self.actionStartExternalApp,self.btShowExternal)
        self.Bind(wx.EVT_BUTTON,self.actionUpdateRecord,self.btUpdateRecord)
        self.Bind(wx.EVT_BUTTON,self.actionBuildRequest,self.btBuildFilter)
        #self.Bind(wx.EVT_BUTTON,self.actionTestOCR,self.btDoOCR)

        # layout assignment
        self.panel.SetSizerAndFit(self.totalWin)
        self.totalWin.Fit(self)
        self.Maximize()
        if not database.theConfig.existedConfigFile:
            wizard = startupWizard.StartupWizard(self)
            wizard.RunWizard(wizard.pageDatabase)
        self.actionSearch(None)
        

    def create_menu(self,row):
        rows = self.recordPart.getRow()
        menu=wx.Menu()
        menu.Append(self.ID_MENU_REMOVE,_('Remove / delete'))
        menu.Append(self.ID_MENU_ADD_BASKET,_('Add to the basket'))
        menu.Append(self.ID_MENU_REMOVE_BASKET,_('Remove from the basket'))
        if len(rows)==1:
            menu.Append(self.ID_MENU_CONCATENATE_FILE,_('Add file content after this document'))
            menu.Append(self.ID_MENU_CONCATENATE_SCAN,_('Add scan content after this document'))
        else:
            menu.Append(self.ID_MENU_CONCATENATE_ITEMS,_('Merge documents together'))
        return menu
    def action_menu(self,row_list,menu_id):
        if menu_id == self.ID_MENU_REMOVE:
            self.actionRemoveRecord(row_list)
        elif menu_id == self.ID_MENU_ADD_BASKET:
            self.basket_add(row_list)
        elif menu_id == self.ID_MENU_REMOVE_BASKET:
            self.basket_add_remove(row_list)
        elif menu_id == self.ID_MENU_CONCATENATE_FILE:
            self.actionAddFile(None,row_list[0])
        elif menu_id == self.ID_MENU_CONCATENATE_SCAN:
            self.actionAddScan(None,row_list[0])
        elif menu_id == self.ID_MENU_CONCATENATE_ITEMS:
            self.merge_documents(row_list)
    def merge_documents(self,row_list):
        fm = fileMerge.FileMerger(self,row_list)
        fm.ShowModal()
        self.actionSearch(None)
    def redraw_items(self):
        self.flatViewFrame.draw_content()
        self.folderViewFrame.draw_content()
        self.tagFolderViewFrame.draw_content()
    def basket_idList(self):
        return [row[database.theBase.IDX_ROWID] for row in self.basket]
    def basket_remove(self,row_list):
        idList = self.basket_idList()
        for row in row_list:
            if row[database.theBase.IDX_ROWID] in idList :
                self.basket.remove(row)
        self.redraw_items()#self.actionSearch(None)
        self.basketViewFrame.fillWith(self.basket)
    def basket_add(self,row_list):
        idList = self.basket_idList()
        for row in row_list:
            if row[database.theBase.IDX_ROWID] not in idList :
                self.basket.append(row)
        self.redraw_items()#self.actionSearch(None)
        self.basketViewFrame.fillWith(self.basket)
    def basket_add_remove(self,row_list):
        idList = self.basket_idList()
        for row in row_list:
            if row[database.theBase.IDX_ROWID] in idList :
                self.basket.remove(row)
            else:
                self.basket.append(row)
        self.redraw_items()#self.actionSearch(None)
        
        self.basketViewFrame.fillWith(self.basket)
    def actionBasket(self,event):
        rows = self.recordPart.getRow()
        row_list = [row for row in rows if row is not None]
        self.basket_add(row_list)
    def actionBuildRequest(self,event):
        builder = requestBuilder.builder(self)
        builder.ShowModal()
        if builder.request is not None:
            self.tbFilter.Value = builder.request
            self.actionSearch(None)
    def actionRecordModified(self):
        self.modified=True
                
    def actionTestOCR(self,event):
        words_dict = data.theData.get_content()
        for w,n in list(words_dict.items()) : print(w + '(' + str(n) + ' fois)')
    #===========================================================================
    # click on add scan button
    #===========================================================================
    def actionAddScan(self,event,row=None):
        data.theData.clear_all()
        filename=None
        if row is not None :
            try:
                docID = row[database.theBase.IDX_ROWID]
                title = row[database.theBase.IDX_TITLE]
                description = row[database.theBase.IDX_DESCRIPTION]
                documentDate = row[database.theBase.IDX_DOCUMENT_DATE]
                tags = row[database.theBase.IDX_TAGS]
                folderID_list = database.theBase.folders_list_for(docID)
                filename = row[database.theBase.IDX_FILENAME]
                data.theData.load_file(filename, do_clear=False)
            except :
                pass
        Frame = scanWindow.ScanWindow(self,_("Scan a new document"))
        if filename is not None : Frame.recordPart.SetFields(filename, title, description, documentDate,tags,False,folderID_list)
        Frame.ShowModal()
        theData.clear_all()
        self.actionSearch(None)

    #===========================================================================
    # click on add file button
    #===========================================================================
    def actionAddFile(self,event,row=None):
        data.theData.clear_all()
        filename=None
        if row is not None :
            try:
                docID = row[database.theBase.IDX_ROWID]
                title = row[database.theBase.IDX_TITLE]
                description = row[database.theBase.IDX_DESCRIPTION]
                documentDate = row[database.theBase.IDX_DOCUMENT_DATE]
                tags = row[database.theBase.IDX_TAGS]
                folderID_list = database.theBase.folders_list_for(docID)
                filename = row[database.theBase.IDX_FILENAME]
                data.theData.load_file(filename, do_clear=False)
            except :
                pass
        Frame = addFileWindow.AddFileWindow(self,_("Add a new document"))
        if filename is not None : Frame.recordPart.SetFields(filename, title, description, documentDate,tags,False,folderID_list)
        Frame.ShowModal()
        self.actionSearch(None)
    #===========================================================================
    # click on search button (or press enter on the search text entry)
    #===========================================================================
    def actionSearch(self,event):
        # clear the listbox
        #self.flatViewFrame.lbDocuments.Clear()
        if database.theBase is None: return
        sFilter = self.tbFilter.Value
        if len(sFilter)==0:
            docList = database.theBase.find_documents(None)
        else:
            [request,pars] = SF.req_to_sql(self.tbFilter.Value)
            docList = database.theBase.find_sql(request,pars)
        if docList is None : docList=[]
        #if not docList: return
        # otherwise show them in the listbox
        self.docList=[row for row in docList]
        self.flatViewFrame.fillWith(self.docList)
        self.folderViewFrame.fillWith(self.docList)
        self.tagFolderViewFrame.fillWith(self.docList)
#        for row in docList:
#            self.flatViewFrame.lbDocuments.Append(row[database.theBase.IDX_TITLE] , row)
    #===========================================================================
    # actionDocSelect : show the selected item on the doc part
    #===========================================================================
    def actionDocSelect(self,row):
        if self.recordPart.getRow() == row : return
        if (self.modified or theData.is_modified) and utilities.ask(_('The current record has modifications are not yet saved. Do you want to save it before selecting another record?')):
            if self.actionUpdateRecord(None):
                self.modified=False
            else:
                return
        else:
            self.modified=False
            
        self.recordPart.setRow(row)
        if len(row)!=1  or row[0] is None: return
        row=row[0]
        docID = row[database.theBase.IDX_ROWID]
        filename = self._normalize_filename(row[database.theBase.IDX_FILENAME])
        title = row[database.theBase.IDX_TITLE]
        description = row[database.theBase.IDX_DESCRIPTION]
        documentDate = row[database.theBase.IDX_DOCUMENT_DATE]
        tags = row[database.theBase.IDX_TAGS]
        folderID_list = database.theBase.folders_list_for(docID)
        if filename and os.path.exists(filename):
            try:
                file_md5 = hashlib.md5(open(filename, "rb").read()).hexdigest()
                if row[database.theBase.IDX_CHECKSUM] !=  file_md5:
                    if utilities.ask(_('The file content has changed! Do you wish to update its signature ?')):
                        if not database.theBase.update_doc_signature(docID, file_md5):
                            wx.MessageBox(_('Unable to update the database'))
            except Exception as E:
                utilities.show_message(_('Unable to check the file signature...'))
                logging.exception('Error checking MD5 signature ->' + str(E))
        self.recordPart.SetFields(filename, title, description, documentDate,tags,False,folderID_list)
        #print row
        try:
            theData.load_file(filename)
            self.docWin.resetView()
            self.docWin.showCurrentImage()
        except Exception as E:
            logging.exception('Unable to load image:'+str(E))
            theData.clear_all()
        self.modified=False
        
    #===========================================================================
    # actionStartExternalApp : start the system default application associated with the file
    #===========================================================================
    def actionStartExternalApp(self,event):
        row = self.recordPart.getRow()
        if row is None or len(row)!=1 or row[0] is None: return
        row=row[0]
        filename = self._normalize_filename(row[database.theBase.IDX_FILENAME])
        if not filename:
            return
        if os.name == 'posix' :
            subprocess.Popen(['xdg-open', filename])
        else:
            os.startfile(filename)
    #===========================================================================
    # actionUpdateRecord : update the current record
    #===========================================================================
    def actionUpdateRecord(self,event):
        row = self.recordPart.getRow()
        if row is None  or len(row)!=1 or row[0] is None: return
        row=row[0]
        docID = row[database.theBase.IDX_ROWID]
        if not self.recordPart.update_record(docID) :
            utilities.show_message(_('Unable to apply the record changes.'))
            return False
        else:
            self.modified=False
        if theData.is_modified :
            if utilities.ask(_('The image itself has changed, do you want to save the modified image ?')):
                filename = self._normalize_filename(row[database.theBase.IDX_FILENAME])
                title = row[database.theBase.IDX_TITLE]
                description = row[database.theBase.IDX_DESCRIPTION]
                keywords = database.theBase.get_list_of_tags_for(docID)
                theData.save_file(filename, title, description, keywords)
                new_md5 = hashlib.md5(open(filename, "rb").read()).hexdigest()
                database.theBase.update_doc_signature(docID, new_md5)
                
        self.actionSearch(event)
        return True
    #===========================================================================
    # actionRemoveRecord : remove the selected items
    #===========================================================================
    def actionRemoveRecord(self,event):
        if isinstance(event,list) :
            rows = event
        else:
            rows = self.recordPart.getRow()
        database.theBase.delete_documents(rows,parent=self)
        #for doc in docID : print "Want to remove " + str(doc) + " from database"
        self.actionSearch(None)
        
    #===========================================================================
    # actionStartSurvey : show the document survey window
    #===========================================================================
    def actionStartSurvey(self,event):
        theData.clear_all()
        Frame = survey.SurveyWindow(self)
        Frame.ShowModal()
        theData.clear_all()
        self.actionSearch(None)
    #===========================================================================
    # actionShowPrefs : show the preferences window
    #===========================================================================
    def actionShowPrefs(self,event):
        Frame = Preferences.PrefGui(self)
        Frame.ShowModal()
        self.actionSearch(event)
    #===========================================================================
    # actionDoPrint : print the current document
    #===========================================================================
    def actionDoPrint(self,event):
        printData = wx.PrintData()
        printData.SetPaperId(wx.PAPER_A4)
        printData.SetPrintMode(wx.PRINT_MODE_PRINTER)
        pdd = wx.PrintDialogData(printData)
        pdd.SetToPage(theData.nb_pages)
        P = wx.Printer(pdd)
        pr = docPrinter.docPrinter()
        if not P.Print(self , pr) :
            wx.MessageBox(_("Unable to print the document"))
    #===========================================================================
    # actionDocToGo :start the doc to go wizard
    #===========================================================================
    def actionDocToGo(self,event):
        if isinstance(event,list) :
            rows = event
        else:
            rows = self.recordPart.getRow()
        if rows is None or len(rows)<1 :
            rows = self.docList
        docToGo = documentToGo.DocToGoWizard(self,self.docList,rows, isinstance(event,list))
        docToGo.RunWizard(docToGo.page_chooser)
        self.actionSearch(None)
    #===========================================================================
    # actionAbout : show the about dialog box
    #===========================================================================
    def actionAbout(self,event):
        description = """MALODOS (for MAnagement of LOcal DOcument System) is a simple but useful \
software aimed to help the process of archiving and navigate between the documents presents \
in your hard-drive.
It is written in python and mainly merges numerous external libraries to \
give a fast and simple way to scan and numerically record your personal documents (such \
as invoices, taxes declaration, etc...).
Being written in python, it is portable (works on windows and linux at least, not tested \
on other systems).

The complete documentation can be found here : http://sites.google.com/site/malodospage/
The latest version can be downloaded from here : http://code.google.com/p/malodos/
If you like and use this software, please consider to donate to support its development.

The author would like to thanks Christophe Terpreau, Bill Peters and Yves SAINT-GERARD for their very useful feedbacks \
which are helping me debugging and improving the MALODOS.
"""

        licence = """MALODOS is free software; you can redistribute it and/or modify it 
under the terms of the GNU General Public License as published by the Free Software Foundation; 
either version 3 of the License, or (at your option) any later version.

MALODOS is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; 
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  
See the GNU General Public License for more details. You should have received a copy of 
the GNU General Public License along with File Hunter; if not, write to 
the Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA"""


        info = wx.AboutDialogInfo()

        info.SetIcon(wx.Icon(Resources.get_icon_filename('APPLICATION'), wx.BITMAP_TYPE_PNG))
        info.SetName('MALODOS')
        info.SetVersion(__version__)
        info.SetDescription(description)
        info.SetCopyright('(C) 2010 David GUEZ')
        info.SetWebSite('http://sites.google.com/site/malodospage')
        info.AddArtist('http://icones.pro')
        info.SetLicence(licence)
        wx.AboutBox(info)
    def actionSupport(self,event):
        webbrowser.open('https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=D7H33JFSFA98J&lc=IL&item_name=David%20GUEZ&item_number=MALODOS&currency_code=ILS&bn=PP%2dDonationsBF%3abtn_donateCC_LG%2egif%3aNonHosted')
    def actionReport(self,event):
            theBugReport = bugReportWindow(self)
            theBugReport.ShowModal()
