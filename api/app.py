import os
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, select
from flask_restful import Api, Resource
from flask_marshmallow import Marshmallow
from datetime import datetime
import shortuuid

basedir = os.path.abspath(os.path.dirname(__file__))

# initialize flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, 'database', 'adventure_log.db')}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# specify upload folder for snapshots
UPLOAD_FOLDER = 'uploads/snapshots'
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

# initialize marshmallow (data serialization)
ma = Marshmallow(app)

# SQLALCHEMY MODELS
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
    photo_path: Mapped[str]     # pathname of image file
    instruction: Mapped[str]    # last instruction robot received
    description: Mapped[str]    # comment generated for blog
    # many-to-one relationship with robots
    robot = db.relationship('Robot', back_populates='snapshots')

# MARSHMALLOW SCHEMAS
class RobotSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Robot
        load_instance = True

class SnapshotSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Snapshot
        load_instance = True
    robot = ma.Nested(RobotSchema)

# initialize schemas
snapshot_schema = SnapshotSchema()

# REST API RESOURCES
class SnapshotAPI(Resource):
    def post(self):
        try:
            # valid input fields
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
                file_extension = photo.filename.rsplit('.', 1)[1].lower()
                # generate unique filename
                unique_filename = f"{shortuuid.uuid()}.{file_extension}"
                photo_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                photo.save(photo_path)
            else:
                return {"message": f"Invalid file type. Valid types are: {', '.join(list(ALLOWED_EXTENSIONS))}"}, 400
            
            # UPDATE DATABASE
            # if robot not already in db, add it
            if not db.session.execute(db.select(Robot).where(Robot.robot_id == robot_id)).scalars().first():
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
    
    def get(self):
        try:
            # valid query args
            robot_id = request.args.get('robot_id', type=int)
            snapshot_id = request.args.get('snapshot_id', type=int)
            t_start = request.args.get('t_start', type=str)
            t_end = request.args.get('t_end', type=str)
            
            # start building query
            stmt = select(Snapshot)
            
            # filter by args
            if robot_id:
                stmt = stmt.filter(Snapshot.robot_id == robot_id)
                
            if snapshot_id:
                stmt = stmt.filter(Snapshot.snapshot_id == snapshot_id)
            
            if t_start:
                # check timestamp format; convert to datetime if possible
                try:
                    t_start = datetime.strptime(t_start, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    return {"message": "Invalid timestamp format for t_start. Use YYYY-MM-DD HH:MM:SS"}, 400
                stmt = stmt.filter(Snapshot.timestamp >= t_start)
            if t_end:
                try:
                    t_end = datetime.strptime(t_end, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    return {"message": "Invalid timestamp format for t_end. Use YYYY-MM-DD HH:MM:SS"}, 400
                stmt = stmt.filter(Snapshot.timestamp <= t_end)
            
            # execute query
            snapshots = db.session.execute(stmt).scalars().all()
            
            data = snapshot_schema.dump(snapshots, many=True)
            return snapshot_schema.dump(data, many=True), 200
            
        except KeyError as e:
            return {"message": {str(e)}}, 400
        
        except Exception as e:
            return {"message": {str(e)}}, 500
                    
api.add_resource(RobotAPI, '/robots')
api.add_resource(SnapshotAPI, '/snapshots')

# test connection at http://localhost:5001/test_db
# code adapted from https://python-adv-web-apps.readthedocs.io/en/latest/flask_db1.html
@app.route('/test_db')
def test_db():
    try:
        db.session.query(text('1')).from_statement(text('SELECT 1')).all()
        return '<h1>Connection successful.</h1>'
    except Exception as e:
        error_text = "<p>The error:<br>" + str(e) + "</p>"
        hed = '<h1>Something is broken.</h1>'
        return hed + error_text

if __name__ == '__main__':
    app.run(debug=True, port=5001)
