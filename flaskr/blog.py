import imghdr
import os
from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename
from flaskr.auth import login_required
from flaskr.db import get_db
from flask import current_app, Flask, send_from_directory
from flask.cli import with_appcontext

UPLOAD_FOLDER = os.path.join(os.getcwd()) + '/flaskr/uploads'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
bp = Blueprint("blog", __name__)
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def validate_image(stream):
    header = stream.read(512)
    stream.seek(0)
    format = imghdr.what(None, header)
    if not format:
        return None
    return '.' + (format if format != 'jpeg' else 'jpg')


def allowed_file(filename):
    return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],filename)


@bp.route("/")
def index():
    """Show all the posts, most recent first."""
    db = get_db()
    posts = db.execute(
        "SELECT p.id,p.like, title,image, body, created, author_id, username"
        " FROM post p JOIN user u ON p.author_id = u.id"
        " ORDER BY created DESC"
    ).fetchall()
    return render_template("blog/index.html", posts=posts)


def get_post(id, check_author=True):
    """Get a post and its author by id.

    Checks that the id exists and optionally that the current user is
    the author.

    :param id: id of post to get
    :param check_author: require the current user to be the author
    :return: the post with author information
    :raise 404: if a post with the given id doesn't exist
    :raise 403: if the current user isn't the author
    """
    post = (
        get_db()
        .execute(
            "SELECT p.id,p.like, title, body,image, created, author_id, username"
            " FROM post p JOIN user u ON p.author_id = u.id"
            " WHERE p.id = ?",
            (id,),
        )
        .fetchone()
    )

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")

    if check_author and post["author_id"] != g.user["id"]:
        abort(403)

    return post


@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
    """Create a new post for the current user."""
    if request.method == "POST":
        title = request.form["title"]
        body = request.form["body"]
        image = request.files['file']
        error = None
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        image = secure_filename(image.filename)
        if not title:
            error = "Title is required."
        if not body:
            error = "Body is required"
        if not image:
            error = "Image is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "INSERT INTO post (title,image, body, author_id) VALUES (?,?, ?,?)",
                (title, image,body, g.user["id"]),
            )
            db.commit()
            return redirect(url_for("blog.index"))

    return render_template("blog/create.html")


@bp.route("/<int:id>/update", methods=("GET", "POST"))
@login_required
def update(id):
    """Update a post if the current user is the author."""
    post = get_post(id)

    if request.method == "POST":
        title = request.form["title"]
        body = request.form["body"]
        image = request.files['file']
        image = secure_filename(image.filename)
        error = None

        if not title:
            error = "Title is required."
        
        if not image:
            error = "Image is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "UPDATE post SET title = ?, body = ?, image = ?"
                " WHERE id = ?", 
                (title, body,image, id)
            )
            db.commit()
            return redirect(url_for("blog.index"))

    return render_template("blog/update.html", post=post)


@bp.route("/<int:id>/delete", methods=("POST",))
@login_required
def delete(id):
    """Delete a post.

    Ensures that the post exists and that the logged in user is the
    author of the post.
    """
    get_post(id)
    db = get_db()
    db.execute("DELETE FROM post WHERE id = ?", (id,))
    db.commit()
    return redirect(url_for("blog.index"))

@bp.route("/<int:id>/detail")
def detail(id):
    db = get_db()
    comments = db.execute(
        'select p.id, body, created, author_id, username'
        ' from comment p join user u on p.author_id = u.id'
        ' order by created desc'
    ).fetchall()
    post = get_post(id, check_author=False)
    if post is None:
        abort(404, f"Post id {id} doesn't exist.")
    return render_template('blog/detail.html', post=post, comments=comments)

@bp.route('/<int:id>/comment', methods=('GET', 'POST'))
def comment(id):
    post = get_post(id, check_author=False)
    if request.method == 'POST':
        body = request.form['body']
        error = None

        if not body:
            error = 'Body is required.'
        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO comment (body, author_id)'
                ' VALUES (?, ?)',
                (body,  g.user['id'])
            )
            db.commit()
            return redirect(url_for('blog.detail', id=post['id']))
    return render_template('blog/comment.html')


