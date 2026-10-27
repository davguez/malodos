# -*- coding: utf-8 -*-
'''
Created on 21 juin 2010. Copyright 2010, David GUEZ
@author: david guez (guezdav@gmail.com)
This file is a part of the source code of the MALODOS project.
You can use and distribute it freely, but have to conform to the license
attached to this project (LICENSE.txt file)
=====================================================================
    algorithms operating on strings
'''
import database
import algorithms.words
import datetime
import Crypto.Cipher.AES as AES
import Crypto.Hash.MD5 as md5
from os import urandom
#import gui.utilities
import logging
import unicodedata

ENCRYPT_TEXT='MALODOS encrypted'
ENCRYPT_IV_LENGTH=16


def _to_bytes(value, encoding='utf-8'):
    if isinstance(value, bytes):
        return value
    if isinstance(value, str):
        return value.encode(encoding)
    return str(value).encode(encoding)

def char_type(c):
    if c.isspace() : return 0
    if c.isdigit() : return 1
    if c.isalpha() or c=='!': return 2
    if c=='"' or c=="'" : return 3
    return 4

def str_next_elem(S):
    ''' return the next element of a string and the trailing string 
    '''
    if S=="" : return ("","")
    if S[0]=='"' or S[0]=="'": # everything inside comma is atomic
        p=1
        while p<len(S):
            if S[p] == S[0] : break
            p+=1
        return (S[0:p+1] , S[p+1:])

    t = char_type(S[0]) # otherwise : continue until char change type (ie. from num to str) 
    p=1
    while p<len(S): # go over the string
        t2 = char_type(S[p]) 
        if (t2 != t) and not (t==2 and t2==1) : break # if char type change, stop
        p+=1 # next char
    if p>=len(S): # if string end reached : nothing left
        R=  ( S , '')
    else:
        R = ( S[:p] , S[p:] ) # else cut it and return the two parts
    if t==0 : R=(' ',R[1])
    return R
        
def cut_str(the_str):
    '''
    cut a string and return a list of element
    each element could be a date string, a number, or a text entry
    '''
    elems=[]
    dateStep=0
    dateStr=''
    while the_str!="" :
        [E,the_str] = str_next_elem(the_str) # get the next entry
        if E==' ' or E=='' : continue # skip blanks
        if dateStep==1 or dateStep==3 : # in case the month or year separator is expected
            if E != '-'  and E != '/' and E!='.': # and not encountered -> error
                dateStep = 0
                elems.append(dateStr)
                elems.append(E)
            else: # else go wait the next field of the date
                dateStr += '-'
                dateStep+=1
            continue
        elif dateStep==2 : # in case the month field of date is expected  
            if not E[0].isdigit() or int(E)>12 or int(E)<1:
                dateStep = 0 # error if not a number between 1 and 12
                elems.append(dateStr)
                elems.append(E)
            else:
                dateStr += E # wait year now 
                dateStep+=1
            continue
        elif dateStep==4 : # if the year is expected
            if not E[0].isdigit(): # error if not a number
                dateStep = 0
                elems.append(dateStr)
                elems.append(E)
            else:
                E=int(E,10)
                if E<100 and E>60 : E+=1900 # treat the case where only the decade is given
                if E<100 : E+=2000 # treat the case where only the decade is given
                dateStr += str(E)
                dateStep=0
                dateStr = datetime.datetime.strptime(dateStr,"%d-%m-%Y").strftime("%Y-%m-%d")
                elems.append(dateStr)
            continue
        if dateStep==0 and E[0].isdigit() and int(E)>0 and int(E)<=31: # could be the beginning of a date
            dateStep=1
            dateStr=E
            continue
        if dateStep==0 and E[0].isdigit() and int(E)>1900 and int(E)<=2100: # assumed to be a year
            dateStr = datetime.datetime.strptime("01-01-"+str(E),"%d-%m-%Y").strftime("%Y-%m-%d")
            elems.append(dateStr)
            continue
        elems.append(E)
        
    return elems
        
        
def is_world(e):
    '''
    is this string a text value
    '''
    return e[0].isalnum() or e[0]=='!' \
           or (e[0]=="'" and e[-1]=="'")\
           or (e[0]=='"' and e[-1]=='"')


def str_field_constraint(field_name,req_value):
    '''
    replace a simple request element into its SQL equivalent along with its parameters
    '''
    
    S=''
    lst=[]
    
    field_name = field_name.upper()
    if field_name[-1]=='*':
        field_name=field_name[0:-1]
        strict_comp=True
    else:
        strict_comp=False
    

    req_value = req_value.lower()
    if req_value[0]=="'" or req_value[0]=='"' :
        req_value_search = req_value[1:-1]
        searchField = 'KEYWORD'
    else:
        req_value_search = algorithms.words.phonex(req_value)
        searchField = 'soundex_word'   

    if req_value_search[0]=='!':
        req_value_search=req_value_search[1:]
        whole_word=True
    else:
        whole_word=False

    
    
    if field_name == 'ANY':
        if whole_word:
            S= "( " + searchField +" = ?)"
            lst=[ req_value_search  ]
        else:
            S= "( " + searchField +" LIKE ?)"
            lst=[ '%' + req_value_search + '%' ]
    elif field_name == 'TITLE' or field_name == 'TI':
        if whole_word:
            S= "( " + searchField +" = ?" + " AND FIELD=" +  str(database.db.Base.ID_TITLE) +  ")"
            lst=[ req_value_search ]
        else:
            S= "( " + searchField +" LIKE ?" + " AND FIELD=" +  str(database.db.Base.ID_TITLE) +  ")"
            lst=[ '%' + req_value_search + '%' ]
    elif field_name == 'DESCRIPTION' or field_name == 'DE':
        if whole_word:
            S= "( " + searchField +" = ?" + " AND FIELD=" +  str(database.db.Base.IDX_DESCRIPTION) +  ")"
            lst=[ req_value_search ]
        else:
            S= "( " + searchField +" LIKE ?" + " AND FIELD=" +  str(database.db.Base.IDX_DESCRIPTION) +  ")"
            lst=[ '%' + req_value_search + '%' ]
    elif field_name == 'TAG' or field_name == 'TA':
        S= "( "+ searchField +"= ?" + " AND FIELD=" +  str(database.db.Base.ID_TAG) +  ")"
        lst=[req_value_search]
    elif field_name == 'FULLTEXT' or field_name == 'FU':
        if whole_word:
            S= "( "+searchField +" = ?"+ " AND FIELD=" +  str(database.db.Base.ID_FULL_TEXT) +  ")"
            lst=[ req_value_search  ]
        else:
            S= "( "+searchField +" LIKE ?"+ " AND FIELD=" +  str(database.db.Base.ID_FULL_TEXT) +  ")"
            lst=[ '%' + req_value_search + '%' ]
    elif field_name=="DATE" or field_name == 'DD':
        S= "( documentDate = ?)"
        lst=[req_value]
    elif field_name=="DATEMIN":
        if strict_comp :
            S= "( documentDate > ?)"
        else:
            S= "( documentDate >= ?)"
        lst=[req_value]
    elif field_name=="DATEMAX":
        if strict_comp :
            S= "( documentDate < ?)"
        else:
            S= "( documentDate <= ?)"
        lst=[req_value]
    elif field_name=="REGISTERDATE" or field_name == 'RD':
        S= "( registerDate = ?)"
        lst=[req_value]
    elif field_name=="REGISTERDATEMIN":
        if strict_comp :
            S= "( REGISTERDATE > ?)"
        else:
            S= "( REGISTERDATE >= ?)"
        lst=[req_value]
    elif field_name=="REGISTERDATEMAX":
        if strict_comp :
            S= "( REGISTERDATE < ?)"
        else:
            S= "( REGISTERDATE <= ?)"
        lst=[req_value]
    return (S , lst)

def req_to_sql(req):
    '''
    transform a simple request string into its SQL equivalent
    '''
    elems = cut_str(req) # transform the string to list of elements 
    #print ','.join(elems)
    S=''
    SS=''
    L=[]
    LL = []
    i = 0
    had_operator=True
    while i<len(elems): # go over elements
        e = elems[i]
        if is_world(e) :
            if e=='and' or e=='or' or e=='not' or e=='xor' :
                had_operator=True
                S+=' ' + e +' '
                SS+=' ' + e +' '
                i+=1
            else:
                if not had_operator:
                    S += ' and '
                    SS += ' and '
                if  i+2<len(elems) and (elems[i+1]==':' or elems[i+1]=='=')\
                      and is_world(elems[i+2]):
                    [ss,ll]=str_field_constraint(e,elems[i+2])
                    S+=ss
                    L+=ll
                    i+=3
                elif i+2<len(elems) and (elems[i].upper()=='DATE' or elems[i].upper()=='REGISTERDATE') \
                      and (elems[i+1]=='<' or elems[i+1]=='<=') \
                      and is_world(elems[i+2]):
                    e=e+'MAX'
                    if elems[i+1][-1]!='=': e=e+'*'
                    [ss,ll]=str_field_constraint(e,elems[i+2])
                    S+=ss
                    L+=ll
                    i+=3
                elif i+2<len(elems) and (elems[i].upper()=='DATE' or elems[i].upper()=='REGISTERDATE') \
                      and (elems[i+1]=='>' or elems[i+1]=='>=') \
                      and is_world(elems[i+2]):
                    e=e+'MIN'
                    if elems[i+1][-1]!='=': e=e+'*'
                    [ss,ll]=str_field_constraint(e,elems[i+2])
                    S+=ss
                    L+=ll
                    i+=3
                else :
                    [ss,ll]=str_field_constraint('any',e)
                    S+=ss
                    L+=ll
                    i+=1
                cur = database.theBase.find_sql(ss, ll)
                if not (cur is None) :
                    rowIDs = [r[-1] for r in cur]
                    SS += 'docID in ' + database.theBase.make_placeholder_list(len(rowIDs))
                    LL += rowIDs
                    
                had_operator=False
        else:
            S += e
            i+=1
    #print S
    #print L
    return (SS,LL)
def no_accent(S):
    if isinstance(S, bytes):
        S = S.decode('utf-8', 'ignore')
    return unicodedata.normalize('NFKD', S).encode('ASCII', 'ignore').decode('ascii')


def encrypt(s,cipher,prefixed=True):
    s = _to_bytes(s)
    npad = (cipher.block_size - (len(s) % cipher.block_size)) % cipher.block_size
    if npad>0:
        if prefixed:
            s=s+urandom(npad)
        else:
            s=s+b' '*npad
    sss = cipher.encrypt(s)
    if prefixed:
        x= ('%.2d' % npad).encode('ascii')
        sss=x+sss
    return sss.hex()
    #return sss
def decrypt(s,cipher,prefixed=True,encodeUTF=True):
    try:
        if s is None : return 'internal error'
        if isinstance(s, bytes):
            s = s.decode('ascii')
        s = bytes.fromhex(s)
        if prefixed:
            npad = int(s[0:2].decode('ascii'))
            s = s[2:]
            s = cipher.decrypt(s)
            if npad>0 :
                ans = s[:-npad]
            else:
                ans = s
        else:
            s = cipher.decrypt(s)
            ans = s.rstrip(b' ')
        if encodeUTF:
            ans = ans.decode('utf-8', 'replace')
        return ans
    except Exception as E:
        logging.debug('SQL ERROR ' + str(E))
        logging.debug('s was ' + str(s) + ' of type ' + str(type(s)))
        return s
  
def save_encrypted_data(txt,filename):
    iv = urandom(ENCRYPT_IV_LENGTH)
    cipher = AES.new(database.get_current_password(), AES.MODE_CBC, iv=iv)
    
    sss = encrypt(txt,cipher)
    digest = md5.new()
    digest.update(_to_bytes(txt))
    
    with open(filename, "wb") as ff:
        ff.write(_to_bytes(ENCRYPT_TEXT, 'ascii'))
        ff.write(iv)
        x=digest.digest()
        ff.write(x)
        ff.write(_to_bytes(sss, 'ascii'))
def is_encrypted(filename):
    with open(filename, "rb") as ff:
        tst = ff.read(len(ENCRYPT_TEXT))
        return tst == _to_bytes(ENCRYPT_TEXT, 'ascii')
def is_good_password(filename,thePassword):
    with open(filename, "rb") as ff:
        iv = ff.read(ENCRYPT_IV_LENGTH)
        dgst = ff.read(16)
        txt = ff.read()
        cipher = AES.new(thePassword, AES.MODE_CBC, iv=iv)
        sss=decrypt(txt,cipher,True,False)
        digest = md5.new()
        digest.update(sss)
        if digest.digest() != dgst:
            return False
        else:
            return True
    
def load_encrypted_data(filename):
    with open(filename, "rb") as ff:
        tst = ff.read(len(ENCRYPT_TEXT))
        if tst == _to_bytes(ENCRYPT_TEXT, 'ascii'):
            thePassword = database.get_current_password()
            again=True
            iv = ff.read(ENCRYPT_IV_LENGTH)
            dgst = ff.read(16)
            txt = ff.read()
            while again:
                cipher = AES.new(thePassword, AES.MODE_CBC, iv=iv)
                sss=decrypt(txt,cipher,True,False)
                digest = md5.new()
                digest.update(sss)
                if digest.digest() != dgst:
                    thePassword = database.get_current_password(_('Wrong password, please give the correct one (or leave it empty to cancel operation)'),True,False)
                    if thePassword == '' : return ''
                else:
                    again=False
            return sss
        else:
            return None