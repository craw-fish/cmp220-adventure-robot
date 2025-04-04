import os
import shortuuid
from datetime import datetime
from flask import Flask, request, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey, DateTime, select
from sqlalchemy.sql import text
from sqlalchemy.orm import Mapped, mapped_column
from flask_restful import Api, Resource
from flask_marshmallow import Marshmallow
from config import Config
from utils import allowed_extensions, allowed_file

# initialize flask app
app = Flask(__name__)
app.config.from_object(Config)

# initialize flask extensions
db = SQLAlchemy(app)
ma = Marshmallow(app)
api = Api(app)

# SQLALCHEMY MODELS
class Robot(db.Model):
    __tablename__ = 'robots'
    robot_id: Mapped[int] = mapped_column(primary_key=True)
    robot_name: Mapped[str] = mapped_column(nullable=False)
    # one-to-many relationship with snapshots
    snapshots = db.relationship('Snapshot', back_populates='robot')

class Snapshot(db.Model):
    __tablename__ = 'snapshots'
    snapshot_id: Mapped[int] = mapped_column(primary_key=True)
    robot_id: Mapped[int] = mapped_column(ForeignKey('robots.robot_id'), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    photo_filename: Mapped[str] = mapped_column(nullable=False)
    instruction: Mapped[str] = mapped_column(nullable=True)
    description: Mapped[str] = mapped_column(nullable=True)
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
        exclude = ('photo_filename',)
    
    robot = ma.Nested(RobotSchema)
    # computed field for static file url
    photo_url = ma.Method('get_photo_url')
    
    def get_photo_url(self, obj):
        return url_for('get_snapshot_photo', filename=obj.photo_filename, _external=True)

# initialize schemas
robot_schema = RobotSchema()
snapshot_schema = SnapshotSchema()

# REST API RESOURCES
class RobotAPI(Resource):
    def post(self):
        try:
            robot_id = request.form.get('robot_id')
            robot_name = request.form.get('robot_name', type=str)
            
            # check for non-nullable inputs
            required_fields = {
                'robot_name': robot_name
            }
            missing_fields = [key for key, value in required_fields.items() if not value]
            if missing_fields:
                return {"message": f"Missing or invalid input: {', '.join(missing_fields)}"}, 400
            
            # id specified -> overwrite existing robot
            # no id specified -> create new robot (auto-increment)
            if robot_id:
                # robot at specified id
                robot = db.session.execute(db.select(Robot).where(Robot.robot_id == robot_id)).scalars().first()
                if robot:
                    robot.robot_name = robot_name
                    db.session.commit()
                    return {"message": f"Robot with ID {robot_id} overwritten successfully."}, 201
                else:
                    return {"message": f"No robot with ID {robot_id}."}, 400

            robot = Robot(
                robot_name = robot_name
            )
            db.session.add(robot)
            
            db.session.commit()
            return {"message": "New robot registered successfully."}, 201
        
        except KeyError as e:
            return {"message": str(e)}, 400
        
        except Exception as e:
            return {"message": str(e)}, 500
    
    def get(self):
        try:
            # valid query args
            robot_id = request.args.get('robot_id', type=int)
            robot_name = request.args.get('robot_name', type=str)
            
            # start building query
            stmt = select(Robot)
            
            # filter by args
            if robot_id:
                stmt = stmt.filter(Robot.robot_id == robot_id)
                
            if robot_name:
                # 'like' query (supports wildcards)
                stmt = stmt.filter(Robot.robot_name.like(robot_name))
            
            # execute query
            robots = db.session.execute(stmt).scalars().all()
            
            return robot_schema.dump(robots, many=True), 200
        
        except KeyError as e:
            return {"message": str(e)}, 400
        
        except Exception as e:
            return {"message": str(e)}, 500
        

class SnapshotAPI(Resource):
    def post(self):
        try:
            # valid input fields
            photo = request.files.get('photo')
            timestamp = request.form.get('timestamp', type=str)
            instruction = request.form.get('instruction', type=str)
            robot_id = request.form.get('robot_id', type=int)
            
            # VALIDATE INPUT
            # check for non-nullable inputs
            required_fields = {
                'photo': photo,
                'timestamp': timestamp,
                'robot_id': robot_id
            }
            missing_fields = [key for key, value in required_fields.items() if not value]
            if missing_fields:
                return {"message": f"Missing or invalid input: {', '.join(missing_fields)}"}, 400
            
            # check timestamp format; convert to datetime if possible
            try:
                timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                return {"message": "Invalid timestamp format. Use YYYY-MM-DD HH:MM:SS"}, 400
            
            # check if robot in db
            robot = db.session.execute(db.select(Robot).where(Robot.robot_id == robot_id)).scalars().first()
            if not robot:
                return {"message": f"No robot with ID {robot_id}."}, 400
            
            # check file type; if allowed, save to upload folder
            if photo and allowed_file(photo.filename):
                photo_extension = photo.filename.rsplit('.', 1)[1].lower()
                photo_filename = f"{shortuuid.uuid()}.{photo_extension}"
                photo.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_filename))
            else:
                return {"message": f"Invalid file type. Valid types are: {', '.join(list(allowed_extensions))}"}, 400
            
            # UPDATE DATABASE
            snapshot = Snapshot(
                robot_id = robot_id,
                timestamp = timestamp,
                instruction = instruction,
                photo_filename = photo_filename
            )
            db.session.add(snapshot)
            
            db.session.commit()
            return {"message": "Snapshot saved successfully."}, 201
        
        except KeyError as e:
            return {"message": str(e)}, 400
        
        except Exception as e:
            return {"message": str(e)}, 500
    
    def get(self):
        try:
            # valid query args
            robot_id = request.args.get('robot_id', type=int)
            snapshot_id = request.args.get('snapshot_id', type=int)
            t_start = request.args.get('t_start', type=str)
            t_end = request.args.get('t_end', type=str)
            instruction = request.args.get('instruction', type=str)
            
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
                
            if instruction:
                # 'like' query (supports wildcards)
                stmt = stmt.filter(Snapshot.instruction.like(instruction))
            
            # execute query
            snapshots = db.session.execute(stmt).scalars().all()
            
            return snapshot_schema.dump(snapshots, many=True), 200
            
        except KeyError as e:
            return {"message": str(e)}, 400
        
        except Exception as e:
            return {"message": str(e)}, 500
                    
api.add_resource(RobotAPI, '/robots')
api.add_resource(SnapshotAPI, '/snapshots')

# snapshot photos retrievable via http://.../snapshots/
@app.route('/snapshots/<filename>')
def get_snapshot_photo(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# test connection at http://.../test_db
@app.route('/test_db')
def test_db():
    try:
        db.session.execute(text('SELECT 1')).all()
        return '<h1>Connection successful.</h1>'
    except Exception as e:
        error_text = "<p>The error:<br>" + str(e) + "</p>"
        hed = '<h1>Something is broken.</h1>'
        return hed + error_text

if __name__ == '__main__':
    app.run(port=5001)
