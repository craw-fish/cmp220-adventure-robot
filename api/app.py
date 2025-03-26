import os
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey

basedir = os.path.abspath(os.path.dirname(__file__))

# initialize flask app
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(basedir, 'database', 'adventure_log.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# initialize sqlalchemy
db = SQLAlchemy()
db.init_app(app)

class Robot(db.Model):
    __tablename__ = 'robots'
    # columns
    robot_id: Mapped[int] = mapped_column(primary_key=True)
    robot_name: Mapped[str]
    # one-to-many relationship with snapshots
    snapshots = db.relationship('Snapshot', back_populates='robot')

class Snapshot(db.Model):
    __tablename__ = 'snapshots'
    # columns
    snapshot_id: Mapped[int] = mapped_column(primary_key=True)
    robot_id: Mapped[int] = mapped_column(ForeignKey('robots.robot_id'), nullable=False)
    timestamp: Mapped[str]
    photo_path: Mapped[str]
    description: Mapped[str]
    # many-to-one relationship with robots
    robot = db.relationship('Robot', back_populates='snapshots')

# test connection at http://localhost:5001/
# code from https://python-adv-web-apps.readthedocs.io/en/latest/flask_db1.html
@app.route('/')
def testdb():
    try:
        db.session.query(text('1')).from_statement(text('SELECT 1')).all()
        return '<h1>It works.</h1>'
    except Exception as e:
        # e holds description of the error
        error_text = "<p>The error:<br>" + str(e) + "</p>"
        hed = '<h1>Something is broken.</h1>'
        return hed + error_text

if __name__ == '__main__':
    app.run(debug=True, port=5001)

