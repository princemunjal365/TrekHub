import os, time

os.system("python -m pip install --upgrade pip")
os.system("python -m pip install bcrypt==4.0.1 Flask==3.1.3 Flask-SQLAlchemy==3.1.1")

    
try: 
    from app import *

    db.create_all()
    
    users = User_Credentials.query.all()
    
    if (len(users) == 0) : 
        print("#####  Enter Database Admin details  #####")
        email = input("Set admin email : ")
        pswd = input("Set admin password : ")

        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(pswd.encode('utf-8'),salt)

        admin = User_Credentials(user_id = 0, email = email, password = hashed_password,role = 'admin')

        try:
            db.session.add(admin)
            db.session.commit()
            print("TrekHub Setup done....")
            time.sleep(3)
        except Exception as e:
            db.session.rollback()
            print("Failed to setup admin record....")
            print(f"Problem : {e}")
            time.sleep(3)
    else:
        print("Setup been done already....")
        time.sleep(3)
except (ModuleNotFoundError) as e :
    print(f"Failed to install or module {e}")
    time.sleep(3)