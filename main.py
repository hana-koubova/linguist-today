from datetime import datetime
from bson import ObjectId
import os
import random
from categories import dropdown_cats, sub_cats_simple
from helper import art_images

from flask import Flask, render_template, request, url_for, redirect, flash, session, jsonify, send_file, send_from_directory, make_response
from flask_bootstrap import Bootstrap5

## MondoDB related
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from pymongo import MongoClient


from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi


from forms import AdminForm, ArticleForm, ImageForm
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash

## WTFORMS

from flask_wtf.csrf import CSRFProtect

## CK editor

from flask_ckeditor import CKEditor, CKEditorField

## APP initiasion

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY')

ckeditor = CKEditor(app)

bootstrap = Bootstrap5(app)

# Login manager and User model

login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin):
    pass

@login_manager.user_loader
def user_loader(username):
    user = User()
    user.id = username
    return user

## CSFP protection

csrf = CSRFProtect(app)
csrf.init_app(app)

## Mongo DB


uri = os.environ.get('MONGO_URI')
# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))
# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

db = client['linguisttoday']
articles = db['articles']
admins = db['admins']
images_db = db['images']


## All published articles
articles_published = articles.find({'publish': True})


@app.route("/")
def index():
    latest_articles = articles.find({}).sort({'date_published': -1})
    images_all = images_db.find({})

    images_dict = {}
    for image in images_all:
        images_dict[image['name']] = {'alt': image['alt'],
                                      'description': image['description']}
    category_random = random.choice(sub_cats_simple)
    print(category_random)
    return render_template('index.html',
                           latest_articles=latest_articles[:4],
                           latest = latest_articles[0],
                           images_dict = images_dict)

@app.route('/<article_url>')
def article(article_url):
    article = articles.find_one({'url': article_url})
    return render_template('article.html',
                           article=article,
                           article_url=article_url)



@app.route('/test')
def test_connection():
    try:
        # Try listing collections as a basic test
        databases = client.list_database_names()
        collections = db.list_collection_names()
        return f"Connected! Collections: {collections}"
    except Exception as e:
        return f"Connection failed: {str(e)}", 500


    
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    error = None
    login_form = AdminForm()
    if login_form.validate_on_submit() and request.method == 'POST':
        print('Validated')
        admin_name = request.form['admin_name']
        password = request.form['password']
        print('We have name and password')

        # Find user by admin_name
        current_admin = admins.find_one({'admin_name': admin_name}, {"_id": 0, "admin_name": 1, "password": 1})
        print(current_admin)
        if current_admin == None:
            error = 'Admin not found in database.'
        # Check password hash
        else:
            try:
                if password == current_admin['password']:
                    print('Password matches')
                    user = User()
                    user.id = admin_name
                    login_user(user)
                    print('Logging user in')
                    return redirect(url_for('dashboard'))
                else:
                    print('There was an error')
                    error = 'Wrong password'
                    #return error
            except:
                error = 'Wrong password'
    return render_template('admin.html',
                           form=login_form,
                           error=error)

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    current_articles = articles.find({})
    return render_template('dashboard.html',
                           current_articles = current_articles)

@app.route('/add_article', methods=['GET', 'POST'])
@login_required
def add_article():
    form = ArticleForm()
    if form.validate_on_submit() and request.method == 'POST':
        print('Here we go!')

        # Publish or Draft
        publish = False
        if bool(request.form['publish'] == 'Publish'):
            publish = True


        new_article = {
            'title': request.form['title'],
            'author': request.form['author'],
            'date_published': datetime.now(),#.strftime("%Y/%m/%d %H:%M:%S"),
            'category': request.form['category'],
            'metadata': request.form['metadata'],
            'text': request.form['text'],
            'url': request.form['url'],
            'image_main': request.form['image_main'],
            'publish': publish
        }
        print(new_article['date_published'])
        articles.insert_one(new_article)
        return "Article added!"


    return render_template('add_article.html',
                           form = form)

@app.route('/edit_article/<article_id>', methods=['GET', 'POST'])
@login_required
def edit_article(article_id):
    form = ArticleForm()
    print('STARTED')
    article_to_edit = articles.find_one({"_id": ObjectId(article_id)})
    #print(article_to_edit['publish'])
    publish = article_to_edit['publish']
    
    if form.validate_on_submit() and request.method == 'POST':

        if request.form['publish'] == 'Publish':
            publish = True
        else:
            publish = False

        new_values = {"$set": { 'title': request.form['title'],
                               'author':  request.form['author'],
                               'date_edited': datetime.now(),#.strftime("%Y/%m/%d %H:%M:%S"),
                               'category': request.form['category'],
                               'metadata': request.form['metadata'],
                               'text': request.form['text'],
                               'url': request.form['url'],
                               'image_main': request.form['image_main'],
                               'publish': publish}}
        articles.update_one(article_to_edit, new_values)
        return redirect(url_for('dashboard'))
    
    print(form.errors)
    return render_template('edit_article.html',
                           article = article_to_edit,
                           form = form,
                           dropdown_cats = dropdown_cats,
                           art_images = art_images,
                           publish = publish)

@app.route('/images')
@login_required
def images():
    images_all = images_db.find({})
    return render_template('images.html',
                           images_all=images_all)

@app.route('/scan_images', methods=['GET', 'POST'])
def scan_images():
    print(art_images)
    for image in art_images:
        print(image)
        upload = 0
        allowed_formats = ['jpg', 'jpeg', 'png', 'gif']
        image_exist = images_db.find_one({'name': image})
        if image_exist == None and image.split('.')[1] in allowed_formats:
            new_image = {
                'name': image,
                'alt': '',
                'description': ''
            }
            images_db.insert_one(new_image)
            upload += 1
    if upload > 0:
        return 'Images uploaded to database.'
    return 'No new images to upload.'

@app.route('/edit_image/<image_id>', methods=['GET', 'POST'])
@login_required
def edit_image(image_id):
    form = ImageForm()
    image_to_edit = images_db.find_one({"_id": ObjectId(image_id)})
    print(image_to_edit['name'])

    if form.validate_on_submit() and request.method == 'POST':
        
        name_ending = (image_to_edit['name']).split('.')[1]
        new_name = '.'.join([request.form['name'], name_ending])
        old_name = image_to_edit['name']
        
        new_values = {"$set": { 'name': new_name,
                               'alt': request.form['alt'],
                               'description': request.form['description']}}
        images_db.update_one(image_to_edit, new_values)
        os.rename(f'static/images/article_images/{old_name}', f'static/images/article_images/{new_name}')
        
        return redirect(url_for('images'))
                               
    return render_template('edit_image.html',
                           image=image_to_edit,
                           form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/users')
def users():
     return 'Nothing yet'

  

if __name__ == "__main__":
    app.run(debug=True)