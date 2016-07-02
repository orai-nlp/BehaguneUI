# BehaguneUI

Django Web application for monitoring opinions about events

This repository contains the User Interface and data visualization software. Data is read from a MYSQL database fed by Elhuyar/MSM software(https://github.com/Elhuyar/MSM) and sentiment analysis is provided by the Elhuyar/Elixa software (https://github.com/Elhuyar/Elixa).


Installation
-------------

Just clone the repositorty and execute the usual django buildout programs.

````shell
git clone https://github.com/Elhuyar/BehaguneUI
cd BehaguneUI
python bootstrap.py
./bin/buildout
````

If buildout command ends with errors, you are probably missing some python development files. Common error are given by the regex and Pillow libraries. In linux (ubuntu 14.04) Install the following packages and execute the buildout command again:
```shell
$sudo apt-get install python-all-dev zlib1g zlib1g-dev zlibc libjpeg-dev
$./bin/buildout
```


Setting up Django
-------------------

In order to setup your django application, edit the ```src/behagunea/settings.py``` file and fill the following fields according to your configuration:
```
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
 	'NAME': 'yourDBNAME',                      # Or path to database file if using sqlite3. 
	'PASSWORD': 'yourMYSQLuserPassword',                  # Not used with sqlite3.
	'USER':'yourMYSQLuser',                  # Not used with sqlite3.
	'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
	'PORT': '',  
	}
}

...


TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(BASEDIR,'/behagunea_templates/'),
    '/home/ubuntu/BehaguneUI/src/behagunea/behagunea_templates/',
    '/home/ubuntu/BehaguneUI/src/behagunea/behagunea_templates/ajax/',
)
```

Setting up the Database
------------------------

Django takes care of creating the database, but it requires that the schema exists in mysql.

Create database schema (your mysql user must have create privileges)

```shell
$mysql -u yourMYSQLuser -p yourMYSQLuserPassword -e "create schema yourDBNAME;"
``` 

and execute django syncdb command.
 
```shell
$./bin/django syncdb
```

* Common problems with syncdb: 
*- mysqldb is missing: install python-mysqldb package. 

```shell
$sudo apt-get install python-mysqldb
```
*- syncdb complains about permission to access/create temporal files: 
  execute the command again:

```shell
$./bin/django syncdb
```


Launch Django
================

Now your django application is ready. In order to test it run the runserver in a port of your choice (8001 in the example bellow):

````shell
nohup ./bin/django runserver 127.0.0.1:8001 &
````


