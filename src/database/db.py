#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on 21 juin 2010. Copyright 2010, David GUEZ
@author: david guez (guezdav@gmail.com)
This file is a part of the source code of the MALODOS project.
You can use and distribute it freely, but have to conform to the license
attached to this project (LICENSE.txt file)
=====================================================================

interface between the application and the database engine
'''

import sqlite3
import datetime
import hashlib
import string
import ast
import os.path
import configparser
import algorithms.general
from database import Resources
import shutil
import zipfile
import logging
import re
import base64
from os import urandom
import database
import Crypto.Cipher.AES as AES
import bcrypt


class _FallbackUtilities(object):
    @staticmethod
    def show_message(message):
        logging.warning(str(message))

    @staticmethod
    def ask(message):
        logging.warning(str(message))
        return False

    @staticmethod
    def ask_password(message):
        logging.warning(str(message))
        return ''

    @staticmethod
    def multichoice(choices, message):
        logging.warning(str(message))
        return 0 if choices else -1

    class MultipleButtonDialog(object):
        def __init__(self, *args, **kwargs):
            self.choice = 0

        def ShowModal(self):
            return 0


_ui = _FallbackUtilities()


def _phonex(word):
    try:
        from algorithms import words as _words
        return _words.phonex(word)
    except Exception:
        return str(word)


class ConfigReader(object):
    def __init__(self,conf_file=None):
        self.config = None
        self.conf_file = conf_file
        if conf_file is None : return
        if not os.path.exists(self.conf_file) :
            try:
                theFile = open(self.conf_file,'w')
            except:
                return
            theFile.close()
        self.config = configparser.ConfigParser()
        self.read_config()

    def get_param(self,section,key,defaultValue=None,create_if_not_exist=False):
        #if not self.config : raise _("Configuration not found")
        try:
            return self.config.get(section,key)
        except Exception as E:
            if defaultValue is None : raise E
            if create_if_not_exist :
                try:
                    self.set_param(section,key,defaultValue,True)
                except Exception as Ex:
                    raise Ex
            return defaultValue
                
    def set_param(self,section,key,value,allow_create_section=True):
        if not self.config : raise _("Configuration not found")
        if not self.config.has_section(section) and allow_create_section: self.config.add_section(section)
        return self.config.set(section, key,value)
    def get_all_params_in(self,section):
        if not self.config : raise _("Configuration not found")
        if not self.config.has_section(section) : return dict()
        return dict(self.config.items(section))
    def read_config(self):
        if os.path.exists(self.conf_file) :
            self.config = configparser.ConfigParser()
            self.config.read(self.conf_file)
    def commit_config(self):
            try:
                theFile = open(self.conf_file,'w')
                self.config.write(theFile)
                theFile.close()
                return True
            except Exception as E:
                logging.exception('Unable to commit config :' + str(E))
                return False

class OCRConfiguration(ConfigReader):
    def __init__(self,conf_file):
        ConfigReader.__init__(self,conf_file)
    def get_available_ocr_programs(self):
        return self.config.sections()
    def get_needed_image_format(self,ocr_sequence):
        return self.get_param(ocr_sequence, 'inputFormat', 'tif', False)
    def get_output_format(self,ocr_sequence):
        return self.get_param(ocr_sequence, 'outputFormat', 'ascii', False).lower()
    def build_call_sequence(self,ocr_section,input_file,output_file):
        needed_format = self.get_needed_image_format(ocr_section).lower()
        if os.path.splitext(input_file)[1].lower() != '.'+  needed_format :
            msg = _('Unable to get the image in format %(needed_format) for section %(section) ') % {'needed_format':needed_format,'ocr_section':ocr_section}
            _ui.show_message(msg)
            return []
        pname = self.get_param(ocr_section, 'programName', '', False)
        if pname == '' : return []
        placeHolder = ['','','']
        to_place=[]
        try:
            to_place.append(self.get_param(ocr_section, 'inputOption', None, False))
            to_place.append(self.get_param(ocr_section, 'outputOption', None, False))
            otherOpts = self.get_param(ocr_section, 'otherOptions', '', False)
            if otherOpts != '' : to_place.append(otherOpts)
        except:
            logging.debug('Unable to build the call sequence for the OCR %s') %ocr_section
            return []
        to_place2=[]
        outF=None
        for s in to_place:
            if s.startswith('$1') or s.startswith('$2') or s.startswith('$3'):
                ps = int(s[1])-1
                s=s[2:]
                if placeHolder[ps] != '':
                    msg = _('Misformatted OCR configuration for section %s ')% ocr_section
                    _ui.show_message(msg) 
                    return ([],None)
                else:
                    placeHolder[ps] = s
            elif s.startswith('>'):
                outF = s[1:]
            else:
                to_place2.append(s)
        for s in to_place2:
            not_placed=True
            for i in range(len(placeHolder)) :
                if placeHolder[i] == '' :
                    placeHolder[i] = s
                    not_placed=False
                    break
            if not_placed :
                msg = _('Misformatted OCR configuration for section %s ')% ocr_section
                _ui.show_message(msg) 
                return ([],None)
        def do_replace(s):
            s = s.replace("$outputFilenameNoExt" , os.path.splitext(output_file)[0])
            s = s.replace("$outputFilename" , output_file)
            s = s.replace("$inputFilenameNoExt" , os.path.splitext(input_file)[0])
            s = s.replace("$inputFilename" , input_file)
            return s
            
        for i in range(len(placeHolder)) :
            placeHolder[i] = do_replace(placeHolder[i])
        if outF is not None : outF=do_replace(outF)
        ans = [pname]
        for s in placeHolder : ans.extend(s.split())
        return (ans,outF)


class Configuration(ConfigReader):
    def __init__(self):
        # code from http://zhigang.org/wiki/PythonTips
        try:
            from win32com.shell import shellcon, shell
            self.conf_dir = shell.SHGetFolderPath(0, shellcon.CSIDL_PERSONAL, 0, 0)
            self.conf_dir = os.path.abspath(os.path.join(self.conf_dir,'..'))
            self.conf_dir=str(self.conf_dir)
        except Exception: # quick semi-nasty fallback for non-windows/win32com case
            #logging.exception(str(EE))
            self.conf_dir = os.path.expanduser("~")
        # end of code from http://zhigang.org/wiki/PythonTips
        if os.name=='nt':
            self.conf_dir = os.path.join(self.conf_dir,'malodos')
        else:
            self.conf_dir = os.path.join(self.conf_dir,'.malodos')
        #print type(self.conf_dir) , self.conf_dir
        
        if not os.path.isdir(self.conf_dir) :
            try:
                os.mkdir(self.conf_dir)
            except Exception as E:
                logging.exception('Unable to create the folder' + self.conf_dir + '->' + str(E))
                self.conf_dir = input(_('Choose a folder for the MALODOS configuration and database'))
                if not os.path.isdir(self.conf_dir) :
                    try:
                        os.mkdir(self.conf_dir)
                    except Exception as E2:
                        logging.exception('Unable to create the folder' + self.conf_dir + '->' + str(E2))
                ConfigReader.__init__(self)
                return
        if not os.path.exists(self.conf_dir) :
            logging.exception('Unable to get the folder' + self.conf_dir)
            ConfigReader.__init__(self)
            return
        conf_file = os.path.join(self.conf_dir,'malodos.ini')
        self.existedConfigFile = os.path.exists(conf_file)
        ConfigReader.__init__(self,conf_file)
        if not self.config.has_section('survey'):
            self.config.add_section('survey')
        if not self.config.has_option('survey', 'directory_list'):
            self.set_survey_directory_list( (os.path.join(self.conf_dir,'documents'),) , (0,))
        if not self.config.has_option('survey', 'extension_list'):
            self.set_survey_extension_list( 'png tif tiff pdf jpg jpeg gif bmp' )

        if not self.config.has_section('scanner'):
            self.config.add_section('scanner')
        if not self.config.has_option('scanner', 'source'):
            self.set_current_scanner('None')

        if not self.config.has_section('language'):
            self.config.add_section('language')
        if not self.config.has_option('language', 'installed'):
            self.set_installed_languages('system/sys,english/en,french/fr_FR')
        if not self.config.has_option('language', 'current'):
            self.set_current_language('sys')

        if not self.config.has_section('database'):
            self.config.add_section('database')
        if not self.config.has_option('database', 'filename'):
            self.set_database_name( os.path.join(self.conf_dir,'malodos.db'))
        self.commit_config()
        self.read_config()

    def get_survey_extension_list(self):
        return self.get_param('survey', 'extension_list')
    def set_survey_extension_list(self,S):
        return self.set_param('survey', 'extension_list',S)
    def get_survey_directory_list(self):
        S = self.get_param('survey', 'directory_list')
        return self.decode_dir_list(S)
    def set_survey_directory_list(self,dir_list,recursiveIndex):
        S = self.encode_dir_list(dir_list, recursiveIndex)
        return self.set_param('survey', 'directory_list',S)
    def get_installed_languages(self):
        return self.get_param('language', 'installed').split(',')
    def set_installed_languages(self,S):
        if hasattr(S, '__iter__') : S = ','.join(S)
        return self.set_param('language', 'installed',S)
    def get_current_language(self):
        try:
            return self.get_param('language', 'current')
        except:
            return 'en'
    def set_current_language(self,S):
        return self.set_param('language', 'current',S)
    def get_current_scanner(self):
        return self.get_param('scanner', 'source')
    def set_current_scanner(self,S):
        return self.set_param('scanner', 'source',S)
    def get_database_name(self):
        return self.get_param('database', 'filename')
    def set_database_name(self,S):
        return self.set_param('database', 'filename',S)
    def get_resource_filename(self):
        return self.get_param('general', 'resourceFile')
    def get_ocr_confname(self):
        defConf = os.path.join(Resources.get_resource_dir(),'OCR.ini')
        return self.get_param('OCR', 'configurationFile',defConf,True)
    def get_ocr_configuration(self):
        return OCRConfiguration(self.get_ocr_confname())
    
    def encode_dir_list(self , dir_list , checked):
        answer = ""
        for i in range(len(dir_list)) :
            if i in checked : answer = answer + '*'
            answer = answer + dir_list[i] + '|'
        return answer
    def decode_dir_list(self,S):
        items_list = S.split('|')
        checked = []
        dir_list = []
        
        for item in items_list :
            item = item.strip()
            if len(item)<1 : continue
            if item[0] == '*' :
                checked.append(len(dir_list))
                item=item[1:]
            dir_list.append(item)
        return (dir_list , checked)

class Base(object):
    '''(
    this class is the interface between the application and the database engine
    )'''
    #===========================================================================
    # constants
    #===========================================================================
    documents_tableName = 'documents'
    keywords_tableName = 'keywords'
    docWords_tableName = 'docWords'
    persons_tableName = 'persons'
    params_tableName = 'parameters'
    folders_tableName='folders'
    folderDoc_tableName='folderDocs'
    
    param_DB_VERSION='DB_VERSION'
    param_ENCRYPTED='ENCRYPTED'
    param_INI_VECTOR='INI_VECTOR'
    param_SALT='SALT'
    param_HASHED='HASHED'
    DB_VERSION=1.21
    
    IDX_TITLE=0
    IDX_DESCRIPTION=1
    IDX_FILENAME=2
    IDX_REGISTER_DATE=3
    IDX_REGISTER_PERSON_ID=4
    IDX_DOCUMENT_DATE=5
    IDX_TAGS=6
    IDX_CHECKSUM=7
    IDX_ROWID=8
    IDX_COUNT=9
    
    ID_TAG=0
    ID_TITLE=1
    ID_DESCRIPTION=2
    ID_FULL_TEXT=3
    
    ID_DEL_ASK=0
    ID_DEL_NOT=1
    ID_DEL_DB=2
    ID_DEL_DB_AND_FS=3
    
    ENCRYPT_IV_LENGTH=16
    #===========================================================================
    # constructor
    #===========================================================================
    def __init__(self,base_name=None):
        '''
        Constructor
        '''
        if base_name is not None : self.use_base(base_name)
    def utf_or_str(self,s):
        if s is None:
            return None
        if isinstance(s, memoryview):
            s = s.tobytes()
        if isinstance(s, bytes):
            for encoding in ('utf-8', 'utf-8-sig', 'latin-1', 'ascii'):
                try:
                    return s.decode(encoding)
                except UnicodeDecodeError:
                    continue
            return s.decode('utf-8', 'replace')
        if isinstance(s, str):
            if s.startswith(("b'", 'b"')):
                try:
                    parsed = ast.literal_eval(s)
                    if isinstance(parsed, bytes):
                        for encoding in ('utf-8', 'utf-8-sig', 'latin-1', 'ascii'):
                            try:
                                return parsed.decode(encoding)
                            except UnicodeDecodeError:
                                continue
                        return parsed.decode('utf-8', 'replace')
                except Exception:
                    pass
            return s
        try:
            return str(s)
        except Exception:
            return s
    def create_and_use(self,base_name,psw=None):
        self.connexion = sqlite3.connect(base_name, detect_types=sqlite3.PARSE_DECLTYPES)
        self.connexion.text_factory = self.utf_or_str
        self.base_name = base_name
        self.encrypted = not (psw is None)
        if self.encrypted:
            psw=database.transform_password(psw)
            self.iv=urandom(self.ENCRYPT_IV_LENGTH)
            self.salt= bcrypt.gensalt()
            self.hashed=bcrypt.hashpw(psw, self.salt)
            self.cypher = AES.new(psw, AES.MODE_CBC, iv=self.iv)
        else:
            self.cypher = None
        self.create_function()
        if self.encrypted:
            database.theConfig.set_param('encryption','salt',self.salt.decode('utf-8'))
            database.theConfig.set_param('encryption','hash',self.hashed.decode('utf-8'))
            database.theConfig.commit_config()
           
        
    def use_base(self,base_name):
        self.connexion = sqlite3.connect(base_name, detect_types=sqlite3.PARSE_DECLTYPES)
        self.connexion.text_factory = self.utf_or_str
        self.base_name = base_name
        self.encrypted = algorithms.general.str_to_bool(self.get_parameter(self.param_ENCRYPTED))
        if self.encrypted:
            iv_b64 = self.get_parameter(self.param_INI_VECTOR)
            self.iv = base64.b64decode(iv_b64.encode('ascii'))
            salt = self.get_parameter(self.param_SALT).encode('utf-8')
            hashed = self.get_parameter(self.param_HASHED).encode('utf-8')
            psw = database.get_password(checker=(salt,hashed))
            self.cypher = AES.new(psw, AES.MODE_CBC, iv=self.iv)
        self.create_function()
    def create_function(self):
        if os.name == 'nt' or os.name == 'win32' :
            self.connexion.create_function("IS_IN_DIR", 2, lambda fname,dirname : self.win32_samefile(os.path.dirname(fname), dirname))
        else:
            self.connexion.create_function("IS_IN_DIR", 2, lambda fname,dirname : os.path.samefile(os.path.dirname(fname), dirname))
        self.connexion.create_function("EXTENSION", 1, lambda fname : os.path.splitext(fname)[1])
        self.connexion.create_function("PHONEX", 1, lambda word: _phonex(word))
        self.connexion.create_function("MAKE_FULL_PATH", 2, self.make_full_name)
        
        if self.encrypted and self.cypher is not None:
            self.connexion.create_function("decrypt", 1, lambda s:algorithms.stringFunctions.decrypt(s,self.cypher,False))
            self.encrypt = lambda s : algorithms.stringFunctions.encrypt(s, self.cypher,False)
        else:
            self.connexion.create_function("decrypt", 1, lambda s:s)
            self.encrypt = lambda s :s

    #===========================================================================
    # test if a table exists
    #===========================================================================
    def exist_table(self, base_name):
        '''(
        Test if a given table exists
        )'''
        try:
            cur = self.connexion.execute("SELECT name FROM sqlite_master WHERE name = '" + base_name + "' AND type='table' ;")
            return (cur and cur.arraysize>0)
        except:
            logging.debug('SQL ERROR')
            return False
    #===========================================================================
    # create the table
    #===========================================================================
    def create_table(self, table_name, structure):
        '''(
        Automatically create the asked table, if not already exists in the database
        )'''
        sql_statement = "CREATE TABLE IF NOT EXISTS " + table_name + "(" + structure + ")"
        try:
            self.connexion.execute(sql_statement)
            return True
        except:
            logging.debug('SQL ERROR')
            return False
    def win32_samefile(self,p1,p2):
        return os.path.abspath(p1).lower() == os.path.abspath(p2).lower()
    #===========================================================================
    # build the database
    #===========================================================================
    def buildDB(self):
        '''( 
        create the database (all the tables)
        database structures:
        documents = title,description,filename,registerDate,registeringPersonID,documentDate,tags,checksum
        keywords = keyword , soundex_word (indexed)
        docWords = keyID,docID,field,count
        persons = name
        params = name , value
        folders = name,parentID
        foldDocs = docID,folderID
        )'''
        self.__doc_fields__ = 'title,description,filename,registerDate,registeringPersonID,documentDate,tags,checksum'
        self.__doc_nbfields__ = 8
        if 0 and self.encryd:
            self.create_table(self.documents_tableName, 'documentID INTEGER PRIMARY KEY AUTOINCREMENT ,title BLOB(64), description BLOB(256), filename TEXT(256), registerDate DATE, registeringPersonID INTEGER, documentDate DATE,tags BLOB,checksum TEXT')
            self.create_table(self.keywords_tableName, 'keywordID INTEGER PRIMARY KEY AUTOINCREMENT ,keyword BLOB , soundex_word BLOB ')
        else:
            self.create_table(self.documents_tableName, 'documentID INTEGER PRIMARY KEY AUTOINCREMENT ,title TEXT(64), description TEXT(256), filename TEXT(256), registerDate DATE, registeringPersonID INTEGER, documentDate DATE,tags TEXT,checksum TEXT')
            self.create_table(self.keywords_tableName, 'keywordID INTEGER PRIMARY KEY AUTOINCREMENT ,keyword TEXT , soundex_word TEXT ')
        sql_statement = "CREATE INDEX IF NOT EXISTS SOUNDEX ON " + self.keywords_tableName + "(soundex_word)"
        try:
            self.connexion.execute(sql_statement)
        except Exception as E:
            logging.debug('SQL ERROR')
            _ui.show_message('Error during database index creation : ' + str(E))
            
        #self.create_table(self.docWords_tableName, 'keyID INTEGER references ' + self.keywords_tableName + '(ROWID) ,docID INTEGER references ' + self.documents_tableName + '(ROWID)')
        self.create_table(self.docWords_tableName, 'keyID INTEGER references {0}(rowID) ,docID INTEGER references {1}(rowID), field INT,count INT default 1'.format(self.keywords_tableName,self.documents_tableName))
        self.create_table(self.persons_tableName, 'persID INTEGER PRIMARY KEY AUTOINCREMENT ,name TEXT')
        self.create_table(self.params_tableName, 'name TEXT , value TEXT')
        self.create_table(self.folders_tableName, 'foldID INTEGER PRIMARY KEY AUTOINCREMENT ,name TEXT , parentID INT references {0}(rowID)'.format(self.folders_tableName))
        self.create_table(self.folderDoc_tableName, 'docID INT  references {0}(rowID), folderID INT references {1}(rowID)'.format(self.documents_tableName,self.folders_tableName))
        db_version = self.get_parameter(self.param_DB_VERSION)
        if not db_version:
            self.set_parameter(self.param_DB_VERSION, self.DB_VERSION)
            db_version = self.DB_VERSION
        db_version = float(db_version)
        if db_version > self.DB_VERSION:
            _ui.show_message(_('Unstable state: Your database version is newer than the program itself...'))
            return False
        if db_version<1.1 :
            sql_statement = 'ALTER TABLE %s ADD COUNT INT default 1' % self.docWords_tableName
            try:
                self.connexion.execute(sql_statement)
            except Exception as E:
                logging.debug('SQL ERROR ' + str(E))
                _ui.show_message('Error during database view creation : ' + str(E))
            sql_statement = 'DROP VIEW fullDoc'
            try:
                self.connexion.execute(sql_statement)
                self.connexion.commit()
            except Exception as E:
                logging.exception('error in commit->'+str(E))
        sql_statement = 'create view if not exists fullDoc as select D.title as title,D.description,D.filename,D.registerDate,D.registeringPersonID,D.documentDate,D.tags,D.checksum, D.RowID docID,K.keyword,K.soundex_word as soundex_word,DW.field,DW.count '
        sql_statement += 'FROM ' + self.keywords_tableName + ' K,' + self.documents_tableName + ' D,'
        sql_statement += self.docWords_tableName + ' DW'
        sql_statement += ' WHERE DW.keyID = K.rowID AND DW.docID = D.RowID'
        try:
            self.connexion.execute(sql_statement)
        except Exception as E:
            _ui.show_message('Error during database view creation :' + str(E))
            logging.debug('SQL ERROR ' + str(E))
            return False
        if db_version<1.21 :
            it=1
            while 1:
                save_name = self.base_name+'.bak' + str(it)
                if not os.path.exists(save_name) : break
                it+=1
            try:
                shutil.copy(self.base_name, save_name)
                if not os.path.exists(save_name) : raise _('unable to backup the database')
                it=1
                while 1:
                    tmp_name = self.base_name+'.tmp' + str(it)
                    if not os.path.exists(tmp_name) : break
                    it+=1
                self.replicate_in(tmp_name)
                if not os.path.exists(tmp_name) : raise _('unable to upgrade the database')
                self.connexion.close()
                os.remove(self.base_name)
                os.rename(tmp_name, self.base_name)
                if not os.path.exists(self.base_name): raise _('unable to upgrade the database')
                self.use_base(self.base_name)
            except Exception as E:
                logging.debug('SQL ERROR ' + str(E))
                return False
            
        self.set_parameter(self.param_DB_VERSION, self.DB_VERSION)
        self.set_parameter(self.param_ENCRYPTED, str(self.encrypted))
        if self.encrypted:
            self.set_parameter(self.param_INI_VECTOR, base64.b64encode(self.iv).decode('ascii'))
            self.set_parameter(self.param_SALT, self.salt.decode('utf-8'))
            self.set_parameter(self.param_HASHED, self.hashed.decode('utf-8'))
        return True
    
    #===========================================================================
    # set a parameter
    #===========================================================================
    def set_parameter(self,parameter_name,parameter_value):
        try:
            Q = 'DELETE FROM %s WHERE name=?' %self.params_tableName
            self.connexion.execute(Q,(parameter_name,))
            Q = 'INSERT INTO ' + self.params_tableName +' VALUES (?,?)'
            self.connexion.execute(Q,(parameter_name,str(parameter_value)))
            self.connexion.commit()
            return True
        except Exception as E:
            logging.debug('SQL ERROR ' + str(E))
            return False
    #===========================================================================
    # get a parameter
    #===========================================================================
    def get_parameter(self,parameter_name):
        Q = 'SELECT value FROM ' + self.params_tableName +' WHERE name=?'
        try:
            cur = self.connexion.execute(Q,(parameter_name,))
            row = cur.fetchone()
            if row :
                return row[0]
            else:
                return None
        except Exception as E:
            logging.debug('SQL ERROR ' + str(E))
            return None
         
    #===============================================================================
    # add a new document to the database
    #===============================================================================
    def add_document(self, fileName, title = 'untitled', description = '', registeringPerson = None\
                     , documentDate = None, keywordsGroups = None , tags = '',folderID_list=None):
        '''(
        Add a new document to the database
        only the filename is mandatory
        the registering date is automatically taken from the system
        )'''
        docID = None
        registeringDate = datetime.date.today()
        cur = self.connexion.cursor()
        if not documentDate : documentDate = registeringDate
        personID = 0
        file_md5 = hashlib.md5(open(fileName, "rb").read()).hexdigest()

        # try to find the given person (if a value is given)
        if registeringPerson:
            sql_statement = 'SELECT ROWID FROM ' + self.persons_tableName + " WHERE name=?"
            try:
                cur = self.connexion.execute(sql_statement,(registeringPerson,))
                row = cur.fetchone()
                # if not found --> create the person in the database
                if not row:
                    sql_statement = "INSERT INTO " + self.persons_tableName + "(name) VALUES (?)"
                    cur = self.connexion.execute(sql_statement,(registeringPerson,))
                    personID = cur.lastrowid
                else:
                    personID = row[0]
            except Exception as E:
                _ui.show_message(_('Unable to assign the registering person'))
                logging.debug('SQL ERROR ' + str(E))
        try:
            # add the document entry in the database
            #sql_statement = 'INSERT INTO ' + self.documents_tableName + " VALUES ('" + title + "','" + description + "','" + fileName + "','" + str(registeringDate) + "'," + str(personID) + ",'" + str(documentDate) + "','" + str(file_md5) + "')"
            sql_statement = 'INSERT INTO ' + self.documents_tableName + " (title,description,filename,registerDate,registeringPersonID,documentDate,tags,checksum) VALUES (?,?,?,?,?,?,?,?)"
            cur = self.connexion.execute(sql_statement,(self.encrypt(title),self.encrypt(description),fileName,registeringDate,personID,documentDate,self.encrypt(tags),str(file_md5)))
            docID = cur.lastrowid
        except Exception as E:
            logging.debug('SQL ERROR ' + str(E))
            _ui.show_message(_('Unable to add the document'))
            return False
        self.connexion.commit()
        if keywordsGroups :
            # find the list of keyword not yet registered
            if not self.update_keywords_for(docID,keywordsGroups) : return False
        return self.folders_set_doc_to(docID, folderID_list)

    
    #===============================================================================
    # remove and eventually delete from disk a list of documents
    #===============================================================================
    def delete_documents(self,rows,delete_files=ID_DEL_ASK,parent=None,exclusion=[]):
        # delete_files code
        # 0 = ask
        # 1 = do not delete
        # 2 = just from database
        # 3 = database AND filesystem
        docID = [row[self.IDX_ROWID] for row in rows if row is not None]

        #confirmation = wx.MessageDialog(self,msg,style=wx.OK|wx.CANCEL | wx.CENTRE)
        #x= confirmation.ShowModal()
        #if x == wx.ID_CANCEL : return
        if delete_files is self.ID_DEL_ASK :
            if len(docID)==1:
                msg = _('This will delete the record (') + rows[0][self.IDX_TITLE] + ').'        
            else:
                msg = _('This will delete these ') + str(len(docID)) + _(' records.')
            msg=msg+_('Please, choose an action below')
            choiceWin = _ui.MultipleButtonDialog(parent,-1,_('What to do'),msg,
                                                       [_('remove from database'),_('remove from database AND FROM DISK'),_('cancel')])
            choiceWin.ShowModal()
            if choiceWin.choice == 2 :
                self.ID_DEL_NOT
            elif choiceWin.choice == 1 :
                delete_files = self.ID_DEL_DB_AND_FS
            elif choiceWin.choice == 0 :
                delete_files = self.ID_DEL_DB
        
        #print 'must remove ' + str(docID) + ' because x is ' + str(x)
        if delete_files == self.ID_DEL_DB_AND_FS:
            listFiles = [row[self.IDX_FILENAME] for row in rows if row is not None]
            try:
                from send2trash import send2trash
                for f in listFiles :
                    #print f + " was send to trash"
                    if f in exclusion : continue
                    send2trash(f)
            except Exception :
                #print str(E)
                for f in listFiles :
                    if f in exclusion : continue
                    os.remove(f)
                    #print f + " was deleted"
        if delete_files == self.ID_DEL_DB_AND_FS or delete_files == self.ID_DEL_DB : self.remove_documents(docID)
    
    
    #===============================================================================
    # finding keywords rows
    #===============================================================================
    def find_keywords(self, keywords):
        '''(
        find all the rows of the keywords table corresponding to the given input
        keyword is a list of list of words
        ((word11,word12,...word1N1),(word21,word22,...word2N2),...,(wordM1,wordM2,...,wordMNM))
        means (word11 AND word12 AND ... AND word1N1) OR ... OR  (wordM1 AND wordM2 AND ... AND wordMNM)
        )'''
        cur = None
        if not keywords : return None
        keywords = [_phonex(s) for s in keywords]
        # first : find the keyword in the keywords table
        if isinstance(keywords,list):
            Q = "SELECT ROWID FROM " + self.keywords_tableName + " WHERE decrypt(soundex_word) IN " + self.make_placeholder_list(len(keywords))
        else:
            Q = "SELECT ROWID FROM " + self.keywords_tableName + " WHERE decrypt(soundex_word) = ?"
        try:
            #print "finding keys via " + Q
            cur = self.connexion.execute(Q , keywords)
            return cur
        except Exception as E:
            logging.debug('SQL ERROR ' + str(E))
            _ui.show_message(_('Unable to search keywords'))
            return None

    
    #===============================================================================
    # find documents corresponding to the sql request
    #===============================================================================
    def find_sql(self,request='',pars=[]):
        if request=='': return self.find_documents(None)     
        try:
            sql_command = "SELECT docID FROM fullDoc "
            if request!='' : sql_command +=' WHERE '+ request
            sql_command += " GROUP BY docID" 
#            print sql_command,pars
            cur = self.connexion.execute(sql_command,pars)
            rowIDList = self.rows_to_str(cur,0,'')
            sql_command = "SELECT decrypt(title),decrypt(description),filename,registerDate,registeringPersonID,documentDate,decrypt(tags),checksum,ROWID FROM "+ self.documents_tableName + ' WHERE ROWID IN ' + str(rowIDList)
            cur = self.connexion.execute(sql_command)
            return cur
        except Exception as E:
            logging.debug('SQL ERROR ' + str(E))
            _ui.show_message('SQL search failed ' + str(E))
            #print E 
            return None
    #===============================================================================
    # find documents corresponding to the row list
    #===============================================================================
    def get_by_doc_id(self,docIDlist):
        if len(docIDlist)<1 : return None
        try:
            sql_command = "SELECT decrypt(title),decrypt(description),filename,registerDate,registeringPersonID,documentDate,decrypt(tags),checksum,ROWID FROM %s WHERE rowID IN %s" %(self.documents_tableName,self.make_placeholder_list(len(docIDlist))) 
#            print sql_command,pars
            cur = self.connexion.execute(sql_command,docIDlist)
            return cur
        except Exception as E:
            logging.debug('SQL ERROR ' + str(E))
            _ui.show_message('SQL search failed ' + str(E))
            #print E 
            return None
    #===============================================================================
    # find tag entry starting by a given prefix and for an optional given field
    #===============================================================================
    def find_keywords_by_prefix(self,prefix='',field_num=None):
        try:
            sql_command = "SELECT rowID,decrypt(keyword) FROM " + self.keywords_tableName + " WHERE decrypt(keyword) LIKE ?" 
            cur = self.connexion.execute(sql_command,(prefix + '%' ,))
            if field_num is None:
                return [ row[1] for row in cur]
            else:
                keyXX = self.rows_to_str(cur,0,'')
                sql_command = "SELECT DISTINCT keyID from " + self.docWords_tableName + " WHERE keyID IN " + keyXX + " AND field = ?"
                cur = self.connexion.execute(sql_command,(field_num,))
                sql_command = "SELECT decrypt(keyword) FROM " + self.keywords_tableName + " WHERE rowID IN " + self.rows_to_str(cur,0,'')
                cur = self.connexion.execute(sql_command)
                return [ row[0] for row in cur]
        except Exception as E:
            logging.debug('SQL ERROR ' + str(E))
            _ui.show_message('SQL search failed ' + str(E) )
            return None
    #===============================================================================
    # find entry starting by a given prefix and for a given field
    #===============================================================================
    def find_field_by_prefix(self,prefix='',field_str='title'):
        try:
            sql_command = "SELECT %s FROM %s WHERE %s LIKE ?" % (field_str,self.documents_tableName,field_str)
            p = prefix+'%'
            cur = self.connexion.execute(sql_command,(p,))
            return [ row[0] for row in cur]
        except Exception as E:
            logging.debug('SQL ERROR ' + str(E))
            _ui.show_message('SQL search failed ' + str(E) )
            return None
    
    #===============================================================================
    # find documents corresponding to keywords
    #===============================================================================
    def find_documents(self, keywords = None,fields=None):
        '''(
        find all the document of the database that contain any of the given keywords
        keyword is a list of list of words
        ((word11,word12,...word1N1),(word21,word22,...word2N2),...,(wordM1,wordM2,...,wordMNM))
        means (word11 AND word12 AND ... AND word1N1) OR ... OR  (wordM1 AND wordM2 AND ... AND wordMNM)
        )'''
       
        cur = None
        sql_statement = 'SELECT decrypt(title),decrypt(description),filename,registerDate,registeringPersonID,documentDate,decrypt(tags),checksum,ROWID FROM ' + self.documents_tableName
        if keywords:
            # first : find the keyword in the keyword table
            cur = self.find_keywords(keywords)
            if not cur or cur.arraysize<1: return None
            # if some keywords are found, find the corresponding doc lines
            lst = self.rows_to_str(cur)
            Q = "SELECT docID FROM " + self.docWords_tableName + " WHERE keyID IN " + lst
            if fields :
                Q += ' AND FIELD IN ' + self.make_placeholder_list(len(fields))
            #print Q
            try:
                if fields :
                    cur = self.connexion.execute(Q , fields)
                else:  
                    cur = self.connexion.execute(Q)
            except Exception as E:
                logging.debug('SQL ERROR ' + str(E))
                _ui.show_message(_('Keyword search failed'))
                return None
            # cur now contain the docID to take
            if cur:
                rowIDList = self.rows_to_str(cur)
                sql_statement += ' WHERE ROWID IN ' + str(rowIDList)
        try:
            cur = self.connexion.execute(sql_statement)
        except Exception as E:
            logging.debug('SQL ERROR ' + str(E))
            _ui.show_message(_('Document search failed'))
            return None
        return cur
    #===========================================================================
    # create a list with n placeholder (?,?,...?) 
    #===========================================================================
    def make_placeholder_list(self,n):
        ''' create a string (?,?,...,?) with n < ? > chars inside '''
        if n<1 : return '()'
        if n<2 : return '(?)'
        return '(' + '?,' * (n-1) + '?)'
    #===========================================================================
    # utility function transform the content of a python list into an (e1,e2,...) string format
    #===========================================================================
    def iterable_to_sqlStrList(self,iterable,stringChar='"'):
        ''' transform an iterable into a (E1,E2,...En) string, where Ei is the ith element of <iterable> '''
        if len(iterable)<1: return '()'
        sql_list = [ stringChar + str(i) + stringChar for i in iterable]
        sql_list = '(' + ','.join(sql_list) + ')'
        return sql_list
    #===========================================================================
    # utility function transform the content of a column from cur into a (e1,e2,...) string format
    #===========================================================================
    def rows_to_str(self,cur,idx=0,stringChar='"'):
        ''' utility function transform the content of a column from cur into a (e1,e2,...) string format '''
        return self.iterable_to_sqlStrList([x[idx] for x in cur],stringChar)
    #===========================================================================
    # return the list of keywords absent from the database
    #===========================================================================
    def find_absent_keywords(self,keywords):
        ''' return the list of keywords absent from the database '''
#        keywords_str = [ '"' + i + '"' for i in keywords]
#        keywords_str = '(' + ','.join(keywords_str) + ')'
        
        Q = 'SELECT decrypt(keyword) FROM ' + self.keywords_tableName + ' WHERE decrypt(keyword) IN ' + self.make_placeholder_list(len(keywords))
        try:
            cur = self.connexion.execute(Q,keywords)
            already_present = [ i[0] for i in cur]
        except Exception as E:
            logging.debug('SQL ERROR ' + str(E))
            _ui.show_message(_('Keyword search failed'))
            already_present = [ ]
        absents = [ s for s in keywords if s not in already_present]
        return list(set(absents))
    #===========================================================================
    # remove_document : remove the selected documents (docID must be a list of ids)
    # and all the keys referencing it
    #===========================================================================
    def remove_documents(self,docID):
        # first find and delete all the corresponding lines in keyword index
        Q = 'DELETE FROM ' + self.docWords_tableName + ' WHERE docID IN ' + self.make_placeholder_list(len(docID))
        try:
            self.connexion.execute(Q,docID)
        except Exception as E:
            logging.debug('SQL ERROR ' + str(E))
            _ui.show_message(_('Unable to remove documents/word associations'))
            return
        # second find and delete all the corresponding lines in folders index
        Q = 'DELETE FROM ' + self.folderDoc_tableName + ' WHERE docID IN ' + self.make_placeholder_list(len(docID))
        try:
            self.connexion.execute(Q,docID)
        except Exception as E:
            logging.debug('SQL ERROR ' + str(E))
            _ui.show_message(_('Unable to remove documents/word associations'))
            return
        # then delete the documents entries themselves
        Q = 'DELETE FROM ' + self.documents_tableName + ' WHERE ROWID IN ' + self.make_placeholder_list(len(docID))
        try:
            self.connexion.execute(Q,docID)
            self.connexion.commit()
        except Exception as E:
            logging.debug('SQL ERROR ' + str(E))
            _ui.show_message(_('Unable to remove documents entries'))
            return
    #===========================================================================
    # update_keywords_for : remove all the keyword reference to docID
    # and  replace by a new list
    #===========================================================================
    def update_keywords_for(self,docID,keywordsGroups,keepFullTextIfNotGiven=True):
        # first : delete all the keyword references to docID
        if not hasattr(docID,'__iter__') : docID = (docID,)
        hasFullText = False
        for iField in range(len(keywordsGroups)) :
            if keywordsGroups[iField][0] == self.ID_FULL_TEXT :
                hasFullText=True
                break
        Q = 'DELETE FROM ' + self.docWords_tableName + ' WHERE docID IN ' + self.make_placeholder_list(len(docID))
        if keepFullTextIfNotGiven and not hasFullText :
            Q = Q+' AND field <> ' + str(self.ID_FULL_TEXT)
        try:
            #print Q
            self.connexion.execute(Q,docID)
        except Exception as E:
            logging.debug('SQL ERROR ' + str(E))
            _ui.show_message(_('Unable to remove doc/word association'))
            return False
        for iField in range(len(keywordsGroups)) :
            keyGroup = keywordsGroups[iField]
            field = keyGroup[0]
            # add all absent keywords to the keywords table
            if type(keyGroup[1]) is list:
                all_keywords = dict([ (item.lower(),keyGroup[1].count(item)) for item in keyGroup[1] ])
            elif type(keyGroup[1]) is dict:
                all_keywords = dict([ (item.lower(),weight) for item,weight in list(keyGroup[1].items()) ])
            absents = self.find_absent_keywords(list(all_keywords.keys()))
            absents = [(self.encrypt(x), self.encrypt(_phonex(x))) for x in absents]
            if len(absents)>0 :
                Q = 'INSERT INTO ' + self.keywords_tableName + ' (keyword,soundex_word) VALUES (?,?)'
                try:
                    self.connexion.executemany(Q,absents)
                except  Exception as E:
                    logging.debug('SQL ERROR ' + str(E))
                    _ui.show_message(_('Unable to insert new keywords : ') + str(E))
                    return False
            # get back all the keyword IDs for the current field
            Q = 'SELECT ROWID,decrypt(KEYWORD) FROM ' + self.keywords_tableName + ' WHERE decrypt(keyword) IN ' + self.make_placeholder_list(len(all_keywords))
            addedKeys = []
            try:
                cur = self.connexion.execute(Q,list(all_keywords.keys()))
                addedKeys = [ (row[0],all_keywords[row[1].lower()]) for row in cur]
            except Exception as E:
                logging.debug('SQL ERROR ' + str(E))
                _ui.show_message(_('Unable to search for keywords'))
                return False
            # add the new keyID to the table
            for adoc_i in docID:
                #word_count=1 # TODO UPDATE COUNTERS
                #Q = 'INSERT INTO ' + self.docWords_tableName + ' VALUES (?,' +  str(adoc_i) + ',' + str(field) + ',' + str(word_count) + ')'
                Q = 'INSERT INTO ' + self.docWords_tableName + ' VALUES (?,' +  str(adoc_i) + ',' + str(field) + ',?)'
                try:
                    self.connexion.executemany(Q , addedKeys)
                except Exception as E:
                    logging.debug('SQL ERROR ' + str(E))
                    _ui.show_message(_('Unable to insert new document/word association'))
                    return False
            try:
                self.connexion.commit()
            except Exception as E:
                logging.debug('SQL ERROR ' + str(E))
                return False
        return True
    
    #===========================================================================
    # update_doc : replace the values for a given doc
    #===========================================================================
    def update_doc(self,docID,title,description,documentDate,filename,tags,fullText=None,folderID_list=None):
        Q = 'UPDATE ' + self.documents_tableName + ' SET title=? , description=?, documentDate=? ,tags=? , filename=? WHERE ROWID=?'
        try:
            self.connexion.execute(Q,(self.encrypt(title),self.encrypt(description),documentDate,self.encrypt(tags),filename,docID))
            self.connexion.commit()
        except Exception as E:
            logging.debug('SQL ERROR ' + str(E))
            _ui.show_message(_('Unable to update document into database'))
            return False
        keywordsGroups = self.get_keywordsGroups_from(title, description, filename,tags,fullText)
        if not self.update_keywords_for(docID,keywordsGroups) : return False
        return self.folders_set_doc_to(docID, folderID_list)
    #===========================================================================
    # update_doc : replace the values for a given doc
    #===========================================================================
    def update_doc_signature(self,docID,file_md5):
        Q = 'UPDATE ' + self.documents_tableName + ' SET checksum=? WHERE ROWID=?'
        try:
            self.connexion.execute(Q,(file_md5,docID))
            self.connexion.commit()
        except Exception as E:
            logging.debug('SQL ERROR ' + str(E))
            _ui.show_message(_('Unable to reassign checksum into database entry'))
            return False
        return True
    #===========================================================================
    # get_keywords_from : find the keywords from a document
    #===========================================================================
    def get_keywordsGroups_from(self,title,description,filename,tags,fullText=None):
        p=re.compile('[0-9a-z]{2,}', re.IGNORECASE)
        keywords_title = string.split(title, ' ')
        keywords_title = [i.lower() for i in keywords_title if len(i)>3 and p.search(i) is not None]
        
        keywords_descr = string.split(description, ' ')
        keywords_descr = [i.lower() for i in keywords_descr if len(i)>3 and  p.search(i) is not None]
        
        keywords_tag = string.split(tags , ',')
        keywords_tag =  [s.lower() for s in keywords_tag]
        
        if fullText is None:
            return ( ( self.ID_TITLE, keywords_title) , (self.ID_DESCRIPTION , keywords_descr) , (self.ID_TAG ,keywords_tag ) )
        else:
            return ( ( self.ID_TITLE, keywords_title) , (self.ID_DESCRIPTION , keywords_descr) , (self.ID_TAG ,keywords_tag ) ,(self.ID_FULL_TEXT,fullText) )
    #===========================================================================
    # get_files_under : retrieve all the documents of the database whose filename
    # are on the directory <directory> (directly and not under subdir)
    #===========================================================================
    def get_files_under(self,directory,acceptedExt=None):
        if acceptedExt:
            Q = "SELECT filename FROM " + self.documents_tableName + " WHERE IS_IN_DIR(filename,?) AND EXTENSION(filename) IN " + self.make_placeholder_list(len(acceptedExt))
        else:
            Q = "SELECT filename FROM " + self.documents_tableName + " WHERE IS_IN_DIR(filename,?) "
        try:
            if acceptedExt:
                acceptedExt = [ i for i in acceptedExt];
                acceptedExt.insert(0, directory)
                cur = self.connexion.execute(Q,acceptedExt)
            else:
                cur = self.connexion.execute(Q,(directory,))
            return cur
        except Exception as E:
            logging.debug('SQL ERROR ' + str(E))
            #_ui.show_message('Unable to get file list from database')
            return None
    #===========================================================================
    # get_all_keywords : retrieve all the recorded keywords
    #===========================================================================
    def get_all_keywords(self):
        Q = "SELECT decrypt(keyword) FROM " + self.keywords_tableName
        try:
            cur = self.connexion.execute(Q)
            return tuple([row[0].encode('utf-8').lower() for row in cur])
        except Exception as E:
            logging.debug('SQL ERROR ' + str(E))
            return ()
    #===========================================================================
    # doc_without_ocr : retrieve all docs without any OCR term recored
    #===========================================================================
    def doc_without_ocr(self):
        Q = "select distinct docID from %s except select distinct docID from %s where field=%d" %(self.docWords_tableName,self.docWords_tableName,self.ID_FULL_TEXT)
        try:
            cur = self.connexion.execute(Q)
            rowIDList = self.rows_to_str(cur,0,'')
            sql_command = "SELECT decrypt(title),decrypt(description),filename,registerDate,registeringPersonID,documentDate,decrypt(tags),checksum,ROWID FROM "+ self.documents_tableName + ' WHERE ROWID IN ' + str(rowIDList)
            cur = self.connexion.execute(sql_command)
            return cur
        except Exception as E:
            logging.debug('SQL ERROR ' + str(E))
            return None
    #===========================================================================
    # folders_childs_of(ID) : retrieve all folders whose parent is ID
    #===========================================================================
    def folders_childs_of(self,ID):
        Q = 'select rowID,name from %s where parentID==?' % self.folders_tableName 
        try:
            cur = self.connexion.execute(Q, [ID,])
            return cur
        except Exception as E:
            logging.debug('SQL ERROR ' + str(E))
            return []
    #===========================================================================
    # folders_find(name_list) : find the folder ID with the specified name hierarchy
    #===========================================================================
    def folders_find(self,name_list):
        current_id=0
        for folder_name in name_list:
            lst = self.folders_childs_of(current_id)
            has_found=False
            for row in lst:
                if row[1] == folder_name :
                    current_id = row[0]
                    has_found=True
                    break
            if not has_found :
                return None
        return current_id
            
        
    #===========================================================================
    # folders_doc_childs_of(ID) : retrieve all docs whose parent is ID
    #===========================================================================
    def folders_doc_childs_of(self,ID):
        Q = 'select docID from %s where folderID==?' % self.folderDoc_tableName
        try:
            cur = self.connexion.execute(Q, [ID,])
            return [row[0] for row in cur]
        except Exception as E:
            logging.debug('SQL ERROR ' + str(E))
            return ()
    #===========================================================================
    # folders_add_child_under(name,ID) : add a child named name under folder ID
    #===========================================================================
    def folders_add_child_under(self,name,ID):
        Q = 'INSERT INTO %s (name,parentID) VALUES (?,?)' % self.folders_tableName 
        try:
            self.connexion.execute(Q, [name,ID])
            self.connexion.commit()
            return True
        except Exception as E:
            logging.debug('SQL ERROR ' + str(E))
            return False
    #===========================================================================
    # folders_remove(ID) : remove a folder from database 
    #===========================================================================
    def folders_remove(self,ID,recursiveRemove=False):
        docList = self.folders_doc_childs_of(ID)
        foldList = self.folders_childs_of(ID)
        foldList = [row[0] for row in foldList]
        if not recursiveRemove and (len(docList)+len(foldList)>0):
            actionList=[_('Remove content') , _('Set to parent folder'),_('cancel')]
            action = _ui.multichoice(actionList, _('This folder is not empty, please choose the action to take'))
            if action==0 : recursiveRemove=True
            if action==1 :
                parentID = self.folders_genealogy_of(ID, False, 2)
                if len(parentID)==0 : return False
                if len(parentID)==1 :
                    parentID=0
                else:
                    parentID=parentID[0][0]
                self.folders_change_folder_parent(ID, parentID)
                self.folders_change_doc_parent(ID, parentID)
            if action==2 : return True
        if recursiveRemove:
            for folderID in foldList : self.folders_remove(folderID, True)
        try:
            if recursiveRemove:
                Q = 'DELETE FROM %s WHERE folderID=?' % self.folderDoc_tableName
                self.connexion.execute(Q, [ID,])
            Q = 'DELETE FROM %s WHERE rowID=?' % self.folders_tableName 
            self.connexion.execute(Q, [ID,])
            self.connexion.commit()
            return True
        except Exception as E:
            logging.debug('SQL ERROR ' + str(E))
            return False
    
    #===========================================================================
    # folders_rename(ID,name) : rename the folder ID with name <name> 
    #===========================================================================
    def folders_rename(self,ID,name):
        try:
            Q = 'UPDATE %s SET name=? WHERE rowID=?' % self.folders_tableName 
            self.connexion.execute(Q, [name,ID])
            self.connexion.commit()
            return True
        except Exception as E:
            logging.debug('SQL ERROR ' + str(E))
            return False
    #===========================================================================
    # folders_change_doc_parent(ID,ID,parentID) : change the parentship of a folder 
    #===========================================================================
    def folders_change_doc_parent(self,oldParentID,newParentID,docID=None):
        try:
            Q = 'UPDATE %s SET folderID=? WHERE folderID=?' % self.folderDoc_tableName
            P=[newParentID,oldParentID]
            if docID is not None :
                Q=Q+' AND docID=?'
                P.append(docID)
            self.connexion.execute(Q, P)
            self.connexion.commit()
            return True
        except Exception as E:
            logging.debug('SQL ERROR ' + str(E))
            return False
    #===========================================================================
    # folders_change_folder_parent(ID,ID,parentID) : change the parentship of a folder 
    #===========================================================================
    def folders_change_folder_parent(self,oldParentID,newParentID):
        try:
            Q = 'UPDATE %s SET parentID=? WHERE parentID=?' % self.folders_tableName
            P=[newParentID,oldParentID]
            self.connexion.execute(Q, P)
            self.connexion.commit()
            return True
        except Exception as E:
            logging.debug('SQL ERROR ' + str(E))
            return False
    #===========================================================================
    # folders_change_parent(folderID,newParentID) : change the parentship of a folder 
    #===========================================================================
    def folders_change_parent(self,folderID,newParentID):
        try:
            Q = 'UPDATE %s SET parentID=? WHERE rowID=?' % self.folders_tableName 
            self.connexion.execute(Q, [newParentID,folderID])
            self.connexion.commit()
            return True
        except Exception as E:
            logging.debug('SQL ERROR ' + str(E))
            return False
    #===========================================================================
    # folders_genealogy_of(folderID) : return the parent, grandparent, grand-grand parents,... of a folder
    #===========================================================================
    def folders_genealogy_of(self,folderID,stringAnswer=True,level=None):
        genealogy = []
        currentLevel=0
        try:
            cont=True
            while cont:
                Q = 'SELECT parentID,name FROM %s WHERE rowID=?' % self.folders_tableName 
                cur = self.connexion.execute(Q, [folderID,])
                V = cur.fetchone()
                parent=V[0]
                if stringAnswer:
                    genealogy.append(V[1])
                else:
                    genealogy.append((folderID,V[1]))
                folderID=parent
                currentLevel+=1
                if level is not None and currentLevel>=level : break
                cont = (parent != 0)
            genealogy.reverse()
            return genealogy
        except Exception as E:
            logging.debug('SQL ERROR ' + str(E))
            return []
    #===========================================================================
    # folders_is_descendant_of(folderID,baseID) : does folder folderID in the descendant of parentID
    #===========================================================================
    def folders_is_descendant_of(self,folderID,baseID):
        genealogy = self.folders_genealogy_of(folderID,False)
        return folderID in [g(0) for g in genealogy]
    #===========================================================================
    # folders_list_for(docID) : list of folderID owning docID
    #===========================================================================
    def folders_list_for(self,docID):
        try:
            Q = 'SELECT folderID FROM %s WHERE docID =?' % self.folderDoc_tableName
            cur = self.connexion.execute(Q, [docID])
            folderID_list = [row[0] for row in cur]
        except Exception as E:
            logging.debug('SQL ERROR ' + str(E))
            folderID_list=[]
        return folderID_list
    #===========================================================================
    # folders_does_doc_descendant_from(docID,baseID) : does doc docID in the descendant of parentID
    #===========================================================================
    def folders_does_doc_descendant_from(self,docID,baseID):
        folderID_list = self.folder_list_for(docID)
        for folderID in folderID_list:
            genealogy = self.folders_genealogy_of(folderID,False)
            if (folderID in [g(0) for g in genealogy]) : return True
        return False
    #===========================================================================
    # folders_set_doc_to(docID,folderID_list) : set the list of folders to which docID belongs
    #===========================================================================
    def folders_set_doc_to(self,docID,folderID_list=None,clear_before=True):
        try:
            if clear_before and not self.folders_remove_doc_from(docID) : return False
            if folderID_list is None or len(folderID_list)<1 : return True
            Q = 'INSERT INTO %s VALUES (?,?)' % self.folderDoc_tableName
            params = [[docID,folderID] for folderID in folderID_list]
            self.connexion.executemany(Q, params)
            self.connexion.commit()
            return True
        except Exception as E:
            logging.debug('SQL ERROR ' + str(E))
            return False
    #===========================================================================
    # folders_rem_doc_from(docID,folderID) : remove the document docID under the folder ID 
    #===========================================================================
    def folders_remove_doc_from(self,docID,folderID_list=None):
        try:
            Q = 'DELETE FROM %s WHERE docID=?' % self.folderDoc_tableName
            params=[docID,]
            if (not folderID_list is None) and len(folderID_list)>0:
                if not hasattr(folderID_list, '__iter__') : folderID_list=[folderID_list,]
                QQ = 'AND folderID_list IN %s' %self.make_placeholder_list(len(folderID_list))
                Q=Q+QQ
                params.extend(folderID_list)
            self.connexion.execute(Q, params)
            self.connexion.commit()
            return True
        except Exception as E:
            logging.debug('SQL ERROR ' + str(E))
            return False
    #===========================================================================
    # get_list_of_tags_for(docList) : list of tags used into the list of docs, ordered by number of occurence 
    #===========================================================================
    def get_list_of_tags_for(self,docID,refusedKeys=None,onlyTags=True):
        try:
            added_cond=''
            params = docID[:]
            if refusedKeys is not None and len(refusedKeys)>0:
                added_cond=' AND keyID NOT IN %s' %self.make_placeholder_list(len(refusedKeys))
                params.extend(refusedKeys)
            if onlyTags : added_cond += ' AND DK.field={0}'.format(self.ID_TAG)
            Q = 'SELECT decrypt(K.keyword),sum(count) as total,DK.keyID FROM %s as K,%s as DK WHERE DK.keyID==K.rowID AND DK.docID in %s %s GROUP BY keyID ORDER BY total DESC' % (self.keywords_tableName,self.docWords_tableName,self.make_placeholder_list(len(docID)),added_cond)
            #print Q
            cur = self.connexion.execute(Q, params)
            return cur
        except Exception as E:
            logging.debug('SQL ERROR ' + str(E))
            return None
    #===========================================================================
    # get_list_of_docs_with_all_keys(keyList) : list of docs containing all the given keys 
    #===========================================================================
    def get_list_of_docs_with_all_keys(self,keys,onlyTags=True):
        try:
            if onlyTags :
                added_cond = ' AND field={0}'.format(self.ID_TAG)
            else:
                added_cond =''
            Q = 'SELECT DISTINCT docID from %s WHERE keyID in %s %s GROUP BY docID HAVING COUNT(docID)=%d ' % (self.docWords_tableName,self.make_placeholder_list(len(keys)),added_cond,len(keys))
            #print Q
            cur = self.connexion.execute(Q,keys)
            return [row[0] for row in cur]
        except Exception as E:
            logging.debug('SQL ERROR ' + str(E))
            return []
    #===========================================================================
    # replicate_in(new_base_name,docList) 
    #===========================================================================
    def replicate_in(self,new_base_name,docList=None,file_replacer=None,new_password=None):
        try:
            # creation of the new database
            newDB = Base()
            newDB.create_and_use(new_base_name, new_password)
            if not newDB.buildDB(): return False
            # replicate the whole folder structure
            Q='SELECT name,parentID,rowID FROM %s' %self.folders_tableName
            cur = self.connexion.execute(Q)
            Q='INSERT INTO %s (name,parentID,rowID) VALUES (?,?,?)'% self.folders_tableName
            newDB.connexion.executemany(Q,cur)

            # replicate the whole person structure
            Q='SELECT name,rowID FROM %s' %self.persons_tableName
            cur = self.connexion.execute(Q)
            Q='INSERT INTO %s (name,rowID) VALUES (?,?)'% self.persons_tableName
            newDB.connexion.executemany(Q,cur)
            
            # replicate the whole keyword structure            
            #     first : find the keywords used
            Q0='SELECT keyID FROM %s' % self.docWords_tableName
            cont=True
            keyIDlist=set()
            pos=0
            # keyIDlist is built by slice of 900 docID since sqlite cannot treat more than 900 params in request
            while cont:
                if docList is not None:
                    pos2=min(pos+900,len(docList))
                    Q=Q0+' WHERE docID IN %s' % self.make_placeholder_list(pos2-pos)
                    P=docList[pos:pos2]
                else:
                    pos2=0
                    Q=Q0
                    P=[]
                cur = self.connexion.execute(Q,P)
                keyIDlist = set.union(keyIDlist,set([row[0] for row in cur]))
                pos=pos2
                if docList is None or pos>=len(docList) : cont=False
            keyIDlist=list(keyIDlist)
            #    then copy these keywords
            Q0='SELECT decrypt(keyword),decrypt(soundex_word),rowid FROM %s' % self.keywords_tableName
            cont=True
            pos=0
            while cont:
                pos2=min(pos+900,len(keyIDlist))
                Q=Q0+' WHERE RowID IN %s' % self.make_placeholder_list(pos2-pos)
                P=keyIDlist[pos:pos2]
                cur = self.connexion.execute(Q,P)
                Q='INSERT INTO %s (keyword,soundex_word,rowid) VALUES (?,?,?)'% self.keywords_tableName
                newDB.connexion.executemany(Q,cur)
                pos=pos2
                if pos>=len(keyIDlist) : cont=False

            # replicate the whole params structure
            Q='SELECT name,value FROM %s' %self.params_tableName
            cur = self.connexion.execute(Q)
            Q='INSERT INTO %s (name,value) VALUES (?,?)'% self.params_tableName
            newDB.connexion.executemany(Q,cur)
            
            # replicate the documents structure (only with docID if specified, all otherwise)
            Q0='SELECT decrypt(title),decrypt(description),filename,registerDate,registeringPersonID,documentDate,decrypt(tags),checksum,rowID FROM %s' % (self.documents_tableName)
            cont=True
            pos=0
            while cont:
                if docList is not None:
                    pos2=min(pos+900,len(docList))
                    Q=Q0+' WHERE rowID IN %s' % self.make_placeholder_list(pos2-pos)
                    P=docList[pos:pos2]
                else:
                    pos2=0
                    Q=Q0
                    P=[]
                cur = self.connexion.execute(Q,P)
                new_cur=[]              
                for row in cur :
                    r=list(row)
                    r[self.IDX_TITLE] = self.encrypt(row[self.IDX_TITLE])
                    r[self.IDX_DESCRIPTION] = self.encrypt(row[self.IDX_DESCRIPTION])
                    r[self.IDX_TAGS] = self.encrypt(row[self.IDX_TAGS])
                    new_cur.append(r)
                cur=new_cur
                Q='INSERT INTO %s (title,description,filename,registerDate,registeringPersonID,documentDate,tags,checksum,rowID) VALUES %s'% (self.documents_tableName,self.make_placeholder_list(self.__doc_nbfields__+1))
                if file_replacer is None:
                    newDB.connexion.executemany(Q,cur)
                else:
                    for row in cur:
                        try:
                            # print "replacing %s by %s" %(row[self.IDX_FILENAME] , str(file_replacer(row[self.IDX_FILENAME])))
                            r=list(row)
                            r[self.IDX_FILENAME] = file_replacer(row[self.IDX_FILENAME])
                            if r[self.IDX_FILENAME] is not None and r[self.IDX_FILENAME] != '': newDB.connexion.execute(Q,r)
                        except Exception as E:
                            logging.debug('SQL ERROR ' + str(E))
                        
                pos=pos2
                if docList is None or pos>=len(docList) : cont=False
            # replicate the docWords structure (only with docID if specified, all otherwise)
            Q0='SELECT keyID,docID,field,count FROM %s' % self.docWords_tableName
            cont=True
            pos=0
            while cont:
                if docList is not None:
                    pos2=min(pos+900,len(docList))
                    Q=Q0+' WHERE docID IN %s' % self.make_placeholder_list(pos2-pos)
                    P=docList[pos:pos2]
                else:
                    pos2=0
                    Q=Q0
                    P=[]
                cur = self.connexion.execute(Q,P)
                Q='INSERT INTO %s (keyID,docID,field,count) VALUES (?,?,?,?)'% (self.docWords_tableName)
                newDB.connexion.executemany(Q,cur)
                pos=pos2
                if docList is None or pos>=len(docList) : cont=False
            # replicate the folderDoc structure (only with docID if specified, all otherwise)
            Q0='SELECT docID,folderID FROM %s' % (self.folderDoc_tableName)
            cont=True
            pos=0
            while cont:
                if docList is not None:
                    pos2=min(pos+900,len(docList))
                    Q=Q0+' WHERE docID IN %s' % self.make_placeholder_list(pos2-pos)
                    P=docList[pos:pos2]
                else:
                    pos2=0
                    Q=Q0
                    P=[]
                cur = self.connexion.execute(Q,P)
                Q='INSERT INTO %s (docID,folderID) VALUES (?,?)'% (self.folderDoc_tableName)
                newDB.connexion.executemany(Q,cur)
                pos=pos2
                if docList is None or pos>=len(docList) : cont=False

            newDB.connexion.commit()
            newDB.connexion.close()
            return True
        except Exception as E:
            logging.debug('SQL ERROR ' + str(E))
            _ui.show_message(_('Unable to create the database {name} : {err}'.format(name=new_base_name,err=str(E))))
            return False
        
    def export_database(self,filename,rows):
        docIDlist = [row[self.IDX_ROWID] for row in rows]
        self.replicate_in(filename, docIDlist)
    def export_archive(self,filename,rows):
        docIDlist = [row[self.IDX_ROWID] for row in rows]
        (name,ext) =  os.path.splitext(filename)
        self.replicate_in(filename, docIDlist)
        zf = zipfile.ZipFile(filename,'w')
        fileDict = dict()
        for f in [row[self.IDX_FILENAME] for row in rows] :
            arcname = os.path.basename(f)
            if arcname in list(fileDict.values()):
                (name,ext) = os.path.splitext(arcname)
                nn=1
                while arcname in list(fileDict.values()):
                    nn+=1
                    arcname=name+'_'+str(nn)+ext
            fileDict[f] = arcname
            zf.write(f, arcname, zipfile.ZIP_DEFLATED)
        tmpFile = os.tmpnam()
        self.replicate_in(tmpFile,docIDlist,file_replacer = lambda f:  fileDict[f])
        zf.write(tmpFile, 'database.db', zipfile.ZIP_DEFLATED)
        zf.close()
    def import_archive(self,filename,dirname):
        zf = zipfile.ZipFile(filename,'r')
        try:
            zf.extractall(dirname)
            self.use_base(os.path.join(dirname,'database.db'))
            self.set_directory(dirname)
        except Exception as E:
            logging.debug('SQL ERROR ' + str(E))
            _ui.show_message(_('Unable to open the archive {0}'.format(filename)))
    def make_full_name(self,fname,dirname):
        if os.path.isabs(fname) :
            return fname
        else:
            return os.path.abspath(os.path.join(dirname,fname))
    def set_directory(self,dirname):
        try:
            Q = "UPDATE %s SET filename=MAKE_FULL_PATH(filename,'%s')" %(self.documents_tableName,dirname)
            self.connexion.execute(Q)
            self.connexion.commit()
        except Exception as E:
            logging.debug('SQL ERROR ' + str(E))
