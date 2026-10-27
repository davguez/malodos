'''
Created on 21 juin 2010. Copyright 2010, David GUEZ
@author: david guez (guezdav@gmail.com)
This file is a part of the source code of the MALODOS project.
You can use and distribute it freely, but have to conform to the license
attached to this project (LICENSE.txt file)
=====================================================================
GUI dialog for addition of a scanned document to the database
'''

import wx
import os
from gui import utilities
from wx.lib.intctrl import IntCtrl
from wx.lib.agw.floatspin import FloatSpin
from scannerAccess import scannerOption
#from scannerAccess.scannerOption import TYPE_BUTTON
if os.name == 'posix' :
	from scannerAccess import saneAccess
else:
	from scannerAccess import twainAccess
import gui.docWindow as docWindow
import data
from . import RecordWidget
import database
#import wx.lib.intctrl
#import wx.lib.agw.floatspin
from database import theConfig
from algorithms.general import str_to_bool
import logging
from database import Resources

class OptionsWindow(wx.Dialog):
	def __init__(self, parent, optList,defaultValues=None):
		wx.Dialog.__init__(self, parent, -1, _('Scanning options'), wx.DefaultPosition)
		self.ScrollWindow = wx.ScrolledWindow(self, -1)
		self.panel = wx.Panel(self.ScrollWindow,-1)
		self.totalWin = wx.GridSizer(1,2)

		k=0
		self.txtOpt = list()
		self.wOptions = list()
		self.parName=list()
		self.definedParams=dict()
		for a in optList :
			#a = optList[o]
			#if not a.is_settable() : continue
			if a.type==scannerOption.TYPE_BUTTON: continue
			self.parName.append(a.name)
			self.txtOpt.append( wx.StaticText(self.panel,-1, a.title) ) 
			self.txtOpt[k].SetToolTipString(a.name + ' : ' +a.description)
			self.totalWin.Add(self.txtOpt[k],0,wx.EXPAND)
			
			if isinstance(defaultValues,dict) and self.parName[k] in defaultValues :
				defVal = defaultValues[self.parName[k]]
			else:
				defVal=None
			if a.type == scannerOption.TYPE_BOOL :
				self.wOptions.append( wx.CheckBox(self.panel , -1))
				if defVal : self.wOptions[k].SetValue(defVal.lower()=='true')
			elif  a.type == scannerOption.TYPE_INT:
				try:
					defVal = int(defVal)
				except:
					defVal=0  
				if a.constraint and isinstance(a.constraint,tuple) and len(a.constraint)==3:
					if defVal < a.constraint[0] : defVal = a.constraint[0]
					if defVal > a.constraint[1] : defVal = a.constraint[1]
					if a.constraint[2]==1 or a.constraint[2]==0:
						self.wOptions.append( wx.SpinCtrl(self.panel,-1,min=a.constraint[0],max=a.constraint[1]))
						self.wOptions[k].SetValue(defVal)
					else:
						self.wOptions.append( FloatSpin(self.panel,-1,min_val=a.constraint[0],max_val=a.constraint[1],increment=a.constraint[2],digits=4))
						self.wOptions[k].SetValue(defVal)
				elif a.constraint and isinstance(a.constraint,list):
					available_choices = [str(x) for x in a.constraint]
					self.wOptions.append( wx.ComboBox(self.panel,-1,choices=available_choices,style=wx.CB_READONLY|wx.CB_SORT))
					try:
						i = a.constraint.index(defVal)
						self.wOptions[k].SetStringSelection(available_choices[i])
					except:
						pass
				else:
					self.wOptions.append( IntCtrl(self.panel,-1,0))
			elif a.type == scannerOption.TYPE_FIXED:
				try:
					defVal = float(defVal)
				except:
					defVal = 0.0 
				if a.constraint and isinstance(a.constraint,tuple) and len(a.constraint)==3:
					if defVal < a.constraint[0] : defVal = a.constraint[0]
					if defVal > a.constraint[1] : defVal = a.constraint[1]
					if a.constraint[2]==0: 
						self.wOptions.append( FloatSpin(self.panel,-1,min_val=a.constraint[0],max_val=a.constraint[1],increment=1.0,digits=4))
						self.wOptions[k].SetValue(defVal)
					else:
						self.wOptions.append( FloatSpin(self.panel,-1,min_val=a.constraint[0],max_val=a.constraint[1],increment=a.constraint[2],digits=4))
						self.wOptions[k].SetValue(defVal)
				elif a.constraint and isinstance(a.constraint,list):
					available_choices = [str(x) for x in a.constraint]
					self.wOptions.append( wx.ComboBox(self.panel,-1,choices=available_choices,style=wx.CB_READONLY|wx.CB_SORT))
					try:
						i = a.constraint.index(defVal)
						self.wOptions[k].SetStringSelection(available_choices[i])
					except:
						pass
				else:
					self.wOptions.append( IntCtrl(self.panel,-1,0)) # TODO : modify to use double values
			elif  a.type == scannerOption.TYPE_STRING :
				if not a.constraint:
					self.wOptions.append( wx.TextCtrl(self.panel,-1))
					self.wOptions[k].SetValue(defVal)
				elif a.constraint and isinstance(a.constraint,list):
					self.wOptions.append( wx.ComboBox(self.panel,-1,choices=[str(x) for x in a.constraint],style=wx.CB_READONLY|wx.CB_SORT))
					try:
						self.wOptions[k].SetStringSelection(defVal)
					except:
						pass
			else:
				self.wOptions.append( wx.StaticText(self.panel,-1,''))			
			
			self.wOptions[k].SetToolTipString(a.description)
			self.totalWin.Add(self.wOptions[k],0,wx.EXPAND)
			
			k=k+1
			
		self.btOk = wx.Button(self.panel,-1,_('Ok'))
		self.totalWin.Add(self.btOk,0,wx.EXPAND)
		self.btCancel = wx.Button(self.panel,-1,_('Cancel'))
		self.totalWin.Add(self.btCancel,0,wx.EXPAND)
		self.panel.SetSizer(self.totalWin)
		self.panel.SetAutoLayout(True)
		self.panel.Layout()
		self.panel.Fit()
		width,height=self.panel.GetSizeTuple()
		u = 10.0
		self.ScrollWindow.SetScrollbars(u, u, width/u, height/u)
		if width>400 : width=400
		if height>600 : height=600
		if height<80 : height=80
		self.SetSize((width+10,height+10))
		self.Center()
		
		self.Bind(wx.EVT_BUTTON,self.actionOk,self.btOk)
		self.Bind(wx.EVT_BUTTON,self.actionCancel,self.btCancel)
	def actionCancel(self,event):
		self.Close()
	def actionOk(self,event):
		for k in range(len(self.parName)) :
			try:
				n = self.parName[k]
				v = self.wOptions[k].GetValue()
				#print n + '=' + str(v)
				self.definedParams[n] = str(v)
			except:
				pass
		self.Close()

class ScanWindow(wx.Dialog):
	scanner = None
	#==============================================================================
	# constructor (gui building)
	#==============================================================================
	def __init__(self, parent, title,clear_data=True):
		wx.Dialog.__init__(self, parent, -1, _('Scanning a new document'), wx.DefaultPosition, (372, 700), style=wx.CLOSE_BOX | wx.SYSTEM_MENU | wx.CAPTION | wx.RESIZE_BORDER  | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX)
		self.panel = wx.Panel(self, -1)

		self.totalWin = wx.BoxSizer(wx.VERTICAL)
		self.upPart = wx.GridBagSizer(3,2)

		self.stSource = wx.StaticText(self.panel,-1,_("Source :"))
		#self.btSource = wx.Button(self.panel, -1, _('Select Scanner'))

		self.buttonPart = wx.BoxSizer(wx.HORIZONTAL)

		self.btScan = wx.BitmapButton(self.panel,-1, wx.Bitmap(Resources.get_icon_filename('PERFORM_SCAN')))
		self.btScan.SetToolTipString(_('Scan'))
		self.buttonPart.Add(self.btScan ,0)

		self.btAddScan = wx.BitmapButton(self.panel, 666, wx.Bitmap(Resources.get_icon_filename('ADD_PERFORM_SCAN')))
		self.btAddScan.SetToolTipString(_('Add scan'))
		self.buttonPart.Add(self.btAddScan ,0)

		self.btSave = wx.BitmapButton(self.panel, -1, wx.Bitmap(Resources.get_icon_filename('RECORD_SCANNED')))
		self.btSave.SetToolTipString(_('Record'))
		self.buttonPart.Add(self.btSave ,0)

		self.btSource = wx.BitmapButton(self.panel, -1, wx.Bitmap(Resources.get_icon_filename('CHOOSE_SCANNER')))
		self.btSource.SetToolTipString(_('Select Scanner'))
		self.buttonPart.Add(self.btSource ,0)

		self.btOptions = wx.BitmapButton(self.panel,-1,wx.Bitmap(Resources.get_icon_filename('SCANNER_PREFERENCES')))
		self.btOptions.SetToolTipString(_('Options'))
		self.buttonPart.Add(self.btOptions ,0)


		#self.btScan = wx.Button(self.panel, -1, _('Scan'))
		#self.cbMultiplePage = wx.CheckBox(self.panel, -1, _('Manual MultiPage'))
		#self.btSave = wx.Button(self.panel, -1, _('Record'))
		#self.btOptions = wx.Button(self.panel,-1,_('Options'))
		
		self.docWin = docWindow.docWindow(self.panel,-1)
		self.recordPart = RecordWidget.RecordWidget(self.panel,file_style=wx.FLP_SAVE | wx.FLP_OVERWRITE_PROMPT | wx.FLP_USE_TEXTCTRL)
		self.recordPart.cbOCR.SetValue(str_to_bool(theConfig.get_param('OCR', 'autoStart','1')))

		self.upPart.Add(wx.StaticText(self.panel,-1,_("Source :")),(0,0),flag=wx.ALL | wx.ALIGN_CENTRE_VERTICAL)
		self.upPart.Add(self.stSource,(0,1),flag=wx.ALL| wx.ALIGN_CENTRE_VERTICAL)
		#self.upPart.Add(self.btSource,0,wx.EXPAND | wx.CENTER)
		#self.upPart.Add(self.btScan,0,wx.EXPAND | wx.CENTER)
		#self.upPart.Add(self.btSave,0,wx.EXPAND | wx.CENTER)
		#self.upPart.Add(self.btOptions,0,wx.EXPAND | wx.CENTER)
		#self.upPart.Add(self.cbMultiplePage,0,wx.EXPAND | wx.CENTER)
		self.upPart.Add(self.buttonPart,(1,0),span=(1,2),flag=wx.EXPAND)
	
		self.totalWin.Add(self.upPart,0,wx.EXPAND)
		self.totalWin.Add(self.recordPart,0,wx.EXPAND)
		self.totalWin.Add(self.docWin,1,wx.EXPAND)
		# BINDING EVENTS
		self.Bind(wx.EVT_BUTTON, self.actionChooseSource, self.btSource)
		self.Bind(wx.EVT_BUTTON, self.actionPerformScan, self.btScan)
		self.Bind(wx.EVT_BUTTON, self.actionPerformScan, self.btAddScan)
		self.Bind(wx.EVT_BUTTON, self.actionSaveRecord, self.btSave)
		self.Bind(wx.EVT_BUTTON, self.actionOpenOptions, self.btOptions)
		self.Bind(wx.EVT_CLOSE,self.onClose)
		# OTHER INITIALISATIIONS
		if os.name == 'posix' :
			self.scanner = saneAccess.SaneAccess(self.GetHandle(),self.onNewScannerData)
		else:
			self.scanner = twainAccess.TwainAccess(self.GetHandle(),self.onNewScannerData)
		self.panel.SetSizerAndFit(self.totalWin)
		self.SetSize(self.GetSize())
		self.stSource.Label = self.scanner.chooseSource(database.theConfig.get_current_scanner())
		self.SetSizeWH(550,800)
		
		self.currentOptions=dict()
		op_ini  =  database.theConfig.get_all_params_in('scanner_options')
		op_scan = self.scanner.get_options()
		for op in op_scan :
			if op.name in list(op_ini.keys()) :
				self.currentOptions[op.name] = str(op_ini[op.name])
			else:
				self.currentOptions[op.name] = op.value
		for name,val in list(op_ini.items()) :
			if not name in list(self.currentOptions.keys()) : self.currentOptions[name]=val
		#self.recordPart.lbFileName.SetPath(self.defaultNameDir())
		#data.theData.clear_all()
		if str_to_bool(database.theConfig.get_param('scanner', 'autoScan','False',True)) :
#			event.Id = 0 if clear_data else 666 
			self.actionPerformScan(None)
	def onClose(self,event):
		if len(data.theData.pil_images)==0 or utilities.ask(_('The scanned images are not saved. Are you sure you want to quit the scan window?')) : self.Destroy()
	def actionOpenOptions(self,event):
		opts = self.scanner.get_options()
		self.scanner.closeScanner()
		w = OptionsWindow(self , opts,self.currentOptions)
		w.ShowModal()
		if len(w.definedParams)>0:
			self.currentOptions =  w.definedParams
	def actionChooseSource(self,event):
		self.stSource.Label = self.scanner.chooseSource()
	def defaultNameDir(self):
		defDir = database.theConfig.get_param('scanner', 'defaultDir',os.path.join(os.path.expanduser('~'),'MALODOS','Images'),False)
		if str_to_bool(database.theConfig.get_param('scanner', 'useLastDir','False',True)) : 
			defNameDir = database.theConfig.get_param('scanner', 'lastDir',defDir,False)
		else:
			defNameDir = defDir
		return defNameDir
	def do_scan(self):
		try:
			self.scanner.useOptions(self.currentOptions)
		except Exception as E:
			logging.debug('Scan options error ' + str(E))
		try:
			self.scanner.startAcquisition()
		except Exception as E:
			logging.debug('Scan acquisition error ' + str(E))
		
	def actionPerformScan(self,event):
#		try:
#			auto_cont=str_to_bool(self.currentOptions['manual_multipage'])
#		except:
#			auto_cont=False
#		try:
#			self.scanner.useOptions(self.currentOptions)
#		except:
#			if not  utilities.ask(_('Unable to set the scanner options. Do you want to proceed to scan anyway ?')) : return
		
#		cont=True
		if event is not None and event.Id != 666 : data.theData.clear_all()
		data.theData.current_image=0
		self.do_scan()
#		while cont:
#			if auto_cont:
#				if not  utilities.ask(_('Do you want to add new page(s) ?')) : cont=False
#			else:
#				cont=False
#		self.docWin.showCurrentImage()
		if self.recordPart.lbFileName.GetPath() != '' : return
		if not str_to_bool(database.theConfig.get_param('scanner', 'autoFileName','False',True)) : return
		defNameDir = self.defaultNameDir()
		idx=1
		def generated_file_name():
			fnamePrefix = database.theConfig.get_param('scanner', 'autoFileNamePrefix','file',True)
			fname = '%s%.4d.pdf' % (fnamePrefix,idx)
			return os.path.join(defNameDir,fname)
		while os.path.exists(generated_file_name()) : idx+=1
		self.recordPart.lbFileName.SetPath(generated_file_name())
			
	def actionSaveRecord(self,event):
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
				raise Exception('Unable to add the file to the disk')
		try:
			#if not data.theData.save_file(fname,self.recordPart.lbTitle.Value,self.recordPart.lbDescription.Value,self.recordPart.lbTags.Value) : raise _('Unable to add the file to the disk')
			if not data.theData.save_file(fname,self.recordPart.lbTitle.Value,self.recordPart.lbDescription.Value,self.recordPart.lbTags.Value) :
				wx.MessageBox(_('Unable to add the file to the disk'))
				return
				
		except Exception as E:
			logging.debug('Unable to save the file ' + fname + ':' + str(E))
			return
		if not self.recordPart.do_save_record():
			wx.MessageBox(_('Unable to add the file to the database'))
		else:
			# close the dialog if so required
			database.theConfig.set_param('scanner', 'lastDir',os.path.dirname(fname),True)
			database.theConfig.commit_config()
			data.theData.clear_all()
			if str_to_bool(database.theConfig.get_param('scanner', 'autoClose','True',True)) :
				self.Close()
			else:
				self.docWin.showCurrentImage()
				if str_to_bool(database.theConfig.get_param('scanner', 'clearFields','False',True)):
					self.recordPart.clear_all()
				else:
					self.recordPart.lbFileName.SetPath('')
	def onNewScannerData(self):
		data.theData.current_image=len(data.theData.pil_images)-1
		self.docWin.showCurrentImage()
		try:
			auto_cont=str_to_bool(self.currentOptions['manual_multipage'])
		except:
			auto_cont=False
		if auto_cont and utilities.ask(_('Do you want to add new page(s) ?')) : self.do_scan()
			
	