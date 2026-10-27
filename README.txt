Created on 21 juin 2010. Copyright 2010, David GUEZ
@author: david guez (guezdav@gmail.com)
This file is a part of the source code of the MALODOS project.
You can use and distribute it freely, but have to conform to the license
attached to this project (LICENSE.txt file)


MALODOS (for MAnagement of LOcal DOcument System) is simple but usefull software aimed to help the process of archiving and navigate between the documents presents in your harddrive.

It is written in python and mainly merges numereous external libraries to give a fast and simple way to scan and numerically record your personal documents (such as invoices, taxe declaration, etc...)

Being written in python, it is portable (works on windows and linux at least, not tested on other systems)

The libraries onto which it is built are essentially:
- pysqlite3 (and thus sqlite, for database management)
- twain (for scanner access under windows)
- sane (for scanner access under linux)
- Pillow
- wxpython (and thus wxwidgets) for the GUI
- swftools (legacy option for pdf reading)
- pypdfium2 (modern fallback for pdf reading)
- pypdf (for pdf creation)
- pycryptodome and bcrypt (encryption/password handling)

The icons are taken from this website : http://icones.pro

This project is hosted on google code at the following address and can be downloaded from there:
http://code.google.com/p/malodos/downloads/detail?name=homeDoc-0.1.zip&can=2&q=

Python compatibility:
- Current target runtime: Python 3.13 and above.
