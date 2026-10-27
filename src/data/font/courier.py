# -*- coding: latin1 -*-

from ._header import *

fpdf_charwidths['courier']={}

for i in range(255+1):
    fpdf_charwidths['courier'][chr(i)]=600;
  
fpdf_charwidths['courierB']=fpdf_charwidths['courier'];
fpdf_charwidths['courierI']=fpdf_charwidths['courier'];
fpdf_charwidths['courierBI']=fpdf_charwidths['courier'];


