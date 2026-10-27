'''
Created on 21 juin 2010. Copyright 2010, David GUEZ
@author: david guez (guezdav@gmail.com)
This file is a part of the source code of the MALODOS project.
You can use and distribute it freely, but have to conform to the license
attached to this project (LICENSE.txt file)
=====================================================================

singleton class for memory bitmap data management and sharing 

'''


from PIL import Image , ImageSequence


try:
    import gfx
except:
    gfx = None

try:
    import pypdfium2 as pdfium
except:
    pdfium = None


import wx
from .fpdf import FPDF
import tempfile
#import sys
import os.path
import algorithms.words
import gui.utilities
import logging
from database import Resources
from database import theConfig
from algorithms.general import str_to_bool
#import bcrypt

class imageData(object):
    val = None
    pil_images = []
    current_image = 0
    image_changed = True
    is_modified=False
    current_file=None
    nb_pages=0
    title=None
    subject=None
    keywords=None
    def __init__(self):
        void_file = os.path.join(Resources.get_resource_dir(),'no_preview.png')
        self.image_void = Image.open(void_file)
    def change_image(self,delta):
        " change the current page by delta"
        self.current_image += delta
        if self.current_image<0 or self.current_image>len(self.pil_images):
            self.current_image -= delta
        else:
            self.image_changed = True
            
    def get_image(self,image_num=None):
        "get a given image (current image if not specified)"
        self.image_changed = False
        if len(self.pil_images)<1 : return self.image_void
        if not image_num : image_num = self.current_image
        if image_num>=0 and image_num<len(self.pil_images) :
            return self.pil_images[image_num]
        else:
            return self.image_void
    def apply_transposition(self,image_num,mode):
        "apply the mode transposition to asked image or all if not image specified"
        if image_num is None:
            for image_num in range(len(self.pil_images)):
                self.pil_images[image_num] = self.pil_images[image_num].transpose(mode)
        else:
            if image_num>=0 and image_num<len(self.pil_images):
                self.pil_images[image_num] = self.pil_images[image_num].transpose(mode)
        self.image_changed = True
        self.is_modified=True
    def swap_x(self,image_num=None):
        "swap the image along the x axis (or all images is image_num is not given)"
        self.apply_transposition(image_num,Image.FLIP_LEFT_RIGHT )
    def swap_y(self,image_num=None):
        "swap the image along the y axis (or all images is image_num is not given)"
        self.apply_transposition(image_num,Image.FLIP_TOP_BOTTOM )
    def rotate(self,image_num=None , nbRot=1):
        "rotate the image by nbRot*90 degrees"
        mode = None
        if nbRot==1 : 
            mode = Image.ROTATE_90
        elif nbRot==2 :
            mode = Image.ROTATE_180
        elif nbRot==3 :
            mode = Image.ROTATE_270
        else :
            return
        self.apply_transposition(image_num, mode)
    def rescale_all(self):
        # first find the highest width/height
        wD=0
        hD=0
        for i in range(len(self.pil_images)):
            (ww,hh) = self.pil_images[i].size
            w=min(ww,hh)
            h=max(ww,hh)
            wD=max(wD,w)
            hD=max(hD,h)
        # then rescale any smaller page to the max
        for i in range(len(self.pil_images)):
            (ww,hh) = self.pil_images[i].size
            if ww<hh:
                self.pil_images[i] = self.pil_images[i].resize((wD, hD), Image.BICUBIC)
            else:
                self.pil_images[i] = self.pil_images[i].resize((hD, wD), Image.BICUBIC)
    def clear_all(self):
        "clear the image data"
        self.pil_images=[]
        self.image_changed = True
        self.is_modified=False
        self.current_file=None
        self.title=None
        self.subject=None
        self.keywords=None
    def add_image(self,img):
        "add an image to the cache"
        if img: self.pil_images.append(img)
    def save_file(self,filename,title=None,description=None,keywords=None,allowEncryption=True):
        "save the image data to a file"
        if len(self.pil_images)<1 : return False
        (__,ext) = os.path.splitext(filename)
        
        if allowEncryption and str_to_bool(theConfig.get_param('encryption', 'encryptData','False',True)):
            try:
                fle = tempfile.mkstemp(ext)
                if not self.save_file(fle[1], title, description, keywords,allowEncryption=False) : return False
                #salt = bcrypt.gensalt()
                #salted_key = bcrypt.hashpw(data.get_current_password(),salt)
                with open(fle[1],'rb') as ff: txt = ff.read()
                algorithms.stringFunctions.save_encrypted_data(txt, filename)
                return True
            except Exception as E:
                logging.exception('Encryping file ' + filename + ':' + str(E))
            finally:
                os.close(fle[0])
                os.remove(fle[1])
        self.is_modified=False
        
        ext=ext.lower()
        if ext in ['.jpg'  , '.jpeg'  ,  '.png',  '.bmp' , '.gif']:
            if len(self.pil_images)>1 :
                gui.utilities.show_message(_('Unable to save multi-page document with the asked extension'))
                return False
            try:
                self.pil_images[0].save(filename)
                return True
            except Exception as E:
                logging.exception('Saving file ' + filename + ':' + str(E))
                return False
        if ext in ['.tif' , '.tiff'] :
            if len(self.pil_images)>1 :
#                try:
#                    import tifffile
#                    tifffile.imsave(filename, self.pil_images[0])
#                try:
#                    import pytiff
#                    tiff_writer = pytiff.TiffWriter(filename)
#                    for i in range(len(self.pil_images)):
#                        img = pytiff.MemoryImage(self.pil_images[i])
#                        tiff_writer.append(img)
#                    return True
                try:
                    import FreeImagePy.FreeImagePy as FIPY
                    fip = FIPY.freeimage()
                    imgList=[]
                    for i in range(len(self.pil_images)):
                        fle = tempfile.mkstemp('.png')
                        imgList.append(fle[1])
                        self.pil_images[i].save(fle[1])
                        os.close(fle[0])
                    fip.convertToMultiPage((x for x in imgList), filename,deleteOld=True)
                    return True
                    
                except Exception as E:
                    print(str(E))
                    gui.utilities.show_message(_('Unable to save multipage tiff document for the time being'))
                    return False
            try:
                self.pil_images[0].save(filename)
                return True
            except Exception as E:
                logging.exception('Saving file ' + filename + ':' + str(E))
                return False
        if ext!='.pdf' :
            gui.utilities.show_message(_('Unknown file extension'))
            return False
        wD=0
        hD=0
        for i in range(len(self.pil_images)):
            (ww,hh) = self.pil_images[i].size
            w=min(ww,hh)
            h=max(ww,hh)
            wD=max(wD,w)
            hD=max(hD,h)
        try:
            doc = FPDF(unit='pt',format=(wD,hD))
            doc.SetAuthor('Generated by MALODOS')
            if title is not None : doc.SetTitle(title.encode('utf-8'))
            if description is not None : doc.SetSubject(description.encode('utf-8'))
            if keywords is not None : doc.SetKeywords(keywords.replace(',',' ').encode('utf-8'))
            list_files=[]
            for i in range(len(self.pil_images)):
                fle_tmp_tuple = tempfile.mkstemp(suffix='.png')
                fle_tmp = fle_tmp_tuple[1];
                os.close(fle_tmp_tuple[0]);
                fle_tmp=os.path.abspath(os.path.normpath(fle_tmp))
                list_files.append(fle_tmp)
                IIm=self.pil_images[i]
                (w,h) = IIm.size
                if w<h :
                    orient='P'
                else:
                    orient='L'
                IIm.save(fle_tmp)
                doc.AddPage(orient)
                doc.Image(fle_tmp, 0, 0 )
            doc.Output(filename)
            for f in list_files : os.remove(f)
            return True
        except Exception as E:
            logging.debug('Saving file ' + str(E))
            return False
    def get_content(self,newProgression=True):
        content = {}
        pd = gui.utilities.getGlobalProgressDialog(_('Character recognition'), '')
        if newProgression : pd.clear()
        n = len(self.pil_images)
        for i in range(n):
            pd.new_sub_step(1.0/n)
            page_words = algorithms.words.ocr_image(self.pil_images[i])
            content = algorithms.words.merge_words(content, page_words)
            pd.finish_current_step()
        gui.utilities.closeGlobalProgressDialog()
        #for w in content: print w
        return content
    def load_file(self,filename,page=None,do_clear=True,allowEncrypted=True):
        "Load a given file into memory (only the asked page if given, all the pages otherwise)"
        if allowEncrypted:
            sss = algorithms.stringFunctions.load_encrypted_data(filename)
            if sss is not None:
                if sss=='' : return False
                (__,ext) = os.path.splitext(filename)
                fle = tempfile.mkstemp(ext)
                with open(fle[1], "wb") as ff: ff.write(sss)
                os.close(fle[0])
                self.load_file(fle[1], page, do_clear,False)
                os.remove(fle[1])
                self.current_file=filename
                return True
                
        if do_clear : self.clear_all()
        self.is_modified=False
        self.current_file=filename
        
        try_pdf = filename.lower().endswith('.pdf')
        old_log_level = wx.Log.GetLogLevel()
        wx.Log.SetLogLevel(0)
        if wx.Image.CanRead(filename):
            nmax = wx.Image.GetImageCount(filename)
            if page:
                if page>=nmax:return
                R = [page]
            else :
                R = list(range(nmax))
            progressor = gui.utilities.ProgressDialog('MALODOS',_('Reading image data, please wait...'))
            for idx in R:
                try:
                    progressor.add_to_current_step(1.0/nmax)
                    wxi = wx.Image(filename,index=idx)
                    img = Image.new('RGB', (wxi.GetWidth(), wxi.GetHeight()))
                    img.frombytes(wxi.GetData())
                    self.nb_pages = nmax
                    self.add_image(img)
                    try_pdf=False
                except:
                    pass
            progressor.destroy()
        
        wx.Log.SetLogLevel(old_log_level)
        
        if not try_pdf:
            self.current_image=0
            return
        # This is executed only is try_pdf is TRUE --> loading file was not possible via wx
        progressor = gui.utilities.ProgressDialog('MALODOS',_('Reading image data, please wait...'))
        try:
            if gfx is not None:
                import locale
                l = locale.getdefaultlocale()
                encoding = l[1] or 'utf-8'
                doc = gfx.open("pdf", filename.encode(encoding))
                self.title=doc.getInfo("title")
                self.subject=doc.getInfo("subject")
                self.keywords=doc.getInfo("keywords")
                nmax = doc.pages
                if page:
                    if page>=nmax:
                        progressor.destroy()
                        return
                    R = [page]
                else :
                    R = list(range(nmax))
                for pagenr in R:
                    progressor.add_to_current_step(1.0/nmax)
                    pdf_page = doc.getPage(pagenr+1)
                    bm = pdf_page.asImage(pdf_page.width,pdf_page.height)
                    I = Image.frombytes("RGB",(pdf_page.width,pdf_page.height),bm)
                    self.nb_pages = nmax
                    self.add_image(I)
                self.current_image=0
            elif pdfium is not None:
                pdf = pdfium.PdfDocument(filename)
                nmax = len(pdf)
                if page is not None:
                    if page >= nmax:
                        progressor.destroy()
                        return
                    R = [page]
                else:
                    R = list(range(nmax))
                for pagenr in R:
                    progressor.add_to_current_step(1.0 / max(1, nmax))
                    bitmap = pdf[pagenr].render(scale=2).to_pil()
                    self.nb_pages = nmax
                    self.add_image(bitmap.convert('RGB'))
                self.current_image = 0
            else:
                raise RuntimeError('Neither swftools (gfx) nor pypdfium2 is available for PDF rendering')
        except Exception as E:
            logging.exception("Unable to open the file " + str(filename) + " because " + str(E))
        finally:
            progressor.destroy()
