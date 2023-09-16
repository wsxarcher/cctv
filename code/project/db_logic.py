from datetime import datetime, timezone
from .database import *
from .schema import *

Base.metadata.create_all(bind=engine)

db = SessionLocal()

def create_user(username, password):
    db_user = User(username=username, password=password)
    try:
        db.add(db_user)
        db.commit()
    except Exception as e:
        print(f"Exception: {e}")
        db.rollback()
    return db_user

def login(username, password, user_agent="", ip=""):
    try:
        user = db.query(User).filter_by(username=username).one()
        if user.password == password:
            token = secrets.token_hex(64)
            login_time = datetime.now(timezone.utc).replace(microsecond=0)
            session = Session(token=token, user=user, user_agent=user_agent, ip=ip, login_time=login_time)
            db.add(session)
            db.commit()
            return token
    except Exception as e:
        print(f"Ex {e}")
        db.rollback()

def is_logged(token):
    try:
        session = db.query(Session).filter_by(token=token).one()
        return session.user 
    except:
        pass

def logout(token):
    try:
        db.query(Session).filter_by(token=token).delete(synchronize_session=False)
        db.commit()
    except:
        db.rollback()

def logout_everywhere(username):
    try:
        user = db.query(User).filter_by(username=username).one()
        db.query(Session).filter_by(user=user).delete(synchronize_session=False)
        db.commit()
    except:
        db.rollback()

def sessions(user):
    try:
        sessions = db.query(Session).filter_by(user=user).all()
        return sessions
    except:
        return []

def intrusiondetection(camera_index: int, enable=None):
    try:
        camera = db.query(Camera).filter_by(id=camera_index).first()
        if enable == None:
            if camera:
                return camera.detection_enabled
            else:
                return True
        else:
            try:
                if camera:
                    camera.detection_enabled = enable
                else:
                    camera = Camera(id=camera_index, detection_enabled=enable)
                    db.add(camera)
                db.commit()
            except:
                db.rollback()
            return enable
    except Exception as e:
        raise e