#from distutils.core import setup
from setuptools import setup , find_packages , findall
from os import listdir
from os.path import splitext , split , join , isfile

txt_files = listdir('..')
for i in txt_files : print(join('..',i))
txt_files = [ join('..',i) for i in txt_files if splitext(i)[1] == '.txt' ]

setup(
    url='http://sites.google.com/site/malodospage/',
    license='GPL v3',
    install_requires=['Pillow','wxPython','pyenchant','bcrypt','pycryptodome','pypdfium2'],
    name='MALODOS',
    description='Personal EDM (Scan, describe and manage your personal documents)',
    version='1.3.1',
    author='David GUEZ',
    author_email='guezdav@gmail.com',
    packages=['algorithms','database','data','gui','scannerAccess','font'],
    scripts = ['homeDocs.py'],
    classifiers=['Topic :: Office/Business','Operating System :: Microsoft :: Windows','Operating System :: POSIX','Programming Language :: Python','Development Status :: 5 - Production/Stable','Intended Audience :: End Users/Desktop','License :: OSI Approved :: GNU Affero General Public License v3'],
    data_files = [ ('',txt_files) , ('resources/icons',findall('../resources/icons')), ('resources',[i for i in findall('../resources') if isfile(i)]),('locale',findall('locale')) ]
)
