'''
Created on 21 juin 2010. Copyright 2010, David GUEZ
@author: david guez (guezdav@gmail.com)
This file is a part of the source code of the MALODOS project.
You can use and distribute it freely, but have to conform to the license
attached to this project (LICENSE.txt file)
=====================================================================
GUI dialog for documents survey
'''

import wx
from . import docWindow
from . import RecordWidget
import database
import os.path
import data
from algorithms.general import str_to_bool
import algorithms.stringFunctions
import hashlib
from database import theConfig
import gui.utilities
import logging
class SurveyWindow(wx.Dialog):
    '''
    classdocs
    '''
# ****************************************************
# ****    abstract base for any content tab       ****
# ****    ---------------------------------       ****
# ****************************************************
    class Content(wx.NotebookPage):
        def __init__(self,parent,baseWin,tabName):
            wx.NotebookPage.__init__(self,parent,-1,name=tabName)
            self.baseWin=baseWin
            self.panel = wx.Panel(self, -1)
        def populate(self):
            raise NotImplementedError("populate method must be implemented")
        #self.prefSizer.Add(self.tabFrame,(1,0),span=(1,3),flag=wx.EXPAND|wx.ALL)
# ******************************************
# ****    tab for files not in DB       ****
# ****    -----------------------       ****
# ******************************************
    class SurveyContent(Content):
        def __init__(self,parent,baseWin):
            SurveyWindow.Content.__init__(self,parent,baseWin,_("Directory survey"))
            self.sizer = wx.BoxSizer(wx.VERTICAL)
            self.docList = wx.TreeCtrl(self.panel,-1,style=wx.TR_DEFAULT_STYLE|wx.TR_HIDE_ROOT|wx.TR_FULL_ROW_HIGHLIGHT)
            self.sizer.Add(self.docList,1,flag=wx.ALL|wx.EXPAND|wx.GROW)
            self.panel.SetSizerAndFit(self.sizer)
            self.Bind(wx.EVT_TREE_SEL_CHANGED,self.actionDocSelect,self.docList)
        def populate(self):
            accepted_ext = database.theConfig.get_survey_extension_list()
            accepted_ext = [ '.' + i.lower() for i in accepted_ext.split(' ') ]
            rootItem = None
            def append_dir(rootDir,dr,file_list):
                cur = database.theBase.get_files_under(dr)
                presents = set( (os.path.basename(str(row[0])) for row in cur ) )
                dir_list = set(f for f in file_list if os.path.isdir(os.path.join(dr,f)))
                file_list = set(f for f in file_list if not os.path.isdir(os.path.join(dr,f)) and os.path.splitext(f)[1].lower() in accepted_ext)
                file_list = file_list - presents
                #if len(file_list)<1 : return
                relPath = os.path.relpath(dr, rootDir)
                if relPath == '.' :
                    currentItem = self.docList.AppendItem(self.docList.GetRootItem() , rootDir ,data=wx.TreeItemData(rootDir))
                else:
                    dir_comp = relPath.split(os.path.sep)
                    currentItem = rootItem
                    (currentItem,__) = self.docList.GetFirstChild(currentItem)
                    while currentItem and (self.docList.GetPyData(currentItem) != rootDir) :
                            currentItem = self.docList.GetNextSibling(currentItem)
                    for depth in range(len(dir_comp)):
                        searchedItem = dir_comp[depth]
                        if currentItem : (currentItem,__) = self.docList.GetFirstChild(currentItem)
                        while currentItem and (self.docList.GetPyData(currentItem) != searchedItem) :
                            currentItem = self.docList.GetNextSibling(currentItem)
                        if not currentItem : break
                    
                if not currentItem :
                    logging.error( 'problem for ' , relPath)
                    return
                for f in dir_list:
                    fname = os.path.join(dr,f)
                    self.docList.AppendItem(currentItem,f,data=wx.TreeItemData(f))
                for f in file_list:
                    fname = os.path.join(dr,f)
                    self.docList.AppendItem(currentItem,f,data=wx.TreeItemData('*'+fname))
            
            self.docList.DeleteAllItems() #self.docList.Clear()# 
            rootItem = self.docList.AddRoot(_('Files not in the database'),data=wx.TreeItemData("root"))
            (dir_list,recursiveIdx) = database.theConfig.get_survey_directory_list()
            for i in range(len(dir_list)):
                dname = dir_list[i]
                if i in recursiveIdx:
                    try:
                        for walk_root, __dirs, files in os.walk(dname):
                            append_dir(dname, walk_root, files)
                    except Exception as E:
                        logging.exception('Problem to survey path:'+dname+"=>"+str(E))
                        continue
                else:
                    append_dir(dname, dir_list[i], os.listdir(dir_list[i]))
            self.docList.ExpandAll()
        def actionDocSelect(self,event):
            sel = self.docList.GetSelection()
            if sel :
                fname = self.docList.GetPyData(sel)
                if fname[0]=='*' :
                    fname=fname[1:]
                else:
                    return
            else:
                return
            #fname = self.docList.GetClientData(sel)
            #if not fname : return
            self.baseWin.recordPart.clear_all()
            self.baseWin.recordPart.SetFields(filename = fname,doOCR=str_to_bool( database.theConfig.get_param('OCR', 'autoStart','1') ),selectedList=[],title='',description='',tags='')
            try:
                data.theData.load_file(fname)
                self.baseWin.docWin.resetView()
                self.baseWin.docWin.showCurrentImage()
                self.baseWin.SetModeAdd()
            except:
                data.theData.clear_all()
# ******************************************
# ****    tab for OCR content missing   ****
# ****    ---------------------------   ****
# ******************************************
    class MissOCRContent(Content):
        def __init__(self,parent,baseWin):
            SurveyWindow.Content.__init__(self,parent,baseWin,_("Missing OCR"))
            self.sizer = wx.GridBagSizer(1,1)
            self.docList = wx.ListBox(self.panel,-1,style=wx.LB_SORT|wx.LB_MULTIPLE)
            self.btFixSel = wx.Button(self.panel,-1,_("Fix selected"))
            self.btFixAll = wx.Button(self.panel,-1,_("Fix All"))
            self.sizer.Add(self.docList,(0,0),span=(1,3),flag=wx.ALL|wx.EXPAND|wx.GROW)
            self.sizer.Add(self.btFixSel,(1,0),flag=wx.ALL|wx.EXPAND|wx.GROW)
            self.sizer.Add(self.btFixAll,(1,1),flag=wx.ALL|wx.EXPAND|wx.GROW)
            self.sizer.AddGrowableRow(0)
            self.sizer.AddGrowableCol(2)
            self.panel.SetSizerAndFit(self.sizer)
            self.Bind(wx.EVT_LISTBOX,self.actionDocSelect,self.docList)
            self.Bind(wx.EVT_BUTTON,self.action_OCR_for_selection,self.btFixSel)
            self.Bind(wx.EVT_BUTTON,self.action_OCR_for_all,self.btFixAll)
        def actionDocSelect(self,event):
            sel = self.docList.GetSelections()
            if len(sel)!=1 : return
            sel=sel[0]
            if sel is None : return
            row = self.docList.GetClientData(sel)
            
            docID = row[database.theBase.IDX_ROWID]
            filename = row[database.theBase.IDX_FILENAME]
            title = row[database.theBase.IDX_TITLE]
            description = row[database.theBase.IDX_DESCRIPTION]
            documentDate = row[database.theBase.IDX_DOCUMENT_DATE]
            tags = row[database.theBase.IDX_TAGS]
            self.baseWin.recordPart.SetFields(filename, title, description, documentDate,tags,True)
            try:
                data.theData.load_file(filename)
                self.baseWin.docWin.resetView()
                self.baseWin.docWin.showCurrentImage()
                self.baseWin.SetModeUpdate(docID)
            except:
                data.theData.clear_all()
        def populate(self):
            self.docList.Clear()
            docIDs = database.theBase.doc_without_ocr()
            for row in docIDs:
                self.docList.Append(row[database.theBase.IDX_TITLE] , row)
        def action_OCR_for_selection(self,event):
            self.do_OCR_for(self.docList.GetSelections())
        def action_OCR_for_all(self,event):
            self.do_OCR_for(list(range(self.docList.GetCount())))
        def do_OCR_for(self,selection):
            pd = gui.utilities.getGlobalProgressDialog(_('Character recognition'), '')
            pd.clear()
            n = len(selection)
            for sel in selection :
                pd.new_sub_step(1.0/n)
                row = self.docList.GetClientData(sel)
                docID = row[database.theBase.IDX_ROWID]
                filename = row[database.theBase.IDX_FILENAME]
                title = row[database.theBase.IDX_TITLE]
                description = row[database.theBase.IDX_DESCRIPTION]
                tags = row[database.theBase.IDX_TAGS]
                try:
                    imData = data.imageData.imageData()
                    imData.load_file(filename)
                    fullText = imData.get_content(False)
                except:
                    fullText = None
                finally:
                    pd.finish_current_step()
                #if fullText is None or len(fullText)==0 : fullText = {'NOTHING FOUND':1}
                # add the document to the database
                keywordsGroups = database.theBase.get_keywordsGroups_from(title, description, filename , tags, fullText)
                database.theBase.update_keywords_for(docID, keywordsGroups, True)
                
            self.populate()

# ******************************************
# ****    tab for files missing         ****
# ****    ---------------------         ****
# ******************************************
    class FileProblemContent(Content):
        def __init__(self,parent,baseWin):
            SurveyWindow.Content.__init__(self,parent,baseWin,_("Removes/modified files"))
            self.sizer = wx.GridBagSizer(1,1)
            self.docList = wx.ListBox(self.panel,-1,style=wx.LB_SORT|wx.LB_MULTIPLE)
            self.btFixSel = wx.Button(self.panel,-1,_("Fix selected"))
            self.btFixAll = wx.Button(self.panel,-1,_("Fix All"))
            self.sizer.Add(self.docList,(0,0),span=(1,3),flag=wx.ALL|wx.EXPAND|wx.GROW)
            self.sizer.Add(self.btFixSel,(1,0),flag=wx.ALL|wx.EXPAND|wx.GROW)
            self.sizer.Add(self.btFixAll,(1,1),flag=wx.ALL|wx.EXPAND|wx.GROW)
            self.sizer.AddGrowableRow(0)
            self.sizer.AddGrowableCol(2)
            self.panel.SetSizerAndFit(self.sizer)
            self.Bind(wx.EVT_LISTBOX,self.actionDocSelect,self.docList)
            self.Bind(wx.EVT_BUTTON,self.actionFixSelection,self.btFixSel)
            self.Bind(wx.EVT_BUTTON,self.actionFixAll,self.btFixAll)
        def actionDocSelect(self,event):
            sel = self.docList.GetSelections()
            if len(sel)!=1 : return
            sel=sel[0]
            if sel is None : return
            row = self.docList.GetClientData(sel)
            
            docID = row[database.theBase.IDX_ROWID]
            filename = row[database.theBase.IDX_FILENAME]
            title = row[database.theBase.IDX_TITLE]
            description = row[database.theBase.IDX_DESCRIPTION]
            documentDate = row[database.theBase.IDX_DOCUMENT_DATE]
            tags = row[database.theBase.IDX_TAGS]
            folderID_list = database.theBase.folders_list_for(docID)
            md5_cs  = row[database.db.Base.IDX_CHECKSUM]
            if not os.path.exists(filename):
                filename = self.tryToFind(os.path.splitext(filename)[1],md5_cs)
            if filename is None : filename=''
            doOCR = str_to_bool(theConfig.get_param('OCR', 'autoStart','1'))
            self.baseWin.recordPart.SetFields(filename, title, description, documentDate,tags,doOCR,folderID_list)
            try:
                data.theData.load_file(filename)
                self.baseWin.docWin.resetView()
                self.baseWin.docWin.showCurrentImage()
                self.baseWin.SetModeUpdate(docID)
            except:
                data.theData.clear_all()
        def actionFixSelection(self,event):
            self.doFixFor(self.docList.GetSelections())
        def actionFixAll(self,event):
            self.doFixFor(list(range(self.docList.GetCount())))
        def tryToFind(self,filename,md5_cs):
            #return None
            (dir_list,recursiveIdx) = database.theConfig.get_survey_directory_list()
            for i in range(len(dir_list)):
                dname = dir_list[i]
                if i in recursiveIdx:
                    L=[]
                    LL = os.walk(dname)
                    if filename[0]=='.':
                        L.extend([os.path.join(x[0],y) for x in LL for y in x[2] if os.path.splitext(y)[1] == filename])
                    else:
                        L.extend([os.path.join(x[0],y) for x in LL for y in x[2] if y == filename])
                else:
                    LL = os.listdir(dname)
                    if filename[0]=='.':
                        L= [x for x in LL if os.path.splitext(x)[1]==filename]
                    else:
                        L= [x for x in LL if os.path.split(x)[1]==filename]
                candidates = []
                for iL in L:
                    #print iL
                    md = hashlib.md5(open(iL, "rb").read()).hexdigest()
                    if md == md5_cs : candidates.append(iL)
                if len(candidates)==1:
                    return candidates[0]
                else:
                    return None
        def doFixRow(self,row):
            docID = row[database.theBase.IDX_ROWID]
            filename = row[database.theBase.IDX_FILENAME]
            title = row[database.theBase.IDX_TITLE]
            description = row[database.theBase.IDX_DESCRIPTION]
            documentDate = row[database.theBase.IDX_DOCUMENT_DATE]
            tags = row[database.theBase.IDX_TAGS]
            md5_cs  = row[database.db.Base.IDX_CHECKSUM]
            folderIDList = database.theBase.folders_list_for(docID)
            if not os.path.exists(filename):
                filename = self.tryToFind(os.path.splitext(filename)[1],md5_cs)
                #filename = self.tryToFind(os.path.split(filename)[1],md5_cs)
                #print filename
                #return
                if filename is None :
                    database.theBase.remove_documents((docID,))
                else:
                    #print "updating with" + filename 
                    database.theBase.update_doc(docID, title, description, documentDate, filename, tags,folderID_list=folderIDList)
                return
            new_md5_cs = hashlib.md5(open(filename, "rb").read()).hexdigest()
            database.theBase.update_doc_signature(docID, new_md5_cs)
        def doFixFor(self,selection):
            for sel in selection :
                row = self.docList.GetClientData(sel)
                self.doFixRow(row)
            self.populate()
        def populate(self):
            self.docList.Clear()
            docLst = database.theBase.find_documents(None)
            #problems = [0]*len(docLst)
            for row in docLst:
                #row = docLst[i]
                md5_cs  = row[database.db.Base.IDX_CHECKSUM]
                filename    = row[database.db.Base.IDX_FILENAME]
                if not os.path.exists(filename):
                    #problems[i] = 1
                    self.docList.Append(row[database.theBase.IDX_TITLE] , row)
                    continue 
                md5_file = hashlib.md5(open(filename, "rb").read()).hexdigest()
                if md5_file != md5_cs :
                    #problems[i] = 2
                    self.docList.Append(row[database.theBase.IDX_TITLE] , row)

# ******************************************
# ****    tab for files missing         ****
# ****    ---------------------         ****
# ******************************************
    class PasswordProblemContent(Content):
        def __init__(self,parent,baseWin):
            if database.currentPassword=='' :
                SurveyWindow.Content.__init__(self,parent,baseWin,_("Encrypted files"))
            else:
                SurveyWindow.Content.__init__(self,parent,baseWin,_("Not encrypted files"))
            self.sizer = wx.GridBagSizer(1,1)
            self.docList = wx.ListBox(self.panel,-1,style=wx.LB_SORT|wx.LB_MULTIPLE)
            self.btFixSel = wx.Button(self.panel,-1,_("Fix selected"))
            self.btFixAll = wx.Button(self.panel,-1,_("Fix All"))
            self.sizer.Add(self.docList,(0,0),span=(1,3),flag=wx.ALL|wx.EXPAND|wx.GROW)
            self.sizer.Add(self.btFixSel,(1,0),flag=wx.ALL|wx.EXPAND|wx.GROW)
            self.sizer.Add(self.btFixAll,(1,1),flag=wx.ALL|wx.EXPAND|wx.GROW)
            self.sizer.AddGrowableRow(0)
            self.sizer.AddGrowableCol(2)
            self.panel.SetSizerAndFit(self.sizer)
            self.Bind(wx.EVT_LISTBOX,self.actionDocSelect,self.docList)
            self.Bind(wx.EVT_BUTTON,self.actionFixSelection,self.btFixSel)
            self.Bind(wx.EVT_BUTTON,self.actionFixAll,self.btFixAll) 

        def actionDocSelect(self,event):
            sel = self.docList.GetSelections()
            if len(sel)!=1 : return
            sel=sel[0]
            if sel is None : return
            row = self.docList.GetClientData(sel)
            
            docID = row[database.theBase.IDX_ROWID]
            filename = row[database.theBase.IDX_FILENAME]
            title = row[database.theBase.IDX_TITLE]
            description = row[database.theBase.IDX_DESCRIPTION]
            documentDate = row[database.theBase.IDX_DOCUMENT_DATE]
            tags = row[database.theBase.IDX_TAGS]
            folderID_list = database.theBase.folders_list_for(docID)
            md5_cs  = row[database.db.Base.IDX_CHECKSUM]
            if not os.path.exists(filename):
                filename = self.tryToFind(os.path.splitext(filename)[1],md5_cs)
            if filename is None : filename=''
            doOCR = str_to_bool(theConfig.get_param('OCR', 'autoStart','1'))
            self.baseWin.recordPart.SetFields(filename, title, description, documentDate,tags,doOCR,folderID_list)
            try:
                data.theData.load_file(filename)
                self.baseWin.docWin.resetView()
                self.baseWin.docWin.showCurrentImage()
                self.baseWin.SetModeUpdate(docID)
            except:
                data.theData.clear_all()
        def actionFixSelection(self,event):
            self.doFixFor(self.docList.GetSelections())
        def actionFixAll(self,event):
            self.doFixFor(list(range(self.docList.GetCount())))
        def tryToFind(self,filename,md5_cs):
            #return None
            (dir_list,recursiveIdx) = database.theConfig.get_survey_directory_list()
            for i in range(len(dir_list)):
                dname = dir_list[i]
                if i in recursiveIdx:
                    L=[]
                    LL = os.walk(dname)
                    if filename[0]=='.':
                        L.extend([os.path.join(x[0],y) for x in LL for y in x[2] if os.path.splitext(y)[1] == filename])
                    else:
                        L.extend([os.path.join(x[0],y) for x in LL for y in x[2] if y == filename])
                else:
                    LL = os.listdir(dname)
                    if filename[0]=='.':
                        L= [x for x in LL if os.path.splitext(x)[1]==filename]
                    else:
                        L= [x for x in LL if os.path.split(x)[1]==filename]
                candidates = []
                for iL in L:
                    #print iL
                    md = hashlib.md5(open(iL, "rb").read()).hexdigest()
                    if md == md5_cs : candidates.append(iL)
                if len(candidates)==1:
                    return candidates[0]
                else:
                    return None
        def doFixRow(self,row):
            docID = row[database.theBase.IDX_ROWID]
            filename = row[database.theBase.IDX_FILENAME]
            title = row[database.theBase.IDX_TITLE]
            description = row[database.theBase.IDX_DESCRIPTION]
            documentDate = row[database.theBase.IDX_DOCUMENT_DATE]
            tags = row[database.theBase.IDX_TAGS]
            md5_cs  = row[database.db.Base.IDX_CHECKSUM]
            folderIDList = database.theBase.folders_list_for(docID)
            if not os.path.exists(filename):
                filename = self.tryToFind(os.path.splitext(filename)[1],md5_cs)
                #filename = self.tryToFind(os.path.split(filename)[1],md5_cs)
                #print filename
                #return
                if filename is None :
                    database.theBase.remove_documents((docID,))
                else:
                    #print "updating with" + filename 
                    database.theBase.update_doc(docID, title, description, documentDate, filename, tags,folderID_list=folderIDList)
                return
            new_md5_cs = hashlib.md5(open(filename, "rb").read()).hexdigest()
            database.theBase.update_doc_signature(docID, new_md5_cs)
        def doFixFor(self,selection):
            for sel in selection :
                row = self.docList.GetClientData(sel)
                self.doFixRow(row)
            self.populate()
        def populate(self):
            pss = database.currentPassword
            
            self.docList.Clear()
            docLst = database.theBase.find_documents(None)
            #problems = [0]*len(docLst)
            for row in docLst:
                filename    = row[database.db.Base.IDX_FILENAME]
                problem=False
                if pss=="" and algorithms.stringFunctions.is_encrypted(filename)  : problem=True
                if pss!="" and not algorithms.stringFunctions.is_encrypted(filename) : problem=True
                if pss!="" and not algorithms.stringFunctions.is_good_password(filename,pss) : problem=True
                if problem : self.docList.Append(row[database.theBase.IDX_TITLE] , row)


    def __init__(self, parent):
        '''
        Constructor
        '''
        wx.Dialog.__init__(self, parent, -1, _('Survey directory'),style=wx.CLOSE_BOX | wx.SYSTEM_MENU | wx.CAPTION | wx.RESIZE_BORDER  | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX)
        self.panel = wx.Panel(self, -1)
        self.docViewSizer = wx.BoxSizer(wx.VERTICAL)
        self.upPart =  wx.BoxSizer(wx.HORIZONTAL)
        self.recordSizer =  wx.BoxSizer(wx.HORIZONTAL)
        self.moreAdd=None
        self.docID=None
        #self.docList = wx.TreeCtrl(self.panel,-1,style=wx.TR_DEFAULT_STYLE|wx.TR_HIDE_ROOT|wx.TR_FULL_ROW_HIGHLIGHT) #wx.ListBox(self.panel,-1)# 
        self.tabFrame = wx.Notebook(self.panel,-1)
        self.dirSurveyFrame = self.SurveyContent(self.tabFrame,self)
        self.missOCRFrame = self.MissOCRContent(self.tabFrame,self)
        self.passwordProblemFrame = self.PasswordProblemContent(self.tabFrame,self)
        self.fileProblemsFrame = self.FileProblemContent(self.tabFrame,self)
        self.tabFrame.AddPage(self.dirSurveyFrame,self.dirSurveyFrame.GetName())
        self.tabFrame.AddPage(self.missOCRFrame,self.missOCRFrame.GetName())
        self.tabFrame.AddPage(self.fileProblemsFrame,self.fileProblemsFrame.GetName())
        self.tabFrame.AddPage(self.passwordProblemFrame,self.passwordProblemFrame.GetName())
        #self.prefSizer.Add(self.tabFrame,(1,0),span=(1,3),flag=wx.EXPAND|wx.ALL)
        self.upPart.Add(self.tabFrame,1,wx.EXPAND)
        
        self.docWin = docWindow.docWindow(self.panel,-1)
        self.docViewSizer.Add(self.upPart,1,wx.EXPAND)
        #self.upPart.Add(self.docList,1,wx.EXPAND)
        self.upPart.Add(self.docWin,1,wx.EXPAND)
        
        self.recordPart = RecordWidget.RecordWidget(self.panel)
        self.recordPart.lbFileName.Disable()
        self.recordSizer.Add(self.recordPart,1,wx.EXPAND)
        self.btAddRecord = wx.Button(self.panel,-1,_('Add/Update'))
        self.docViewSizer.Add(self.recordSizer,0,wx.EXPAND)
        self.recordButtonSizer = wx.BoxSizer(wx.VERTICAL)
        self.recordButtonSizer.Add(self.btAddRecord,1,wx.EXPAND)
        self.recordSizer.Add(self.recordButtonSizer)
        self.panel.SetSizerAndFit(self.docViewSizer)

        #self.Bind(wx.EVT_TREE_SEL_CHANGED,self.actionDocSelect,self.docList)
        #self.docList.Bin(wx.EVT_TREE_SEL_CHANGED, handler)
        self.Bind(wx.EVT_BUTTON, self.actionDoAdd, self.btAddRecord)
        
        for ipage in range(self.tabFrame.GetPageCount()) : self.tabFrame.GetPage(ipage).populate()
#        self.dirSurveyFrame.populate()
#        self.missOCRFrame.populate()
#        self.fileProblemsFrame.populate()
        self.SetSizeWH(1000,600)
    #===========================================================================
    def SetModeAdd(self):
        self.btAddRecord.SetLabel(_('Add'))
        self.modeAdd=True
        self.docID=None
    #===========================================================================
    def SetModeUpdate(self,docID):
        self.btAddRecord.SetLabel(_('Update'))
        self.modeAdd=False
        self.docID=docID
    #===========================================================================
    # Click on Add document button
    #===========================================================================
    def actionDoAdd(self,event):
        if self.modeAdd is None: return
        if self.modeAdd :
            rep = self.recordPart.do_save_record()
        else:
            if self.docID is None : return
            rep = self.recordPart.update_record(self.docID)
        if not rep:
            wx.MessageBox(_('Unable to add/update the file to the database'))
        else:
            data.theData.clear_all()
            self.recordPart.clear_all()
            for ipage in range(self.tabFrame.GetPageCount()) : self.tabFrame.GetPage(ipage).populate()
            self.modeAdd=None