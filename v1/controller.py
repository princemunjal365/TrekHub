from flask import current_app as app, render_template, request, redirect
from model import *
import bcrypt, random
from datetime import datetime

def auth_key():
    return random.randbytes(16).hex()[:16]  

def dayCount(d1, d2):
    date1 = datetime.strptime(d1, "%Y-%m-%d")
    date2 = datetime.strptime(d2, "%Y-%m-%d")
    return (date2 - date1).days

@app.route("/")
def home():
    return redirect('/signin') 

@app.route("/signin/", methods = ["GET","POST"])
def signin():
    if (request.method == "GET"):
        return render_template("signin.html",alert_visibility="d-none")
    elif (request.method == "POST"):
        email = request.form['email']
        password = request.form['password']
        user = User_Credentials.query.filter_by(email = email).first()
        if (user and bcrypt.checkpw(password.encode('utf-8'), user.password)) :
            role = user.role
            if (role == 'admin'):
                try:
                    user.auth_key = auth_key()
                    db.session.add(user)
                    db.session.commit()
                    return redirect(f'/admin_dashboard/{user.user_id}/{user.auth_key}')
                except Exception as e:
                    db.session.rollback()
                    return render_template("signin.html",alert_type = 'danger', alert_status = 'Failure', alert_message = "There might be a problem with server, please try again later")
            elif (role == 'trekker'):
                trekker = Trekker_Profile.query.filter_by(user_id = user.user_id).first()
                if (trekker):
                    if (trekker.status == 'blacklisted'):
                        return render_template("signin.html",alert_type = 'danger', alert_status = 'Failure', alert_message = "You have been blacklisted by admin")
                    elif (trekker.status == 'active'):
                        try:
                            user.auth_key = auth_key()
                            db.session.add(user)
                            db.session.commit()
                            return redirect(f'/trekker_dashboard/{user.user_id}/{trekker.trekker_id}/{user.auth_key}')
                        except Exception as e:
                            db.session.rollback()
                            return render_template("signin.html",alert_type = 'danger', alert_status = 'Failure', alert_message = "There might be a problem with server, please try again later")
            elif (role == 'staff'):
                staff = Staff_Profile.query.filter_by(user_id = user.user_id).first()
                if (staff):
                    if (staff.status == 'blacklisted'):
                        return render_template("signin.html",alert_type = 'danger', alert_status = 'Failure', alert_message = "You have been blacklisted by admin")
                    elif (staff.status == 'pending'):
                        return render_template("signin.html",alert_type = 'warning', alert_status = 'Failure', alert_message = "Your request has not been approved by admin , please wait")
                    elif (staff.status == 'active'):
                        try:
                            user.auth_key = auth_key()
                            db.session.add(user)
                            db.session.commit()
                            return redirect(f'/staff_dashboard/{user.user_id}/{staff.staff_id}/{user.auth_key}')
                        except Exception as e:
                            db.session.rollback()
                            return render_template("signin.html",alert_type = 'danger', alert_status = 'Failure', alert_message = "There might be a problem with server, please try again later")
        else:
            return render_template("signin.html",alert_type = 'danger', alert_status = 'Failure', alert_message = "incorrect user credentials")

@app.route("/signup/", methods = ["GET","POST"])
def signup():
    if (request.method == "GET"):
        return render_template("signup.html",alert_visibility="d-none")
    elif (request.method == "POST"):
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        address = request.form['address']
        existing_email = User_Credentials.query.filter_by(email=email).first()
        if (existing_email):
            return render_template("signup.html",alert_type='danger',alert_status='Failure',alert_message=' User already existed with the email, Please select different one')
        else:
            try:
                salt = bcrypt.gensalt()
                hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
                new_user = User_Credentials(email=email,password=hashed_password,role=role)
                db.session.add(new_user)
                db.session.commit()
                user = User_Credentials.query.filter_by(email = email).first()
                if user:
                    try:
                        if (role == "trekker"):
                            new_trekker = Trekker_Profile(user_id = user.user_id, name = name, address = address)
                            db.session.add(new_trekker)
                        elif (role == "staff"):
                            new_stadd = Staff_Profile(user_id = user.user_id, name = name, address = address)
                            db.session.add(new_stadd)
                        db.session.commit()
                        return render_template("signup.html",alert_type='success',alert_status='Success',alert_message=' Registered Successfully, now you can signin')
                    except Exception as e:
                        print(e)
                        db.session.rollback()
                        db.session.delete(user)
                        db.session.commit()
                        return render_template("signup.html",alert_type='danger',alert_status='Failure',alert_message=' There might be a problem with server, please try again later')
            except Exception as e:
                print(e)
                db.session.rollback()
                return render_template("signup.html",alert_type='danger',alert_status='Failure',alert_message=' There might be a problem with server, please try again later')
                
@app.route("/admin_dashboard/<user_id>/<auth_key>/",methods=["GET","POST"])
def admin_dashboard(user_id,auth_key):
    user = User_Credentials.query.filter_by(user_id = user_id).first()
    trekker_count = Trekker_Profile.query.count()
    staff_count = Staff_Profile.query.count()
    trek_count = Treks.query.count()
    pending_staff = Staff_Profile.query.filter_by(status = 'pending').all()
    if ((user) and (user.auth_key == auth_key)):
        if (request.method == "GET"):
            return render_template("admin_dashboard.html",alert_visibility = 'd-none',user = user,trekker_count = trekker_count,staff_count = staff_count, trek_count = trek_count, pending_staff = pending_staff)
        elif(request.method == "POST" and request.form.get('logout')):
            user.auth_key = None
            db.session.commit()
            return redirect("/signin/")
        elif(request.method == "POST" and request.form.get('approve')):
            staff = Staff_Profile.query.filter_by(staff_id = request.form.get('approve')).first()
            if staff:
                staff.status = 'active'
                try:
                    db.session.commit()
                    return redirect(f"/admin_dashboard/{user_id}/{auth_key}/")
                except:
                    db.session.rollback()
                    return render_template("admin_dashboard.html",alert_type = 'danger',alert_status='Failure',alert_message = 'Failed to Activate Staff, please try again later',user = user,trekker_count = trekker_count,staff_count = staff_count, trek_count = trek_count, pending_staff = pending_staff)
    else :
        return redirect("/signin/")
    
@app.route("/admin_dashboard/<user_id>/<auth_key>/trekkers/",methods=["GET","POST"])
def admin_trekkers(user_id,auth_key):
    user = User_Credentials.query.filter_by(user_id = user_id).first()
    trekkers = Trekker_Profile.query.all()
    if ((user) and (user.auth_key == auth_key)):
        if (request.method == "GET"):
            return render_template("admin_trekkers.html",alert_visibility = 'd-none',user = user,trekkers = trekkers)
        elif(request.method == "POST" and request.form.get('logout')):
            user.auth_key = None
            db.session.commit()
            return redirect("/signin/")
        elif(request.method == "POST" and request.form.get('block')):
            trekker = Trekker_Profile.query.filter_by(trekker_id = request.form.get('block')).first()
            trekker.status = "blacklisted"
            try:
                db.session.commit()
                return redirect(f"/admin_dashboard/{user_id}/{auth_key}/trekkers/")
            except:
                db.session.rollback()
                return render_template("admin_trekkers.html",user = user,trekkers = trekkers,alert_type = 'danger',alert_status = 'Failure', alert_message = 'Failed to block trekker, please try again later')
        elif(request.method == "POST" and request.form.get('activate')):
            trekker = Trekker_Profile.query.filter_by(trekker_id = request.form.get('activate')).first()
            trekker.status = "active"
            try:
                db.session.commit()
                return redirect(f"/admin_dashboard/{user_id}/{auth_key}/trekkers/")
            except:
                db.session.rollback()
                return render_template("admin_trekkers.html",user = user,trekkers = trekkers,alert_type = 'danger',alert_status = 'Failure', alert_message = 'Failed to activate trekker, please try again later')
        elif(request.method == "POST" and request.form.get('search')):
            trekkers = Trekker_Profile.query.filter(Trekker_Profile.name.like(f"%{request.form.get('search')}%")).all()
            return render_template("admin_trekkers.html",alert_visibility = 'd-none',user = user,trekkers = trekkers)
        elif(request.method == "POST" and request.form.get('view')):
            trekker = Trekker_Profile.query.filter_by(trekker_id = request.form.get('view')).first()
            return redirect(f"/admin_dashboard/{user_id}/{auth_key}/trekkers/history/{trekker.trekker_id}/")
    else :
        return redirect("/signin/")
    
@app.route("/admin_dashboard/<user_id>/<auth_key>/trekkers/history/<trekker_id>/",methods=["GET","POST"])
def admin_trekker_history(user_id,auth_key,trekker_id):
    user = User_Credentials.query.filter_by(user_id = user_id).first()
    trekker = Trekker_Profile.query.filter_by(trekker_id = trekker_id).first()
    if ((user) and (trekker) and (user.auth_key == auth_key)):
        id = trekker.user_id
        user_details = User_Credentials.query.filter_by(user_id = id).first()
        email = user_details.email
        bookings = Bookings.query.filter_by(trekker_id = trekker_id).all()
        if (request.method == "GET"):
            return render_template("admin_trekkers_history.html",alert_visibility = 'd-none',user = user,trekker = trekker,bookings = bookings,email = email)
        elif(request.method == "POST" and request.form.get('logout')):
            user.auth_key = None
            db.session.commit()
            return redirect("/signin/")
    else:
        return redirect("/signin/")
    
@app.route("/admin_dashboard/<user_id>/<auth_key>/staff/",methods=["GET","POST"])
def admin_staff(user_id,auth_key):
    user = User_Credentials.query.filter_by(user_id = user_id).first()
    staff = Staff_Profile.query.all()
    if ((user) and (user.auth_key == auth_key)):
        if (request.method == "GET"):
            return render_template("admin_staff.html",alert_visibility = 'd-none',user = user,staff = staff)
        elif(request.method == "POST" and request.form.get('logout')):
            user.auth_key = None
            db.session.commit()
            return redirect("/signin/")
        elif(request.method == "POST" and request.form.get('block')):
            staff = Staff_Profile.query.filter_by(staff_id = request.form.get('block')).first()
            staff.status = "blacklisted"
            try:
                db.session.commit()
                return redirect(f"/admin_dashboard/{user_id}/{auth_key}/staff/")
            except:
                db.session.rollback()
                return render_template("admin_staff.html",user = user,staff = staff,alert_type = 'danger',alert_status = 'Failure', alert_message = 'Failed to block staff, please try again later')
        elif(request.method == "POST" and request.form.get('activate')):
            staff = Staff_Profile.query.filter_by(staff_id = request.form.get('activate')).first()
            staff.status = "active"
            try:
                db.session.commit()
                return redirect(f"/admin_dashboard/{user_id}/{auth_key}/staff/")
            except:
                db.session.rollback()
                return render_template("admin_staff.html",user = user,staff = staff,alert_type = 'danger',alert_status = 'Failure', alert_message = 'Failed to activatestaff, please try again later')
        elif(request.method == "POST" and request.form.get('search')):
            staff = Staff_Profile.query.filter(Staff_Profile.name.like(f"%{request.form.get('search')}%")).all()
            return render_template("admin_staff.html",alert_visibility = 'd-none',user = user,staff = staff)
        elif(request.method == "POST" and request.form.get('view')):
            staff = Staff_Profile.query.filter_by(staff_id = request.form.get('view')).first()
            return redirect(f"/admin_dashboard/{user_id}/{auth_key}/staff/history/{staff.staff_id}/")
    else :
        return redirect("/signin/")
    
@app.route("/admin_dashboard/<user_id>/<auth_key>/staff/history/<staff_id>/",methods=["GET","POST"])
def admin_staff_history(user_id,auth_key,staff_id):
    user = User_Credentials.query.filter_by(user_id = user_id).first()
    staff = Staff_Profile.query.filter_by(staff_id = staff_id).first()
    if ((user) and (staff) and (user.auth_key == auth_key)):
        id = staff.user_id
        user_details = User_Credentials.query.filter_by(user_id = id).first()
        email = user_details.email
        treks = Treks.query.filter_by(assigned_staff = staff_id).all()
        if (request.method == "GET"):
            return render_template("admin_staff_history.html",alert_visibility = 'd-none',user = user,staff = staff,treks = treks,email = email)
        elif(request.method == "POST" and request.form.get('logout')):
                    user.auth_key = None
                    db.session.commit()
                    return redirect("/signin/")
    else:
        return redirect("/signin/")
    
@app.route("/admin_dashboard/<user_id>/<auth_key>/treks/",methods=["GET","POST"])
def admin_treks(user_id,auth_key):
    user = User_Credentials.query.filter_by(user_id = user_id).first()
    treks = Treks.query.all()
    if ((user) and (user.auth_key == auth_key)):
        if (request.method == "GET"):
            return render_template("admin_treks.html",alert_visibility = 'd-none',user = user,treks = treks)
        elif(request.method == "POST" and request.form.get('logout')):
            user.auth_key = None
            db.session.commit()
            return redirect("/signin/")
        elif(request.method == "POST" and request.form.get('search')):
            treks = Treks.query.filter(Treks.trek_name.like(f"%{request.form.get('search')}%")).all()
            return render_template("admin_treks.html",alert_visibility = 'd-none',user = user,treks =treks)
    else:
        return redirect("/signin/")

@app.route("/admin_dashboard/<user_id>/<auth_key>/treks/add/",methods = ["GET","POST"])
def trek_add(user_id,auth_key):
    user = User_Credentials.query.filter_by(user_id = user_id).first()
    staff = Staff_Profile.query.filter_by(status = 'active').all()
    if ((user) and (user.auth_key == auth_key)):
        if (request.method == "GET"):
            return render_template("admin_treks_add.html",alert_visibility = 'd-none',user=user,staff = staff)
        elif(request.method == "POST" and request.form.get('logout')):
            user.auth_key = None
            db.session.commit()
            return redirect("/signin/")
        elif(request.method == "POST" and request.form.get('add')):
            trek_name = request.form.get('name')
            slots = int(request.form.get('slots'))
            location = request.form.get('location')
            difficulty = request.form.get('difficulty')
            assigned_staff = request.form.get('staff_id')
            booking_end = request.form.get('last_date')
            trek_start = request.form.get('trek_start')
            trek_end = request.form.get('trek_end')
            trek_start_obj = datetime.strptime(trek_start, "%Y-%m-%d")
            trek_end_obj = datetime.strptime(trek_end, "%Y-%m-%d")
            booking_end_obj = datetime.strptime(booking_end, "%Y-%m-%d")
            if (((booking_end_obj.date() - datetime.today().date()).days > 0) and (dayCount(booking_end,trek_start) > 0) and (dayCount(trek_start,trek_end) >= 0)):
                duration = (dayCount(trek_start,trek_end) + 1)
                if (slots > 0):
                    selected_staff_trek = Treks.query.filter(Treks.assigned_staff == assigned_staff, Treks.end_date >= trek_start,Treks.start_date <= trek_end).first()
                    if (selected_staff_trek):
                        return render_template("admin_treks_add.html",alert_type='danger',alert_status='Failure',alert_message=' Selected staff is assigned to another trek, please select different staff',user=user,staff = staff)
                    else:
                        trek = Treks(trek_name = trek_name,assigned_staff = assigned_staff, location = location, difficulty = difficulty, available_slots = slots, booking_last_date = booking_end_obj, duration = duration, start_date = trek_start_obj, end_date = trek_end_obj)
                        try:
                            db.session.add(trek)
                            db.session.commit()
                            return render_template("admin_treks_add.html",alert_type='success',alert_status='Success',alert_message=' Trek added successfully',user=user,staff = staff)
                        except Exception as e:
                            print(e)
                            db.session.rollback()
                            return render_template("admin_treks_add.html",alert_type='danger',alert_status='Failure',alert_message=' There might be a problem with server, please try again later',user = user, staff = staff)
                else:
                    return render_template("admin_treks_add.html",alert_type='danger',alert_status='Failure',alert_message=' Please enter valid number of slots',user=user,staff = staff)
            else :
                return render_template("admin_treks_add.html",alert_type='danger',alert_status='Failure',alert_message=' Please select all the dates carefully',user=user,staff = staff)
    else:
        return redirect("/signin/")
    
@app.route("/admin_dashboard/<user_id>/<auth_key>/treks/details/<trek_id>/",methods=["GET","POST"])
def admin_treks_details(user_id,auth_key,trek_id):
    user = User_Credentials.query.filter_by(user_id = user_id).first()
    trek = Treks.query.filter_by(trek_id = trek_id).first()
    if ((user) and (trek) and (user.auth_key == auth_key)):
        bookings = Bookings.query.filter(Bookings.trek_id == trek_id, Bookings.status != 'canceled').all()
        if (request.method == "GET"):
            return render_template("admin_treks_details.html",alert_visibility = 'd-none',user = user,trek = trek,bookings = bookings)
        elif(request.method == "POST" and request.form.get('logout')):
                    user.auth_key = None
                    db.session.commit()
                    return redirect("/signin/")
    else:
        return redirect("/signin/")
    
@app.route("/staff_dashboard/<user_id>/<staff_id>/<auth_key>/",methods = ["GET","POST"])
def staff_dashboard(user_id,auth_key,staff_id):
    user = User_Credentials.query.filter_by(user_id = user_id).first()
    staff = Staff_Profile.query.filter_by(staff_id = staff_id).first()
    if ((user) and (staff) and (user.auth_key == auth_key) and (str(staff.user_id) == user_id)):
        my_treks = Treks.query.filter(Treks.assigned_staff == staff_id, Treks.status != 'completed').all()
        my_Treks_ids = [trek.trek_id for trek in my_treks]
        pending_bookings = Bookings.query.filter(Bookings.trek_id.in_(my_Treks_ids), Bookings.status == 'pending').all()
        tday = datetime.now().date()
        if (request.method == "GET"):
            return render_template("staff_dashboard.html",alert_visibility="d-none",user=user,staff = staff, pending_bookings = pending_bookings,my_treks = my_treks,tday = tday)
        elif(request.method == "POST" and request.form.get('logout')):
            user.auth_key = None
            db.session.commit()
            return redirect("/signin/")
        elif(request.method == "POST" and request.form.get('accept')):
            trekker_id, trek_id = map(int, request.form.get('accept').split('-'))
            booking = Bookings.query.filter(Bookings.trekker_id == trekker_id, Bookings.trek_id == trek_id).first()
            if booking:
                booking.status = 'booked'
                try:
                    db.session.commit()
                    return redirect(f"/staff_dashboard/{user_id}/{staff_id}/{auth_key}/")
                except:
                    db.session.rollback()
                    return render_template("staff_dashboard.html",alert_type = 'danger',alert_status='Failure',alert_message = 'Failed to Accept booking, please try again later',user=user,staff = staff, pending_bookings = pending_bookings,my_treks = my_treks,tday = tday)
        elif(request.method == "POST" and request.form.get('reject')):
            trekker_id, trek_id = map(int, request.form.get('reject').split('-'))
            booking = Bookings.query.filter(Bookings.trekker_id == trekker_id, Bookings.trek_id == trek_id).first()
            trek = Treks.query.filter_by(trek_id = trek_id).first()
            if booking and trek:
                booking.status = 'canceled'
                trek.available_slots = trek.available_slots + 1
                try:
                    db.session.commit()
                    return redirect(f"/staff_dashboard/{user_id}/{staff_id}/{auth_key}/")
                except:
                    db.session.rollback()
                    return render_template("staff_dashboard.html",alert_type = 'danger',alert_status='Failure',alert_message = 'Failed to Reject Booking, please try again later',user=user,staff = staff, pending_bookings = pending_bookings,my_treks = my_treks,tday = tday)
        elif(request.method == "POST" and request.form.get('ongoing')):
            booking = Bookings.query.filter_by(trek_id = request.form.get('ongoing')).all()
            check = [b for b in booking if b.status == 'pending']
            if check:
                return render_template("staff_dashboard.html",alert_type = 'danger',alert_status='Failure',alert_message = 'Please clear all request of trek first',user=user,staff = staff, pending_bookings = pending_bookings,my_treks = my_treks,tday = tday)
            else:
                trek = Treks.query.filter_by(trek_id = request.form.get('ongoing')).first()
                trek.status = 'ongoing'
                try:
                    db.session.commit()
                    return render_template("staff_dashboard.html",alert_visibility = 'd-none',user=user,staff = staff, pending_bookings = pending_bookings,my_treks = my_treks,tday = tday)
                except:
                    db.session.rollback()
                    return render_template("staff_dashboard.html",alert_type = 'danger',alert_status='Failure',alert_message = 'Failed to update status, please try again later',user=user,staff = staff, pending_bookings = pending_bookings,my_treks = my_treks,tday = tday)
        elif(request.method == "POST" and request.form.get('complete')):
            trek = Treks.query.filter_by(trek_id = request.form.get('complete')).first()
            trek.status = 'completed'
            s_staff = Staff_Profile.query.filter_by(staff_id = staff_id).first()
            s_staff.treks_completed = s_staff.treks_completed + 1 
            try:
                db.session.commit()
                return redirect(f"/staff_dashboard/{user_id}/{staff_id}/{auth_key}/")
            except:
                db.session.rollback()
                return render_template("staff_dashboard.html",alert_type = 'danger',alert_status='Failure',alert_message = 'Failed to update status, please try again later',user=user,staff = staff, pending_bookings = pending_bookings,my_treks = my_treks,tday = tday)
    else:
        return redirect("/signin/")  
    
@app.route("/staff_dashboard/<user_id>/<staff_id>/<auth_key>/treks/",methods = ["GET","POST"])
def staff_history(user_id,auth_key,staff_id):
    user = User_Credentials.query.filter_by(user_id = user_id).first()
    staff = Staff_Profile.query.filter_by(staff_id = staff_id).first()
    if ((user) and (staff) and (user.auth_key == auth_key) and (str(staff.user_id) == user_id)):
            my_treks = Treks.query.filter(Treks.status == 'completed').all()
            if (request.method == "GET"):
                return render_template("staff_treks.html",alert_visibility = 'd-none',user = user,staff = staff,my_treks = my_treks)
            elif(request.method == "POST" and request.form.get('logout')):
                user.auth_key = None
                db.session.commit()
                return redirect("/signin/")
    else:
        return redirect("/signin/")
    
@app.route("/staff_dashboard/<user_id>/<staff_id>/<auth_key>/trek/<trek_id>/",methods = ["GET","POST"])
def staff_trek(user_id,auth_key,staff_id,trek_id):
    user = User_Credentials.query.filter_by(user_id = user_id).first()
    staff = Staff_Profile.query.filter_by(staff_id = staff_id).first()
    trek = Treks.query.filter(Treks.assigned_staff == staff_id,Treks.trek_id == trek_id).first()
    if ((user) and (staff) and (trek) and (user.auth_key == auth_key) and (str(staff.user_id) == user_id)):
            bookings = Bookings.query.filter(Bookings.trek_id == trek_id, Bookings.status != 'canceled').all()
            if (request.method == "GET"):
                return render_template("staff_bookings.html",alert_visibility = 'd-none',user = user,staff = staff,bookings = bookings,trek = trek)
            elif(request.method == "POST" and request.form.get('logout')):
                user.auth_key = None
                db.session.commit()
                return redirect("/signin/")
    else:
        return redirect("/signin/")

@app.route("/trekker_dashboard/<user_id>/<trekker_id>/<auth_key>/",methods = ["GET","POST"])
def user_dashboard(user_id,trekker_id,auth_key):
    user = User_Credentials.query.filter_by(user_id = user_id).first()
    trekker = Trekker_Profile.query.filter_by(trekker_id = trekker_id).first()
    if ((user) and (trekker) and (user.auth_key == auth_key) and (str(trekker.user_id) == user_id)):
        if (request.method == 'GET'):
            treks = Treks.query.filter(Treks.booking_last_date >= datetime.today().date()).all()
            my_bookings = Bookings.query.filter_by(trekker_id = trekker_id).all()
            my_bookings_ids = [booking.trek_id for booking in my_bookings]
            final = []
            temp = []
            for i in treks:
                temp.append(i.trek_id)
                temp.append(i.trek_name)
                temp.append(i.location)
                temp.append(i.difficulty)
                temp.append(i.available_slots)
                temp.append(i.booking_last_date)
                temp.append(i.start_date)
                temp.append(i.end_date)
                temp.append(i.duration)
                temp.append(i.status)
                if (i.trek_id in my_bookings_ids):
                    x = my_bookings_ids.index(i.trek_id)
                    temp.append(my_bookings[x].status)
                final.append(temp)
                temp = []
            return render_template('trekker_dashboard.html', user = user, trekker = trekker, final = final, alert_visibility = 'd-none')
        elif(request.method == "POST" and request.form.get('book')):
            t_trekker_id, t_trek_id = map(int, request.form.get('book').split('-'))
            m_trek = Treks.query.filter_by(trek_id = t_trek_id).first()
            if (m_trek.available_slots > 0):
                try:
                    booking = Bookings(trekker_id = t_trekker_id, trek_id = t_trek_id, booking_date = datetime.today())
                    db.session.add(booking)
                    db.session.commit()
                    m_trek.available_slots = m_trek.available_slots - 1
                    db.session.commit()
                    treks = Treks.query.filter(Treks.booking_last_date >= datetime.today().date()).all()
                    my_bookings = Bookings.query.filter_by(trekker_id = trekker_id).all()
                    my_bookings_ids = [booking.trek_id for booking in my_bookings]
                    final = []
                    temp = []
                    for i in treks:
                        temp.append(i.trek_id)
                        temp.append(i.trek_name)
                        temp.append(i.location)
                        temp.append(i.difficulty)
                        temp.append(i.available_slots)
                        temp.append(i.booking_last_date)
                        temp.append(i.start_date)
                        temp.append(i.end_date)
                        temp.append(i.duration)
                        temp.append(i.status)
                        if (i.trek_id in my_bookings_ids):
                            x = my_bookings_ids.index(i.trek_id)
                            temp.append(my_bookings[x].status)
                        final.append(temp)
                        temp = []
                    return render_template('trekker_dashboard.html', user = user, trekker = trekker, final = final, alert_visibility = 'd-none')
                except:
                    db.session.rollback()
                    treks = Treks.query.filter(Treks.booking_last_date >= datetime.today().date()).all()
                    my_bookings = Bookings.query.filter_by(trekker_id = trekker_id).all()
                    my_bookings_ids = [booking.trek_id for booking in my_bookings]
                    final = []
                    temp = []
                    for i in treks:
                        temp.append(i.trek_id)
                        temp.append(i.trek_name)
                        temp.append(i.location)
                        temp.append(i.difficulty)
                        temp.append(i.available_slots)
                        temp.append(i.booking_last_date)
                        temp.append(i.start_date)
                        temp.append(i.end_date)
                        temp.append(i.duration)
                        temp.append(i.status)
                        if (i.trek_id in my_bookings_ids):
                            x = my_bookings_ids.index(i.trek_id)
                            temp.append(my_bookings[x].status)
                        final.append(temp)
                        temp = []
                    return render_template('trekker_dashboard.html', user = user, trekker = trekker, final = final, alert_type = 'danger', alert_status = 'Failure', alert_message = 'There might be a problem with server, please try again later')
            else:
                treks = Treks.query.filter(Treks.booking_last_date >= datetime.today().date()).all()
                my_bookings = Bookings.query.filter_by(trekker_id = trekker_id).all()
                my_bookings_ids = [booking.trek_id for booking in my_bookings]
                final = []
                temp = []
                for i in treks:
                    temp.append(i.trek_id)
                    temp.append(i.trek_name)
                    temp.append(i.location)
                    temp.append(i.difficulty)
                    temp.append(i.available_slots)
                    temp.append(i.booking_last_date)
                    temp.append(i.start_date)
                    temp.append(i.end_date)
                    temp.append(i.duration)
                    temp.append(i.status)
                    if (i.trek_id in my_bookings_ids):
                        x = my_bookings_ids.index(i.trek_id)
                        temp.append(my_bookings[x].status)
                    final.append(temp)
                    temp = []
                return render_template('trekker_dashboard.html', user = user, trekker = trekker, final = final, alert_type = 'danger', alert_status = 'Failure', alert_message = 'All slots booked, you may get a chance in case any booking been cancelled')
        elif(request.method == "POST" and request.form.get('cancel')):
            t_trekker_id, t_trek_id = map(int, request.form.get('cancel').split('-'))
            t_booking = Bookings.query.filter(Bookings.trekker_id == t_trekker_id, Bookings.trek_id == t_trek_id).first()
            t_booking.status = 'canceled'
            try:
                db.session.commit()
                t_trek = Treks.query.filter_by(trek_id = t_trek_id).first()
                t_trek.available_slots = t_trek.available_slots + 1
                db.session.commit()
                treks = Treks.query.filter(Treks.booking_last_date >= datetime.today().date()).all()
                my_bookings = Bookings.query.filter_by(trekker_id = trekker_id).all()
                my_bookings_ids = [booking.trek_id for booking in my_bookings]
                final = []
                temp = []
                for i in treks:
                    temp.append(i.trek_id)
                    temp.append(i.trek_name)
                    temp.append(i.location)
                    temp.append(i.difficulty)
                    temp.append(i.available_slots)
                    temp.append(i.booking_last_date)
                    temp.append(i.start_date)
                    temp.append(i.end_date)
                    temp.append(i.duration)
                    temp.append(i.status)
                    if (i.trek_id in my_bookings_ids):
                        x = my_bookings_ids.index(i.trek_id)
                        temp.append(my_bookings[x].status)
                    final.append(temp)
                    temp = []
                return render_template('trekker_dashboard.html', user = user, trekker = trekker, final = final, alert_visibility = 'd-none')
            except:
                db.session.rollback()
                treks = Treks.query.filter(Treks.booking_last_date >= datetime.today().date()).all()
                my_bookings = Bookings.query.filter_by(trekker_id = trekker_id).all()
                my_bookings_ids = [booking.trek_id for booking in my_bookings]
                final = []
                temp = []
                for i in treks:
                    temp.append(i.trek_id)
                    temp.append(i.trek_name)
                    temp.append(i.location)
                    temp.append(i.difficulty)
                    temp.append(i.available_slots)
                    temp.append(i.booking_last_date)
                    temp.append(i.start_date)
                    temp.append(i.end_date)
                    temp.append(i.duration)
                    temp.append(i.status)
                    if (i.trek_id in my_bookings_ids):
                        x = my_bookings_ids.index(i.trek_id)
                        temp.append(my_bookings[x].status)
                    final.append(temp)
                    temp = []
                return render_template('trekker_dashboard.html', user = user, trekker = trekker, final = final, alert_type = 'danger', alert_status = 'Failure', alert_merssage = 'There might be a problem with server, please try again later')
        elif(request.method == "POST" and request.form.get('logout')):
            user.auth_key = None
            db.session.commit()
            return redirect("/signin/")
    else:
        return redirect("/signin/")  
    
@app.route("/trekker_dashboard/<user_id>/<trekker_id>/<auth_key>/treks/", methods = ["GET","POST"])
def my_treks(user_id,trekker_id,auth_key):
    user = User_Credentials.query.filter_by(user_id = user_id).first()
    trekker = Trekker_Profile.query.filter_by(trekker_id = trekker_id).first()
    if ((user) and (trekker) and (user.auth_key == auth_key) and (str(trekker.user_id) == user_id)):
        if (request.method == 'GET'):
            my_bookings = Bookings.query.filter(Bookings.trekker_id == trekker_id, Bookings.status == 'booked').all()
            final = []
            temp = []
            for i in my_bookings:
                temp.append(i.trek_id)
                temp.append(i.booking_date)
                temp.append(i.rated_staff)
                temp.append(i.rated_trek)
                booked_trek = Treks.query.filter_by(trek_id = i.trek_id).first()
                temp.append(booked_trek.status)
                temp.append(booked_trek.trek_name)
                temp.append(booked_trek.assigned_staff)
                temp.append(i.booking_id)
                final.append(temp)
                temp = []
            return render_template('trekker_treks.html',alert_visibility = 'd-none', user = user, trekker = trekker, final = final)
        elif(request.method == "POST" and request.form.get('logout')):
            user.auth_key = None
            db.session.commit()
            return redirect("/signin/")
        elif(request.method == "POST" and request.form.get('rate')):
            r_staff, r_trek, r_booking = request.form.get('rate').split("-")
            t_r_staff = Staff_Profile.query.filter_by(staff_id = r_staff).first()
            t_r_trek = Treks.query.filter_by(trek_id = r_trek).first()
            t_r_booking = Bookings.query.filter_by(booking_id = r_booking).first()
            if (t_r_staff.rated_by > 0):
                t_r_staff.ratings = ((t_r_staff.ratings)*(t_r_staff.rated_by) + (int(request.form.get('rate_staff')))) / (t_r_staff.rated_by + 1)
                t_r_staff.rated_by = t_r_staff.rated_by + 1
            else:
                t_r_staff.ratings = int(request.form.get('rate_staff'))
                t_r_staff.rated_by = 1
            if (t_r_trek.rated_by > 0):
                t_r_trek.ratings = ((t_r_trek.ratings)*(t_r_trek.rated_by) + (int(request.form.get('rate_trek')))) / (t_r_trek.rated_by + 1)
                t_r_trek.rated_by = t_r_trek.rated_by + 1
            else:
                t_r_trek.ratings = int(request.form.get('rate_trek'))
                t_r_trek.rated_by = 1
            t_r_booking.rated_staff = 'yes'
            t_r_booking.rated_trek = 'yes'
            try:
                db.session.commit()
                my_bookings = Bookings.query.filter(Bookings.trekker_id == trekker_id, Bookings.status == 'booked').all()
                final = []
                temp = []
                for i in my_bookings:
                    temp.append(i.trek_id)
                    temp.append(i.booking_date)
                    temp.append(i.rated_staff)
                    temp.append(i.rated_trek)
                    booked_trek = Treks.query.filter_by(trek_id = i.trek_id).first()
                    temp.append(booked_trek.status)
                    temp.append(booked_trek.trek_name)
                    temp.append(booked_trek.assigned_staff)
                    temp.append(i.booking_id)
                    final.append(temp)
                    temp = []
                return render_template('trekker_treks.html',alert_visibility = 'd-none', user = user, trekker = trekker, final = final)
            except:
                db.session.rollback()
                my_bookings = Bookings.query.filter(Bookings.trekker_id == trekker_id, Bookings.status == 'booked').all()
                final = []
                temp = []
                for i in my_bookings:
                    temp.append(i.trek_id)
                    temp.append(i.booking_date)
                    temp.append(i.rated_staff)
                    temp.append(i.rated_trek)
                    booked_trek = Treks.query.filter_by(trek_id = i.trek_id).first()
                    temp.append(booked_trek.status)
                    temp.append(booked_trek.trek_name)
                    temp.append(booked_trek.assigned_staff)
                    temp.append(i.booking_id)
                    final.append(temp)
                    temp = []
                return render_template('trekker_treks.html',alert_type = 'danger',alert_status = 'Failure',alert_message = 'There might be a problem with server, please try again later', user = user, trekker = trekker, final = final)
    else:
        return redirect("/signin/")  