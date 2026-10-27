'''
Created on 21 juin 2010. Copyright 2010, David GUEZ
@author: david guez (guezdav@gmail.com)
This file is a part of the source code of the MALODOS project.
You can use and distribute it freely, but have to conform to the license
attached to this project (LICENSE.txt file)
=====================================================================
GUI dialog for building a search request
'''

import wx
import wx.richtext as rt
import logging
from . import utilities

operators=((_('and'),'and'),(_('or'),'or'),(_('or (exclusive)'),'xor'))
fields=((_('any field'),'any'),(_('title'),'title'),(_('description'),'description'),(_('tags'),'tags'),(_('fulltext'),'fulltext'),(_('document date'),'date'),(_('Registering date'),'RegisterDate'))
conditions_text=((_('sounds like'),'={0}'),(_('spells exactly'),"='{0}'"))
conditions_date=((_('is on'),'={0}'),(_('is before'),'<{0}'),(_('is on or before'),'<={0}'),(_('is after'),'>{0}'),(_('is on or after'),'>={0}'))

class condition:
    operator=None
    field=None
    cond_type=None
    criteria=None
    wholeWord=None
    def __init__(self,operator,field,cond_type,criteria,wholeWord):
        self.operator=operator
        self.field=field
        self.cond_type=cond_type
        self.criteria=criteria
        self.wholeWord=wholeWord
    def to_human(self,isfirst):
        if not isfirst and self.operator is not None:
            txt = operators[self.operator][0]+' '
        else:
            txt=''
        txt += fields[self.field][0] + ' '
        if self.field<4 :
            txt += conditions_text[self.cond_type][0]
        else:
            txt += conditions_date[self.cond_type][0]
        txt += ' ' + str(self.criteria)
        if self.wholeWord is not None  and self.wholeWord : txt += ' (whole word)'
        return txt
    def to_request(self,isfirst):
        if not isfirst and self.operator is not None:
            txt = ' '+operators[self.operator][1]+' '
        else:
            txt=''
        txt += fields[self.field][1] +' '
        if self.field<4 :
            txt += conditions_text[self.cond_type][1]
        else:
            txt += conditions_date[self.cond_type][1]
        if self.wholeWord is not None  and self.wholeWord :
            txt = txt.format('!'+str(self.criteria))
        else:
            txt = txt.format(str(self.criteria))
        return txt
        
class condition_list:
    conditions=[]
    operator=None
    def __init__(self,operator=None,v=[]):
        self.operator=operator
        self.conditions=v[:]
    def get_condition(self,levels):
        if len(levels)<1 : return self
        l=levels[0]
        if l==-1 : return self
        if l>=len(self.conditions) : return None
        x = self.conditions[l]
        if len(levels)==1 : return x
        levels = levels[1:]
        if not isinstance(x,condition_list) : return None
        return x.get_condition(levels)
    def get_number_sub_conditions(self,levels):
        c = self.get_condition(levels)
        if c is None : return 0
        if isinstance(c, condition_list) :
            return len(c.conditions)
        else:
            return 0
    def append(self,cond,levels):
        if len(levels)<1 :
            self.conditions.append(cond)
            return
        l=levels[0]
        if l>len(self.conditions) : return None
        if len(levels)==1:
            self.conditions.insert(l+1,cond)
            return
        x = self.conditions[l]
        levels = levels[1:]
        if not isinstance(x,condition_list) : return None
        return x.append(cond,levels)
    def delete(self,levels):
        if len(levels)<1 : return
        l=levels[0]
        if l>=len(self.conditions) : return None
        if len(levels)==1:
            if l<len(self.conditions) :
                del self.conditions[l]
            return
        x = self.conditions[l]
        levels = levels[1:]
        if not isinstance(x,condition_list) : return None
        return x.delete(levels)
    def is_empty_group(self,levels):
        return self.get_condition(levels) is None
    def set_condition(self,cond,levels):
        if len(levels)<1 : return
        l=levels[0]
        if l>=len(self.conditions) : return
        if len(levels)==1 : self.conditions[l] = cond
        x = self.conditions[l]
        levels = levels[1:]
        if not isinstance(x,condition_list) : return None
        return x.set_condition(cond,levels)
    def __len__(self):
        return len(self.conditions)
        

class builderConditionPanel(wx.Panel):
    cond = None
    def __init__(self,builderDialog,isFirstCondition,operator=None,field=None,condType=None,wholeWord=None,criteria=None):
        #wx.Dialog.__init__(self,builderDialog)
        wx.Panel.__init__(self,builderDialog)
        self.isFirstCondition=isFirstCondition

        self.totSizer = wx.GridBagSizer(4,2)
        
        if not self.isFirstCondition:
            self.cbOperator = wx.ComboBox(self,choices=[x[0] for x in operators])
            if operator is None : 
                self.cbOperator.Selection=0
            else:
                self.cbOperator.Selection=operator
        
        self.cbField = wx.ComboBox(self,choices=[x[0] for x in fields])
        if field is None:
            self.cbField.Selection=0
        else:
            self.cbField.Selection=field
        self.cbCondType = wx.ComboBox(self,choices=[x[0] for x in conditions_text])
        if condType is None:
            self.cbCondType.Selection=0
        else:
            self.cbCondType.Selection=condType
        self.tcCondText = wx.TextCtrl(self)
        try:
            if criteria is not None : self.tcCondText.SetValue(criteria)
        except:
            pass
        self.chbWholeWord = wx.CheckBox(self,label=_('Whole word'))
        if wholeWord is None:
            self.chbWholeWord.Value=False
        else:
            self.chbWholeWord.Value=wholeWord
        self.dcCondDate = wx.DatePickerCtrl(self)
        try:
            if criteria is not None : self.dcCondDate.SetValue(criteria)
        except:
            pass
        #self.dcCondDate.Hide()
        self.btOk = wx.Button(self,-1,_('Ok'))
        self.btCancel = wx.Button(self,-1,_('Cancel'))
        
        l=0
        if not self.isFirstCondition:
            self.totSizer.Add(wx.StaticText(self,label=_('How to link the condition with the previous one in the current group')) , pos=(l,0),span=(1,5),flag=wx.EXPAND)
            self.totSizer.Add(self.cbOperator, pos=(l+1,0),span=(1,5),flag=wx.EXPAND)
            l+=2
        self.totSizer.Add(wx.StaticText(self,label=_('Field on which the condition apply')) , pos=(l,0),span=(1,5),flag=wx.EXPAND)
        self.totSizer.Add(self.cbField, pos=(l+1,0),span=(1,5),flag=wx.EXPAND)
        l+=2
        self.totSizer.Add(wx.StaticText(self,label=_('Condition type')) , pos=(l,0),span=(1,5),flag=wx.EXPAND)
        self.totSizer.Add(self.cbCondType, pos=(l+1,0),span=(1,5),flag=wx.EXPAND)
        l+=2
        self.totSizer.Add(wx.StaticText(self,label=_('Condition')) , pos=(l,0),span=(1,5),flag=wx.EXPAND)
        self.totSizer.Add(self.tcCondText, pos=(l+1,0),span=(1,4),flag=wx.EXPAND)
        self.totSizer.Add(self.chbWholeWord, pos=(l+1,4),span=(1,1),flag=wx.EXPAND)
        l+=2
        self.totSizer.Add(self.dcCondDate, pos=(l,0),span=(1,5),flag=wx.EXPAND)
        self.totSizer.Add(self.btOk, pos=(l+1,3),span=(1,1),flag=wx.EXPAND)
        self.totSizer.Add(self.btCancel, pos=(l+1,4),span=(1,1),flag=wx.EXPAND)
        l+=2
        
        #self.Bind(wx.EVT_BUTTON, lambda e : self.Close(), self.btCancel)
        #self.Bind(wx.EVT_BUTTON, self.action_ok, self.btOk)
        self.Bind(wx.EVT_COMBOBOX,self.action_change_field,self.cbField)
        self.Bind(wx.EVT_SIZE,self.action_resize)
        self.totSizer.AddGrowableCol(0)
        
        self.SetSizerAndFit(self.totSizer)
        self.totSizer.Fit(self)
        self.cbField.SetSelection(0)
        self.action_change_field(None)
    def action_resize(self,event):
        self.SetSize(event.Size)
        self.Layout()
    def action_ok(self,event):
        if self.isFirstCondition:
            c_operator=None
        else:
            c_operator=self.cbOperator.GetSelection()
        c_field = self.cbField.GetSelection()
        c_cond_type = self.cbCondType.GetSelection()
        if self.cbField.Selection < 5 :
            c_criteria = self.tcCondText.Value
            c_wholeWord = self.chbWholeWord.Value
        else:
            c_criteria = self.dcCondDate.Value.Format('%d-%m-%Y')
            c_wholeWord = None
        self.cond=condition(c_operator,c_field,c_cond_type,c_criteria,c_wholeWord)
        self.Close()
    def action_change_field(self,event):
        if self.cbField.Selection < 5 :
            self.tcCondText.Show()
            self.chbWholeWord.Show()
            self.dcCondDate.Hide()
            self.cbCondType.SetItems([x[0] for x in conditions_text])
        else:
            self.tcCondText.Hide()
            self.chbWholeWord.Hide()
            self.dcCondDate.Show()
            self.cbCondType.SetItems([x[0] for x in conditions_date])
        self.cbCondType.SetSelection(0)

class builderConditionDialog(wx.Dialog):
    def __init__(self,builderDialog,isFirstCondition,operator=None,field=None,condType=None,wholeWord=None,criteria=None):
        wx.Dialog.__init__(self,builderDialog,-1, _('Defining a condition'), style=wx.CLOSE_BOX | wx.SYSTEM_MENU | wx.CAPTION | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX)
        self.winCond = builderConditionPanel(self,isFirstCondition,operator,field,condType,wholeWord,criteria)
        self.totSizer=wx.BoxSizer(wx.HORIZONTAL)
        self.totSizer.Add(self.winCond,flag=wx.EXPAND|wx.ALL|wx.GROW)
        self.SetSizerAndFit(self.totSizer)

        self.Bind(wx.EVT_BUTTON, lambda e : self.Close(), self.winCond.btCancel)
        self.Bind(wx.EVT_BUTTON, self.action_ok, self.winCond.btOk)
        self.SetSize((600,260))
        self.totSizer.Fit(self)
    def action_ok(self,event):
        self.winCond.action_ok(None)
        self.Close()


class builderConditionPage(wx.NotebookPage):
    def __init__(self,parent,builder):
        wx.NotebookPage.__init__(self,parent)
        self.builder=builder
        self.winCond = builderConditionPanel(self,True)
        self.totSizer=wx.BoxSizer(wx.HORIZONTAL)
        self.totSizer.Add(self.winCond,flag=wx.EXPAND|wx.ALL|wx.GROW)
        self.SetSizerAndFit(self.totSizer)

        self.Bind(wx.EVT_BUTTON, lambda e : self.builder.Close(), self.winCond.btCancel)
        self.Bind(wx.EVT_BUTTON, self.action_ok, self.winCond.btOk)
#        self.SetSize((600,260))
#        self.totSizer.Fit(self)
    def action_ok(self,event):
        self.winCond.action_ok(None)
        self.builder.request = self.winCond.cond.to_request(True)
        self.builder.Close()



class builderPage(wx.NotebookPage):
    '''
    GUI dialog for addition of a file into the database
    '''


    #===========================================================================
    # constructor (building gui)
    #===========================================================================
    conditions=condition_list()
    def __init__(self,parent,builder):
        '''
        Constructor
        '''
        
        wx.NotebookPage.__init__(self, parent)
        self.builder=builder
        self.panel = wx.Panel(self, -1)
        self.totSizer = wx.GridBagSizer(4,2)
        
        explanations = _('In the following, enter the list of restriction defining your search request\n')
        explanations += _('Every element is clickable\n')
        explanations += _('Click on a condition to change it\n')
        explanations += _('Click on the + button to add another condition after the corresponding line\n')
        explanations += _('Click on the [+] button to add another group of conditions after the corresponding line\n')
        explanations += _('Click on the - button to remove the condition on the corresponding line\n')
        explanations += _('Click on the [-] button to remove the group of conditions for the corresponding line')
        self.totSizer.Add(wx.StaticText(self.panel,-1,explanations,style=wx.TE_MULTILINE),(0,0),span=(1,4),flag=wx.ALIGN_TOP|wx.EXPAND)
        self.rtHuman     = rt.RichTextCtrl(self.panel,-1,style=wx.TE_AUTO_URL)
        self.rtHuman.SetEditable(False)
        self.rtHuman.GetCaret().Hide()
        self.requestPreview=wx.StaticText(self.panel,-1,'',style=wx.TE_MULTILINE)
        self.btOk = wx.Button(self.panel,-1,_('Ok'))
        self.btCancel = wx.Button(self.panel,-1,_('Cancel'))
      
        self.totSizer.Add(self.rtHuman,(1,0),span=(1,4),flag=wx.EXPAND)
        self.totSizer.Add(self.requestPreview,(2,0),span=(1,4),flag=wx.ALIGN_TOP|wx.EXPAND)
        self.totSizer.Add(self.btOk, pos=(3,0),span=(1,1),flag=wx.ALIGN_RIGHT)
        self.totSizer.Add(self.btCancel, pos=(3,1),span=(1,1),flag=wx.ALIGN_LEFT)
        
        self.totSizer.AddGrowableCol(2)
        self.totSizer.AddGrowableRow(1)
        
        self.conditions=condition_list()
        self.generateHuman()

        self.panel.SetSizer(self.totSizer)
#        self.totSizer.Fit(self)
#        self.SetSize((600,350))
        
        self.Bind(wx.EVT_BUTTON, lambda e : self.builder.Close(), self.btOk)
        self.Bind(wx.EVT_BUTTON, self.action_cancel, self.btCancel)

        self.rtHuman.Bind(wx.EVT_TEXT_URL,self.onURLclick)
    def action_cancel(self,event):
        self.builder.request=''
        self.builder.Close()
    def onURLclick(self,event):
        #print "Condition : "+event.GetString()
        x = event.GetString().split('/')
        x[0] = x[0][1:-1]
        try:
            if x[0]=='' :
                levels=[]
            else:
                levels = [int(v) for v in x[0].split(',')]
            command=x[1]
        except Exception as E:
            logging.debug('Request builderPage error ' + str(E))
            return
        
        if command=="*":
            cond = self.conditions.get_condition(levels)
            if isinstance(cond,condition_list) :
                bc = builderConditionDialog(self,True)
                bc.ShowModal()
                if bc.winCond.cond is not None :
                    self.conditions.append(bc.winCond.cond,levels)
                self.generateHuman()
                self.generateRequest()
                return
            if not isinstance(cond,condition) : return
            bc = builderConditionDialog(self,False,cond.operator,cond.field,cond.cond_type,cond.wholeWord,cond.criteria)
            bc.ShowModal()
            if bc.winCond.cond is not None :
                self.conditions.set_condition(bc.winCond.cond,levels)
        elif command=="-":
            if self.conditions.is_empty_group(levels): return # can't remove the 'all documents' line
            self.conditions.delete(levels)
        elif command=="+":
            bc = builderConditionDialog(self,False)
            bc.ShowModal()
            if bc.winCond.cond is not None :
                self.conditions.append(bc.winCond.cond,levels)
        elif command=='[+]':
            op=utilities.multichoice([x[0] for x  in operators], _('How to link the condition group with the previous one'))
            cl=condition_list(op)
            self.conditions.append(cl,levels)
        elif command=='[-]':
            if not  utilities.ask(_('Do you want to remove all the conditions from this list ?')) : return
            self.conditions.delete(levels)
        self.generateHuman()
        self.generateRequest()
        
    def generateHuman(self):
        urlStyle = rt.TextAttrEx()
        urlStyle.SetTextColour(wx.BLUE)
        def write_commands(level):
            levelStr=str(level)
            self.rtHuman.WriteText('   ')
            self.rtHuman.BeginURL(levelStr+'/+')
            self.rtHuman.WriteText('+')
            self.rtHuman.EndURL()
            self.rtHuman.WriteText('   ')
            self.rtHuman.BeginURL(levelStr+'/[+]')
            self.rtHuman.WriteText('[+]')
            self.rtHuman.EndURL()
            self.rtHuman.WriteText('   ')
            l = self.conditions.get_condition(level)
            if isinstance(l,condition):
                self.rtHuman.BeginURL(levelStr+'/-')
                self.rtHuman.WriteText('-')
                self.rtHuman.EndURL()
            elif isinstance(l,condition_list):
                self.rtHuman.BeginURL(levelStr+'/[-]')
                self.rtHuman.WriteText('[-]')
                self.rtHuman.EndURL()
        def write_list_at_indent(levels):
            n = self.conditions.get_number_sub_conditions(levels)
            l=levels[:]
            l.append(-1)
            prefix=' '*3*len(levels)
            if n==0 :
                self.rtHuman.BeginStyle(urlStyle)
                self.rtHuman.BeginURL(str(l)+"/*")
                self.rtHuman.WriteText(prefix+_('Please add at least one condition'))
                self.rtHuman.Newline()
                self.rtHuman.EndURL()
                self.rtHuman.EndStyle()
                
            for icond in range(n):
                l[-1] = icond
                cond=self.conditions.get_condition(l)
                if isinstance(cond,condition_list):
                    if cond.operator is not None:
                        self.rtHuman.BeginURL(str(l)+"/*")
                        self.rtHuman.WriteText(prefix+operators[cond.operator][0])
                        self.rtHuman.EndURL()
                        write_commands(l)
                        self.rtHuman.Newline()
                    write_list_at_indent(l)
                else:
                    txt = cond.to_human(icond==0)
                    self.rtHuman.BeginURL(str(l)+"/*")
                    self.rtHuman.WriteText(prefix+txt)
                    self.rtHuman.EndURL()
                    write_commands(l)
                    self.rtHuman.Newline()
                    self.rtHuman.EndStyle()
        self.rtHuman.Clear()
        write_list_at_indent([])
            
        
    def generateRequest(self):
        def write_list_at_indent(levels):
            n = self.conditions.get_number_sub_conditions(levels)
            l=levels[:]
            l.append(-1)
            for icond in range(n):
                l[-1] = icond
                cond=self.conditions.get_condition(l)
                if isinstance(cond,condition_list):
                    if cond.operator is not None:
                        self.builder.request += ' ' + operators[cond.operator][1]+' '
                    self.builder.request += ' ('
                    write_list_at_indent(l)
                    self.builder.request += ')'
                else:
                    txt = cond.to_request(icond==0)
                    self.builder.request += txt
        self.builder.request=''
        write_list_at_indent([])
        self.requestPreview.SetLabel(self.builder.request)

class builder(wx.Dialog):
    request=None
    def __init__(self,parent):
        wx.Dialog.__init__(self,parent,style=wx.DEFAULT_DIALOG_STYLE| wx.RESIZE_BORDER)
        self.panel = wx.Panel(self,-1)
        self.totSizer=wx.BoxSizer(wx.HORIZONTAL)
        
        self.Pane = wx.Notebook(self.panel,-1)
        self.simplePage = builderConditionPage(self.Pane,self)
        self.advancedPage = builderPage(self.Pane,self)
        self.Pane.AddPage(self.simplePage,_('Simple request'))
        self.Pane.AddPage(self.advancedPage,_('Advanced request'))
        
        self.totSizer.Add(self.Pane,1,wx.GROW|wx.EXPAND|wx.ALL)
        self.panel.SetSizerAndFit(self.totSizer)
        self.SetSize((700,400))

