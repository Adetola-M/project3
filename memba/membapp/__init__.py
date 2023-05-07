from flask  import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

#we want to make the object-based config avaliable
from membapp import config

app = Flask(__name__,instance_relative_config=True)

csrf = CSRFProtect(app) #Initialize entension, this will protect all your post routes against csrf and you must pass the csrf_token when submitting to these routes
#to load the config


#load the config form instance folder file
app.config.from_pyfile('config.py',silent=False)
#how to load the config from object-based config that is within your package
app.config.from_object(config.LiveConfig)


db=SQLAlchemy(app)

#to load the routes and form
from membapp import adminroutes,userroutes