#!/usr/bin/env python
# -*- coding: latin1 -*-

import os
import copy

from .font import fpdf_charwidths

FPDF_VERSION = '1.53'
true = True
false = False
count = len


def gzcompress(i_data):
	return i_data

def is_array(i_val):
	if type(i_val) in [ type(list()) ,type(tuple()) ]:
		return True
	
	return False

def array(*args):
	return list(args)
	

def function_exists(i_args):
	return False

def str_replace(i_from,i_to,i_string):
	return str(i_string).replace(str(i_from),str(i_to) )

def is_string(i_string):
	if type(i_string) in [type(""),type('')]:
		return True
	return False

def sprintf(i_format,*args):
	return i_format % args;

def strlen(i_string):
	return len(str(i_string))
	
def strtolower(i_string):
	return str(i_string).lower()
	
	
def strtoupper(i_string):
	return str(i_string).upper()
	
def strpos(i_string,i_pattern):
	try:
		return i_string.index( i_pattern )
	except:
		return False
	
	
def substr(i_string,i_offset,i_size=None):
	if not i_size:
		return i_string[i_offset:]
		
	return i_string[i_offset:i_size]
	
	
def strrpos(i_string,i_token):
	v_size = len(i_string)-1
	
	while v_size >= 0:
		if i_string[v_size] == i_token:
			return v_size
		v_size-=1
		
	
	return False

	
def empty(i_var):
	if not i_var:
		return True
	return False


def fq(i_var,i_op1,i_op2):	
	if i_var:
		return i_op1	
	return i_op2

def include(i_file):
	return

def fopen(i_fileName,i_mode):
	return open(i_fileName,i_mode)
	
def fwrite(i_file,i_string,i_len):
	return i_file.write(i_string)
	
def fclose(i_file):
	return i_file.close()
	
def fread(i_file,i_len):
	return i_file.read(i_len)
	
def method_exists(i_obj,i_method):
	return True


def getimagesize_jpg(filename) :
		import struct

		r = None
		
		f = open(filename, "rb")
		while True :
				s = f.read(1)
				if s :
						marker = struct.unpack('B', s)[0]
						if 0xff == marker :
								s = f.read(1)
								marker = struct.unpack('B', s)[0]
								if 0xff == marker :
										pass
								elif 0xc0 == marker :
										# print "M_SOF15"
										s = f.read(2)
										length = struct.unpack('>H', s)[0]
										# print "length=", length
										s = f.read(5)
										(bits, height, width) = struct.unpack('>BHH', s)
										# print "bits=%d width=%d height=%d" % (bits, width, height)
										# size found
										r = (width, height)
										break
								elif 0xd9 == marker :
										# End Of Image
										break
						# else :
						#		 print "0x%.2x" % c, type(c)
				else :
						break
		
		f.close()
		return r

def GetImageSize(filename) :
		# getimagesize() retourne un tableau de 4 éléments.
		# L'index 0 contient la largeur.
		# L'index 1 contient la longueur.
		# L'index 2 contient le type de l'image :
		# 1 = GIF,
		# 2 = JPG,
		# 3 = PNG,
		# 4 = SWF,
		# 5 = PSD,
		# 6 = BMP,
		# 7 = TIFF (Ordre des octets Intel), 8 = TIFF (Ordre des octets Motorola),
		# 9 = JPC, 10 = JP2, 11 = JPX, 12 = JB2, 13 = SWC, 14 = IFF.
		# Ces valeurs correspondent aux constantes IMAGETYPE
		# qui ont été ajoutées en PHP 4.3.
		# L'index 3 contient la chaîne à placer dans les balises IMG :
		# height="xxx" width="yyy".

		# size of a JPG file
		(w, h) = getimagesize_jpg(filename)

		# a is the return value (dict)
		a = {}
		a[0] = w
		a[1] = h
		a[3] = 'height="%d" width="%d"' % (w, h)
		
		# dict of formats => to be completed according to Image.format return value
		formats = {"JPEG":2, "PNG":3}
		a[2] = formats["JPEG"]
		
		
		return a

class FPDF:
	def __init__( self ,orientation='P',unit='mm',format='A4'):
		#Private properties
		self.page=None;							 #current page number
		self.n=None;									#current object number
		self.offsets={}; #python: array() => {}						#array of object offsets
		self.buffer=None;						 #buffer holding in-memory PDF
		self.pages=None;							#array containing pages
		self.state=None;							#current document state
		self.compress=None;					 #compression flag
		self.DefOrientation=None;		 #default orientation
		self.CurOrientation=None;		 #current orientation
		self.OrientationChanges=None; #array indicating orientation changes
		self.k=None;									#scale factor (number of points in user unit)
		self.fwPt=None; self.fhPt=None;				 #dimensions of page format in points
		self.fw=None; self.fh=None;						 #dimensions of page format in user unit
		self.wPt=None; self.hPt=None;					 #current dimensions of page in points
		self.w=None; self.h=None;							 #current dimensions of page in user unit
		self.lMargin=None;						#left margin
		self.tMargin=None;						#top margin
		self.rMargin=None;						#right margin
		self.bMargin=None;						#page break margin
		self.cMargin=None;						#cell margin
		self.x=None; self.y=None;							 #current position in user unit for cell positioning
		self.lasth=None;							#height of last cell printed
		self.LineWidth=None;					#line width in user unit
		self.CoreFonts=None;					#array of standard font names
		self.fonts={};								#array of used fonts
		self.FontFiles=None;					#array of font files
		self.diffs=None;							#array of encoding differences
		self.images={};							 #array of used images
		self.PageLinks=[]						 #python: array() => [] list of links in pages
		self.links=[]								 #array of internal links
		self.FontFamily=None;				 #current font family
		self.FontStyle=None;					#current font style
		self.underline=None;					#underlining flag
		self.CurrentFont=None;				#current font info
		self.FontSizePt=None;				 #current font size in points
		self.FontSize=None;					 #current font size in user unit
		self.DrawColor=None;					#commands for drawing color
		self.FillColor=None;					#commands for filling color
		self.TextColor=None;					#commands for text color
		self.ColorFlag=None;					#indicates whether fill and text colors are different
		self.ws=None;								 #word spacing
		self.AutoPageBreak=None;			#automatic page breaking
		self.PageBreakTrigger=None;	 #threshold used to trigger page breaks
		self.InFooter=None;					 #flag set when processing footer
		self.ZoomMode=None;					 #zoom display mode
		self.LayoutMode=None;				 #layout display mode
		self.title=None;							#title
		self.subject=None;						#subject
		self.author=None;						 #author
		self.keywords=None;					 #keywords
		self.creator=None;						#creator
		self.AliasNbPages=None;			 #alias for total number of pages
		self.PDFVersion=None;				 #PDF version number
		
		
		#/*******************************************************************************
		#*																																							*
		#*															 Public methods																 *
		#*																																							*
		#*******************************************************************************/
		#function FPDF($orientation='P',$unit='mm',$format='A4')
		#{
		
		#Some checks
		self._dochecks();
		
		#Initialization of properties
		self.page=0;
		self.n=2;
		self.buffer='';
		self.pages={}; #python: array() => {}
		self.OrientationChanges={}; #python: array() => {}array();
		self.state=0;
		self.fonts={} #python: array() => {} 
		self.FontFiles=array();
		self.diffs=array();
		self.images={};
		self.links=[]
		self.InFooter=false;
		self.lasth=0;
		self.FontFamily='';
		self.FontStyle='';
		self.FontSizePt=12;
		self.underline=false;
		self.DrawColor='0 G';
		self.FillColor='0 g';
		self.TextColor='0 g';
		self.ColorFlag=false;
		self.ws=0;
		
		#Standard fonts
		self.CoreFonts={'courier':'Courier', 'courierB':'Courier-Bold', 'courierI':'Courier-Oblique', 'courierBI':'Courier-BoldOblique', 
				'helvetica':'Helvetica', 'helveticaB':'Helvetica-Bold', 'helveticaI':'Helvetica-Oblique', 'helveticaBI':'Helvetica-BoldOblique', 
				'times':'Times-Roman', 'timesB':'Times-Bold', 'timesI':'Times-Italic', 'timesBI':'Times-BoldItalic', 
				'symbol':'Symbol', 'zapfdingbats':'ZapfDingbats'}
		
		#Scale factor
		if unit=='pt': #{
			self.k=1;
		#}
		elif unit=='mm':#{
			self.k=72/25.4;
		#}
		elif unit=='cm':#{
			self.k=72/2.54;
		#}
		elif unit=='in':#{
			self.k=72;
		#}
		else: #{
			self.Error( 'Incorrect unit: '+unit );
		#}
		
		#Page format
		
		if is_string( format ):#{
			format=strtolower( format );
			
			if ( format=='a3' ):#{
				format=array( 841.89, 1190.55 );
			#}
			elif( format=='a4' ):#{
				format=array( 595.28, 841.89 );
			#}
			elif( format=='a5' ):#{
				format=array( 420.94, 595.28 );
			#}
			elif( format=='letter' ):#{
				format=array( 612, 792 );
			#}
			elif( format=='legal' ):#{
				format=array( 612, 1008 );
			#}
			else:#{
				self.Error( 'Unknown page format: '+format );
			#}
			
			self.fwPt=format[0];
			self.fhPt=format[1];
		#}
		else:#{
			self.fwPt=format[0]*self.k;
			self.fhPt=format[1]*self.k;
		#}
		
		
		self.fw=self.fwPt/self.k;
		self.fh=self.fhPt/self.k;
		
		#Page orientation
		
		orientation=strtolower( orientation );
		
		if( orientation=='p' or orientation=='portrait' ):#{
			self.DefOrientation='P';
			self.wPt=self.fwPt;
			self.hPt=self.fhPt;
		#}
		
		elif( orientation=='l' or orientation=='landscape' ):#{
			self.DefOrientation='L';
			self.wPt=self.fhPt;
			self.hPt=self.fwPt;
		#}
		else:#{
			self.Error( 'Incorrect orientation: '+orientation );
		#}
		
		self.CurOrientation=self.DefOrientation;
		self.w=self.wPt/self.k;
		self.h=self.hPt/self.k;
		
		#Page margins (1 cm)
		margin=28.35/self.k;
		self.SetMargins( margin, margin );
		
		#Interior cell margin (1 mm)
		self.cMargin=margin/10;
		
		#Line width (0.2 mm)
		self.LineWidth=.567/self.k;
		
		#Automatic page break
		self.SetAutoPageBreak( true, 2*margin );
			
		#Full width display mode
		self.SetDisplayMode( 'fullwidth' );
			
		#Enable compression
		self.SetCompression( true );
			
		#Set default PDF version number
		self.PDFVersion='1.3';
		
		return
	
	
	
	def SetMargins(self,left,top,right=-1):
		#Set left, top and right margins
		self.lMargin=left;
		self.tMargin=top;
		if(right==-1):
			right=left;
		self.rMargin=right;
		return
	
	
	def SetLeftMargin(self,margin):
		#Set left margin
		self.lMargin=margin;
		if(self.page>0 and self.x<margin):
			self.x=margin;
		return
	
	
	def SetTopMargin(self,margin):
		#Set top margin
		self.tMargin=margin;
		return
	
	def SetRightMargin(self,margin):
		#Set right margin
		self.rMargin=margin;
		return
	
	def SetAutoPageBreak(self,auto,margin=0):
		#Set auto page break mode and triggering margin
		self.AutoPageBreak=auto;
		self.bMargin=margin;
		self.PageBreakTrigger=self.h-margin;
		return
	
	def SetDisplayMode(self,zoom,layout='continuous'):
		#Set display mode in viewer
		if(zoom=='fullpage' or zoom=='fullwidth' or zoom=='real' or zoom=='default' or not is_string(zoom)):#{
			self.ZoomMode=zoom;
		#}
		else:#{
			self.Error('Incorrect zoom display mode: '.zoom);
		#}
		
		if(layout=='single' or layout=='continuous' or layout=='two' or layout=='default'):#{
			self.LayoutMode=layout;
		#}
		else:#{
			self.Error('Incorrect layout display mode: '+layout);
		#}
		return
	
	def SetCompression(self,compress):
		#Set page compression
		if(function_exists('gzcompress')):
			self.compress=compress;
		else:
			self.compress=false;
		return
	
	def SetTitle(self,title):
		#Title of document
		self.title=title;
		return
	
	
	def SetSubject(self,subject):
		#Subject of document
		self.subject=subject;
		return
	
	
	def SetAuthor(self,author):
		#//Author of document
		self.author=author;
		return
	
	
	def SetKeywords(self,keywords):
		#Keywords of document
		self.keywords=keywords;
		return
	
	def SetCreator(self,creator):
		#Creator of document
		self.creator=creator;
		return
	
	
	def AliasNbPages(self,alias='{nb}'):
		#Define an alias for total number of pages
		self.AliasNbPages=alias;
		return
	
	
	def Error(self,msg):
		#Fatal error
		print('FPDF error: %s' % msg);
		1/0
		return
	
	
	def Open(self):
		#Begin document
		self.state=1;
		return
	
	def Close(self):
		#Terminate document
		if(self.state==3):
			return;
		
		if(self.page==0):
			self.AddPage();
			
		#Page footer
		#self.InFooter=true;
		#self.Footer();
		#self.InFooter=false;
		#Close page
		
		self._endpage();
		#Close document
		self._enddoc();
		return
	
	
	def AddPage(self,orientation=''):
		#Start a new page
		if(self.state==0):
			self.Open();
		
		family=self.FontFamily;
		
		tmp=''
		if self.underline:
			tmp = 'U'
			
		style=self.FontStyle=tmp;
		size=self.FontSizePt;
		lw=self.LineWidth;
		dc=self.DrawColor;
		fc=self.FillColor;
		tc=self.TextColor;
		cf=self.ColorFlag;
		if(self.page>0):#{
			#Page footer
			self.InFooter=true;
			self.Footer();
			self.InFooter=false;
			#Close page
			self._endpage();
		#}
		
		#Start new page
		self._beginpage(orientation);
		
		#Set line cap style to square
		self._out('2 J');
		
		#Set line width
		self.LineWidth=lw;
		self._out(sprintf('%.2f w',lw*self.k));
		#Set font
		if(family):
			self.SetFont(family,style,size);
		
		#Set colors
		self.DrawColor=dc;
		if(dc!='0 G'):
			self._out(dc)
		
		self.FillColor=fc;
		
		if(fc!='0 g'):
			self._out(fc)
		
		self.TextColor=tc;
		self.ColorFlag=cf;
		
		#Page header
		self.Header();
		
		#Restore line width
		
		if(self.LineWidth!=lw): #{
			self.LineWidth=lw;
			self._out(sprintf('%.2f w',lw*self.k));
		#}
		
		
		#Restore font
		if(family):
			self.SetFont(family,style,size)
			
		#Restore colors
		
		if(self.DrawColor!=dc):#{
			self.DrawColor=dc;
			self._out(dc);
		#}
		
		if(self.FillColor!=fc):#{
			self.FillColor=fc;
			self._out(fc);
		#}
		
		self.TextColor=tc;
		self.ColorFlag=cf;
		
		return
	
	
	def Header(self):
		#To be implemented in your own inherited class
		return
	
	def Footer(self):
		#To be implemented in your own inherited class
		return
	
	def PageNo(self):
		#Get current page number
		return self.page;
	
	
	def SetDrawColor(self,r,g=-1,b=-1):
		#Set color for all stroking operations
		if((r==0 and g==0 and b==0) or g==-1):
			self.DrawColor=sprintf('%.3f G',float(r)/255);
		else:
			self.DrawColor=sprintf('%.3f %.3f %.3f RG',float(r)/255,float(g)/255,float(b)/255);
			
		if(self.page>0):
			self._out(self.DrawColor);
			
		return
	
	
	def SetFillColor(self, r, g=-1, b=-1) :
		#Set color for all filling operations
		if((r==0 and g==0 and b==0) or g==-1) :
			self.FillColor = sprintf('%.3f g', float(r)/255)
		else:
			self.FillColor = sprintf('%.3f %.3f %.3f rg', float(r)/255, float(g)/255, float(b)/255)

		self.ColorFlag=(self.FillColor!=self.TextColor)
		if(self.page>0):
			self._out(self.FillColor)
		return
	
	def SetTextColor(self,r,g=-1,b=-1):
		#Set color for text
		if((r==0 and g==0 and b==0) or g==-1):
			self.TextColor=sprintf('%.3f g',float(r)/255);
		else:
			self.TextColor=sprintf('%.3f %.3f %.3f rg',float(r)/255,float(g)/255,float(b)/255);
			
		self.ColorFlag=(self.FillColor!=self.TextColor);
		return
	
	def GetStringWidth(self,s):
		#Get width of a string in the current font
		s=str(s);
		cw=self.CurrentFont['cw'];
		w=0;
		l=strlen(s);
		for i in range(l):
			w+=cw[s[i]];
		
		return w*self.FontSize/1000;
	
	
	def SetLineWidth(self,width):
		#Set line width
		self.LineWidth=width;
		if(self.page>0):
			self._out(sprintf('%.2f w',width*self.k));
			
		return
	
	
	def Line(self,x1,y1,x2,y2):
		#Draw a line
		self._out(sprintf('%.2f %.2f m %.2f %.2f l S',x1*self.k,(self.h-y1)*self.k,x2*self.k,(self.h-y2)*self.k));
		return
	
	
	def Rect(self,x,y,w,h,style=''):
		#Draw a rectangle
		if(style=='F'):
			op='f';
		elif(style=='FD' or style=='DF'):
			op='B';
		else:
			op='S';
			
		self._out(sprintf('%.2f %.2f %.2f %.2f re %s',x*self.k,(self.h-y)*self.k,w*self.k,-h*self.k,op));
		return
	
#
#def AddFont(family,style='',file='')
#{
#	//Add a TrueType or Type1 font
#	family=strtolower(family);
#	if(file=='')
#		file=str_replace(' ','',family).strtolower(style).'.php';
#	if(family=='arial')
#		family='helvetica';
#	style=strtoupper(style);
#	if(style=='IB')
#		style='BI';
#	fontkey=family.style;
#	if(isset(self.fonts[fontkey]))
#		self.Error('Font already added: '.family.' '.style);
#	include(self._getfontpath().file);
#	if(!isset(name))
#		self.Error('Could not include font definition file');
#	i=count(self.fonts)+1;
#	self.fonts[fontkey]=array('i'=>i,'type'=>type,'name'=>name,'desc'=>desc,'up'=>up,'ut'=>ut,'cw'=>cw,'enc'=>enc,'file'=>file);
#	if(diff)
#	{
#		//Search existing encodings
#		d=0;
#		nb=count(self.diffs);
#		for(i=1;i<=nb;i++)
#		{
#			if(self.diffs[i]==diff)
#			{
#				d=i;
#				break;
#			}
#		}
#		if(d==0)
#		{
#			d=nb+1;
#		self.diffs[d]=diff;
#		}
#		self.fonts[fontkey]['diff']=d;
#	}
#	if(file)
#	{
#		if(type=='TrueType')
#		self.FontFiles[file]=array('length1'=>originalsize);
#		else
#		self.FontFiles[file]=array('length1'=>size1,'length2'=>size2);
#	}
#}
#
	def SetFont(self,family,style='',size=0):
		#Select a font; size given in points
		global fpdf_charwidths;
		
		family=strtolower(family);
		if(family==''):
			family=self.FontFamily;
		
		if(family=='arial'):
			family='helvetica';
			
		elif(family=='symbol' or family=='zapfdingbats'):
			style='';
			
		style=strtoupper(style);
		if(strpos(style,'U')!=false):#{
			self.underline=true;
			style=str_replace('U','',style);
		#}
		else:#{
			self.underline=false;
		#}
		
		if(style=='IB'):#{
			style='BI';
		#}
		if(size==0):#{
			size=self.FontSizePt;
		#}
		
		#Test if font is already selected
		if(self.FontFamily==family and self.FontStyle==style and self.FontSizePt==size):
			return;
		
		#Test if used for the first time
		fontkey=family+style;
		
		#if(!isset(self.fonts[fontkey]))
		if not self.fonts.__contains__( fontkey ):#{
			#Check if one of the standard fonts
			#if( isset(self.CoreFonts[fontkey]) )
			if self.CoreFonts.__contains__( fontkey ):#{
				
				#if(!isset(fpdf_charwidths[fontkey]))
				if not fpdf_charwidths.__contains__(fontkey):#{
					#Load metric file
					file=family;
					if(family=='times' or family=='helvetica'):
						file+=strtolower(style);
					
					include(self._getfontpath()+file);
					
					#if(!isset(fpdf_charwidths[fontkey]))
					if not fpdf_charwidths.__contains__(fontkey):
						self.Error('Could not include font metric file');
				#}
				
				i=count(self.fonts)+1;
				self.fonts[fontkey]={'i':i,'type':'core','name':self.CoreFonts[fontkey],'up':-100,'ut':50,'cw':fpdf_charwidths[fontkey]}
			#}
			else:#{
				self.Error('Undefined font: '+family+' '+style);
			#}
		#}
		
		#Select it
		self.FontFamily=family;
		self.FontStyle=style;
		self.FontSizePt=size;
		self.FontSize=size/self.k;
		self.CurrentFont=self.fonts[fontkey];
		if(self.page>0):
			self._out(sprintf('BT /F%d %.2f Tf ET',self.CurrentFont['i'],self.FontSizePt));
		
		return
	


	def SetFontSize(self,size):
		#Set font size in points
		if(self.FontSizePt==size):
			return;
		
		self.FontSizePt=size;
		self.FontSize=size/self.k;
		
		if(self.page>0):
			self._out(sprintf('BT /F%d %.2f Tf ET',self.CurrentFont['i'],self.FontSizePt));
		return
	
	
	def AddLink(self) :
		#Create a new internal link
		#n=count(self.links)+1;
		#self.links[n]=array(0,0);
		self.links += [(0, 0)]
		n = len(self.links) - 1
		#print "AddLink()=", n
		#print "links=", self.links
		return n
	
	def SetLink(self,link,y=0,page=-1):
		#Set destination of internal link
		if (y==-1):
			y = self.y;
		if(page==-1):
			page=self.page;

		self.links[link] = (page, y)
		#print "SetLink(", link, ")=", (page, y)
		#print "links=", self.links
		return
	
	def Link(self,x,y,w,h,link):
		#Put a link on the page
		#print "Link()=", x,y,w,h,link
		if len(self.PageLinks) < (self.page + 1) :
			#print "self.page=", self.page
			for i in range(self.page - len(self.PageLinks) + 1) :
				#print "i=", i
				self.PageLinks += [[]]

		#print "PageLinks=", self.PageLinks
		#print "len(self.PageLinks)=", len(self.PageLinks)
		#print "self.page=", self.page
		self.PageLinks[self.page] += [(x*self.k,self.hPt-y*self.k,w*self.k,h*self.k,link)]
		return
	
	
	def Text(self,x,y,txt):
		#Output a string
		s=sprintf('BT %.2f %.2f Td (%s) Tj ET',x*self.k,(self.h-y)*self.k,self._escape(txt));
		if(self.underline and txt!=''):
			s+=' '+self._dounderline(x,y,txt);
		
		if(self.ColorFlag):
			s='q '+self.TextColor+' '+s+' Q';
			
		self._out(s);
		return
	
	def AcceptPageBreak(self):
		#Accept automatic page break or not
		return self.AutoPageBreak;
	

	def Cell(self, w, h=0,txt='',border=0,ln=0,align='',fill=0,link=None):
		#Output a cell
		k=self.k
		
		if(self.y+h>self.PageBreakTrigger and not self.InFooter and self.AcceptPageBreak()):#{
			#Automatic page break
			x=self.x;
			ws=self.ws;
			
			if(ws>0):#{
				self.ws=0;
				self._out('0 Tw');
			#}
			
			self.AddPage(self.CurOrientation);
			self.x=x;
			
			if(ws>0):#{
				self.ws=ws;
				self._out(sprintf('%.3f Tw',ws*k));
			#}
		#}
		
		if(w==0):
			w=self.w-self.rMargin-self.x;
		
		s='';
		if(fill==1 or border==1):#{
			if(fill==1):
				op=fq(border==1,'B','f');
			else:
				op='S';
				
			s=sprintf('%.2f %.2f %.2f %.2f re %s ',self.x*k,(self.h-self.y)*k,w*k,-h*k,op);
		#}
		
		if(is_string(border)):#{
			x=self.x;
			y=self.y;
			
			#if(strpos(border,'L')!=false):
			if "L" in border :
				s+=sprintf('%.2f %.2f m %.2f %.2f l S ',x*k,(self.h-y)*k,x*k,(self.h-(y+h))*k)

			#if(strpos(border,'T')!=false):
			if "T" in border :
				s+=sprintf('%.2f %.2f m %.2f %.2f l S ',x*k,(self.h-y)*k,(x+w)*k,(self.h-y)*k);
				
			#if(strpos(border,'R')!=false):
			if "R" in border :
				s+=sprintf('%.2f %.2f m %.2f %.2f l S ',(x+w)*k,(self.h-y)*k,(x+w)*k,(self.h-(y+h))*k);
				
			#if(strpos(border,'B')!=false):
			if "B" in border :
				s+=sprintf('%.2f %.2f m %.2f %.2f l S ',x*k,(self.h-(y+h))*k,(x+w)*k,(self.h-(y+h))*k);
				
		#}
		
		
		if(txt!=''):#{
			if(align=='R'):
				dx=w-self.cMargin-self.GetStringWidth(txt);
			elif(align=='C'):
				dx=(w-self.GetStringWidth(txt))/2;
			else:
				dx=self.cMargin;
				
			if(self.ColorFlag):
				s+='q '+self.TextColor+' ';
				
			txt2=str_replace(')','\\)',str_replace('(','\\(',str_replace('\\','\\\\',txt)));
			s+=sprintf('BT %.2f %.2f Td (%s) Tj ET',(self.x+dx)*k,(self.h-(self.y+.5*h+.3*self.FontSize))*k,txt2);
			
			if(self.underline):
				s+=' '+self._dounderline(self.x+dx,self.y+.5*h+.3*self.FontSize,txt);
				
			if(self.ColorFlag):
				s+=' Q';
			if None != link :
				self.Link(self.x+dx,self.y+.5*h-.5*self.FontSize,self.GetStringWidth(txt),self.FontSize,link);
		
		if(s):
			self._out(s);
			
		self.lasth=h;
		if(ln>0):#{
			#Go to next line
			self.y+=h;
			if(ln==1):
				self.x=self.lMargin;
		#}
		else:#{
			self.x+=w;
		#}
		
		return
	


	
	def MultiCell(self, w, h, txt, border=0, align='J', fill=0) :
	
		# Output text with automatic or explicit line breaks
		cw = self.CurrentFont['cw']
		if (w == 0) :
			w = float(self.w-self.rMargin-self.x)
		else :
			w = float(w)
			
		wmax = (w - 2 * self.cMargin) * 1000 / self.FontSize
		s = txt.replace("\r", "")
		nb = len(s)
		if (nb > 0 and s[nb - 1] == "\n") :
			nb -= 1

		b = 0
		if (border) :

			if (border == 1) :
				border = 'LTRB'
				b = 'LRT'
				b2 = 'LR'
			else :
				b2 = ''
				if strpos(border,'L') :
					b2 += 'L'
				if strpos(border,'R') :
					b2 +='R'
				if strpos(border,'T') :
					b = b2 + 'T'
				else :
					b = b2

		sep = -1
		i = 0
		j = 0
		l = float(0)
		ns = 0
		nl = 1
		while(i < nb) :
			#Get next character
			c = s[i]
			if (c=="\n") :
				# Explicit line break
				if (self.ws > 0) :
					self.ws = float(0)
					self._out('0 Tw')

				self.Cell(w, h, s[j:i], b, 2, align, fill)
				i += 1
				sep = -1
				j = i
				l = float(0)
				ns = 0
				nl +=1
				if (border and nl == 2) :
					b = b2
				continue
			
			if (c == ' ') :
				sep = i
				ls = l
				ns += 1

			l += cw[c]
			if (l > wmax) :
				# Automatic line break
				if (sep == -1) :
					if (i == j) :
						i += 1
					if (self.ws > 0) :
						self.ws = float(0)
						self._out('0 Tw')

					self.Cell(w, h, s[j:i], b, 2, align, fill)

				else :

					if (align=='J') :
						if (ns > 1) :
							self.ws = (wmax - ls) / 1000 * self.FontSize / (ns - 1)
						else :
							self.ws = float(0)
							
						self._out(sprintf('%.3f Tw', self.ws * self.k))

					self.Cell(w, h, s[j:sep], b, 2, align, fill)
					i = sep + 1

				sep = -1
				j =i
				l = float(0)
				ns = 0
				nl += 1
				if (border and nl == 2) :
					b = b2

			else :
				i += 1

		# Last chunk
		if (self.ws > 0) :
			self.ws = 0
			self._out('0 Tw')


		if (border and strpos(border,'B')) :
			b +='B'
		self.Cell(w, h, s[j:i], b, 2, align, fill)
		self.x = self.lMargin

		return
	

	def Write(self, h, txt, link=None) :
		#print "Write(link=", link,")"
		# Output text in flowing mode
		cw = self.CurrentFont['cw']
		w = float(self.w - self.rMargin - self.x)
		wmax = float( (w - 2 * self.cMargin) * 1000 / self.FontSize)
		s = txt.replace("\r", "")
		nb = len(s)
		sep = -1
		i = 0
		j = 0
		l = float(0)
		nl = 1

		while(i < nb) :
			# Get next character
			c = s[i]
			#print "c=", c
			if (c == "\n") :
				# Explicit line break
				self.Cell(float(w), h, s[j:i], 0, 2, '', 0, link)
				i += 1
				sep = -1
				j = i
				l = float(0)
				if (nl == 1) :
					self.x = self.lMargin
					w = float(self.w - self.rMargin - self.x)
					wmax = float((w - 2 * self.cMargin) * 1000 / self.FontSize)
				nl += 1
				continue
	
			if (c == ' ') :
				sep = i
			l += cw[c]
	
			if (l > wmax) :
				# Automatic line break
				if (sep == -1) :
					if (self.x > self.lMargin) :
					#if (self.x > self.rMargin) :
						# Move to next line
						self.x = self.lMargin
						self.y += h
						w = float(self.w - self.rMargin - self.x)
						wmax = float((w - 2 * self.cMargin) * 1000 / self.FontSize)
						i += 1
						nl += 1
						continue
	
					if (i == j) :
						i += 1
	
					self.Cell(float(w), h, s[j:i], 0, 2, '', 0, link)
	
				else :
					self.Cell(float(w), h, s[j:sep], 0, 2, '', 0, link)
					i = sep + 1
	
				sep = -1
				j = i
				l = float(0)
				if (nl == 1) :
					self.x = self.lMargin
					w = float(self.w - self.rMargin - self.x)
					wmax = float((w - 2 * self.cMargin) * 1000 / self.FontSize)
	
				nl += 1
	
			else :
				i += 1
	
		# Last chunk
		if (i != j) :
			self.Cell(float(l / 1000 * self.FontSize), h, s[j:], 0, 0, '', 0, link)
			# hack
			#print "s[-1]=", s[-1]
			#self.x += cw[s[-1]]
			#self.x += 1.0 / 1000.0 * self.FontSize
		return
	
	
	def Image(self,fname,x,y,w=0,h=0,v_type='',link=None):
		#Put an image on the page
		#if(!isset(self.images[fname])):#{
		if not self.images.__contains__(fname):
			#First use of image, get info
			if(v_type==''):#{
				pos=strrpos(fname,'.');
				if(not pos):
					self.Error('Image file has no extension and no type was specified: '+fname);
					
				v_type=substr(fname,pos+1);
			#}
			
			#print "v_type=",v_type
			v_type=strtolower(v_type);
			#mqr=get_magic_quotes_runtime();
			#set_magic_quotes_runtime(0);
			if(v_type=='jpg' or v_type=='jpeg'):
				info=self._parsejpg(fname);
			elif(v_type=='png'):
				info=self._parsepng(fname);
			else:#{
				#Allow for additional formats
				mtd='_parse'+v_type;
				
				if(not method_exists(self,mtd)):
					self.Error('Unsupported image type: '+v_type);
				
				#python
				#info=self.mtd(file) #python
				info=eval( "self.%s('%s')" % (mtd,fname) )
			#}
			
			#set_magic_quotes_runtime(mqr);
			info['i']=count(self.images)+1;
			self.images[fname]=info;

		#}
		else:
			info=self.images[fname];
			
		#Automatic width and height calculation if needed
		if(w==0 and h==0):#{
			#Put image at 72 dpi
			w=info['w']/self.k;
			h=info['h']/self.k;
		#}
		
		if(w==0):
			w=h*info['w']/info['h'];
		
		if(h==0):
			h=w*info['h']/info['w'];
			
		self._out(sprintf('q %.2f 0 0 %.2f %.2f %.2f cm /I%d Do Q',w*self.k,h*self.k,x*self.k,(self.h-(y+h))*self.k,info['i']));
		
		if None != link :
			self.Link(x,y,w,h,link)
		
		return
	
	def Ln(self,h=''):
		#Line feed; default value is last cell height
		self.x=self.lMargin;
		if(is_string(h)):
			self.y+=self.lasth;
		else:
			self.y+=h;
		return
	
	def GetX(self):
		#Get x position
		return self.x;
	
	def SetX(self,x):
		#Set x position
		if(x>=0):
			self.x=x;
		else:
			self.x=self.w+x;
			
		return
	
	def GetY(self):
		#Get y position
		return self.y;
	
	def SetY(self,y):
		#Set y position and reset x
		self.x=self.lMargin;
		
		if(y>=0):
			self.y=y;
		else:
			self.y=self.h+y;
		return
	
	
	def SetXY(self,x,y):
		#Set x and y positions
		self.SetY(y);
		self.SetX(x);
		return
	
	
	def Output(self,name='',dest=''):
		#Output PDF to some destination
		#Finish document if necessary
		
		if(self.state<3):
			self.Close();
			
			
		#Save to local file
		f=fopen(name,'wb');
		if not f:
			self.Error('Unable to create output file: '+name);
			
		fwrite(f,self.buffer,strlen(self.buffer));
		fclose(f);
		return


#/*******************************************************************************
#*																																							*
#*															Protected methods															 *
#*																																							*
#*******************************************************************************/
	def _dochecks(self):
		#Check for locale-related bug
		if(1.1==1):
			self.Error('Don\'t alter the locale before including class file');
			
		#Check for decimal separator
		if(sprintf('%.1f',1.0)!='1.0'):
			setlocale(LC_NUMERIC,'C');
		return
	
	def _getfontpath(self):
		#if(!defined('FPDF_FONTPATH') && is_dir(dirname(__FILE__).'/font')):
			#define('FPDF_FONTPATH',dirname(__FILE__).'/font/');
		#return defined('FPDF_FONTPATH') ? FPDF_FONTPATH : '';
		return ""
	
	
	def _putpages(self):
		nb=self.page;
		
		if( not empty(self.AliasNbPages)):#{
			#Replace number of pages
			for n in range(1,nb+1):
				self.pages[n]=str_replace(self.AliasNbPages,nb,self.pages[n]);
			#}
		#}
		if(self.DefOrientation=='P'):#{
			wPt=self.fwPt;
			hPt=self.fhPt;
		#}
		else: #{
			wPt=self.fhPt;
			hPt=self.fwPt;
		#}
		
		filter=fq(self.compress,'/Filter /FlateDecode ','');
		
		for n in range(1,nb+1):#{
			#Page
			self._newobj();
			self._out('<</Type /Page');
			self._out('/Parent 1 0 R');
			#if(isset(self.OrientationChanges[n])): #python
			if self.OrientationChanges.__contains__(n):
				self._out(sprintf('/MediaBox [0 0 %.2f %.2f]',hPt,wPt));
				
			self._out('/Resources 2 0 R');
			
			#print "links=", self.links
			#print "PageLinks=", self.PageLinks
			#if(isset(self.PageLinks[n])):#{ #python
			if (len(self.PageLinks) > n) and self.PageLinks[n] != [] :
				#Links
				annots='/Annots [';
				for pl in self.PageLinks[n] :
					#print "pl=", pl
					rect = sprintf('%.2f %.2f %.2f %.2f', pl[0], pl[1], pl[0] + pl[2], pl[1] - pl[3])
					annots += '<</Type /Annot /Subtype /Link /Rect ['+rect+'] /Border [0 0 0] '
					#print "pl[1]=", pl[1], type(pl[4])
					#print "pl[4]=", pl[4], type(pl[4])
					if (is_string(pl[4])) :
						annots += '/A <</S /URI /URI '+self._textstring(pl[4])+'>>>>'
					else :
						l=self.links[pl[4]];
						#print "l=", l, type(l)
						#if isset(self.OrientationChanges[l[0]]) :
						if self.OrientationChanges.__contains__(n) :
							h = wPt
						else :
							h = hPt
							
						annots += sprintf('/Dest [%d 0 R /XYZ 0 %.2f null]>>',1+2*l[0],h-l[1]*self.k)

				self._out(annots+']')

			self._out('/Contents '+str(self.n+1)+' 0 R>>');
			self._out('endobj');
		
			#TODO:COMPRESS
			#Page content
			#p=fq(self.compress) ? gzcompress(self.pages[n]) : self.pages[n];
			p = self.pages[n]
			
			self._newobj();
			self._out('<<'+filter+'/Length '+str(strlen(p))+'>>');
			self._putstream(p);
			self._out('endobj');
		#}
	
		#Pages root
		self.offsets[1]=strlen(self.buffer);
		self._out('1 0 obj');
		self._out('<</Type /Pages');
		kids='/Kids [';
		
		for i in range(nb):
			kids+=str(3+2*i)+' 0 R ';
			
		self._out(kids+']');
		self._out('/Count '+str(nb) );
		self._out(sprintf('/MediaBox [0 0 %.2f %.2f]',wPt,hPt));
		self._out('>>');
		self._out('endobj');
		return
	
	





	def _putfonts(self):
		nf=self.n;
		
		for diff in self.diffs:#{
			#Encodings
			self._newobj();
			self._out('<</Type /Encoding /BaseEncoding /WinAnsiEncoding /Differences ['+diff+']>>');
			self._out('endobj');
		#}
		
		#mqr=get_magic_quotes_runtime();
		#set_magic_quotes_runtime(0);
		
#		foreach(self.FontFiles as file=>info)
#	{
#		//Font file embedding
#		self._newobj();
#		self.FontFiles[file]['n']=self.n;
#		font='';
#		f=fopen(self._getfontpath().file,'rb',1);
#		if(!f)
#		self.Error('Font file not found');
#		while(!feof(f))
#			font.=fread(f,8192);
#		fclose(f);
#		compressed=(substr(file,-2)=='.z');
#		if(!compressed && isset(info['length2']))
#		{
#			header=(ord(font{0})==128);
#			if(header)
#			{
#				//Strip first binary header
#				font=substr(font,6);
#			}
#			if(header && ord(font{info['length1']})==128)
#			{
#				//Strip second binary header
#				font=substr(font,0,info['length1']).substr(font,info['length1']+6);
#			}
#		}
#		self._out('<</Length '.strlen(font));
#		if(compressed)
#		self._out('/Filter /FlateDecode');
#		self._out('/Length1 '.info['length1']);
#		if(isset(info['length2']))
#		self._out('/Length2 '.info['length2'].' /Length3 0');
#		self._out('>>');
#		self._putstream(font);
#		self._out('endobj');
#	}
#	set_magic_quotes_runtime(mqr);

		#foreach(self.fonts as k=>font)
		#print self.fonts
		for k in self.fonts:#{
			font = self.fonts[k]
			
			
			#Font objects
			self.fonts[k]['n']=self.n+1;
			v_type=font['type'];
			name=font['name'];
			if(v_type=='core'):#{
				#Standard font
				self._newobj();
				self._out('<</Type /Font');
				self._out('/BaseFont /'+name);
				self._out('/Subtype /Type1');
				
				if(name!='Symbol' or name!='ZapfDingbats'):
					self._out('/Encoding /WinAnsiEncoding');
				
				self._out('>>');
				self._out('endobj');
			#}
			elif(v_type=='Type1' or v_type=='TrueType'):#{
				#Additional Type1 or TrueType font
				self._newobj();
				self._out('<</Type /Font');
				self._out('/BaseFont /'+name);
				self._out('/Subtype /'+v_type);
				self._out('/FirstChar 32 /LastChar 255');
				self._out('/Widths '+str(self.n+1)+' 0 R');
				self._out('/FontDescriptor '+str(self.n+2)+' 0 R');
				
				if(font['enc']):#{
					#if(isset(font['diff'])) #python
					if font.__contains__('diff'):
						self._out('/Encoding '+str(nf+font['diff'])+' 0 R');
					else:
						self._out('/Encoding /WinAnsiEncoding');
				#}
				
				self._out('>>');
				self._out('endobj');
				
				#Widths
				self._newobj();
				cw=font['cw'];
				s='[';
				
				#print "cw=",cw
				
				for i in range(32,255+1):
					s+=str(cw[chr(i)])+' ';
					
				self._out(s+']');
				self._out('endobj');
				
				#Descriptor
				self._newobj();
				s='<</Type /FontDescriptor /FontName /'+name;
				
				#foreach(font['desc'] as k=>v)
				for (k,v) in font['desc']:#{
					s+=' /'+k+' '+v;
					file=font['file'];
					if(file): #FIXME: xxx
						#s+=' /FontFile'+(type=='Type1' ? '' : '2').' '.self.FontFiles[file]['n'].' 0 R';
						pass
					
					self._out(s+'>>');
					self._out('endobj');
				#}
			#}
			else:#{
				#Allow for additional types
				#mtd='_put'.strtolower(type);
				#if(!method_exists(this,mtd)):
				self.Error('Unsupported font type: '+v_type);
				#	self.mtd(font);
				
			#}
		#}
		return




	def _putimages(self):
		#FIXME
		filter=fq(self.compress,'/Filter /FlateDecode ','');
		
		#reset(self.images);
		
		#while(list(file,info)=each(self.images))
		for i in range( len( self.images) ):
			file = list(self.images.keys())[i]
			info = self.images[file]
			self._newobj();
			self.images[file]['n']=self.n;
			self._out('<</Type /XObject');
			self._out('/Subtype /Image');
			self._out('/Width '+str(info['w']));
			self._out('/Height '+str(info['h']));
			
			if(info['cs']=='Indexed'):
				self._out('/ColorSpace [/Indexed /DeviceRGB '+str(strlen(info['pal'])/3-1)+' '+str(self.n+1)+' 0 R]');
			else:#{
				self._out('/ColorSpace /'+info['cs']);
				if(info['cs']=='DeviceCMYK'):
					self._out('/Decode [1 0 1 0 1 0 1 0]');
					
			self._out('/BitsPerComponent '+str(info['bpc']));
			
			#if(isset(info['f'])):
			if info.__contains__('f'):
				self._out('/Filter /'+info['f']);
				
			#if(isset(info['parms'])):
			if info.__contains__('parms'):
				self._out(info['parms']);
				
			
			#if(isset(info['trns']) && is_array(info['trns'])):#{
			if info.__contains__('trns') and is_array(info['trns']):
				trns='';
				for i in range(0,count(info['trns'])):
					trns+=info['trns'][i]+' '+info['trns'][i]+' ';
					
				self._out('/Mask ['+trns+']');
			#}
			
			self._out('/Length '+str( strlen(info['data']) )+'>>');
			self._putstream( info['data'] );
			#unset(self.images[file]['data']);
			self.images[file]['data']=None
			self._out('endobj');
			
			
			#Palette
			if(info['cs']=='Indexed'):#{
				self._newobj();
				pal=fq(self.compress,gzcompress(info['pal']),info['pal']);
				self._out('<<'+filter+'/Length '+str(strlen(pal))+'>>');
				self._putstream(pal);
				self._out('endobj');
			#}
		#}
		return
	
	def _putxobjectdict(self):
		#foreach(self.images as image)
		#	self._out('/I'.image['i'].' '.image['n'].' 0 R');
		for image in self.images :
			self._out('/I'+str(self.images[image]['i'])+' '+str(self.images[image]['n'])+' 0 R')
		return
	
	def _putresourcedict(self):
		self._out('/ProcSet [/PDF /Text /ImageB /ImageC /ImageI]');
		self._out('/Font <<');
		
		for font in list(self.fonts.values()):
			self._out('/F'+str(font['i'])+' '+str(font['n'])+' 0 R');
			
		self._out('>>');
		self._out('/XObject <<');
		self._putxobjectdict();
		self._out('>>');
		return
	
	def _putresources(self):
		self._putfonts();
		self._putimages();
		
		#Resource dictionary
		self.offsets[2]=strlen(self.buffer);
		self._out('2 0 obj');
		self._out('<<');
		self._putresourcedict();
		self._out('>>');
		self._out('endobj');
		return
	
	def _putinfo(self):
		self._out('/Producer '+self._textstring('FPDF '+FPDF_VERSION));
		if( not empty(self.title)):
			self._out('/Title '+self._textstring(self.title));
			
		if( not empty(self.subject)):
			self._out('/Subject '+self._textstring(self.subject));
			
		if( not empty(self.author)):
			self._out('/Author '+self._textstring(self.author));
			
		if( not empty(self.keywords)):
			self._out('/Keywords '+self._textstring(self.keywords));
		
		if( not empty(self.creator)):
			self._out('/Creator '+self._textstring(self.creator));
			#self._out('/CreationDate '.self._textstring('D:'.date('YmdHis')));
			#FIXME:date
		return
	
	def _putcatalog(self):
		self._out('/Type /Catalog');
		self._out('/Pages 1 0 R');
		
		if(self.ZoomMode=='fullpage'):
			self._out('/OpenAction [3 0 R /Fit]');
		elif(self.ZoomMode=='fullwidth'):
			self._out('/OpenAction [3 0 R /FitH null]');
		elif(self.ZoomMode=='real'):
			self._out('/OpenAction [3 0 R /XYZ null null 1]');
		elif(not is_string(self.ZoomMode)):
			self._out('/OpenAction [3 0 R /XYZ null null '+(self.ZoomMode/100)+']');
		
		if(self.LayoutMode=='single'):
			self._out('/PageLayout /SinglePage');
		elif(self.LayoutMode=='continuous'):
			self._out('/PageLayout /OneColumn');
		elif(self.LayoutMode=='two'):
			self._out('/PageLayout /TwoColumnLeft');
		return
	
	def _putheader(self):
		self._out('%PDF-'+self.PDFVersion);
		return
	
	def _puttrailer(self):
		self._out('/Size '+str(self.n+1));
		self._out('/Root '+str(self.n)+' 0 R');
		self._out('/Info '+str(self.n-1)+' 0 R');
		return
	
	def _enddoc(self):
		self._putheader();
		self._putpages();
		self._putresources();
		
		#Info
		self._newobj();
		self._out('<<');
		self._putinfo();
		self._out('>>');
		self._out('endobj');
		
		#Catalog
		self._newobj();
		self._out('<<');
		self._putcatalog();
		self._out('>>');
		self._out('endobj');
		
		#Cross-ref
		o=strlen(self.buffer);
		self._out('xref');
		self._out('0 '+str(self.n+1));
		self._out('0000000000 65535 f ');
		for i in range(1,self.n+1):
			self._out(sprintf('%010d 00000 n ',self.offsets[i]));
			
		#Trailer
		self._out('trailer');
		self._out('<<');
		self._puttrailer();
		self._out('>>');
		self._out('startxref');
		self._out(o);
		self._out('%%EOF');
		self.state=3;
		return
	



	def _beginpage(self,orientation):
		self.page+=1;
		self.pages[self.page]='';
		self.state=2;
		self.x=self.lMargin;
		self.y=self.tMargin;
		self.FontFamily='';
		
		#Page orientation
		if(not orientation):
			orientation=self.DefOrientation;
		else:#{
			orientation=strtoupper(orientation[0]);
			if(orientation!=self.DefOrientation):
				self.OrientationChanges[self.page]=True
		#}
		
		if(orientation!=self.CurOrientation):#{
			#Change orientation
			
			if(orientation=='P'):#{
				self.wPt=self.fwPt;
				self.hPt=self.fhPt;
				self.w=self.fw;
				self.h=self.fh;
			#}
			else: #{
				self.wPt=self.fhPt;
				self.hPt=self.fwPt;
				self.w=self.fh;
				self.h=self.fw;
			#}
			
			self.PageBreakTrigger=self.h-self.bMargin;
			self.CurOrientation=orientation;
		#}
		return
	
	def _endpage(self):
		#End of page contents
		self.state=1;
		
	def _newobj(self):
		#Begin a new object
		self.n+=1;
		self.offsets[self.n]=strlen(self.buffer);
		self._out(str(self.n)+' 0 obj');
		return
	


	def _dounderline(self,x,y,txt):
		#Underline text
		up=self.CurrentFont['up'];
		ut=self.CurrentFont['ut'];
		w=self.GetStringWidth(txt)+self.ws*substr_count(txt,' ');
		return sprintf('%.2f %.2f %.2f %.2f re f',x*self.k,(self.h-(y-up/1000*self.FontSize))*self.k,w*self.k,-ut/1000*self.FontSizePt);
	
	

	def _parsejpg(self, file) :
		# Extract info from a JPEG file
		a = GetImageSize(file)
		if not a :
			self.Error('Missing or incorrect image file: '.file)

		if (a[2] != 2) :
			self.Error('Not a JPEG file: '.file)
			
		#if(!isset(a['channels']) || a['channels']==3)
		if ('channels' not in a) or (a['channels']==3) :
			colspace='DeviceRGB'
		elif (a['channels']==4) :
			colspace='DeviceCMYK'
		else :
			colspace='DeviceGray'
				
		#bpc = isset(a['bits']) ? a['bits'] : 8;
		if 'bits' in a :
			bpc = a['bits']
		else :
			bpc = 8
			
		# Read whole file
		f = fopen(file,'rb')
		#data='';
		#while(!feof(f))
		#data.=fread(f,4096);
		#fclose(f);
		data = f.read()
		f.close()

		#return array('w'=>a[0],'h'=>a[1],'cs'=>colspace,'bpc'=>bpc,'f'=>'DCTDecode','data'=>data);
		return {'w':a[0], 'h':a[1],'cs':colspace,'bpc':bpc,'f':'DCTDecode','data':data}


	def _parsepng(self,file):
		#Extract info from a PNG file
		f=fopen(file,'rb');
		if(not f):
			self.Error('Can\'t open image file: '+file);
			
		#Check signature
		if(fread(f,8)!=chr(137)+'PNG'+chr(13)+chr(10)+chr(26)+chr(10)):
			self.Error('Not a PNG file: '+file);
			
		#Read header chunk
		fread(f,4);
		
		if(fread(f,4)!='IHDR'):
			self.Error('Incorrect PNG file: '+file);
			
		w=self._freadint(f);
		h=self._freadint(f);
		bpc=ord(fread(f,1));
		
		if(bpc>8):
			self.Error('16-bit depth not supported: '+file);
			
		ct=ord(fread(f,1));
		
		if(ct==0):
			colspace='DeviceGray';
		elif(ct==2):
			colspace='DeviceRGB';
		elif(ct==3):
			colspace='Indexed';
		else:
			self.Error('Alpha channel not supported: '+file);
			
			
		if(ord(fread(f,1))!=0):
			self.Error('Unknown compression method: '+file);
			
		if(ord(fread(f,1))!=0):
			self.Error('Unknown filter method: '+file);
			
		if(ord(fread(f,1))!=0):
			self.Error('Interlacing not supported: '+file);
			
		fread(f,4);
		parms='/DecodeParms <</Predictor 15 /Colors '+str(fq(ct==2,3,1))+' /BitsPerComponent '+str(bpc)+' /Columns '+str(w)+'>>';
		
		#Scan chunks looking for palette, transparency and image data
		
		pal='';
		trns='';
		data='';
		
		#do #python:
		while True:#{
			n=self._freadint(f);
			v_type=fread(f,4);
			#print "v_type='%s',%d" % (v_type,n)
			
			if(v_type=='PLTE'):#{
				#Read palette
				pal=fread(f,n);
				fread(f,4);
			#}
			elif(v_type=='tRNS'):#{
				#Read transparency info
				t=fread(f,n);
				
				if(ct==0):
					trns=array(ord(substr(t,1,1)));
				elif(ct==2):
					trns=array(ord(substr(t,1,1)),ord(substr(t,3,1)),ord(substr(t,5,1)));
				else:#{
					pos=strpos(t,chr(0));
					if(pos!=false):
						trns=array(pos);
				#}
				
				fread(f,4);
			#}
			
			elif(v_type=='IDAT'):#{
				#Read image data block
				
				data+=fread(f,n)
				fread(f,4);
			#}
			elif(v_type=='IEND'):
				break;
			else:
				fread(f,n+4);
				
			
			#while(n); #python:
			if not n:
				break;
		#}
		
		if(colspace=='Indexed' and empty(pal)):
			self.Error('Missing palette in '+file);
			
		fclose(f);
		#return array('w'=>w,'h'=>h,'cs'=>colspace,'bpc'=>bpc,'f'=>'FlateDecode','parms'=>parms,'pal'=>pal,'trns'=>trns,'data'=>data);
		return {'w':w,'h':h,'cs':colspace,'bpc':bpc,'f':'FlateDecode','parms':parms,'pal':pal,'trns':trns,'data':data}
	


	def _freadint(self,f):
		#Read a 4-byte integer from file
		#a=unpack('Ni',fread(f,4));
		i_val = fread(f,4)
		import struct
		a=struct.unpack('!l',i_val);
		#print a		
		return a[0]
		
		
	def _textstring(self,s):
		#Format a text string
		return '('.encode('utf-8')+self._escape(s)+')';
	
	def _escape(self,s):
		#Add \ before \, ( and )
		return str_replace(')','\\)',str_replace('(','\\(',str_replace('\\','\\\\',s)));
	
	
	def _putstream(self,s):
		self._out('stream');
		self._out(s);
		self._out('endstream');
		return
	
	
	def _out(self,s):
		#Add a line to the document
		if(self.state==2):
			self.pages[self.page]+=s+"\n";
		else:
			self.buffer+=str(s)+"\n";
		return
	
#//End of class

