import logging
import threading
import sqlite3
import sys

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort

logger = logging.getLogger("app")

class AtomicCounter():

    def __init__(self, value=0):
        self._value = value
        self.lock = threading.Lock()

    def inc(self, d=1):
        with self.lock:
            self._value += 1
    @property
    def value(self):
        with self.lock:
            return self._value

connection_counter = AtomicCounter()

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    connection = sqlite3.connect('database.db')
    connection_counter.inc(1)
    connection.row_factory = sqlite3.Row
    return connection

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    return post

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

# Define the main route of the web application
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
        logger.debug('Article with id %d does not exist', post_id)
        return render_template('404.html'), 404
    else:
        logger.debug('Article "%s" retrieved!', post[2])
        return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    logger.debug('"About Us" page is retrieved')
    return render_template('about.html')

# Define the post creation functionality
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()

            logger.debug('Article "%s" created!', title)

            return redirect(url_for('index'))

    return render_template('create.html')

# Healthcheck endpoint
@app.route('/healthz', methods=('GET', ))
def healthz():
    return {"result": "OK - healthy"}

# Metrics endpoint
@app.route('/metrics', methods=('GET', ))
def metrics():
    with get_db_connection() as connection:
        post_count = connection.execute("SELECT COUNT(1) FROM posts").fetchone()
    return {"db_connection_count": connection_counter.value,
            "post_count": post_count[0]}

def setup_logging():
    formatter = logging.Formatter('%(asctime)s, %(message)s', '%d/%m/%Y, %H:%M:%S')
    stderr = logging.StreamHandler(sys.stderr)
    stdout = logging.StreamHandler(sys.stdout)
    handlers = [stderr, stdout]
    for ch in handlers:
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[logging.StreamHandler(sys.stderr), logging.StreamHandler(sys.stdout)]
    )

# start the application on port 3111
if __name__ == "__main__":
   setup_logging()
   app.run(host='0.0.0.0', port='3111')
