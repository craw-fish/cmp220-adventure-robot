import os
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey
from flask_restful import Api, Resource
from werkzeug.utils import secure_filename
from datetime import datetime

basedir = os.path.abspath(os.path.dirname(__file__))

# initialize flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, 'database', 'adventure_log.db')}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# specify upload folder for snapshots
UPLOAD_FOLDER = os.path.join(basedir, 'uploads', 'snapshots')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# specify file types for snapshots
# TODO: migrate to utils.py?
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# initialize sqlalchemy
db = SQLAlchemy()
db.init_app(app)

# initialize rest api
api = Api(app)

# MODELS
# TODO: migrate to models.py
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
    timestamp: Mapped[str]      # time of photo
    photo_path: Mapped[str]     # location of image file
    instruction: Mapped[str]    # last instruction robot received
    description: Mapped[str]    # comment generated for blog
    # many-to-one relationship with robots
    robot = db.relationship('Robot', back_populates='snapshots')

# REST API RESOURCES
class LogAPI(Resource):
    def post(self):
        try:
            photo = request.files.get('photo')
            timestamp = request.form.get('timestamp')
            instruction = request.form.get('instruction')
            robot_id = request.form.get('robot_id')
            robot_name = request.form.get('robot_name')
            
            # VALIDATE INPUT
            # check for non-nullable inputs
            required_fields = {
                "photo": photo,
                "timestamp": timestamp,
                "robot_id": robot_id
            }
            missing_fields = []
            for key, value in required_fields.items():
                if not value:
                    missing_fields.append(key)
            if missing_fields:
                return {"message": f"Missing required input: {', '.join(missing_fields)}"}, 400
            
            # check timestamp format; convert to datetime if possible
            try:
                timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                return {"message": "Invalid timestamp format. Use YYYY-MM-DD HH:MM:SS"}, 400
            
            # check file type; if allowed, save to upload folder
            if photo and allowed_file(photo.filename):
                photo_name = secure_filename(photo.filename)
                photo_path = os.path.join(app.config['UPLOAD_FOLDER'], photo_name)
                photo.save(photo_path)
            else:
                return {"message": f"Invalid file type. Valid types are: {', '.join(list(ALLOWED_EXTENSIONS))}"}, 400
            
            # UPDATE DATABASE
            # if robot not already in db, add it
            if not db.session.execute(db.select(Robot).where(Robot.robot_id == robot_id)).scalars():
                robot = Robot(
                    robot_id = robot_id,
                    robot_name = robot_name
                )
                db.session.add(robot)
                
            snapshot = Snapshot(
                robot_id = robot_id,
                timestamp = timestamp,
                instruction = instruction,
                photo_path = photo_path
            )
            db.session.add(snapshot)
            
            db.session.commit()
            return {"message": "Snapshot saved successfully."}, 201
        
        except KeyError as e:
            return {"message": {str(e)}}, 400
        
        except Exception as e:
            return {"message": {str(e)}}, 500

api.add_resource(LogAPI, '/log')

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


# with app.app_context():        
    # test_query()

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

