'''
Created on 3 oct. 2010. Copyright 2010, David GUEZ
@author: david guez (guezdav@gmail.com)
This file is a part of the source code of the MALODOS project.
You can use and distribute it freely, but have to conform to the license
attached to this project (LICENSE.txt file)
=====================================================================
printing a document

'''


import wx
from data import theData

class docPrinter(wx.Printout):
    '''
    class for printing the image present in data singleton 
    '''
    def __init__(self):
        "Prepares the Printing object."
        wx.Printout.__init__(self)
        self.printer_config = wx.PrintData()
        self.printer_config.SetPaperId(wx.PAPER_A4)
    def HasPage(self, page_num):
        "Does the page exists."
        return page_num<=theData.nb_pages
    def GetPageInfo(self):
        return (1, 1, 1, 1)
    def OnPrintPage(self, page_num):
        "Print the given page"
        dc = self.GetDC()
        if not dc : return False
        dcSize = dc.GetSize()
        pil_image = theData.get_image(page_num-1)
        if not pil_image : return False
        img = wx.Image(pil_image.size[0],pil_image.size[1])
        print("PIL image size is {0}".format(pil_image.size))
        img.SetData(pil_image.convert("RGB").tobytes())
        img.Rescale(dcSize[0],dcSize[1],wx.IMAGE_QUALITY_HIGH)
        print("print image size is {0}".format(dcSize))
        bm = img.ConvertToBitmap()        
        dc.DrawBitmap(bm,0,0)
        return True
    