# BehaguneUI

Django Web application for monitoring opinions about events

This repository contains the User Interface and data visualization software. Data is read from a MYSQL database fed by Elhuyar/MSM software(https://github.com/Elhuyar/MSM) and sentiment analysis is provided by the Elhuyar/Elixa software (https://github.com/Elhuyar/Elixa).
The database structure and the information required for setting up the database is part of the MSM crawler documentation: https://github.com/Elhuyar/MSM

Just clone the repositorty and execute the usual django buildout programs.

````shell
git clone https://github.com/Elhuyar/BehaguneUI
cd BehaguneUI
python bootstrap.py
./bin/buildout
````

The last step is to setup your django application. Edit the ```src/behagunea/settings.py``` file and fill the following fields according to your configuration:
```
      'NAME': 'yourDBNAME',                      # Or path to database file if using sqlite3. 
      'PASSWORD': 'yourMYSQLuserPassword',                  # Not used with sqlite3.
      'USER':'yourMYSQLuser',                  # Not used with sqlite3.
      'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
      'PORT': '',  
```

Now your django application is ready. In order to test it run the runserver in a port of your choice (8001 in the example bellow):

````shell
nohup ./bin/django runserver 127.0.0.1:8001 &
````


