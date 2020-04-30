from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps

app=Flask(__name__)
app.secret_key="PB-PYTHON BLOG"
app.config["MYSQL_HOST"]="localhost"
app.config["MYSQL_USER"]="root"
app.config["MYSQL_PASSWORD"]=""
app.config["MYSQL_DB"]="pythonblog"
app.config["MYSQL_CURSORCLASS"]="DictCursor"
#Kullanıcı giriş Decoratoru
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu sayfayı görüntülemek için lütfen giriş yappın","danger")
            return redirect(url_for("login"))
    return decorated_function
#Kullanıcı Kayıt Formu
class RegisterForm(Form):
    name=StringField("İsim Soyisim",validators=[validators.Length(min =5,max=25),validators.DataRequired(message="Lütfen Bir Ad Girin")])
    username=StringField("KUllanıcı Adı",validators=[validators.Length(min =8,max=25),validators.DataRequired(message="Lütfen Bir Kullanıcı Adı Belirleyin")])
    email=StringField("Email",validators=[validators.Email(message="Lütfen Geçerli Bir E-Mail Adresi Giriniz"),validators.DataRequired(message="Lütfen Bir E-Mail Belirleyin")])
    password=PasswordField("Parola",validators=[validators.length(min=8,max=25),validators.DataRequired(message="Lütfen Bir Parola Belirleyin"),validators.EqualTo(fieldname="confirm",message="Parolanız Uyuşmuyor")])
    confirm=PasswordField("Parola Doğrula")
class KayitOl(Form):
    username_login=StringField("Kullanıcı Adı",validators=[validators.length(min=5,max=25),validators.DataRequired(message="Lütfen Bu Alanı Boş Bırakmayınız")])
    password_login=PasswordField("Parola",validators=[validators.length(min=8,max=25),validators.DataRequired(message="Lütfen Bu Alanı Boş Bırakmayınız")])

#Kayıt OLma
mysql=MySQL(app)


@app.route("/")
def index():
    return render_template("index.html")
@app.route("/about")
def hakkımda():
    return render_template("about.html")
@app.route("/register",methods=["GET","POST"])
def register():
    form=RegisterForm(request.form)
    if request.method=="POST" and form.validate():
        name=form.name.data
        username=form.username.data
        email=form.email.data
        password=sha256_crypt.encrypt(form.password.data)
        cursor=mysql.connection.cursor()
        if cursor.execute("Select * from users where username = %s ",(username,))==0 and cursor.execute("Select * from users where email = %s ",(email,))==0:
            sorgu="Insert into users(name,email,username,password) VALUES(%s,%s,%s,%s)"
            cursor.execute(sorgu,(name,email,username,password))
            mysql.connection.commit()
            cursor.close()
            flash("Başarıyla Kayıt Oldunuz","success")
            return redirect(url_for("login"))
        else:
            flash("Girdiğiniz email veya kullanıcı adı kullanımdadır lütfen daha arklı bir kullanıcı adı veya email giriniz","danger")
            return redirect(url_for("register"))
    else:
        return render_template("register.html",form=form)
#Arama Url
@app.route("/search",methods=["GET","POST"])
def search():
    if request.method=="GET":
        return redirect(url_for("index"))
    else:
        keyword=request.form.get("keyword")
        cursor=mysql.connection.cursor()
        sorgu="Select * From articles where title like '%"+keyword+"%'"

        result=cursor.execute(sorgu)
        if result==0:
            flash("Aranan kelimeye uygun makale bulunamadı","warning")
            return redirect(url_for("articles"))
        else:
            articles=cursor.fetchall()
            return render_template("articles.html",articles=articles)
#Makale Güncelleme
@app.route("/edit/<string:id>",methods=["GET","POST"])
@login_required
def edit(id):
    if request.method== "GET":
        cursor=mysql.connection.cursor()
        sorgu="Select * from articles where id = %s and author=%s"
        result=cursor.execute(sorgu,(id,session["username"]))
        if result==0:
            flash("Böyle bir makale yok veya buna yetkiniz yok","danger")
            return redirect(url_for("index"))
        else:
            article = cursor.fetchone()
            form=ArticleForm()

            form.title.data=article["title"]
            form.content.data=article["content"]
            return render_template("edit.html",form=form)



    else:
        #Post Request
        form=ArticleForm(request.form)

        newTitle=form.title.data
        newContent=form.content.data
        sorgu2="Update articles Set title = %s,content = %s where id = %s "
        cursor=mysql.connection.cursor()
        cursor.execute(sorgu2,(newTitle,newContent,id))
        mysql.connection.commit()
        flash("Makale Başarıyla Güncellendi","success")
        return redirect(url_for("dashboard"))




#Makale Silme
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor=mysql.connection.cursor()
    sorgu="Select * from articles where author=%s and id=%s"
    result=cursor.execute(sorgu,(session["username"],id))
    if result>0:
        sorgu2="Delete from articles where id=%s"
        cursor.execute(sorgu2,(id,))
        mysql.connection.commit()
        return redirect(url_for("dashboard"))
    else:
        flash("Böyle bir makale yok veya yetkiniz yok","danger")
        return redirect(url_for("index"))

@app.route("/login",methods=["GET","POST"])
def login():
    form2=KayitOl(request.form)
    if request.method=="POST":
        username1=form2.username_login.data
        password1=form2.password_login.data
        cursor=mysql.connection.cursor()
        sorgu="Select * From users where username = %s"
        result = cursor.execute(sorgu,(username1,))
        if result>0:
            data=cursor.fetchone()
            real_password=data["password"]
            if sha256_crypt.verify(password1,real_password):
                flash("Başarıyla Giriş Yaptınız...","success")
                session["logged_in"]=True
                session["username"]=username1
                return redirect(url_for("index"))
            else:
                flash("Parolanızı yanlış girdiniz","danger")
                return redirect(url_for("login"))
        else:
            flash("Böyle bir kullanıcı bulunnmuyor","danger")
            return redirect(url_for("login"))
        return redirect(url_for("index"))
    else:
        return render_template("login.html",form=form2)

@app.route("/article/<string:id>")
def article(id):
    cursor=mysql.connection.cursor()
    sorgu="Select * from articles where id=%s"
    result=cursor.execute(sorgu,(id,))

    if result>0:
        article=cursor.fetchone()
        return render_template("article.html",article=article)
    else:
        return render_template("article.html")


    
@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect(url_for("index"))
@app.route("/dashboard")
@login_required
def dashboard():
    cursor=mysql.connection.cursor()
    sorgu="Select * From articles where author = %s"
    result=cursor.execute(sorgu,(session["username"],))
    if result>0:
        articles=cursor.fetchall()
        return render_template("dashboard.html",articles=articles)
    else:
        return render_template("dashboard.html")
@app.route("/addarticle",methods=["GET","POST"])
@login_required
def addarticle():
    form=ArticleForm(request.form)
    if request.method=="POST" and form.validate():
        title=form.title.data
        content=form.content.data

        cursor=mysql.connection.cursor()
        sorgu="Insert into articles(title,author,content) VALUES(%s,%s,%s)"
        cursor.execute(sorgu,(title,session["username"],content))
        mysql.connection.commit() 
        cursor.close()
        flash("Makale başarıyla eklendi","success")
        return redirect(url_for("dashboard"))
    return render_template("addarticle.html",form=form)
#makale form

class ArticleForm(Form):
    title = StringField("Makale Başlığı",validators=[validators.Length(min=5,max=100)])
    content= TextAreaField("Makale İçeriği",validators=[validators.Length(min=9)])
#makale sayfası
@app.route("/articles")
def articles():
    cursor=mysql.connection.cursor()

    sorgu="Select * From articles"
    result =cursor.execute(sorgu)

    if result>0:
        articles=cursor.fetchall()
        return render_template("articles.html",articles=articles)
    else:
        return render_template("articles.html")

if __name__ == "__main__":
    app.run(debug=True)









