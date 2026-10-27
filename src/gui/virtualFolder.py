# -*- coding: utf-8 -*-
'''
Created on 21 juin 2010. Copyright 2010, David GUEZ
@author: david guez (guezdav@gmail.com)
This file is a part of the source code of the MALODOS project.
You can use and distribute it freely, but have to conform to the license
attached to this project (LICENSE.txt file)
=====================================================================
view / select / edit virtual folders
'''
import wx
import database
from . import utilities


class FolderView (wx.Panel):
    ID_ADD=1
    ID_RENAME=2
    ID_DELETE=3
    ID_SELECT=4
    def __init__(self, parent,selector=True,editor=True,selectedList=set(),selectionChangeCallBack=None):
        '''
        Constructor
        '''
        wx.Panel.__init__(self, parent, -1,style=wx.DEFAULT_FRAME_STYLE)
        self.editor=editor
        self.selector=selector
        self.totSizer = wx.GridBagSizer()
        self.treeView = wx.TreeCtrl(self,-1,style=wx.TR_DEFAULT_STYLE|wx.TR_FULL_ROW_HIGHLIGHT|wx.TR_EDIT_LABELS|wx.VSCROLL)
        self.treeView.SetMinSize((10,10))
        
        self.totSizer.Add(self.treeView,(0,0),span=(1,4),flag=wx.EXPAND)
        if editor:
            self.btAddChild=wx.Button(self,label=_('Add child'))
            self.btRename=wx.Button(self,label=_('Rename'))
            self.btRemove=wx.Button(self,label=_('Remove'))
            self.totSizer.Add(self.btAddChild,(1,0))
            self.totSizer.Add(self.btRename,(1,1))
            self.totSizer.Add(self.btRemove,(1,2))
        self.totSizer.AddGrowableCol(3)
        self.totSizer.AddGrowableRow(0)
        
        self.SetSizerAndFit(self.totSizer)
        self.selectedList=set(selectedList)
        self.fillDirectories()
        self.treeView.Bind(wx.EVT_TREE_ITEM_MENU,self.action_context_menu)
        self.treeView.Bind(wx.EVT_MENU,self.action_menu)
        self.selectionChangeCallBack=selectionChangeCallBack
        if editor :
            self.treeView.Bind(wx.EVT_TREE_BEGIN_DRAG,self.action_drag_drop_begin)
            self.treeView.Bind(wx.EVT_TREE_END_DRAG,self.action_drag_drop_end)
            self.treeView.Bind(wx.EVT_TREE_BEGIN_LABEL_EDIT,self.action_want_changed_label)
            self.treeView.Bind(wx.EVT_TREE_END_LABEL_EDIT,self.action_changed_label)
            self.Bind(wx.EVT_BUTTON,lambda x:self.action_add_subfolder(self.treeView.GetSelection()) , self.btAddChild )
            self.Bind(wx.EVT_BUTTON,lambda x:self.action_ren_subfolder(self.treeView.GetSelection()) , self.btRename )
            self.Bind(wx.EVT_BUTTON,lambda x:self.action_del_subfolder(self.treeView.GetSelection()) , self.btRemove )
        if selector:
            self.treeView.Bind(wx.EVT_TREE_ITEM_ACTIVATED,self.action_double_click)
    def set_selectionChangeCallBack(self,selectionChangeCallBack=None):
        self.selectionChangeCallBack=selectionChangeCallBack
    def action_menu(self,event):
        item = self.itemMenu
        action = event.GetId()
        if action == self.ID_SELECT:
            self.action_double_click(event, self.itemMenu)
        elif action == self.ID_RENAME:
            self.treeView.EditLabel(item)
        elif action == self.ID_DELETE:
            self.action_del_subfolder(item)
        elif action == self.ID_ADD:
            self.action_add_subfolder(item)
    def action_want_changed_label(self,event):
        item = self.treeView.GetPyData(event.GetItem())
        if item==0 : event.Veto()
    def notify_selection(self):
        if self.selectionChangeCallBack is None : return
        self.selectionChangeCallBack(self.selectedList)
    def action_changed_label(self,event):
        if event.IsEditCancelled(): return
        itemID = self.treeView.GetPyData(event.GetItem())
        if itemID==0 : return
        newName = event.GetLabel()
        database.theBase.folders_rename(itemID,newName)
        self.notify_selection()
        
    def action_context_menu(self,event):
        self.itemMenu = event.GetItem()
        menu = wx.Menu()
        if self.selector:
            menu.Append(self.ID_SELECT,_('select'))
        if self.editor :
            menu.Append(self.ID_ADD,_('add sub-menu'))
            if self.treeView.GetPyData(self.itemMenu) != 0:
                menu.Append(self.ID_RENAME,_('rename'))
                menu.Append(self.ID_DELETE,_('delete'))
        self.treeView.PopupMenu(menu)

    def action_double_click(self,event,item=None):
        if item is None : item = event.GetItem()
        folderID = self.treeView.GetPyData(item)
        if folderID in self.selectedList:
            self.treeView.SetItemBold(item,False)
            self.selectedList.remove(folderID)
        else:
            self.treeView.SetItemBold(item,True)
            self.selectedList.add(folderID)
        self.notify_selection()
    def action_drag_drop_begin(self,event):
        self.dragedItem = event.GetItem() 
        event.Allow()
    def action_drag_drop_end(self,event):
        if self.dragedItem == event.GetItem() : return
        oldItem = self.treeView.GetItemText(self.dragedItem)
        newItem = self.treeView.GetItemText(event.GetItem())
        if not  utilities.ask(_('Do you really want to move the folder {src} and all its content under the folder {dst} ?').format(src=oldItem,dst=newItem)) : return
        iniFolderID = self.treeView.GetPyData(self.dragedItem)
        dstFolderID = self.treeView.GetPyData(event.GetItem())
        if not database.theBase.folders_change_parent(iniFolderID,dstFolderID):
            utilities.show_message(_('Unable to move the folder {src} under {dst}').format(src=oldItem,dst=newItem))
        else:
            self.fillDirectories()
            self.notify_selection()
    def fillDirectories(self):
        def fillUnder(itemID):
            addedItems = []
            folderID = self.treeView.GetPyData(itemID)
            if database.theBase is None : return
            descendants = database.theBase.folders_childs_of(folderID)
            for row in descendants:
                idt = row[0]
                name = row[1]
                item = self.treeView.AppendItem(itemID,name,data=wx.TreeItemData(idt))
                if idt in self.selectedList : self.treeView.SetItemBold(item)
                addedItems.append(item)
            for item in addedItems : fillUnder(item)
        self.treeView.DeleteAllItems()
        itemID = self.treeView.AddRoot(_('ROOT'),data=wx.TreeItemData(0))
        fillUnder(itemID)
        self.treeView.ExpandAll()
    def setSelectedList(self,selectedList):
        self.selectedList=set(selectedList)
        self.fillDirectories()
    def getSelectedList(self):
        return self.selectedList
    def action_add_subfolder(self,item):
        name = utilities.ask_string(_('name :'),_('Give a sub-folder name'),_('folder'))
        folderID = self.treeView.GetPyData(item)
        if database.theBase.folders_add_child_under(name,folderID):
            self.fillDirectories()
            self.notify_selection()
        else:
            utilities.show_message(_('unable to add the sub-folder {0}').format(name))
    def action_del_subfolder(self,item):
        folderID = self.treeView.GetPyData(item)
        folderName = self.treeView.GetItemText(item)
        if utilities.ask(_('Are you sure that you want to delete the folder {0}'.format(folderName))):
            if database.theBase.folders_remove(folderID):
                self.fillDirectories()
                self.notify_selection()
            else:
                utilities.show_message(_('unable to remove the sub-folder {0}').format(folderName))
    def action_ren_subfolder(self,item):
        folderID = self.treeView.GetPyData(item)
        folderName = self.treeView.GetItemText(item)
        name = utilities.ask_string(_('name :'),_('Give a sub-folder name'),folderName)
        if name=='' : return
        if utilities.ask(_('Are you sure that you want to rename folder "{iniName}" to "{newName}"'.format(iniName=folderName,newName=name))):
            if database.theBase.folders_rename(folderID,name):
                self.fillDirectories()
                self.notify_selection()
            else:
                utilities.show_message(_('unable to remove the subfolder {0}').format(folderName))