from dotenv import load_dotenv 
import os
from app import app

load_dotenv()

app.config['SECRET_KEY']=os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI']=os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS')
app.config['UPLOAD_FOLDER'] = '/home/vats/Projects/MAD1/static'

PDF_FILES_DIR = '/home/vats/Projects/MAD1/static'