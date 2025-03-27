import os
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey

basedir = os.path.abspath(os.path.dirname(__file__))

# initialize flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, 'database', 'adventure_log.db')}'
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


# DEBUG
def test_query():
    # add an entry to robot and snapshot tables
    db.session.add(Robot(robot_name='Justin'))
    db.session.add(Snapshot(robot_id=1, timestamp='2025-27-03 13:22:00'))
    robots = db.session.execute(db.select(Robot)).scalars()
    # list snapshots for each robot
    for robot in robots:
        print(f'ROBOT {robot.robot_id} ({robot.robot_name})')
        for snapshot in robot.snapshots:
            print(f'- Snapshot {snapshot.snapshot_id} taken {snapshot.timestamp}')
    db.session.rollback()

with app.app_context():        
    test_query()

# test connection at http://localhost:5001/test_db
# code adapted from https://python-adv-web-apps.readthedocs.io/en/latest/flask_db1.html
@app.route('/test_db')
def test_db():
    try:
        db.session.query(text('1')).from_statement(text('SELECT 1')).all()
        return '<h1>Connection successful.</h1>'
    except Exception as e:
        # e holds description of the error
        error_text = "<p>The error:<br>" + str(e) + "</p>"
        hed = '<h1>Something is broken.</h1>'
        return hed + error_text

if __name__ == '__main__':
    app.run(debug=True, port=5001)

