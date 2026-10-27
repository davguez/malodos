#!/usr/bin/env python
# -*- coding: latin1 -*-
# PYPDF class definition based on FPDF python class which has been ported from
# PHP by Juan Fernando Estrada http://juanfernandoe.googlepages.com
# originally FPDF for PHP : http://www.fpdf.org

import math
from .fpdf import FPDF

class PYFPDF(FPDF) :
    def __init__(self):
        FPDF.__init__(self)
        FPDF.AliasNbPages(self, "{nb}")

        self.toc = []
        self.toc_auto_num = [0]
        self.toc_current_level = 0

    def is_string(self, s):
        if type(s) in [type(""), type('')] :
            return True
        return False

    def _percent(self, s) :
        if "%" == s[-1] :
            return float(s[:-1])
        else :
            return 0

    def _width(self) :
        return float((self.w - self.rMargin  - self.lMargin - 2 * self.cMargin))

    # adds a page break if h is too high
    def PageBreak(self, h) :
        # If the height h would cause an overflow, add a new page immediately
        if ((self.y + h) > self.PageBreakTrigger and
            not self.InFooter and
            self.AcceptPageBreak()) :
            self.AddPage(self.CurOrientation)
            return 1
        else :
            return 0

    # adds a link target page # and y
    def AddLinkTarget(self, y=-1, page=-1) :
        self.links += [(page, y)]
        n = len(self.links) - 1
        #print "AddLinkTarget(y=",y,",page=",page,")=", n
        return n

    def _get_target_page_from_alias(self, s) :
        # s= "{pageXXX}"
        if "{page" == s[:5] :
            page = int(s[5:-1])
        else :
            page = 0
        #print "_get_target_page_from_alias(%s)=" % s, page
        return page

    #def Image(self, s, wp=None, hp=None, link=None) :
    #    if None == wp :
    #        w = self._width
    #        h = None

    # based on Richard Bondi's "Table of contents" script :
    # http://www.fpdf.org/en/script/script73.php
    def AddTOCEntry(self, title, level = 0, page=None, y = None) :
        if None == page :
            page = self.PageNo()
        if None == y :
            y = self.y

        self.toc += [{'t':title, 'l':level, 'p':"{page%d}" % page, 'y':y}]
        return
    
    def InsertTOC(self,
                  location=1,
                  labelSize=20,
                  entrySize=10,
                  tocfont='Arial',
                  label='Table of Contents') :
        self.AddPage()
        tocstart = self.page

        self.SetFont(tocfont, 'B', labelSize)
        self.Cell(0, 5, label, 0, 1, 'C')
        self.Ln(10)

        for t in self.toc :
            # Offset
            level = t['l']
            if (level > 0) :
                self.Cell(level * 8)
            weight = ''
            if (level == 0) :
                weight = 'B'
            str=t['t']
            self.SetFont(tocfont,weight,entrySize)
            strsize=self.GetStringWidth(str)

            l = self.AddLinkTarget(page=self._get_target_page_from_alias(t['p']), y=t['y'])
            self.Cell(strsize + 2, self.FontSize+2,str,0,0,"",0, l)

            # Filling dots
            self.SetFont(tocfont,'',entrySize)
            PageCellSize=self.GetStringWidth(t['p'])+2
            w=float(self.w-self.lMargin-self.rMargin-PageCellSize-(level*8)-(strsize+2))
            nb = int(w/self.GetStringWidth('.'))
            dots = '.' * nb

            self.Cell(w,self.FontSize+2,dots,0,0,'R',0, l)

            # Page number
            self.Cell(PageCellSize,self.FontSize+2, t['p'], 0,1,'R',0, l)

        if -1 == location :
            # leave toc at the end
            return
        # grab it and move to selected location
        n = self.page
        # number of pages of the TOC
        n_toc = n - tocstart + 1
        
        last = []
        last_links = []

        # store toc pages and links area
        for i in range(tocstart, n+1) : #for ($i = $tocstart;$i <= $n;$i++)
            last += [self.pages[i]]
            #print "i=", i, "self.PageLinks[i]=", self.PageLinks[i]
            #print "len(self.PageLinks)=", len(self.PageLinks)
            if i < len(self.PageLinks) :
                last_links += [self.PageLinks[i]]
            else :
                last_links += []
            
        # move pages
        #print "tocstart=", tocstart, "location=", location
        for i in range(tocstart-1, location-2, -1) :#for($i=$tocstart - 1;$i>=$location-1;$i--)
            if i > 0 :
                for j in range(1,n+1) :
                    self.pages[i] = self.pages[i].replace("{page%d}"%j, "%s"%(j+n_toc))

                self.pages[i+n_toc]=self.pages[i]
                if i < len(self.PageLinks) and (i+n_toc) < len(self.PageLinks) :
                    self.PageLinks[i+n_toc] = self.PageLinks[i]
            
        for i in range(len(last)) :
            #print "page=", page, type(page)
            for j in range(1,n+1) :
                last[i] = last[i].replace("{page%d}"%j, "%s"%(j+n_toc))

        # Put toc pages at insert point
        for i in range(n_toc) : #for($i = 0;$i < $n_toc;$i++)
            self.pages[location + i] = last[i]
            if (location + i) < len(self.PageLinks) and (i < len(last_links)) :
                self.PageLinks[location + i] = last_links[i]
            
        # TODO : mettre à jour les liens internes :
        # si page < toc_start => page
        # si page >= toc_start => page+n_toc
        for i in range(len(self.links)) :
            p = self.links[i][0]
            #print "self.links[",i,"]=", self.links[i],
            if (p >= location) :
                self.links[i] = (p+n_toc, self.links[i][1])
            #print "=>", self.links[i]

        #print "self.links[]=", self.links


    # Section() => adds a section title which level is specified
    def Section(self, h, title, level) :
        # auto num
        if level > self.toc_current_level :
            for l in range(self.toc_current_level, level) :
                self.toc_auto_num += [1]
        elif level == self.toc_current_level :
            self.toc_auto_num[level] += 1
        else :
            print("self.toc_auto_num=", self.toc_auto_num, "level=", level)
            self.toc_auto_num = self.toc_auto_num[:level+1]
            self.toc_auto_num[level] += 1
            
        self.toc_current_level = level
        s = ""
        for l in self.toc_auto_num :
            s += str(l)+"."
        s += " " + title
        self.AddTOCEntry(s, level)
        self.Cell(0, h, s, 0, 1, "F")

    # Chapter() => adds a chapter title which is a level=0 section
    def Chapter(self, h, title) :
        self.Section(h, title, 0)


    # based on Olivier's "Table with MultiCells" :
    # http://www.fpdf.org/en/script/script3.php
    def NbLines(self, w, txt) :
        # Computes the number of lines a MultiCell of width w will take
        cw = self.CurrentFont['cw']

        if w == 0 :
            w = self.w - self.rMargin - self.x
            
        wmax = (w - 2 * self.cMargin) * 1000 / self.FontSize

        s = txt.replace("\r", '')

        nb = len(s)
        
        if (nb > 0 and s[nb - 1] == "\n") :
            nb -= 1

        sep = -1
        i = 0
        j = 0
        l = 0
        nl = 1
        while (i < nb) :
            c = s[i]
            
            if (c == "\n") :
                i +=1
                sep = -1
                j = i
                l = 0
                nl +=1
                continue
            elif (c == ' ') :
                sep = i
                
            l += cw[c]
            
            if (l > wmax) :
                if (sep == -1) :
                    if (i == j) :
                        i +=1 
                else :
                    i = sep + 1
                sep=-1
                j = i
                l = 0
                nl += 1
            else :
                i += 1
                
        return nl


    def Row(self, data, widths) :
        # Calculate the height of the row
        nb = 0
        for i, c in enumerate(data) :
            nb = max(nb, self.NbLines(widths[i], c))
            
        h = 5 * nb
    
        # Issue a page break first if needed
        self.PageBreak(h)
        
        # Draw the cells of the row
        for i in range(len(data)) :
            w = widths[i]
            
            # $a=isset(self.aligns[$i]) ? self.aligns[$i] : 'L'
            a = 'L'

            # Save the current position
            x = self.GetX()
            y = self.GetY()
        
            # Draw the border
            self.Rect(x, y, w, h)
            
            # Print the text
            self.MultiCell(w, 5, data[i], 0, a)
        
            # Put the position to the right of the cell
            self.SetXY(x + w, y)
    
        # Go to the next line
        self.Ln(h)
            

    # wrapper method for FPDF Table()
    def Table(self, tlist, w=None) :
        ncols = len(tlist[0])
        
        if not w :
            wlist = [self._width() / ncols] * ncols
        elif self.is_string(w[0]) :
            wlist = []
            for s in w :
                wlist += [self._width()*self._percent(s)/100]
                
        else :
            wlist = w
            
        for row in tlist :
            self.Row(row, wlist)

    # draws an arrow from x1,y1 to x2,y2  m is the size of the arrow head
    def Arrow(self, x1, y1, x2, y2, m=3) :
        self.Line(x1, y1, x2, y2)

        a = math.pi / 6
        # atan2 does the job
        g = math.atan2((y2 - y1), (x2 - x1))
        
        self.Line(x2, y2,
                  x2 - m * math.cos(a + g),
                  y2 - m * math.sin(a + g))
        self.Line(x2, y2,
                  x2 - m * math.cos(-a + g),
                  y2 - m * math.sin(-a + g))


    # draws a dataflow (flowchart) :
    # first parameters is a list of strings which specifies the entities
    # that will exchange messages or events.
    # each enity can be provided a list of synonyms with the following syntax :
    # task_list = ["Alice=ALICE=A=a", "BOB=B=b"]
    # msg_list describes the dataflow to draw, it's a list of tuples which
    # first member is a string describing the direction "A->B" and
    # second member is the text to print, example :
    # m = [("A->B", "draws an arrow from Alice to Bob"),
    #      ("B->A", "draws an arrow form Bob to Alice")]
    # please refer to the provided sample. 
    def DataFlow(self, task_list, msg_list, w=100.0) :
        #print "self.bMargin=", self.bMargin
        #print "self.tMargin=", self.tMargin
        
        # w => dataflow width
        tasks_name = {}
        tasks_x = {}
        ntasks = float(len(task_list))
        # largeur de la zone affichable en mm
        #largeuraffmm = float((self.w - self.rMargin  - self.lMargin - 2 * self.cMargin))
        largeuraffmm = self._width()
        largeurmm = largeuraffmm * w / 100.0
        
        #print "largeurmm=", largeurmm
        
        # init task list
        # preparation abscisses des tâches + synonym
        for i in range(len(task_list)) :
            l = task_list[i].split("=")
            key = l[0].strip()
            tasks_name[key] = key
            tasks_x[key] = self.lMargin + (largeuraffmm / 2) + i * largeurmm / (ntasks-1) - largeurmm/2
            
            if len(l) > 1 :
                for syn in l[1:] :
                    tasks_name[syn] = key

        #print "len(tasks_x)=", len(tasks_x)
        #print "tasks_x=", tasks_x
        #print "tasks_name=", tasks_name

        h = 8 # paramètre hauteur de ligne
        self.Ln(h)
        for t in tasks_x :
            self.Text(tasks_x[t] -self.GetStringWidth(t)/2.0, self.y, t)
        self.Ln(h)
            
        for (d, s) in msg_list :
            if d :
                ft = d.split("->")
                #print "ft=", ft
            
                if ft[0] in tasks_name and ft[1] in tasks_name :
                    # draw axis
                    for t in tasks_x :
                        self.SetDrawColor(0, 0, 0) # black
                        self.Line(tasks_x[t], self.y - h/2.0, tasks_x[t], self.y + h/2.0)
                
                    fro = tasks_name[ft[0]]
                    to = tasks_name[ft[1]]

                    x1 = tasks_x[fro]
                    x2 = tasks_x[to]

                    if x1 == x2 :
                        m = 1.5
                        self.Text(x1 + 2 * m, self.y, s)
                        self.Ln(1)
                        self.SetDrawColor(255, 0, 0) # red
                        self.Line(x1 - m, self.y - m, x1 + m, self.y + m)
                        self.Line(x1 - m, self.y + m, x1 + m, self.y - m)
                    else :
                        self.SetDrawColor(0, 0, 0) # black
                        self.Text((0.5*(x1 + x2))-self.GetStringWidth(s)/2.0, self.y, s)
                        self.Ln(1)
                        self.Arrow(x1, self.y, x2, self.y)
            else :
                # not d
                if s :
                    x1 = self.lMargin + (largeuraffmm / 2) - largeurmm/2
                    self.Text(x1, self.y, s)
                else :
                    # draw axis
                    for t in tasks_x :
                        self.SetDrawColor(0, 0, 0) # black
                        self.Line(tasks_x[t], self.y - h/2.0, tasks_x[t], self.y + h/2.0)
                    

            self.Ln(h-1)

            if self.PageBreak(h) :
                # Automatic page break
                for t in tasks_x :
                    self.Text(tasks_x[t] -self.GetStringWidth(t)/2.0, self.y, t)
                self.Ln(h-1)


