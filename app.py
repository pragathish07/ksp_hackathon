from flask import Flask, request,render_template, redirect,session
from flask_sqlalchemy import SQLAlchemy
import bcrypt
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import LabelEncoder


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
app.secret_key = 'secret_key'

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

    def __init__(self,email,password,name):
        self.name = name
        self.email = email
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self,password):
        return bcrypt.checkpw(password.encode('utf-8'),self.password.encode('utf-8'))

with app.app_context():
    db.create_all()


from flask import Flask, render_template
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

def generate_pie_chart(data):

    max_length = 20
    locations = [loc[:max_length] + "..." if len(loc) > max_length else loc for loc in data.index.to_numpy()]

    plt.figure(figsize=(8, 8))
    plt.pie(data.to_numpy(), labels=locations, autopct='%1.1f%%', startangle=90, pctdistance=0.85)
    plt.title("Accident Distribution by Accident Location")
    plt.gca().add_artist(plt.Circle((0, 0), 0.70, fc='white'))
    plt.tight_layout()

    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png')
    plt.close()  # Close the figure to avoid memory leaks

    img_data = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
    return f"data:image/png;base64,{img_data}"

def generate_line_chart(data):

    plt.figure(figsize=(12, 6))
    plt.plot(data['DISTRICTNAME'], data['TotalAccidents'], marker='o', linestyle='-')
    plt.title('Total Accidents per District')
    plt.xlabel('District')
    plt.ylabel('Total Accidents')
    plt.xticks(rotation=90)
    plt.grid(True)
    plt.tight_layout()

    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png')
    plt.close()  # Close the figure to avoid memory leaks

    img_data = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
    return f"data:image/png;base64,{img_data}"

def generate_bar_chart(data):

    plt.figure(figsize=(10, 6))
    data.plot(kind='bar', color='skyblue')
    plt.xlabel('Road Type')
    plt.ylabel('Accident Count')
    plt.title('Accident Distribution by Road Type')
    plt.xticks(rotation=45, ha='right')
    plt.grid(axis='y')
    plt.tight_layout()

    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png')
    plt.close()  # Close the figure to avoid memory leaks

    img_data = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
    return f"data:image/png;base64,{img_data}"

@app.route('/')
def index():
    # Read the data for each analysis
    accident_location_data = pd.read_csv('main.csv')['Accident_Location'].value_counts()
    district_accident_data = pd.read_csv('dis-no.csv')
    road_type_data = pd.read_csv('main.csv')['Road_Type'].value_counts()

    # Generate the chart images as base64 encoded data
    pie_chart_url = generate_pie_chart(accident_location_data)
    line_chart_url = generate_line_chart(district_accident_data)
    bar_chart_url = generate_bar_chart(road_type_data)



@app.route('/register',methods=['GET','POST'])
def register():
    if request.method == 'POST':
        # handle request
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        new_user = User(name=name,email=email,password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect('/login')



    return render_template('register.html')

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            session['email'] = user.email
            return redirect('/dashboard')
        else:
            return render_template('login.html',error='Invalid user')

    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if session['email']:
        user = User.query.filter_by(email=session['email']).first()
        return render_template('dashboard.html',user=user)
    
    return redirect('/login')

@app.route('/logout')
def logout():
    session.pop('email',None)
    return redirect('/login')

@app.route('/plot')
def plot_clusters():
    k = 3  # Number of clusters
    data = pd.read_csv("black.csv")

    label_encoder = LabelEncoder()
    data['Accident_Spot'] = label_encoder.fit_transform(data['Accident_Spot'])
    data['Accident_Location'] = label_encoder.fit_transform(data['Accident_Location'])
    data['Main_Cause'] = label_encoder.fit_transform(data['Main_Cause'])
    data['Severity'] = label_encoder.fit_transform(data['Severity'])
    data['Road_Type'] = label_encoder.fit_transform(data['Road_Type'])
    data_scaled = data.copy()
    data_scaled[['Accident_Spot', 'Accident_Location', 'Main_Cause', 'Road_Type']] = (
        data_scaled[['Accident_Spot', 'Accident_Location', 'Main_Cause', 'Road_Type']].astype(float)
    )

    kmeans = KMeans(n_clusters=k, random_state=42)
    clusters = kmeans.fit_predict(data_scaled)

    cluster_counts = pd.Series(clusters).value_counts().sort_index()
    plt.bar(cluster_counts.index, cluster_counts.values)
    plt.xlabel('Cluster')
    plt.ylabel('Number of Data Points')
    plt.title('Distribution of Clusters')
    plt.xticks(range(k))
    plt.grid(axis='y')

    # Save the plot to a file
    plot_path = 'static/plot.png'
    plt.savefig(plot_path)
    plt.close()

    return render_template('plot.html', plot_path=plot_path)

if __name__ == '__main__':
    app.run(debug=True)