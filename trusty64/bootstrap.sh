#!/bin/bash

sudo apt-get update

# Apache setup
sudo apt-get install -y apache2
if ! [ -L /var/www ]; then
  echo "Vagrant No soft link "
  rm -rf /var/www
  rm -rf /var/www/maze
  ln -fs /vagrant/UI/Maze /var/www
  ln -fs /vagrant/src/maze /var/www/maze
  ln -fs /vagrant/src/notify /var/www/notify
  cp /vagrant/trusty64/000-default.conf /etc/apache2/sites-enabled/000-default.conf 
  cp /vagrant/trusty64/default-ssl.conf /etc/apache2/sites-enabled/default-ssl.conf
  cp /vagrant/trusty64/apache2.conf /etc/apache2/apache2.conf
  cp  /vagrant/trusty64/port.conf  /etc/apache2/ports.conf
fi
sudo a2enmod headers
sudo a2enmod rewrite 
sudo a2enmod ssl
sudo service apache2 restart
sudo apt-get install libapache2-mod-wsgi python-dev
sudo a2enmod wsgi
# APACHE CHANGES
#  apache2.conf -- Directory /var/www
#  ports.conf -- Listen 8080
#
#  sites-enabled/000-default.conf 
#  VirtualHost:80 -- ProxyPass / http://localhost:8080/
# In here make Documentroot point to /var/www
#LoadModule directives
#LoadModule proxy_module /usr/lib/apache2/modules/mod_proxy.so
#LoadModule proxy_http_module /usr/lib/apache2/modules/mod_proxy_http.so
#  Add a new virtualHost for 8080 and locationMatch for 5000 for all api endpoints
# <VirtualHost 127.0.0.1:8080>
#	Header always set Access-Control-Allow-Origin "*"
#	Header always set Access-Control-Allow-Methods "POST, GET, OPTIONS, DELETE, PUT"
#	Header always set Access-Control-Max-Age "1000"
#	Header always set Access-Control-Allow-Headers "x-requested-with, Content-Type, origin, authorization, accept, client-security-token"	
# <LocationMatch "/users">
#    RequestHeader unset RBM-Authorization
#    Header unset Server
#    ProxyPass http://localhost:5000/users
# </LocationMatch>
#<LocationMatch "/professionals">
#    RequestHeader unset RBM-Authorization
#    Header unset Server
#    ProxyPass http://localhost:5000/professionals
#</LocationMatch>
#<LocationMatch "/professions">
#    RequestHeader unset RBM-Authorization
#    Header unset Server
#    ProxyPass http://localhost:5000/professions
#</LocationMatch>
# <LocationMatch "/notify">
#    RequestHeader unset RBM-Authorization
#    Header unset Server
#    ProxyPass http://localhost:5500/notify
# </LocationMatch>
# <LocationMatch "/upload">
#    RequestHeader unset RBM-Authorization
#    Header unset Server
#    ProxyPass http://localhost:5000/upload
# </LocationMatch>
#
#	RewriteEngine On
#	RewriteCond %{REQUEST_METHOD} OPTIONS
#	RewriteRule ^(.*)$ $1 [R=200,L]
#
#</VirtualHost>
# For enabling SSL HTTPS here is the link
#https://www.digitalocean.com/community/tutorials/how-to-create-a-ssl-certificate-on-apache-for-ubuntu-14-04
#sudo a2enmod ssl
#sudo service apache2 restart
#sudo mkdir /etc/apache2/ssl
#sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /etc/apache2/ssl/apache.key -out /etc/apache2/ssl/apache.crt
#sudo vi /etc/apache2/sites-available/default-ssl.conf
'''<IfModule mod_ss.c>
        <VirtualHost _default_:443>
                ServerAdmin webmaster@localhost
                ServerName  33.33.33.33
                DocumentRoot /var/www
                ErrorLog ${APACHE_LOG_DIR}/error.log
                CustomLog ${APACHE_LOG_DIR}/access.log combined
                SSLEngine on
                SSLProtocol all
                SSLCertificateFile      /etc/apache2/ssl/apache.crt
                SSLCertificateKeyFile /etc/apache2/ssl/apache.key
                <FilesMatch "\.(cgi|shtml|phtml|php)$">
                                SSLOptions +StdEnvVars
                </FilesMatch>
<Directory /var/www>
    Options Indexes FollowSymLinks MultiViews
    AllowOverride None
    Order allow,deny
    allow from all
    RewriteEngine on
</Directory>
ProxyPass / http://localhost:8080/
                BrowserMatch "MSIE [2-6]" \
                                nokeepalive ssl-unclean-shutdown \
                                downgrade-1.0 force-response-1.0
                BrowserMatch "MSIE [17-9]" ssl-unclean-shutdown

        </VirtualHost>
</IfModule>'''
#sudo a2ensite default-ssl.conf
#sudo service apache2 restart
#
# If the above setup does not work, copy over the virtualHost config into apache.conf

# MySQL install
sudo debconf-set-selections <<< 'mysql-server mysql-server/root_password password vagrant'
sudo debconf-set-selections <<< 'mysql-server mysql-server/root_password_again password vagrant'
sudo apt-get install -y vim curl python-software-properties
sudo apt-get update
sudo apt-get -y install mysql-server
sudo apt-get -y install libmysqlclient-dev
sed -i "s/^bind-address/#bind-address/" /etc/mysql/my.cnf
mysql -u root -pvagrant -e "GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' IDENTIFIED BY 'root' WITH GRANT OPTION; FLUSH PRIVILEGES;"
sudo /etc/init.d/mysql restart

# Python Flask setup
sudo apt-get -y install python-pip
sudo apt-get -y install python-dev
sudo apt-get -y install build-essential

sudo apt-get -y install redis-server

# Setup virtual env
sudo pip install virtualenv
cd /vagrant
virtualenv --no-site-packages .
source bin/activate

# Flask setup 
sudo pip install Flask==0.9
sudo pip install flask-login
sudo pip install flask-openid
sudo pip install flask-mail
sudo pip install sqlalchemy
sudo pip install flask-sqlalchemy
sudo pip install sqlalchemy-migrate
sudo pip install flask-migrate
sudo pip install Flask-Script
sudo pip install flask-whooshalchemy==0.55a
sudo pip install flask-wtf
sudo pip install pytz
sudo pip install flask-babel
sudo pip install flup
sudo pip install flask-httpauth
sudo easy_install -U distribute
sudo pip install mysql-python
sudo pip install rauth

sudo pip install redis

sudo pip install -r requirements.txt

sudo pip install stripe
pip install flask-classful -U


#ownershipssudo 
sudo touch /var/log/maze.log
sudo chown -R vagrant /var/log/maze.log

# fileserver
sudo mkdir -p /home/vagrant/uploads
sudo mkdir -p /home/vagrant/environment

# copy default picture to uploads

#twilio
sudo pip install twilio

#
sudo apt-get install nodejs-legacy
sudo apt-get install npm
sudo npm install -g ngrok
#login to ngrok account and get AUTH token and run below command
#ngrok -authtoken YOUR_TOKEN_HERE 80 
#ngrok http 80

sudo pip install geopy

#directories
mkdir -p environment
chown -R vagrant:vagrant environment/
chmod 777 environment/
cp -r /vagrant/* /home/vagrant/environment
chmod -R 777 environment/
