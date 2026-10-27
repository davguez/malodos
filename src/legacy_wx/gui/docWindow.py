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
from database import Resources
import wx
import wx.lib.buttons
from PIL import Image
#from BufferedCanvas import BufferedCanvas
class docWindow(wx.Window) :
#    class MyCanvas(BufferedCanvas):
#        theBitmap=None
#        def __init__(self,parent,ID=-1):
#            BufferedCanvas.__init__(self,parent,ID)
#        def SetBitmap(self,bitmap):
#            self.theBitmap=bitmap
#        def draw(self, dc):
##            dc.SetBackground(wx.Brush("White"))
##            dc.Clear()
#            if self.theBitmap is not None : dc.DrawBitmap(self.theBitmap,0,0)
    
    center=[0.5,0.5]
    window=[1.0,1.0]
    dragFirstCenter = None
    dragFirstPos = None

    if hasattr(Image, 'Resampling'):
        RESAMPLE_LANCZOS = Image.Resampling.LANCZOS
    else:
        RESAMPLE_LANCZOS = Image.ANTIALIAS
    #===========================================================================
    # constructor (gui building)
    #===========================================================================
    def __init__(self, parent,doc_id):
        self.center = [0.5 , 0.5]
        self.window=[1.0,1.0]
        wx.Window.__init__(self, parent, doc_id)
        self.panel = wx.Panel(self, -1)
        self.img = None
        self.totalWin = wx.BoxSizer(wx.VERTICAL)
        self.buttonPart = wx.BoxSizer(wx.HORIZONTAL)
        self.btLeft = wx.BitmapButton(self.panel,-1,wx.Bitmap(Resources.get_icon_filename('PREVIOUS_PAGE')))
        self.btLeft.SetToolTipString(_('Previous page'))
        self.btRight = wx.BitmapButton(self.panel,-1,wx.Bitmap(Resources.get_icon_filename('NEXT_PAGE')))
        self.btRight.SetToolTipString(_('Next page'))
        self.btZoomPlus = wx.BitmapButton(self.panel,-1,wx.Bitmap(Resources.get_icon_filename('ZOOM_PLUS')))
        self.btZoomPlus.SetToolTipString(_('Zoom'))
        self.btZoomMinus = wx.BitmapButton(self.panel,-1,wx.Bitmap(Resources.get_icon_filename('ZOOM_MINUS')))
        self.btZoomMinus.SetToolTipString(_('Unzoom'))
        self.btRotate90 = wx.BitmapButton(self.panel,-1,wx.Bitmap(Resources.get_icon_filename('ROTATE_90')))
        self.btRotate90.SetToolTipString(_('Rotate clockwise'))
        self.btRotate270 = wx.BitmapButton(self.panel,-1,wx.Bitmap(Resources.get_icon_filename('ROTATE_270')))
        self.btRotate270.SetToolTipString(_('Rotate anti-clockwise'))
        self.btFlipX = wx.BitmapButton(self.panel,-1,wx.Bitmap(Resources.get_icon_filename('FLIP_X')))
        self.btFlipX.SetToolTipString(_('Flip horizontally'))
        self.btFlipY = wx.BitmapButton(self.panel,-1,wx.Bitmap(Resources.get_icon_filename('FLIP_Y')))
        self.btFlipY.SetToolTipString(_('Flip vertically'))
        self.btAllDocs = wx.lib.buttons.GenBitmapToggleButton(self.panel,-1,wx.Bitmap(Resources.get_icon_filename('ALL_DOCS')))
        self.btAllDocs.SetToolTipString(_('Apply to all pages'))
        #self.btAllDocs.Show(False)
        
        self.lbImage = wx.StaticText(self.panel,-1,_('No page'))
        #self.canvas = self.MyCanvas(self.panel,-1)
        self.canvas = wx.StaticBitmap(self.panel, -1)
        #self.canvas.SetDoubleBuffered(False)
        self.totalWin.Add(self.buttonPart,0,wx.EXPAND)
        self.totalWin.Add(self.canvas,1,wx.GROW|wx.EXPAND)
        self.buttonPart.Add(self.btLeft ,0)
        self.buttonPart.Add(self.btRight,0)
        self.buttonPart.Add(self.btZoomPlus ,0)
        self.buttonPart.Add(self.btZoomMinus,0)
        self.buttonPart.Add(self.btRotate270 ,0)
        self.buttonPart.Add(self.btRotate90,0)
        self.buttonPart.Add(self.btFlipX,0)
        self.buttonPart.Add(self.btFlipY,0)
        self.buttonPart.Add(self.btAllDocs,0)
        self.buttonPart.Add(self.lbImage,1,wx.ALIGN_CENTER_VERTICAL|wx.ALL)

        self.Bind(wx.EVT_BUTTON, self.actionPreviousImage, self.btLeft)
        self.Bind(wx.EVT_BUTTON, self.actionNextImage, self.btRight)
        self.Bind(wx.EVT_BUTTON, self.actionZoomPlus, self.btZoomPlus)
        self.Bind(wx.EVT_BUTTON, self.actionZoomMinus, self.btZoomMinus)
        self.Bind(wx.EVT_BUTTON, self.actionRotate90, self.btRotate90)
        self.Bind(wx.EVT_BUTTON, self.actionRotate270, self.btRotate270)
        self.Bind(wx.EVT_BUTTON, self.actionFlipX, self.btFlipX)
        self.Bind(wx.EVT_BUTTON, self.actionFlipY, self.btFlipY)
        
        self.Bind(wx.EVT_SIZE,self.onResize)
        self.Bind(wx.EVT_MOUSEWHEEL,self.onMouseWheelEvent)
        self.canvas.Bind(wx.EVT_MOTION,self.onMouseMotion)
        self.canvas.Bind(wx.EVT_LEFT_UP,self.onMouseLeftUp)
        
        self.canvas.SetSize(wx.Size(200,300))
        self.panel.SetSizerAndFit(self.totalWin)
        self.showCurrentImage()
    def resetView(self):
        self.center = [0.5,0.5]
        self.window = [1.0,1.0]
    def onMouseLeftUp(self,event):
        self.dragFirstPos = None
        self.showCurrentImage(Image.BILINEAR)
#        self.canvas.Refresh(False)
    def onMouseWheelEvent(self,event):
        delta = float(event.GetWheelRotation()) / event.GetWheelDelta() * 0.05
        self.do_zoom(delta)
    def onMouseMotion(self,event):
        if not event.Dragging() : return
        if not self.dragFirstPos :
            self.dragFirstPos = event.GetPosition()
            self.dragFirstCenter = self.center[:]
        delta  = event.GetPosition() - self.dragFirstPos
        pixelSize = self.canvas.GetSize()
        self.center[0] = self.dragFirstCenter[0] - self.window[0] / pixelSize[0] * delta[0]
        self.center[1] = self.dragFirstCenter[1] - self.window[1] / pixelSize[1] * delta[1]
        self.showCurrentImage(Image.NEAREST,False)
        #print self.dragFirstCenter
    def getViewRect(self):
        s=self.img.size
        # build and test the viewing rect
        viewRect = wx.Rect(
            int((self.center[0]-self.window[0]/2)*s[0]),
            int((self.center[1]-self.window[1]/2)*s[1]),
            int(self.window[0]*s[0]),
            int(self.window[1]*s[1]),
        )
        if viewRect.x<0 : viewRect.x=0;
        if viewRect.y<0 : viewRect.y=0;
        if viewRect.x>= s[0] : viewRect.x = s[0] -1
        if viewRect.y>= s[1] : viewRect.y = s[1] -1
        if viewRect.width<1 : viewRect.width = 1
        if viewRect.height<1 : viewRect.height = 1
        if viewRect.width > s[0] : viewRect.width = s[0]
        if viewRect.height > s[1] : viewRect.height = s[1]
        if viewRect.x + viewRect.width > s[0] : viewRect.x = s[0] - viewRect.width
        if viewRect.y + viewRect.height > s[1] : viewRect.y = s[1] - viewRect.height
        self.center[0] = float(viewRect.x + viewRect.width/2)/s[0]  
        self.center[1] = float(viewRect.y + viewRect.height/2)/s[1]
        self.window[0] = float(viewRect.width) / s[0]  
        self.window[1] = float(viewRect.height) / s[1]  
        return viewRect
    #===========================================================================
    # show the current image in the canvas
    #===========================================================================
    def showCurrentImage(self,quality=Image.BILINEAR,do_layout=True):
        self.canvas.SetEvtHandlerEnabled(False)
        MAX_RESOLUTION = 1024
        if do_layout:
            self.panel.SetSize(self.GetSize())
            self.totalWin.Layout()
        if len(data.theData.pil_images)==0:
            self.lbImage.SetLabel(_('no page'))
        else:
            self.lbImage.SetLabel('page ' + str(data.theData.current_image+1) + '/' + str(len(data.theData.pil_images)))
        if data.theData.image_changed or self.img is None:
            self.img = data.theData.get_image().convert('RGB')
            #self.img = wx.EmptyImage(pil_image.size[0],pil_image.size[1])
            #self.img.SetData(pil_image.convert("RGB").tostring())
            s =self.img.size
            if s[0] > MAX_RESOLUTION or s[1]>MAX_RESOLUTION :
                q = [ MAX_RESOLUTION/float(s[0]) ,MAX_RESOLUTION/float(s[1]) ]
                qmin = min(q)
                if qmin <1 :
                    res_final = [ int(s[0] * qmin) , int(s[1] * qmin) ]
                    self.img=self.img.resize(res_final,self.RESAMPLE_LANCZOS)
        #if self.img is None: return
        viewRect = self.getViewRect()

        # calculating stretching factors
        img_size=self.img.size
        if do_layout:
            self.canvasSize= self.canvas.GetSize()
            self.canvasPos = self.canvas.GetPosition()

        size = self.canvas.GetSize()
        origSize = viewRect.GetSize()
        # factor to apply in each direction
        factors = [ float(self.canvasSize[0])/origSize[0] , float(self.canvasSize[1])/origSize[1] ] # factor to pass from image to screen
        # take only the lowest factor and apply to both x and y direction
        # (thus keeping the initial aspect ratio)
        if factors[0]>factors[1] : # keep y @ canvas size
            q = factors[1]
            s = q * img_size[0] # size in screen that should be used along x
            if s>self.canvasSize[0]: # if x size would be too big 
                w =self.canvasSize[0]/q # part of the image corresponding to canvas size along x
                viewRect.x=viewRect.x+viewRect.width/2-w/2
                if viewRect.x<0:
                    w+=viewRect.x
                    viewRect.x=0
                viewRect.width=int(w)
            else:
                viewRect.x=0
                viewRect.width=img_size[0]
            size[0] = int(q*viewRect.width)
        else:# keep x @ canvas size
            q = factors[0]
            s = q * img_size[1] # size in screen that should be used along y
            if s>self.canvasSize[1]: # if y size would be too big 
                h =self.canvasSize[1]/q # part of the image corresponding to canvas size along y
                viewRect.y=viewRect.y+viewRect.height/2-h/2
                viewRect.height=int(h)
            else:
                viewRect.y=0
                viewRect.height=img_size[1]
            size[1] = int(q*viewRect.height)
        theImage = self.img.crop((viewRect.x,viewRect.y,viewRect.x+viewRect.width-1,viewRect.y+viewRect.height-1))
        if size[0]>0 and size[1]>0:
            # do stretching and drawing if sizes are ok
            displ = [ int(self.canvasPos[0] + (self.canvasSize[0] - size[0])/2) , int(self.canvasPos[1] + (self.canvasSize[1] - size[1])/2) ]
            self.canvas.SetPosition(displ)
            self.canvas.SetSize((int(size[0]), int(size[1])))
            resized = theImage.resize((int(size[0]), int(size[1])), quality)
            wxbm = wx.Bitmap.FromBuffer(int(size[0]),int(size[1]),resized.tobytes())
            self.canvas.SetBitmap(wxbm)
        self.canvas.SetEvtHandlerEnabled(True)
    #===========================================================================
    # on prev button click
    #===========================================================================
    def actionPreviousImage(self,event):
        if data.theData.current_image>0 :
            data.theData.change_image(-1)
            self.showCurrentImage(do_layout=False)
    #===========================================================================
    # on next button click
    #===========================================================================
    def actionNextImage(self,event):
        if data.theData.pil_images and data.theData.current_image+1<len(data.theData.pil_images) :
            data.theData.change_image(1)
            self.showCurrentImage(do_layout=False)
    #===========================================================================
    # zoom
    #===========================================================================
    def do_zoom(self,delta):
        self.window[0] -= delta;
        self.window[1] -= delta;
        if self.window[0]<0 : self.window[0]=0;
        if self.window[1]<0 : self.window[1]=0;
        if self.window[0]>1 : self.window[0]=1;
        if self.window[1]>1 : self.window[1]=1;
        self.showCurrentImage(Image.BILINEAR,do_layout=False)
    #===========================================================================
    # zoom+
    #===========================================================================
    def actionZoomPlus(self,event):
        self.do_zoom(0.05)
    #===========================================================================
    # zoom-
    #===========================================================================
    def actionZoomMinus(self,event):
        self.do_zoom(-0.05)
    #===========================================================================
    # Rotate 90 degrees
    #===========================================================================
    def actionRotate90(self,event):
        if not data.theData.pil_images : return
        if self.btAllDocs.GetValue():
            data.theData.rotate(image_num = None, nbRot = 3)
        else:
            data.theData.rotate(image_num = data.theData.current_image, nbRot = 3)
        self.showCurrentImage(Image.BILINEAR,False)
    #===========================================================================
    # Rotate -90 degrees
    #===========================================================================
    def actionRotate270(self,event):
        if not data.theData.pil_images : return
        if self.btAllDocs.GetValue():
            data.theData.rotate(image_num = None, nbRot = 1)
        else:
            data.theData.rotate(image_num = data.theData.current_image, nbRot = 1)
        self.showCurrentImage(Image.BILINEAR,False)
    #===========================================================================
    # Flip along X axis
    #===========================================================================
    def actionFlipX(self,event):
        if not data.theData.pil_images : return
        if self.btAllDocs.GetValue():
            data.theData.swap_x(image_num = None)
        else:
            data.theData.swap_x(image_num = data.theData.current_image)
        self.showCurrentImage(Image.BILINEAR,False)
    #===========================================================================
    # Flip along Y axis
    #===========================================================================
    def actionFlipY(self,event):
        if not data.theData.pil_images : return
        if self.btAllDocs.GetValue():
            data.theData.swap_y(image_num = None)
        else:
            data.theData.swap_y(image_num = data.theData.current_image)
        self.showCurrentImage(Image.BILINEAR,False)
    #===========================================================================
    # called when resizing window/pane
    #===========================================================================
    def onResize(self,event):
        self.totalWin.Layout()
        self.showCurrentImage(Image.BILINEAR,True)