from datetime import datetime
from bson import ObjectId
import os
import random
from categories import dropdown_cats, sub_cats_simple, url_categories, url_subcategories
from helper import art_images, images_dict, article_suggestion, popular, insert_after_paragraphs
import psycopg2

from flask import Flask, render_template, request, url_for, redirect, flash, session, jsonify, send_file, send_from_directory, make_response
from flask_bootstrap import Bootstrap5

## MondoDB related
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from pymongo import MongoClient

from database import db, articles, images_db, admins, legals

## Forms, Login, Security
from forms import AdminForm, ArticleForm, ImageForm, LegalForm
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.exceptions import HTTPException

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

## All published articles
articles_published = articles.find({'publish': True})

## Errors
    
@app.errorhandler(404)
def handle_404_error(err):
    return render_template('404.html')

#@app.errorhandler(Exception)
#def handle_exception(err):
#    # pass through HTTP errors
#    if isinstance(err, HTTPException):
#        return err#

#    # now you're handling non-HTTP exceptions only
#    return render_template("500.html",
#                           err=err), 500


@app.route("/")
def index():
    latest_articles = articles.find({}).sort({'date_published': -1})
    category_random = random.choice(sub_cats_simple)
    print(category_random)
    #popular = [articles.find_one({'title': 'The Scientifically Proven Benefits of Being Bilingual'}), articles.find_one({'title': "Polyglots’ Brain Activity and What We Know So Far"})]
    spanish_articles = (list(articles.find({'category': '--Spanish Language'}).sort({'date_published': -1})))[:3]
    children_articles = (list(articles.find({'category': 'Kids and Languages'}).sort({'date_published': -1})))[:4]
    #three_spanish = spanish_articles[:2]
    return render_template('index.html',
                           latest_articles=latest_articles[:4],
                           latest = latest_articles[0],
                           images_dict = images_dict,
                           popular=popular,
                           spanish_articles=spanish_articles,
                           children_articles=children_articles)


@app.route('/<category>', defaults={'subcategory': None}, methods=['GET', 'POST'])
@app.route('/<category>/<subcategory>', methods=['GET', 'POST'])
def category_page(category, subcategory):

    if category not in url_categories:
        return render_template('404.html'), 404
    
    cat = url_categories[category]
    category_articles = False

    if subcategory == None:
        subcat=subcategory

        if category not in url_subcategories:
            return render_template('404.html'), 404

        all_subcategories = url_subcategories[category]
        print(all_subcategories)
        if len(all_subcategories) == 1:
            print('ONE CATEGORY')
            category_articles = articles.find({'category': all_subcategories[0]}).sort({'date_published': -1})
        else:
            print('MANY SUBCATEGORIES')
            subcat_list = []
            for one_subcategory in all_subcategories:
                dict_addition = {'category': '--'+one_subcategory}
                subcat_list.append(dict_addition)
            category_articles = articles.find({'$or':subcat_list}).sort({'date_published': -1})

    else:
        print('ONE SUBCATEGORY')

        if subcategory not in url_categories:
            return render_template('404.html'), 404
        subcat = url_categories[subcategory]
        print(subcat)
        category_articles = articles.find({'category': '--'+subcat}).sort({'date_published': -1})

    category_articles_list = list(category_articles)
    #print(category_articles_len)
    if len(category_articles_list) == 0:
        print('EMTPY OBJECT')
        category_articles_list = False

    return render_template('category.html',
                           category=cat,
                           subcategory=subcat,
                           images_dict=images_dict,
                           category_articles=category_articles_list)

@app.route('/article/<article_url>', methods=['GET', 'POST'])
def article(article_url):
    article = articles.find_one({'url': article_url})
    #print(article['category'])
    # If the article doesn't exist, return a 404 page

    #testing_img = '<img src="../static/favicons/favicon-16x16.png"/>'
    # Preprocess the article text
    #article['text'] = insert_after_paragraphs(article['text'], testing_img, 3)

    if not article:
        return render_template('404.html'), 404
    
    suggestions = article_suggestion(article['category'], ObjectId(article['_id']))
    return render_template('article.html',
                           article=article,
                           article_url=article_url,
                           suggestions=suggestions,
                           images_dict=images_dict)

    
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
        return "Article added!", {"Refresh": "3; url=/dashboard"}


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
        return 'Images uploaded to database.', {"Refresh": "3; url=/images"}
    return 'No new images to upload.', {"Refresh": "3; url=/images"}

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
        
        new_values = {"$set": {#'name': new_name,
                               'alt': request.form['alt'],
                               'description': request.form['description']}}
        images_db.update_one(image_to_edit, new_values)
        #os.rename(f'static/images/article_images/{old_name}', f'static/images/article_images/{new_name}')
        
        return redirect(url_for('images'))
                               
    return render_template('edit_image.html',
                           image=image_to_edit,
                           form=form)

@app.route('/legal')
@login_required
def legal():
    legal_docs = legals.find({})
    return render_template('legal.html',
                           legal_docs=legal_docs)

@app.route('/legal_edit/<doc_id>', methods=['GET', 'POST'])
@login_required
def legal_edit(doc_id):
    form = LegalForm()
    legal_doc = legals.find_one({'_id': ObjectId(doc_id)})
    print(legal_doc['name'])
    if form.validate_on_submit() and request.method == 'POST':
        new_values = {"$set": { 'name': request.form['name'],
                               'text': request.form['text']}}
        legals.update_one(legal_doc, new_values)
        return redirect(url_for('legal'))
    
    print(form.errors)

    return render_template('legal_edit.html',
                           doc=legal_doc,
                           form=form)

@app.route('/legal/<legal_url>')
def legal_info(legal_url):
    legal_doc = legals.find_one({'legal_url': legal_url})
    return render_template('legal_info.html',
                           doc = legal_doc)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/users')
def users():
     return 'Nothing yet'

#@app.route('/robots.txt')
#@app.route('/sitemap.xml')
#def static_from_root():
#    return send_from_directory(app.static_folder, request.path[1:])

@app.route('/robots.txt')
def robots():
    return send_from_directory(app.static_folder, 'robots.txt')

@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory(app.static_folder, 'sitemap.xml')

    
if __name__ == "__main__":
    app.run(debug=True)