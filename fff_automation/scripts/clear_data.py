# USE THIS SCRIPT ONLY ON TESTING GROUNDS AS IT WILL ERASE ALL DATA SAVED IN THE DATABASE.
# To use this script, move the file to the parent folder "fff-transparency-wg" and run the file from there.
import os
import sys
from fff_automation.modules import sheet, settings, trelloc

if __name__ == '__main__':
    # DELETE DATABASE
    os.remove('data.db')
    trelloc.clear_data()
    sheet.clear_data()
    
    print('CLEAR_DATA: Done')
    sys.exit(0)
