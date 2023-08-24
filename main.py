import utils
import models
from termcolor import colored

for dir in utils.DIRS: # dir means each collection
    csv_info = utils.get_from_csv(dir=dir)
    print(colored("************* READ CSV INFORMAITION **************","green"))
    connection_string = models.connect_to_mongo(collection_name=utils.MONGO_COLLECTION) # connect to mongo collection
    copied_file = models.add_files_to_collection(dir=dir,connection_string=connection_string, csv_info=csv_info)
    print(colored(f"************* INSERTED DATA OF DIRECTORY {dir} TO MONGO **************", "green"))

print(colored(f"COPIED FILES: \n{copied_file}","yellow"))
