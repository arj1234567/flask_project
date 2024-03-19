from flask import Flask,render_template,request,redirect,url_for,flash,session,jsonify

from dbconnection.datamanipulation import *
import datetime
 
app =Flask(__name__)
app.secret_key="supersecretkey"

@app.route("/")
def index():
    return render_template("index.html")
@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/registerAction", methods=["post"])
def registerAction():
    name=request.form['name']
    age=request.form['age']
    gender=request.form['gender']
    country=request.form['country']
    username=request.form['username']
    password=request.form['password']
    data=sql_edit_insert("Insert into Register_tb values(NULL,?,?,?,?,?,?)",(name,age,gender,country,username + "@myname.com",password))
    flash("Registration Succesfull")
    return redirect(url_for("register"))

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/loginAction",methods=["post"])
def loginAction():
    username=request.form['username']
    password=request.form['password']
    data = sql_query2("select * from Register_tb where Username=? and Password=?",(username,password))
    if len(data)>0:
        session['user']=data[0][0]
        flash("Login succesfull")
        return render_template("userhome.html")
    else:
        flash("Login failed")
        return redirect(url_for("login"))
    
@app.route("/getuser")
def getuser():
    user = request.args.get('us')
    data = sql_query2("select * from Register_tb where Username=?",[user + "@myname.com"])
    if len(data)>0:
        msg="exist"
    else:
        msg="not exist"
    return jsonify({'valid':msg})

@app.route("/userhome")
def userhome():
    return render_template("userhome.html")

@app.route("/send_mail")
def send_mail():
    return render_template("send_mail.html")

@app.route("/send_mailAction",methods=["post"])
def send_mailAction():
    sender_id = session['user']
    reciever_name = request.form['reciever_name']
    data = sql_query2("select * from Register_tb where Username=?",[reciever_name])
    if len(data)>0:
        session['reciever'] = data[0][0]
    else:
        flash("No reciever in this username")
        return redirect(url_for('userhome'))
    reciever_id = session['reciever']
    subject = request.form['subject']
    message = request.form['message']
    date = datetime.date.today()
    time = datetime.datetime.now().strftime("%H:%M")
    sender_data = sql_edit_insert("Insert into Send_mail_tb values(NULL,?,?,?,?,?,?,?)",(sender_id,reciever_id,subject,message,date,time,"pending"))
    return redirect(url_for('userhome'))
    
@app.route("/getreciever")
def getreciever():
    reciever = request.args.get('rec')
    data = sql_query2("select * from Register_tb where Username=?",[reciever])
    if len(data)>0:
        msg = "exist"
    else:
        msg = "not exist"
    return jsonify({'valid':msg})

@app.route("/view_msg")
def view_msg():
    user_id = session['user']
    data = sql_query2("select Register_tb.Username,Send_mail_tb.* from Register_tb inner join Send_mail_tb on Register_tb.id=Send_mail_tb.Reciever_id where Sender_id=? and Status!=?",[user_id,"deleted by sender"])
    return render_template("view_msg.html",msg=data)

@app.route("/delete_msg")
def delete_msg():
    id = request.args.get('data')
    data = sql_query2("select * from Send_mail_tb where id=?",[id])
    status=data[0][7]
    if status == "pending":
        data = sql_edit_insert("update Send_mail_tb set Status=? where id=?",["deleted by sender",id])
    else:
        data= sql_edit_insert("delete from Send_mail_tb where id=?",[id])
    return redirect(url_for('view_msg'))

@app.route("/recieved_msg")
def recieved_msg():
    user_id = session['user']
    data = sql_query2("select Register_tb.Username,Send_mail_tb.* from Register_tb inner join Send_mail_tb on Register_tb.id=Send_mail_tb.Sender_id where Reciever_id=?",[user_id])
    return render_template("recieved_msg.html",rec=data)

@app.route("/move_to_trash",methods=["post"])
def move_to_trash():
    trash = request.form.getlist('trash')
    user_id = session['user']
    date = datetime.date.today()
    time = datetime.datetime.now().strftime("%H:%M")
    for i in trash:
        data = sql_edit_insert("Insert into Trash_tb values(NULL,?,?,?,?)",(i,user_id,date,time))
    return redirect(url_for('userhome'))

@app.route("/view_trash")
def view_trash():
    user_id=session['user']
    data=sql_query2("select Register_tb.Username,Trash_tb.Date,Trash_tb.Time, Send_mail_tb.* from (Register_tb inner join Send_mail_tb  on Register_tb.id=Send_mail_tb.Sender_id ) inner join Trash_tb on Send_mail_tb.id=Trash_tb.Message_id  where User_id=?",[user_id])
    return render_template("trash.html",trash=data)

@app.route("/delete_rec_msg")
def delete_rec_msg():
    id=request.args.get('data')
    data=sql_edit_insert("delete from Trash_tb where id=?",(id))
    data=sql_query2("select * from Send_mail_tb where id=?",(id))
    status=data[0][7]
    if status == "pending":
        data = sql_edit_insert("update Send_mail_tb set Status=? where id=?",("deleted by reciever",id))
    else:
        data = sql_edit_insert("delete from Send_mail_tb where id=?",[id])
        
    return redirect(url_for('view_trash'))

@app.route("/reply")
def reply():
    id = request.args.get('data')
    data=sql_query2("select Send_mail_tb.*,Register_tb.Username from Send_mail_tb inner join Register_tb on Register_tb.id=Send_mail_tb.Sender_id where Send_mail_tb.id=?",[id])
    return render_template("reply.html",reply=data)

@app.route("/replyAction",methods=["post"])
def replyAction():
    sender_id = session['user']
    name=request.form['name']
    data=sql_query2("select * from Register_tb where Username=?",[name])
    if len(data)>0:
        session['reciever']=data[0][0]
    else:
        return redirect(url_for('recieved_msg'))
    reciever_id = session['reciever']
    subject=request.form['subject']
    message=request.form['message']
    date = datetime.date.today()
    time = datetime.datetime.now().strftime("%H:%M")
    data=sql_edit_insert("Insert into Send_mail_tb values(Null,?,?,?,?,?,?,?)",[sender_id,reciever_id,subject,message,date,time,"pending"])
    return redirect(url_for('recieved_msg'))

@app.route("/forward")
def forward():
    id = request.args.get('data')
    data = sql_query2("select * from Send_mail_tb where id=?",[id])
    return render_template("forward.html",forward=data)

@app.route("/forwardAction",methods=["post"])
def forwardAction():
    sender_id=session['user']
    name=request.form['name']
    data = sql_query2("select * from Register_tb where Username=?",[name])
    if len(data)>0:
        session['reciever'] = data[0][0]
    else:
        return redirect(url_for('recieved_msg'))
    reciever_id=session['reciever']
    subject = request.form['subject']
    message=request.form['message']
    date = datetime.date.today()
    time = datetime.datetime.now().strftime("%H:%M")
    data=sql_edit_insert("Insert into Send_mail_tb values(Null,?,?,?,?,?,?,?)",[sender_id,reciever_id,subject,message,date,time,"pending"])
    return redirect(url_for('recieved_msg'))

@app.route("/getforward")
def getforward():
    forward = request.args.get('forward')
    data = sql_query2("select * from Register_tb where Username=?",[forward])
    if len(data)>0:
        msg="exist"
    else:
        msg="not exist"
    return jsonify({'valid':msg})

@app.route("/viewprofile")
def viewprofile():
    user_id = session['user']
    data = sql_query2("select * from Register_tb where id=?",[user_id])
    return render_template("viewprofile.html",prof=data)

@app.route("/updateAction",methods=["post"])
def updateAction():
    user_id = session['user']
    name=request.form['name']
    age = request.form['age']
    gender = request.form['gender']
    country=request.form['country']
    username = request.form['username']
    data = sql_edit_insert("update Register_tb set Name=?,Age=?,Gender=?,Country=?,Username=? where id=?",[name,age,gender,country,username,user_id])
    return redirect(url_for('userhome'))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)