# BehaguneUI
Django Web application for monitoring opinions about events

This repository contains the User Interface and data visualization software. Data is read from a database fed by Elhuyar/MSM software(https://github.com/Elhuyar/MSM) and sentimen analysis is provided by the Elhuyar/Elixa software (https://github.com/Elhuyar/Elixa).

Just clone the repositorty and execute the usual django buildout programs.

````shell
git clone https://github.com/Elhuyar/BehaguneUI
cd BehaguneUI
python bootstrap.py
./bin/buildout
````

Now your django application is ready. In order to test it run the runserver in a port of your choice (8001 in the example bellow):

````shell
nohup ./bin/django runserver 127.0.0.1:8001 &
````
