import fitz
import glob
import subprocess
import pandas as pd
from pathlib import Path
import environ
import zipfile
import filetype

from PIL import Image
from hashlib import md5
from PyPDF2 import PdfReader
from docx import Document
import magic
import os

from termcolor import colored

env = environ.Env()
environ.Env.read_env()

LOCAL_ADDRESS = env("LOCAL_ADDRESS")
ENTITY_DIR = env("ENTITY_DIR")
OLD_FILE_BASE_DIR = env("OLD_FILE_BASE_DIR")
NEW_FILE_BASE_DIR = env("NEW_FILE_BASE_DIR")
MONGO_CON_STR = env("MONGO_CON_STR")
PROJECT_DIR = env("PROJECT_DIR")
MONGO_COLLECTION = env("MONGO_COLLECTION")
DIRS = [
    # 'archive-جامعة الملك سعود- ru archive hast veli fehrestsh nis',
    # 'bgh',
    # 'bkb',
    # 'bkio',
    # 'bm4u',
    'bnr'
    # 'bskn',
    # 'gsh',
    # 'ind',
    # 'ktb',
    # 'M-ALDAHREH',
    # 'maqr',
    # 'mdft',
    # 'mfyz',
    # 'mmjs',
    # 'mmnw',
    # 'mtof',
    # 'mmzy',
    # 'mtymry',
    # 'tu wqf hastنجيبويه',
    # 'دار الكتب القطريةfehrest darad vali bayad chack shavad',
    # 'ولي الدين'
        ]


def copy_file(*,old_file_path,new_file_path):
    mkdir_proc = subprocess.run(
        ["mkdir", "-p", f"{new_file_path}/"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    copy_proc = subprocess.run(
        ["cp",f"{old_file_path}", f"{new_file_path}/"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if mkdir_proc.returncode ==0 and copy_proc.returncode == 0:
        return True
    else:
        return False

def get_from_csv(*,dir):
    columes = ["identifier","title","author","collections","description","topics","language","files"]
    df = pd.read_csv(filepath_or_buffer=f"{PROJECT_DIR}/{dir}.csv",names=columes,sep=",",header=0,encoding="utf8")
    info_dir = df.to_dict('list')
    # info_dir is dict with every header as key and list of values in csv
    # info_dir = {'identifier': ['bnr1', 'bnr100', 'bnr1000'...],'title': ['القران الكريم', 'الخالدون مائة اعظمهم محمد (ص) للكاتب انيس منصور',...],...}
    return info_dir

def split_path(path):
    if path[-1] == '/': # delete / at last of path
        path = path[:-1]

    return path.split('/')  # return every section of path

def is_in_compressed(path): # check compress and split path of zip and folders and files in zip file
    try:
        splitted_path = split_path(path)
        for index, item in enumerate(splitted_path):
            if item.lower().endswith('.zip') and index + 1 != len(splitted_path):
                zip_path = '/'.join(splitted_path[:index + 1]) # zip file path
                file_path = '/'.join(splitted_path[index + 1:]) # folders and files pathes in zip
                return True, zip_path, file_path
    except IndexError:
        pass
    return False, None, None


def is_ok_zip_file(zip_file): #check zip file accuracy
    _zip = zipfile.ZipFile(zip_file)
    if _zip.testzip() is not None:
        return False
    return True

def get_files_in_zip(zip_file):
    _zip = zipfile.ZipFile(zip_file)
    inner_files = [_file for _file in _zip.namelist() if not _file.endswith('/')]
    return inner_files


def get_zip_meta(zip_file,file_path):
    _zip = zipfile.ZipFile(zip_file)
    inner_files = get_files_in_zip(zip_file)
    metas = []
    for i in inner_files:
        meta = get_file_meta(_zip.open(i),file_path)
        meta['path'] = i
        metas.append(meta)
        try:
            size=sum([i['size'] for i in metas])
        except:
            size="None"
    zip_meta = {
        'size': size,
        'type': 'zip',
        'inner_files': metas
    }
    return zip_meta

def get_file_meta(file,file_path):
    _type = get_file_type(file)
    if _type != None:
        if _type.mime.split('/')[0] == 'image':
            meta = get_image_meta(file)
        elif _type.extension == 'pdf':
            meta = get_pdf_meta(file)
        elif _type.extension in ['doc', 'docx']:
            meta = get_doc_meta(file)
        else:
            meta = get_others_meta(file)
    else:
        meta = {'type': None}
    meta['md5'] = md5sum(open(file_path,"rb").read())
    mime = magic.Magic(mime=True)
    meta['mime']=mime.from_file(file_path)
    return meta

def get_file_type(path: str):
    return filetype.guess(path)


def md5sum(data):
    """
    :param data: must be binary
    :return:
    """
    return md5(data).hexdigest()

def get_image_meta(img):
    file=open(img,'rb')
    image = Image.open(img)
    return {
        'type': image.format,
#        'size': len(img.read()),
        'size': len(file.read()),
        'width': image.width,
        'height': image.height
    }

def get_pdf_meta(pdf):
    PDF = PdfReader(pdf)
    if PDF.metadata == None:
        author, creator, keywords, title = "", "", "", ""
    else:
        author = PDF.metadata.get('/Author', None)
        creator = PDF.metadata.get('/Creator', None)
        keywords = PDF.metadata.get('/Keywords', '').split(',')
        title = PDF.metadata.get('/Title', None)
    pages = len(PDF.pages)
    return {
        'type': 'pdf',
        'size': len(pdf.read()),
        'author': author,
        'creator': creator,
        'keywords': keywords,
        'title': title,
        'pages': pages,
    }


def get_doc_meta(doc):
    DOC = Document(doc)
    author = DOC.core_properties.author
    keywords = DOC.core_properties.keywords.split(',')
    title = DOC.core_properties.title
    subject = DOC.core_properties.subject
    return {
        'type': get_file_type(doc).extension,
        'size': len(doc.read()),
        'author': author,
        'keywords': keywords,
        'title': title,
        'subject': subject,
    }


def get_others_meta(others):
    return {
        'type': get_file_type(others).extension,
        'size': len(others.read())
    }

def metadata(*,file_path):
    compressed, zip_path, inner_file_path = is_in_compressed(file_path)
    if compressed: # compressed means files in zip
        if is_ok_zip_file(open(zip_path, 'rb')):
            meta = get_zip_meta(open(zip_path, 'rb'),file_path=file_path)
        else:
            meta = {}
            print(colored(f"!!!!!!!!!!!!! ZIP IS CORRUPTED !!!!!!!!!!!!", "red"))
    elif get_file_type(file_path).extension == 'zip': # means zip itself
        #print(11111)
        if is_ok_zip_file(open(file_path, 'rb')):
            zip_meta = get_zip_meta(open(file_path, 'rb'),file_path=file_path)
        else:
            zip_meta = {}
            print(colored(f"!!!!!!!!!!!!! ZIP IS CORRUPTED !!!!!!!!!!!!", "red"))
        meta_file = get_file_meta(open(file_path, 'rb'),file_path=file_path)
        meta = {}
        meta.update(zip_meta) #zip_meta contains innerfiles metadata
        meta.update(meta_file) # meta_file does replace size mime md5 type in zip_meta
    else:
        meta = get_file_meta(open(file_path, 'rb'),file_path=file_path)
    return meta

def convertion(pdf_path,pdf_file):
    #open your file
    doc = fitz.open(pdf_path+'/'+pdf_file)
    #iterate through the pages of the document and create a RGB image of the page
    for page in doc:
        pix = page.get_pixmap()
        pix.save(f"{pdf_path}/{pdf_file}_files/{pdf_file.strip('.pdf')}-page-%i.jpeg" % page.number)
        if page.number == '0' :
            os.rename(f"{pdf_file.strip('.pdf')}-page-0.jpeg",f"{pdf_file.strip('.pdf')}_thumb.jpeg",f"{pdf_path}/{pdf_file}_files",f"{pdf_path}/{pdf_file}_files")

def convert_pdf_img(dir,entity,pdf_file):
            try:
                os.mkdir(NEW_FILE_BASE_DIR+'/'+dir+'/'+entity+'/'+f'{pdf_file}_files')
            except FileExistsError:
                    pass
            if glob.glob(NEW_FILE_BASE_DIR+'/'+dir+'/'+entity+'/'+f'{pdf_file}_files'+'/'+'*') == []:
                convertion(pdf_path=NEW_FILE_BASE_DIR+'/'+dir+'/'+entity,pdf_file=pdf_file)
            else:
                pass

def get_image_files(dir,entity,pdf_file):
    images = os.listdir(NEW_FILE_BASE_DIR+'/'+dir+'/'+entity+'/'+f'{pdf_file}_files')
    image_files = []
    for image in images:
        image_files.append(os.path.join(NEW_FILE_BASE_DIR+'/'+dir+'/'+entity+'/'+f'{pdf_file}_files',image))
#    print(f'$$$$${image_files}$$$$')
    return image_files
