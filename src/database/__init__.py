'''
Created on 21 juin 2010. Copyright 2010, David GUEZ
@author: david guez (guezdav@gmail.com)
This file is a part of the source code of the MALODOS project.
You can use and distribute it freely, but have to conform to the license
attached to this project (LICENSE.txt file)
=====================================================================
'''
from . import db
import logging
import gui.utilities
import Crypto.Hash.MD5 as md5
import bcrypt

currentPassword=''
def set_current_password(pss):
    global currentPassword
    currentPassword=pss
def transform_password(password):
    if isinstance(password, str):
        password = password.encode('utf-8')
    M =md5.new()
    M.update(password)
    S1 = M.digest()
    x = password[::-1]
    M.update(x)
    S2 = M.digest()
    password = S1+S2
    return password
def record_current_password(pss):
    pss = transform_password(pss)
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pss, salt)
    theConfig.set_param('encryption','salt',salt.decode('utf-8'))
    theConfig.set_param('encryption','hash',hashed.decode('utf-8'))
    theConfig.commit_config()
    set_current_password(pss)

def get_password(msg=_('Please gives your password for data encryption/decryption.'),checker=lambda pss:False):
    global currentPassword
    
    if hasattr(checker, '__contains__') and len(checker)==2 and checker[0] is not None and checker[1] is not None:
        salt = checker[0]
        hashed = checker[1]
        if isinstance(salt, str):
            salt = salt.encode('utf-8')
        if isinstance(hashed, str):
            hashed = hashed.encode('utf-8')
        def the_checker(pss):
            b = bcrypt.hashpw(pss, salt)
            if b != hashed:
                cont = gui.utilities.ask(_('The password does not corresponds to the registered one, do you want to give it back ?..'))
            else:
                cont=False
            return cont
        checker=the_checker

    cont = True
    while cont:
        password = gui.utilities.ask_password(msg)
        if len(password)==0:
            cont=False
        elif len(password)<4:
            gui.utilities.show_message(_('The password length must be at least 4  char long (at least 8 is recommended). Please gives another one..'))
        else:
            password=transform_password(password)
            if callable(checker) :
                cont=checker(password)
            else : 
                cont=False       
    currentPassword=password
    return password
    
def get_current_password(msg=_('Please gives your password for data encryption/decryption.'),forceAsk=False,checkOld=True):
    if not forceAsk and len(currentPassword)>=8 : return currentPassword
    salt = theConfig.get_param('encryption','salt','')
    hashed = theConfig.get_param('encryption','hash','')      
    psw = get_password(msg, (salt,hashed))
    if psw != '':
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(psw, salt)
        theConfig.set_param('encryption','salt',salt.decode('utf-8'))
        theConfig.set_param('encryption','hash',hashed.decode('utf-8'))
        theConfig.commit_config()
    set_current_password(psw)
        
    return psw
def clear_current_password():
    set_current_password('')

theConfig = db.Configuration()
theBase=None
def initialize():
    global theBase
    try:
        theBase = db.Base(theConfig.get_database_name())
    except Exception as E:
        logging.exception( "Unable to connect to database->"+str(E))