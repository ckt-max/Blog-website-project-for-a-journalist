from flask import Flask, render_template, redirect, url_for, request, flash
from flask_compress import Compress
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy, session
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, session
from sqlalchemy import Integer, String, Text, func, Date, and_, LargeBinary, update,text
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, DateField, PasswordField, IntegerField
from wtforms.validators import DataRequired, Email, URL, Optional
from flask_ckeditor import CKEditor, CKEditorField
from werkzeug.security import generate_password_hash, check_password_hash
# for login
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from django.utils.http import url_has_allowed_host_and_scheme
import werkzeug
from flask_wtf.file import FileField, FileRequired
from werkzeug.utils import secure_filename
from datetime import date
import base64
import email_validator
from math import ceil

# for emailing
import os
import smtplib
import ssl
# email body
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

app = Flask(__name__)
# Compress(app)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
Bootstrap5(app)
# initializing ckeditor
app.config['CKEDITOR_PKG_TYPE'] = 'full-all'
ckeditor = CKEditor(app)

# CREATE DATABASE
class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_URI', 'sqlite:///project.db')
db = SQLAlchemy(model_class=Base)
db.init_app(app)

# CONFIGURE TABLES
class BlogPost(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=True)
    date: Mapped[str] = mapped_column(Date, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str] = mapped_column(String(250), nullable=False)
    # cover file is uploaded then file name is saved in
    img_64: Mapped[str] = mapped_column(String, nullable=True)
    categories: Mapped[str] = mapped_column(String(250), nullable=False)
    tags: Mapped[str] = mapped_column(String(250), nullable=False)
    # quote
    quote: Mapped[str] = mapped_column(String(250), nullable=True)
    cite: Mapped[str] = mapped_column(String(50), nullable=True)
    after: Mapped[int] = mapped_column(Integer, nullable=True)


class Podcast(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=True)
    audio_url: Mapped[str] = mapped_column(String(1000))
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str] = mapped_column(String(250), nullable=False)
    categories: Mapped[str] = mapped_column(String(250), nullable=False)
    tags: Mapped[str] = mapped_column(String(250), nullable=False)

class Photo(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    caption: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    img_64: Mapped[str] = mapped_column(String, nullable=True)
    # categories: Mapped[str] = mapped_column(String(250), nullable=False)
class Master(UserMixin, db.Model):
    id: Mapped[str] = mapped_column(String(250), primary_key=True)
    password: Mapped[str] = mapped_column(String(100))

# login_manager:
login_manager = LoginManager()
login_manager.init_app(app)

# create a user_loader callback
@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(Master, user_id)

with app.app_context():
    db.create_all()


# FORMS:

class ContactForm(FlaskForm):
    name = StringField('Your Name', validators=[DataRequired()])
    email = StringField('Your Email', validators=[DataRequired(), Email()])
    message = TextAreaField('Your Message', validators=[DataRequired()])
    submit = SubmitField('Add Comment')

class BlogForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[Optional()])
    categories = StringField("Categories", validators=[DataRequired()])
    tags = StringField("Tags", validators=[DataRequired()])
    author = StringField("Author", validators=[DataRequired()])
    # quote
    quote = StringField("Any highlighted quote", validators=[Optional()])
    cite = StringField("Cited from", validators=[Optional()])
    after = IntegerField("After which para?", validators=[Optional()])

    date = DateField("Date", validators=[Optional()])
    cover = FileField(validators=[Optional()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit")



class PodcastForm(FlaskForm):
    title = StringField("Podcast Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle" , validators=[Optional()])
    categories = StringField("Categories", validators=[DataRequired()])
    tags = StringField("Tags", validators=[DataRequired()])
    author = StringField("Author", validators=[DataRequired()])
    date = DateField("Date")
    audio_url = StringField("Audio URL", validators=[DataRequired()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit")

class PhotoForm(FlaskForm):
    # categories = StringField("Categories", validators=[DataRequired()])
    caption = StringField("Photo Caption", validators=[DataRequired()])
    photo = FileField(validators=[FileRequired()])
    submit = SubmitField("Submit")

class MasterForm(FlaskForm):
    user_id = StringField ("ID", validators=[DataRequired()]),
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField('Submit')

# function to send emails:
def mailer(name, email, message):
    # sending email:
    print(name, email, message)

    # sending email
    print('Composing Email....')

    email_sender = os.environ.get('SENDER_MAIL')
    email_password = os.environ.get('SENDER_PASS')
    email_receiver = os.environ.get('RECIEVER_MAIL')

    content = f'''Hi there's a message from your reader "{name}": 

           "{message}"

           Their email - {email}'''

    # Email details
    msg = MIMEMultipart()  # function to create email
    msg['Subject'] = 'Blog Website Message'
    msg['From'] = email_sender
    msg['to'] = email_receiver
    msg.attach(MIMEText(content))  # to attach email body

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(email_sender, email_password)
        smtp.sendmail(email_sender, email_receiver, msg.as_string())
        print("Mail sent......")

def base64_convert(image_data):
    if image_data is not None:
        return base64.b64encode(image_data).decode('utf-8')
    else:
        return None


# --------APP STARTS
@app.route('/', defaults={'page_no': 1})
@app.route('/<int:page_no>')

def home(page_no):
    # Determine the offset based on the page number
    offset = (page_no - 1) * 8

    # Query to retrieve the blog posts, ordered by descending ID
    posts = (db.session.query(BlogPost).order_by(BlogPost.id.desc()).offset(offset).limit(8)).all()

    # check if its last page
    total_pages = ceil(db.session.query(func.count()).select_from(BlogPost).scalar() / 8)
    last_page_flag = (page_no >= total_pages)

    # latest post for hero
    latest_post = db.session.execute(db.select(BlogPost).order_by(BlogPost.id.desc()).limit(1)).scalar()

    # latest photo
    latest_photo = db.session.execute(db.select(Photo).order_by(Photo.id.desc()).limit(1)).scalar()

    return render_template('index.html', blogs=posts,latest_post=latest_post, page_no=page_no, last_page_flag = last_page_flag, latest_photo = latest_photo)



# -------------ARTICLES/BLOGS----------------------
@app.route('/blog/<int:post_id>', methods = ["GET","POST"])

def blog_post(post_id):

    requested_post = db.session.execute(db.select(BlogPost).where(BlogPost.id == post_id)).scalar()

    if post_id > 1:
        next_post = db.session.execute(db.select(BlogPost).where(BlogPost.id == post_id-1)).scalar()
    else:
        next_post = None
    if post_id != db.session.query(BlogPost).count():
        prev_post = db.session.execute(db.select(BlogPost).where(BlogPost.id == post_id+1)).scalar()
    else:
        prev_post = None
    form = ContactForm()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        message = form.message.data
        mailer(name, email, message)
        return render_template("single-standard.html", blog=requested_post, form=form, prev=prev_post, next=next_post, filled=True)
    return render_template("single-standard.html", blog=requested_post, form=form, filled=False, prev=prev_post, next=next_post)

@app.route('/blog/all/', defaults={'page_no': 1})
@app.route('/blog/all/<int:page_no>')

def all_blogs(page_no):
    # Determine the offset based on the page number
    offset = (page_no - 1) * 8

    # Query to retrieve the blog posts, ordered by descending ID
    posts = (db.session.query(BlogPost).order_by(BlogPost.id.desc()).offset(offset).limit(8)).all()

    # check if its last page
    total_pages = ceil(db.session.query(func.count()).select_from(BlogPost).scalar() / 8)
    last_page_flag = (page_no >= total_pages)

    return render_template('all_posts.html', blogs=posts,  page_no=page_no,
                           last_page_flag = last_page_flag, current_user=current_user)

@app.route('/blog/<category>', defaults={'page_no': 1})
@app.route('/blog/<category>/<page_no>')

def blogs_by_category(category, page_no):
    # Determine the offset based on the page number
    offset = (page_no - 1) * 8

    # Query to retrieve the blog posts, ordered by descending ID
    posts = (db.session.query(BlogPost).where(BlogPost.categories.like(f"%{category}%")).order_by(BlogPost.id.desc()).offset(offset).limit(8)).all()

    # check if its last page
    total_pages = ceil(db.session.query(func.count()).select_from(BlogPost).scalar() / 8)
    last_page_flag = (page_no >= total_pages)

    return render_template('all_posts.html', blogs=posts, page_no=page_no,
                           last_page_flag = last_page_flag, category=category)
# -------------------------------------

#-----PHOTO-GALLERY-------------------
@app.route('/fotografia/', defaults={'page_no': 1},methods=['GET','POST'])
@app.route('/fotografia/<int:page_no>',methods=['GET','POST'])


def photo_gallery(page_no):

    # Determine the offset based on the page number
    offset = (page_no - 1) * 8

    # Query to retrieve the blog posts, ordered by descending ID
    posts = (db.session.query(Photo).order_by(Photo.id.desc()).offset(offset).limit(8)).all()

    # check if its last page
    total_pages = ceil(db.session.query(func.count()).select_from(Photo).scalar() / 8)
    last_page_flag = (page_no >= total_pages)

    form = ContactForm()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        message = form.message.data
        mailer(name, email, message)

        return render_template('photo-gallery.html', blogs=posts, page_no=page_no,
                           last_page_flag=last_page_flag, form=form, filled=True)

    return render_template('photo-gallery.html', blogs=posts, page_no=page_no,
                           last_page_flag = last_page_flag, form=form, filled=False)

#--------------------------------------

# --------- PODCASTS --------------
@app.route('/podcast', methods = ["GET","POST"])


def podcast():
    form = ContactForm()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        message = form.message.data
        mailer(name, email, message)
        return redirect('/')
        # return render_template("single-audio.html", form=form, filled=True)
    # return render_template("single-audio.html", form=form, filled=False)
    return redirect('/')

@app.route('/podcast/all/', defaults={'page_no': 1})
@app.route('/podcast/all/<int:page_no>')


def all_pods(page_no):
    posts = db.session.execute( db.select(Podcast).where(and_(Podcast.id <= 8 * page_no, Podcast.id >= 8 * page_no - 7)).order_by(Podcast.id.desc())).scalars()
    # latest post for hero
    latest_post = db.session.execute(db.select(Podcast).order_by(Podcast.id.desc()).limit(1)).scalar()
    # for pagination
    if (latest_post.id % 8 == 0 and latest_post.id / 8 == page_no) or (
            latest_post.id % 8 >= 0 and (latest_post.id / 8) + 1 == page_no):
        last_page_flag = True
    else:
        last_page_flag = False

    return render_template('all_pods.html', blogs=posts, latest_post=latest_post, page_no=page_no,
                           last_page_flag = last_page_flag)


@app.route('/about', methods=["GET","POST"])


def about():
    form = ContactForm()
    if form.validate_on_submit():
       name = form.name.data
       email = form.email.data
       message = form.message.data

       mailer(name, email, message)

       return render_template("about.html", form=form, filled=True)

    return render_template("about.html", form=form, filled=False)
@app.route('/contact', methods=["GET","POST"])


def contact():
    form = ContactForm()
    if form.validate_on_submit():
       name = form.name.data
       email = form.email.data
       message = form.message.data

       mailer(name, email, message)

       return render_template("contact.html", form=form, filled=True)

    return render_template("contact.html", form=form, filled=False)


# MASTER EDITOR:

# login the user and start the session
@app.route('/shkljdfhoahsohfwoie7r77823729slkdl----master--login----kueihnkjskd275672981928', methods=["GET", "POST"])


def master_login():
    error = None
    if request.method == "POST":
        user = db.session.execute(db.select(Master).where(Master.id == request.form.get('id'))).scalar()

        if user!= None and werkzeug.security.check_password_hash(user.password, request.form.get('password')):
            # to start a logged-in session
            login_user(user)
            flash('Logged in successfully.')
            return redirect("/")
        else:
            error = "Invalid credentials"
    return render_template("master_login.html", error=error)

@app.route('/logout')


def logout():
    logout_user()
    return redirect('/')

# # register a new master
# @app.route('/register', methods = ['GET', 'POST'])
# def register():
#
#     if request.method == 'POST':
#         new_user = Master(
#             id = request.form.get('id'),
#             password = werkzeug.security.generate_password_hash(request.form.get('password'), method='pbkdf2:sha256', salt_length=8))
#         db.session.add(new_user)
#         db.session.commit()
#         return redirect("/")
#
#     return render_template("register.html")


@app.route("/new-post", methods=["GET", "POST"])
@login_required


def add_blog():
    form = BlogForm()
    if form.validate_on_submit():
        # saving the photo
        f = form.cover.data
        filename = secure_filename(f.filename)
        image_data = f.read() # converts image to binary

        new_blog = BlogPost(
            title = form.title.data,
            subtitle = None if form.subtitle.data == '' else form.subtitle.data,
            categories = form.categories.data,
            tags = form.tags.data,
            date = form.date.data,
            body = form.body.data,
            author = form.author.data,
            quote = None if form.quote.data == '' else form.quote.data,
            cite = None if form.cite.data == '' else form.cite.data,
            after = None if form.after.data == '' else form.after.data,
            img_64 = base64_convert(image_data)
        )

        db.session.add(new_blog)
        db.session.commit()
        return render_template("add_blog.html", form=form,new=True, filled=True, user=current_user)
    return render_template("add_blog.html", form=form,new=True, filled=False, user=current_user)

@app.route('/blog/delete/<int:post_id>')
@login_required


def delete_post(post_id):
    post = db.session.execute(db.select(BlogPost).where(BlogPost.id==post_id)).scalar()
    db.session.delete(post)
    db.session.commit()
    return redirect('/blog/all')

@app.route('/fotografia/delete/<int:post_id>')
@login_required


def delete_photo(post_id):
    post = db.session.execute(db.select(Photo).where(Photo.id==post_id)).scalar()
    db.session.delete(post)
    db.session.commit()
    return redirect('/fotografia')

@app.route('/podcast/delete/<int:post_id>')
@login_required


def delete_pod(post_id):
    post = db.session.execute(db.select(BlogPost).where(Podcast.id==post_id)).scalar()
    db.session.delete(post)
    db.session.commit()
    return redirect('/podcasts')

@app.route("/new-photo", methods=["GET", "POST"])
@login_required


def add_photo():
    form = PhotoForm()
    if form.validate_on_submit():
        # saving the photo
        f = form.photo.data
        filename = secure_filename(f.filename)
        image_data = f.read() # converts image to binary
        new_photo = Photo(
            caption = form.caption.data,
            img_64 = base64_convert(image_data)
        )

        db.session.add(new_photo)
        db.session.commit()
        return render_template("add_photo.html", form=form,new=True, filled=True, user=current_user)
    return render_template("add_photo.html", form=form,new=True, filled=False, user=current_user)

# check this
@app.route("/new-podcast", methods=["GET", "POST"])
@login_required


def add_podcast():
    form = PodcastForm()
    if form.validate_on_submit():
        new_pod = Podcast(
            title = form.title.data,
            subtitle = form.subtitle.data,
            categories = form.categories.data,
            tags = form.tags.data,
            date = date.today() if form.date.data == '' else form.date.data,
            body = form.body.data,
            author = form.author.data,
            audio_url = form.audio_url.data
        )
        db.session.add(new_pod)
        db.session.commit()
        return render_template("add_podcast.html", form=form, new=True, filled=True, user=current_user)
    return render_template("add_podcast.html", form=form, new=True, filled=False, user=current_user)

if __name__ == "__main__":
    app.run(debug=False)
