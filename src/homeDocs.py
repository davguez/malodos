#!/usr/bin/python 

'''
Created on 21 juin 2010. Copyright 2010, David GUEZ
@author: david guez (guezdav@gmail.com)
MALODOS (for MAnagement of LOcal DOcument System) is a simple but useful
software aimed to help the process of archiving and navigate between the documents presents
in your hard-drive.
It is written in python and mainly merges numerous external libraries to
give a fast and simple way to scan and numerically record your personal documents (such
as invoices, taxes declaration, etc...).
Being written in python, it is portable (works on windows and linux at least, not tested
on other systems).

The complete documentation can be found here : http://sites.google.com/site/malodospage/
The latest version can be downloaded from here : http://code.google.com/p/malodos/
If you like and use this software, please consider to donate to support its development.
'''
import gettext
import os
import locale
import sys
import logging
import getopt
import datetime


def _real_path(path):
    if not path:
        return ''
    return os.path.realpath(os.path.abspath(path))


_src_root = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_src_root)

seen = set()
filtered = []
for entry in sys.path:
    if entry == '':
        filtered.append(entry)
        continue
    real = _real_path(entry)
    if real in seen:
        continue
    seen.add(real)
    filtered.append(entry)
sys.path[:] = filtered

for candidate in (_src_root, _project_root):
    real = _real_path(candidate)
    if any(_real_path(entry) == real for entry in sys.path):
        continue
    sys.path.insert(0, real)

if _src_root not in sys.path:
    sys.path.insert(0, _src_root)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import algorithms
__version__ = '1.3.1'


exe_name = os.path.dirname(os.path.abspath(os.path.join(algorithms.__file__,'..')))
if not exe_name:
    try:
        exe_name = os.getcwd()
    except:
        pass
if not exe_name :
    try:
        exe_name = os.path.dirname(os.path.realpath(sys.executable))
    except:
        pass
if not exe_name :
    try:
        exe_name = os.path.dirname(__file__)
    except:
        pass
if not exe_name: exe_name = '.'
ld = os.path.join(exe_name ,'locale')
# code bellow copied from http://www.journaldunet.com/developpeur/tutoriel/pyt/070607-python-traduction/2.shtml

gettext.install('malodos', localedir = ld)
import database
choosed_lang = database.theConfig.get_current_language()
#x=gettext.find("malodos", localedir = ld,languages=['en'])
#print ld
#print x
try:
    if os.name == 'nt':
        if choosed_lang=='sys':
            lang = locale.getdefaultlocale()[0][:2]
        else:
            lang=choosed_lang
            cur_lang = gettext.translation('malodos', localedir=ld, languages=[lang])
            cur_lang.install()
    else :
        if choosed_lang=='sys':
            gettext.install('malodos', localedir = ld)
        else:
            tr = gettext.translation('malodos', localedir = ld, languages=[choosed_lang])
            tr.install()
except IOError as E:
    print(str(E))

# end of copy part

def print_query_result(sFilter,frmt='%t',date_format='%d-%m-%Y'):
    import algorithms.stringFunctions as SF
#    print "Querying with " + sFilter
    if len(sFilter)==0:
        docList = database.theBase.find_documents(None)
    else:
        [request,pars] = SF.req_to_sql(sFilter)
        docList = database.theBase.find_sql(request,pars)
    if docList is None : docList=[]
    docList=[row for row in docList]
    for row in docList:
        s = str(frmt)
        docID = row[database.theBase.IDX_ROWID]
        foldList = database.theBase.folders_list_for(docID)
        folderStringList=[]
        for folderID in foldList:
            folderHierarchy = '/'.join(database.theBase.folders_genealogy_of(folderID, True))
            folderStringList.append(folderHierarchy)
        strFolders=','.join(folderStringList)
        try:
            s = s.replace('%t',row[database.theBase.IDX_TITLE])
        except Exception as E:
            logging.exception('Problem in query format : ' + str(E))
        try:
            s = s.replace('%d',row[database.theBase.IDX_DESCRIPTION])
        except Exception as E:
            logging.exception('Problem in query format : ' + str(E))
        try:
            s = s.replace('%D',row[database.theBase.IDX_DOCUMENT_DATE].strftime(date_format))
        except Exception as E:
            logging.exception('Problem in query format : ' + str(E))
        try:
            s = s.replace('%R',row[database.theBase.IDX_REGISTER_DATE].strftime(date_format))
        except Exception as E:
            logging.exception('Problem in query format : ' + str(E))
        try:
            s = s.replace('%m',row[database.theBase.IDX_CHECKSUM])
        except Exception as E:
            logging.exception('Problem in query format : ' + str(E))
        try:
            s = s.replace('%F',strFolders)
            #s = frmt.replace_all('%u',str(row[database.theBase.IDX_REGISTER_PERSON_ID]))
        except Exception as E:
            logging.exception('Problem in query format : ' + str(E))
        try:
            s = s.replace('%f',row[database.theBase.IDX_FILENAME])
        except Exception as E:
            logging.exception('Problem in query format : ' + str(E))
        print(s)

def start_gui():
    from src.mvc.app import MALODOSApp
    app = MALODOSApp([])
    auto_quit_ms = os.environ.get('MALODOS_AUTOTEST_EXIT_MS')
    if auto_quit_ms:
        try:
            from PySide6.QtCore import QTimer
            QTimer.singleShot(int(auto_quit_ms), app.quit)
        except Exception:
            pass
    exit_code = app.exec()
    try:
        sys.stdout.flush()
        sys.stderr.flush()
    except Exception:
        pass
    # Work around a native PySide6 teardown crash happening after app.exec() returns.
    os._exit(int(exit_code) if exit_code is not None else 0)

if __name__ == "__main__":
    logfilename=os.path.join(database.theConfig.conf_dir ,'messages.log')
    logging.basicConfig(filename=logfilename, filemode='w', level=logging.DEBUG,format='%(levelname)s %(message)s at %(filename)s on line %(lineno)d function %(funcName)s ')
    logging.info('Starting MALODOS')
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hvd:q:a:f:F:", ["help","version","database=","format=","add=","dateFormat=","title=",'description=','tags=','folders=','date='])
    except getopt.error as msg:
        print(msg)
        print("for help use --help")
        sys.exit(2)
    # process options
    query_format='%t'
    date_format='%d-%m-%Y'
    title='Untitled'
    description=''
    folderList=''
    docDate=datetime.date.today()
    tagList=''
    queryStr=None
    addFile=None
    for o, a in opts:
        if o in ("-h", "--help"):
            print(__doc__)
            sys.exit(0)
        if o in ('-v','--version'):
            print(__version__)
            sys.exit(0)
        if o in ('-d','--database'): database.theBase.use_base(a)
        if o in ('-f','--format'): query_format=a
        if o in ('-F','--dateFormat'): date_format=a
        if o in ('--title'): title=a
        if o in ('--description'): description=a
        if o in ('--date'): docDate=datetime.datetime.strptime(a,date_format).date()
        if o in ('--folders'): folderList=a
        if o in ('--tags'): tagList=a
        if o in ('-q','--query'):
            queryStr=a
        if o in ('-a','--add'):
            addFile=a
    if queryStr is not None:
        print_query_result(queryStr,query_format,date_format)
    if addFile is not None:
        foldIdList=[]
        lstFolds = folderList.split(',')
        for i in lstFolds:
            name_list = i.split('/')
            doc_id = database.theBase.folders_find(name_list)
            if doc_id is not None and doc_id != 0: foldIdList.append(doc_id)
        keywordsGroups = database.theBase.get_keywordsGroups_from(title, description, addFile , tagList)
        database.theBase.add_document(addFile, title, description, None, docDate, keywordsGroups,tagList,foldIdList)
    if queryStr is None and addFile is None : start_gui()
    logging.info('Exiting MALODOS')
