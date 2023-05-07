import requests
from sqlalchemy import or_
import os,random,string,json
from flask import render_template,request,session,flash,redirect,url_for
from sqlalchemy.sql import text
from werkzeug.security import generate_password_hash,check_password_hash
from membapp import app,db
from membapp.models import User,Party,Topics,Contact,Comments,Lga,State,Donation,Payment
from membapp.forms import ContactForm


#generating random names
def generate_name():
    filename = random.sample(string.ascii_lowercase,10)#this will return a list
    return ''.join(filename)#join every member of the list filename together

#creating routes


@app.route('/check_username',methods=['POST'])
def check_username():
    email=request.form.get('email')
    user=db.session.query(User).filter(User.user_email==email).first()
    if user != None:
        sendback = {'status':0,'feedback':'Email address already exsist. Click <a href="/user/login">here</a> to login'}
        return json.dumps(sendback)
    else:
        sendback = {'status':1,'feedback':'Email is avaliable'}
        return json.dumps(sendback)

@app.route('/user/load_lga/<stateid>')
def load_lga(stateid):
    lga = db.session.query(Lga).filter(Lga.lga_stateid==stateid).all()
    data2send = '<select class="form-control border-success">'
    for s in lga:
        data2send = data2send+"<option>"+s.lga_name+"</option>"
    data2send = data2send + "</select>"
    return data2send

@app.route('/user')
def home():
    
    contact = ContactForm()
    try:
        response = requests.get("http://127.0.0.1:8000/api/v1.0/listall")
        rspjson = json.loads(response.text)
        if response:
            rspjson = json.loads(response.text)
        else:
            rspjson = dict()
    except:
        rspjson = dict()
    return render_template('user/home.html',contact=contact,rspjson=rspjson)


@app.route('/user/donate',methods=['POST','GET'])
def donate():
    if session.get('user') != None:
        deets = User.query.get(session.get('user'))
    else:
        deets = None
    if request.method == 'GET':
        return render_template('user/donation_form.html',deets=deets)
    else:
        #retrieve the form data an insert into Donation table
        #ref = int(random.random() * 100000000)
        amount = request.form.get('amount')
        fullname = request.form.get('fullname')
        d = Donation(don_donor=fullname,don_amt=amount,don_userid=session.get('user'))
        db.session.add(d); db.session.commit()
        session['donation_id'] = d.don_id
        #Generate the ref no and keep in session
        refno = int(random.random() * 100000000)
        session['reference'] = refno
        return redirect("/user/confirm")

@app.route('/user/confirm',methods=['POST','GET'])
def confirm():
    if session.get('donation_id') != None:
        if request.method == 'GET':
            donor = db.session.query(Donation).get(session['donation_id'])
            return render_template('user/confirm.html',donor=donor,refno=session['reference'])
        else:
            p = Payment(pay_donid=session.get('donation_id'),pay_ref=session['reference'])
            db.session.add(p); db.session.commit()
            headers = {"Content-Type":"application/json","Authorization":"Bearer pk_test_7794231269f416bad096302e9e8d7e662f24a23c"}
            data = {"amount":1000,"reference":session['reference'],"email":"adetola@gmail.com"}


            response = requests.post('https://api.paystack.co/transction/initialize',headers=headers,data=json.dumps(data))
            rspjson = json.loads(response.text)
            if rspjson['status'] == True:
                url = rspjson['data']['authorization_url']
                return redirect(url)
            else:
                return redirect('/user/confrim')
    else:
        return redirect('/user/donate')

@app.route('/user/paystack')
def paystack():
    refid = session.get('reference')
    if refid == None:
        return redirect('/user')
    else:
        #connect to paystack
        headers = {"Content-Type":"application/json","Authorization":"Bearer pk_test_7794231269f416bad096302e9e8d7e662f24a23c"}
        verifyurl = "https://api.paystack.co/transaction/verify/"+refid
        response = requests.get(verifyurl,headers=headers)
        rspjson = json.loads(response.text)
        if rspjson['status'] == True:
            return rspjson
        else:
            #payment was not successfull
            return "Paystack response"
@app.route('/user/signup')
def user_signup():
    data = db.session.query(Party).all()
    return render_template('user/signup.html',data=data)

@app.route('/user/login',methods=['POST','GET'])
def user_login():
    if request.method =='GET':
        return render_template("user/login.html")
    else:
        #retrieve the form data
        email=request.form.get('email')
        pwd=request.form.get('pwd')
        #run a query to know if the username exists on the db
        deets=db.session.query(User).filter(User.user_email==email).first()
        #compared the password coming from the form with hashed pwd in db
        if deets != None:
            pwd_indb= deets.user_pwd
        #if the pwd chech above is right,we should log them in
        #by keeping their details(user_id) in session['user']
            chk=check_password_hash(pwd_indb,pwd)
            if chk:
                id= deets.user_id
                session['user']=id
                return redirect (url_for("dashboard"))
            else:
                flash("invalid password")
                return redirect(url_for('user_login'))
        else:
            flash('invalid credential')
            return redirect(url_for('user_login'))
        

@app.route("/register", methods=['POST'])
def register():
    party=request.form.get('partyid')
    email=request.form.get('email')
    pwd=request.form.get('pwd')
    hashed_pwd=generate_password_hash(pwd)

    if party !='' and email !='' and pwd !='':
        u=User(user_fullname='',user_email=email,user_pwd=hashed_pwd,user_partyid=party)
        db.session.add(u)
        db.session.commit()
        userid=u.user_id
        session['user']=userid
        return redirect('/user/dashboard')
    else:
        flash('You must complete all the fields to signup')
        return redirect('user/signup.html')
    
@app.route('/user/dashboard')
def dashboard():
    #protect this route so that only logged in user can gget here
    if session.get('user') != None:
        #retrieve the details of the logged in user
        id=session['user']
        deets=db.session.query(User).get(id)
        return render_template('user/dashboard.html',deets=deets)
    else:
        return redirect('/user/login')
    
# @app.route("/user/demo")
# def demo():
    #data=db.session.query(Party).filter(Party.party_id > 1,Party.party_id < 6).all()
    #data=db.session.query(Party).get(1)
    #data=db.session.query(Party).filter(Party.party_id> 1).filter(Party.party_id <=6).all()

    #data=db.session.query(User).filter(User.user_email==email).filter(User.user_pwd==pwd).first()
    #return render_template("user/test.html")

@app.route('/user/logout')
def user_logout():
    #pop the session and redirect to home page
    if session.get('user')!=None:
        session.pop('user',None)
    return redirect('/user')

@app.route('/user/profile',methods=["POST","GET"])
def profile():
    id=session.get('user')
    if id == None:
        return redirect(url_for('user_login'))
    else:
        if request.method == 'GET':
            allstates = db.session.query(State).all()
            deets=db.session.query(User).get(id)
            allparties = Party.query.all()
            return render_template ('user/profile.html',deets=deets,allstates=allstates,allparties=allparties)
        else:#form was submitted
            fullname=request.form.get('fullname')
            phone=request.form.get('phone')
            #update the db using ORM method
            userobj=db.session.query(User).get(id)
            userobj.user_fullname=fullname
            userobj.user_phone=phone
            db.session.commit()
            flash('profile updated')
            return redirect("/user/profile")
        
@app.route('/user/profile/picture',methods=["POST","GET"])
def profile_picture():
    if session.get('user') == None:
        return redirect(url_for('user_login'))
    else:
        if request.method == 'GET':
            return render_template('user/profile_picture.html')
        else:
            #retrieve the file
            file=request.files['pix']
            #to know the file name
            filename= file.filename
            
            allowed=['.png','.jpg','.jpeg']
            if filename !='':
                name,ext=os.path.splitext(filename)
                if ext.lower() in allowed:
                    newname= generate_name()+ext
                    file.save('membapp/static/uploads/'+newname)
                    user=db.session.query(User).get(session['user'])
                    user.user_pix = newname
                    db.session.commit()
                    return redirect('/user/blog') 
                else:
                    return "File extension not allowed"
            else:
                flash('please choose a file')
                return 'Form was submitted here'

@app.route('/user/demodb')
def demo_db():
    #data = db.session.query(User.user_fullname,Party.party_name,Party.party_contact,Party.party_shortcode).join(Party).all()
    #data = User.query.join(Party).add_columns(Party).filter(Party.party_name=='Labour Party').all()

    #from sqlalchemy import or_
    #data = User.query.join(Party).add_columns(Party).filter((Party.party_id==1) | (Party.party_id==4)).all()
    #data = User.query.join(Party).add_columns(Party).filter(or_(Party.party_id==1 , Party.party_id==4)).all()

    #data = db.session.query(Party).filter(Party.party_id==1).first()
    data = db.session.query(User).get(1)
    return render_template('user/test.html',data=data)

@app.route('/user/blog',methods=['GET'])
def user_blog():
    articles = db.session.query(Topics).filter(Topics.topic_status == '1').all()
    return render_template('user/blog.html',a=articles)

@app.route('/blog/<id>')
def blog_details(id):
    blog_deets=Topics.query.get(id)     
    # Method 2 :db.session.query(Topics).get(id)
    # Method 3:db.session.query(Topics).filter(Topics.topic_id==id).first()  
    return render_template('user/blog_details.html',blog_deets=blog_deets)


@app.route('/user/newtopic',methods=['GET','POST'])
def newtopic():
    if session.get('user') != None:
        if request.method == 'GET':
            return render_template('user/newtopic.html') 
        else:
            #retrieve for data
            content = request.form.get('content') 
            if len(content) > 0:
                t= Topics(topic_title=content,topic_userid=session['user'])
                db.session.add(t)
                db.session.commit()  
                if t.topic_id:
                    flash("Post successfully submitted for approval")
                else:
                    flash("Oops, something went wrong. Please try again")
            else:
                flash("You cannot submit an empty post")
            return redirect('/user/blog')
    else:
        return redirect(url_for('user_login'))

@app.route('/user/contact',methods=['POST','GET'])
def contact_us():
    contact = ContactForm()
    if request.method == 'GET':
        return render_template("user/contact_us.html",contact=contact)
    else:
        if contact.validate_on_submit():#True
            #retrieve from data and insert into db
            email = request.form.get('email')
            upload = request.files['screenshot'] # upload= contact.screenshot.data
            msg = contact.message.data
            m=Contact(msg_content=msg,msg_email=email,)
            db.session.add(m)
            db.session.commit()
            #insert into table message
            flash("Thank you for contacting us")
            return redirect(url_for("contact_us"))
        else:
            return render_template("user/contact_us.html",contact=contact)   

@app.route('/sendcomment')
def sendcomment():
    if session.get('user'):
        #retrieve the data coming from the request
        usermessage = request.args.get('message')
        userid = request.args.get('userid')
        usertopicid = request.args.get('topicid')
        c=Comments(comment_text=usermessage,comment_userid=userid,comment_topicid=usertopicid)
        db.session.add(c)
        db.session.commit()
        commenter = c.user_deets.user_fullname
        dateposted = c.comment_date
        sendback = f"{usermessage} <br><br>by {commenter} on {dateposted}"
        return sendback
    else:
        return 'Comment was not posted u need to login'

@app.route('/ajaxcontact',methods=['POST'])
def contact_ajax():
    email = request.form.get('mail')
    message = request.form.get('context')
    return f'{email} and {message}'