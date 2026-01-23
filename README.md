# Explanation of the different files

## Thread.exe
Exectable that starts the application to visuallise the readings and create the csv reports

## csv_merge
Contains the python script for merging the excel reports.

In the data folder we can find examples of data reports.

In order to execute the script: 

python merge_data.py

or

python3 merge_data.py

Dependencies  to be installed with the following command:

pip install pandas openpyxl

The wotking folder must have the following structure:

working_folder

  |
  
  ¬ merge_data.py
  
  ¬ data
  
    |
    
    ¬(all excel files)
  
