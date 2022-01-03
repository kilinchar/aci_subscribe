# Use this file to store your credentials for the code samples if you want.
# All code samples assume the config.py file is located in the same directory as the code.
# In order to store password, windows/linux environment variables are utilised. 
import os
controller = "X.X.X.X"
username = "admin"
password = os.environ.get("ACI_PASS")
dbuser = os.environ.get("DB_USER")
dbpass = os.environ.get("DB_PASS")
dbip = "X.X.X.X"