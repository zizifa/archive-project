i#from django.db import models
from datetime import datetime
from pymongo import MongoClient
import utils
import requests
from termcolor import colored
from utils import LOCAL_ADDRESS,MONGO_CON_STR,NEW_FILE_BASE_DIR,OLD_FILE_BASE_DIR
# Create your models here.

def connect_to_mongo(*,collection_name):
    client = MongoClient(MONGO_CON_STR)
    mydb = client['archive']
    connection_string = mydb[f'{collection_name}']
    return connection_string

def add_files_to_collection(*,dir,connection_string,csv_info):
    #headers = ["identifier","title","description","mediatype","language","ocr_status","local_address","collections","date_created","date_updated","topics","attachments"]
    #columes = ["identifier","title","author","collections","description","topics","language","files"]
    # mediatype , ocr_status , local_address,"date_created","date_updated",
    copied_file = []
    not_copied_file_name = []
    not_copied_file_identifier = []
    for i in range(len(csv_info['identifier'])):
        db_objects = {} # db_object is original json for inserting database
        this_identifier = csv_info['identifier'][i]
        object_same = connection_string.find_one({"identifier": this_identifier}) #  object_same is None if the identifier not exists in db
        if object_same != None: # it means it exists in db so not insert
            continue
        db_objects['identifier'] = this_identifier
        db_objects['ocr_status'] = ""
        db_objects['local_address'] = f"{NEW_FILE_BASE_DIR}/{dir}/{db_objects['identifier']}/"
        db_objects['date_created'] = datetime.today().strftime('%Y-%m-%d')
        db_objects['date_updated'] = datetime.today().strftime('%Y-%m-%d')
        db_objects['collections'] = csv_info['collections'][i].split("|")
        db_objects['description'] = csv_info['description'][i]
        db_objects['topics'] = csv_info['topics'][i].split("|")
        files_inside = csv_info['files'][i].split("|")
        attachment = []
        for file in files_inside:
            fileobject = {}
            name = file.split("=")[0].strip()
            caption = file.split("=")[1]
            success_copy = utils.copy_file(old_file_path=f"{OLD_FILE_BASE_DIR}/{dir}/{name}",new_file_path=f"{NEW_FILE_BASE_DIR}/{dir}/{db_objects['identifier']}/")
            if success_copy == True:
                copied_file.append(name)
#                print(name)
                metadata = utils.metadata(file_path=f"{OLD_FILE_BASE_DIR}/{dir}/{name}")
                fileobject['id'] = metadata['md5']
                fileobject['name'] = name
                fileobject['caption'] = caption
                fileobject['type'] = metadata['type']
                fileobject['mime'] = metadata['mime']
                fileobject['md5'] = metadata['md5']
                fileobject['size'] = f"{metadata['size']}"
                fileobject['source'] = "original"
                fileobject['format'] = ""
                fileobject['date_created'] = datetime.today().strftime('%Y-%m-%d')
                fileobject['date_updated'] = datetime.today().strftime('%Y-%m-%d')
                fileobject['local_address'] = db_objects['local_address'] + name
                details = {}
                details['name_of_file'] = name
                details['author'] = csv_info['author'][i]
                fileobject['details'] = details
                if metadata['type'] =='zip':
                    fileobject['files_inside'] = []
                elif fileobject['type'] == 'pdf':
                    fileobject['files_inside'] = ['xx']
                else:
                    pass
            else:
                not_copied_file_name.append(name)
                not_copied_file_identifier.append(this_identifier)
            attachment.append(fileobject)
        db_objects['attachments'] = attachment
        if this_identifier in not_copied_file_identifier:
            print(colored(
                f"************* ENTITY WITH IDENTIFIER {this_identifier} NOT INSERTED IN DB. FILES OF THIS ENTITY NOT EXISTS IN SERVER TO COPY **************",
                "red"))
        else:
            connection_string.insert_one(db_objects)
            print(colored(f"************* ENTITY WITH IDENTIFIER {this_identifier} INSERTED IN DB **************","green"))
    return copied_file
