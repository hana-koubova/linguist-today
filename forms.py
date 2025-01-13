from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, Form, IntegerField, SelectField, TextAreaField, HiddenField, RadioField, FileField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from flask_ckeditor import CKEditor, CKEditorField

from categories import dropdown_cats
from helper import art_images

class AdminForm(FlaskForm):
    #email = StringField(label='Email', validators=[DataRequired(), Email(message="Email format not valid")])
    admin_name = StringField(label='Admin Name', validators=[DataRequired()])
    password = PasswordField(label='Password', validators=[DataRequired()])
    submit = SubmitField(label="Access Admin Area")

class ArticleForm(FlaskForm):
    title = StringField(label='Title', validators=[DataRequired()])
    author = StringField(label='Author Name', validators=[DataRequired()])
    category = SelectField(label='Category', choices=dropdown_cats, validators=[DataRequired()])
    url = StringField(label='url', validators=[DataRequired()])
    image_main = SelectField(label='Image', choices=art_images, validators=[DataRequired()])
    metadata = StringField(label='Meta description', validators=[DataRequired()])
    text = CKEditorField(label="Job Description", validators=[DataRequired()])
    publish = RadioField(label="Publish", choices=['Draft', 'Publish'], default='Draft', validators=[DataRequired()])
    submit = SubmitField(label='Save article')

class ImageForm(FlaskForm):
    name = StringField(label='Title', validators=[DataRequired()])
    alt = StringField(label='Alt text', validators=[DataRequired()])
    description = StringField(label='Description', validators=[DataRequired()])
    submit = SubmitField(label='Save')

class LegalForm(FlaskForm):
    name = StringField(label='Name', validators=[DataRequired()])
    text = CKEditorField(label="Job Description", validators=[DataRequired()])
    submit = SubmitField(label='Save text')