# ----------Imports-------------------------------------
from flask import Flask, request,render_template,redirect, url_for,session,logging,flash
from alpha_vantage.timeseries import TimeSeries
import pandas as pd
import numpy as np
from statsmodels.tsa.arima_model import ARIMA
from sklearn.metrics import mean_squared_error
import matplotlib.pyplot as plt
plt.style.use('ggplot')
import math, random
from datetime import datetime
import datetime as dt
import yfinance as yf
import tweepy
import preprocessor as p
import re
from sklearn.linear_model import LinearRegression
from textblob import TextBlob
import constants as ct
from Tweet import Tweet
import plotly.express as px
import nltk
import seaborn as sns
from flask_mysqldb import MySQL,MySQLdb
import bcrypt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,scoped_session
from passlib.hash import sha256_crypt
nltk.download('punkt')
#########################################
# Ignore Warnings
import warnings
warnings.filterwarnings("ignore")
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

########## Connection à la Base de données
engine = create_engine('mysql+pymysql://root:@localhost/flaskDb')
db = scoped_session(sessionmaker(bind=engine))

#***************** FLASK *****************************
app = Flask(__name__)
#To control caching so as to save and retrieve plot figs on client side
@app.after_request
def add_header(response):
    response.headers['Pragma'] = 'no-cache'
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Expires'] = '0'
    return response

###### page d'accueil #########################
#@app.route('/')
#def home():
    #return render_template("test.html")

@app.route('/')
def home():
    return render_template("home.html")

############### Section Registration ##########################""
@app.route('/register',methods=["GET","POST"])
def register():
    if request.method == "POST":
        name = request.form.get('name')
        username = request.form.get('username')
        password = request.form.get('password')
        confirm = request.form.get('confirm')
        hash_password = sha256_crypt.encrypt(str(password))

        if password == confirm:
            db.execute("INSERT INTO users (name, username, password) VALUES(:name,:username,:password)",
            {"name":name,"username":username,"password":hash_password})
            db.commit()
            flash("Registered successfully: You can login","success")
            return redirect(url_for('login'))
        else:
            flash("password does not match","danger")
            return render_template("register.html")

    return render_template("register.html")

############### Section login ##########################""
@app.route('/login',methods=["GET","POST"])
def login():
    if request.method == 'POST':
        username = request.form.get('name')
        password = request.form.get('password')

        usernamedata = db.execute("SELECT username FROM users WHERE username=:username",{"username":username}).fetchone()
        passwordata = db.execute("SELECT password FROM users WHERE username=:username",{"username":username}).fetchone()

        if usernamedata is None:
            flash("no user","danger")
            return render_template("login.html")
        else:
            for password_data in passwordata:
                if sha256_crypt.verify(password,password_data):
                    session["log"]=True
                    flash("you are now login","success")
                    return redirect(url_for('dashboard'))
                else:
                    flash("incorrect password","danger")
                    return render_template("login.html")

    return render_template('login.html')

############### Section Dashboard ##########################""
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

############### Section logout ##########################""
@app.route("/logout")
def logout():
    session.clear()
    flash("you are now logout","success")
    return redirect(url_for('login'))

@app.route('/predict')
def predict():
    return render_template('index.html')

@app.route('/societes')
def societes():
    return render_template('societes.html')

@app.route('/test')
def test():
    return render_template('test.html')

@app.route('/insertintotable',methods = ['POST'])
def insertintotable():
    nm = request.form['nm']

    #**************** FUNCTIONS TO FETCH DATA ***************************
    def get_historical(quote):
        end = datetime.now()
        start = datetime(end.year-2,end.month,end.day)
        data = yf.download(quote, start=start, end=end)
        df = pd.DataFrame(data=data)
        df.to_csv(''+quote+'.csv')
        if(df.empty):
            ts = TimeSeries(key='N6A6QT6IBFJOPJ70',output_format='pandas')
            data, meta_data = ts.get_daily_adjusted(symbol='NSE:'+quote, outputsize='full')
            #Format df
            #
            data=data.head(503).iloc[::-1]
            data=data.reset_index()
            #Keep Required cols only
            df=pd.DataFrame()
            df['Date']=data['date']
            df['Open']=data['1. open']
            df['High']=data['2. high']
            df['Low']=data['3. low']
            df['Close']=data['4. close']
            df['Adj Close']=data['5. adjusted close']
            df['Volume']=data['6. volume']
            df.to_csv(''+quote+'.csv',index=False)
        return

    #******************** ARIMA SECTION ********************
    def ARIMA_ALGO(df):
        uniqueVals = df["Code"].unique()  
        len(uniqueVals)
        df=df.set_index("Code")
        #
        def parser(x):
            return datetime.strptime(x, '%Y-%m-%d')
        def arima_model(train, test):
            history = [x for x in train]
            predictions = list()
            for t in range(len(test)):
                model = ARIMA(history, order=(6,1 ,0))
                model_fit = model.fit(disp=0)
                output = model_fit.forecast()
                yhat = output[0]
                predictions.append(yhat[0])
                obs = test[t]
                history.append(obs)
            return predictions
        for company in uniqueVals[:10]:
            data=(df.loc[company,:]).reset_index()
            data['Price'] = data['Close']
            Quantity_date = data[['Price','Date']]
            Quantity_date.index = Quantity_date['Date'].map(lambda x: parser(x))
            Quantity_date['Price'] = Quantity_date['Price'].map(lambda x: float(x))
            Quantity_date = Quantity_date.fillna(Quantity_date.bfill())
            Quantity_date = Quantity_date.drop(['Date'],axis =1)
            fig = plt.figure(figsize=(7.2,4.8),dpi=65)
            plt.plot(Quantity_date)
            plt.savefig('static/Graph.png')
            plt.close(fig)
            
            quantity = Quantity_date.values
            size = int(len(quantity) * 0.80)
            train, test = quantity[0:size], quantity[size:len(quantity)]
            #fit in model
            predictions = arima_model(train, test)
            
            #plot graph
            fig = plt.figure(figsize=(7.2,4.8),dpi=65)
            plt.plot(test,label='Actual Price')
            plt.plot(predictions,label='Predicted Price')
            plt.legend(loc=4)
            plt.savefig('static/ARIMA.png')
            plt.close(fig)
            print()
            print("##############################################################################")
            arima_pred=predictions[-2]
            print("Demain",quote," Closing Price Prediction Par ARIMA:",arima_pred)
            #rmse calculation
            error_arima = math.sqrt(mean_squared_error(test, predictions))
            print("ARIMA RMSE:",error_arima)
            print("##############################################################################")
            return arima_pred, error_arima

    #************* LSTM SECTION **********************
    def LSTM_ALGO(df):
        #Split data into training set and test set
        dataset_train=df.iloc[0:int(0.8*len(df)),:]
        dataset_test=df.iloc[int(0.8*len(df)):,:]
        ############# NOTE #################
        #
        #
        ###dataset_train=pd.read_csv('Google_Stock_Price_Train.csv')
        training_set=df.iloc[:,4:5].values#
        #

        #Feature Scaling
        from sklearn.preprocessing import MinMaxScaler
        sc=MinMaxScaler(feature_range=(0,1))#Scaled values entre 0,1
        training_set_scaled=sc.fit_transform(training_set)
        #
        
        #Créer la data stucture avec 7 timesteps et 1 output.
        #
        X_train=[]#memoire avec 7 jours from day i
        y_train=[]#day i
        for i in range(7,len(training_set_scaled)):
            X_train.append(training_set_scaled[i-7:i,0])
            y_train.append(training_set_scaled[i,0])
        #Convertir list to numpy arrays
        X_train=np.array(X_train)
        y_train=np.array(y_train)
        X_forecast=np.array(X_train[-1,1:])
        X_forecast=np.append(X_forecast,y_train[-1])
        #Reshaping:
        X_train=np.reshape(X_train, (X_train.shape[0],X_train.shape[1],1))#.shape 0=row,1=col
        X_forecast=np.reshape(X_forecast, (1,X_forecast.shape[0],1))

        
        #Créer le RNN
        import tensorflow as tf
        from tensorflow import keras
        from keras.models import Sequential
        from keras.layers import Dense
        from keras.layers import Dropout
        from keras.layers import LSTM
        
        #Initialise RNN
        regressor=Sequential()
        
        #Add 1er LSTM layer
        regressor.add(LSTM(units=50,return_sequences=True,input_shape=(X_train.shape[1],1)))

        regressor.add(Dropout(0.1))
        
        #Add 2eme LSTM layer
        regressor.add(LSTM(units=50,return_sequences=True))
        regressor.add(Dropout(0.1))
        
        #Add 3eme LSTM layer
        regressor.add(LSTM(units=50,return_sequences=True))
        regressor.add(Dropout(0.1))
        
        #Add 4eme LSTM layer
        regressor.add(LSTM(units=50))
        regressor.add(Dropout(0.1))
        
        #Add  layer
        regressor.add(Dense(units=1))
        
        #Compile
        regressor.compile(optimizer='adam',loss='mean_squared_error')
        
        #Training
        regressor.fit(X_train,y_train,epochs=25,batch_size=32 )
        #For lstm,
        
        #Testing
        ###dataset_test=pd.read_csv('Google_Stock_Price_Test.csv')
        real_stock_price=dataset_test.iloc[:,4:5].values
        
        #
        #
        dataset_total=pd.concat((dataset_train['Close'],dataset_test['Close']),axis=0) 
        testing_set=dataset_total[ len(dataset_total) -len(dataset_test) -7: ].values
        testing_set=testing_set.reshape(-1,1)
        #
        
        #Feature scaling
        testing_set=sc.transform(testing_set)
        
        #Create data structure
        X_test=[]
        for i in range(7,len(testing_set)):
            X_test.append(testing_set[i-7:i,0])
            #Convert list to numpy arrays
        X_test=np.array(X_test)
        
        #Reshaping:
        X_test=np.reshape(X_test, (X_test.shape[0],X_test.shape[1],1))
        
        #Testing Prediction
        predicted_stock_price=regressor.predict(X_test)
        
        #Obtenir l'original prices des values apres le scaled
        predicted_stock_price=sc.inverse_transform(predicted_stock_price)
        fig = plt.figure(figsize=(7.2,4.8),dpi=65)
        plt.plot(real_stock_price,label='Actual Price')  
        plt.plot(predicted_stock_price,label='Predicted Price')
          
        plt.legend(loc=4)
        plt.savefig('static/LSTM.png')
        plt.close(fig)
        
        
        error_lstm = math.sqrt(mean_squared_error(real_stock_price, predicted_stock_price))
        
        
        #Forecasting Prediction
        forecasted_stock_price=regressor.predict(X_forecast)
        
        #Getting original prices
        forecasted_stock_price=sc.inverse_transform(forecasted_stock_price)
        
        lstm_pred=forecasted_stock_price[0,0]
        print()
        print("##############################################################################")
        print("DEMAIN",quote," Closing Price Prediction Par LSTM: ",lstm_pred)
        print("LSTM RMSE:",error_lstm)
        print("##############################################################################")
        return lstm_pred,error_lstm
    #*****************  ******************
    def LIN_REG_ALGO(df):
            #No of days to be forcasted in future
            forecast_out = int(7)
            #Price after n days
            df['Close after n days'] = df['Close'].shift(-forecast_out)
            #New df with only relevant data
            df_new=df[['Close','Close after n days']]

            #Structure data for train, test & forecast
            #lables of known data, discard last 35 rows
            y =np.array(df_new.iloc[:-forecast_out,-1])
            y=np.reshape(y, (-1,1))
            #all cols of known data except lables, discard last 35 rows
            X=np.array(df_new.iloc[:-forecast_out,0:-1])
            #Unknown, X to be forecasted
            X_to_be_forecasted=np.array(df_new.iloc[-forecast_out:,0:-1])

            #Traning, testing to plot graphs, check accuracy
            X_train=X[0:int(0.8*len(df)),:]
            X_test=X[int(0.8*len(df)):,:]
            y_train=y[0:int(0.8*len(df)),:]
            y_test=y[int(0.8*len(df)):,:]

            # Feature Scaling===Normalization
            from sklearn.preprocessing import StandardScaler
            sc = StandardScaler()
            X_train = sc.fit_transform(X_train)
            X_test = sc.transform(X_test)

            X_to_be_forecasted=sc.transform(X_to_be_forecasted)

            #Training
            clf = LinearRegression(n_jobs=-1)
            clf.fit(X_train, y_train)

            #Testing
            y_test_pred=clf.predict(X_test)
            y_test_pred=y_test_pred*(1.04)
            import matplotlib.pyplot as plt2
            fig = plt2.figure(figsize=(7.2,4.8),dpi=65)
            plt2.plot(y_test,label='Actual Price' )
            plt2.plot(y_test_pred,label='Predicted Price')

            plt2.legend(loc=4)
            plt2.savefig('static/LR.png')
            plt2.close(fig)

            error_lr = math.sqrt(mean_squared_error(y_test, y_test_pred))


            #Forecasting
            forecast_set = clf.predict(X_to_be_forecasted)
            forecast_set=forecast_set*(1.04)
            mean=forecast_set.mean()
            lr_pred=forecast_set[0,0]
            print()
            print("##############################################################################")
            print("Tomorrow's ",quote," Closing Price Prediction by Linear Regression: ",lr_pred)
            print("Linear Regression RMSE:",error_lr)
            print("##############################################################################")
            return df, lr_pred, forecast_set, mean, error_lr
    #**************** SENTIMENT ANALYSIS **************************
    def retrieving_tweets_polarity(symbol):
        stock_ticker_map = pd.read_csv('Yahoo-Finance-Ticker-Symbols.csv')
        stock_full_form = stock_ticker_map[stock_ticker_map['Ticker']==symbol]
        symbol = stock_full_form['Name'].to_list()[0][0:12]

        auth = tweepy.OAuthHandler(ct.consumer_key, ct.consumer_secret)
        auth.set_access_token(ct.access_token, ct.access_token_secret)
        user = tweepy.API(auth)
        
        tweets = tweepy.Cursor(user.search, q=symbol, tweet_mode='extended',wait_on_rate_limit=True, lang='en',exclude_replies=True).items(ct.num_of_tweets)
        
        tweet_list = [] #List of tweets
        global_polarity = 0 #Polarité de tous les tweets === Sum of polarities of individual tweets
        tw_list=[] #Liste des  tweets seulement => qui seront affichés sur web page
        #Count Positive, Negative to plot pie chart
        pos=0 #Num of pos tweets
        neg=1 #Num of negative tweets
        for tweet in tweets:
            count=20 #Num of tweets qui sera affiché
            #Convert to Textblob format
            tw2 = tweet.full_text
            tw = tweet.full_text
            date = tweet.created_at
            #Clean
            tw=p.clean(tw)
            #print("-------------------------------CLEAN TWEET-----------------------------")
            #print(tw)
            #Replace &amp; by &
            tw=re.sub('&amp;','&',tw)
            #Remove :
            tw=re.sub(':','',tw)
            #print("------------------------------------------------------------")
            #print(tw)
            #Remove Emojis
            tw=tw.encode('ascii', 'ignore').decode('ascii')

            #print("-----------------------------------------------------------")
            #print(tw)
            blob = TextBlob(tw)
            polarity = 0 #Polarite d'un seul tweet
            for sentence in blob.sentences:
                   
                polarity += sentence.sentiment.polarity
                if polarity>0:
                    pos=pos+1
                if polarity<0:
                    neg=neg+1
                
                global_polarity += sentence.sentiment.polarity
            if count > 0:
                tw_list.append(tw2)
                
            tweet_list.append(Tweet(tw, polarity))
            count=count-1
        if len(tweet_list) != 0:
            global_polarity = global_polarity / len(tweet_list)
        else:
            global_polarity = global_polarity
        neutral=ct.num_of_tweets-pos-neg
        if neutral<0:
        	neg=neg+neutral
        	neutral=20
        print()
        print("##############################################################################")
        print("Positive Tweets :",pos,"Negative Tweets :",neg,"Neutral Tweets :",neutral)
        print("##############################################################################")
        print(date)
        print("##############################################################################")
        ################ Pie_Chart ###################
        labels=['Positive','Negative','Neutral']
        sizes = [pos,neg,neutral]
        explode = (0, 0.1, 0)
        fig = plt.figure(figsize=(7.2,4.8),dpi=65)
        fig1, ax1 = plt.subplots(figsize=(7.2,4.8),dpi=65)
        ax1.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%',
                shadow=True, startangle=90)
        ax1.axis('equal')  # Pour s'assurer que le pie est dessinée en cercle.
        ax1.set_title('Pie Chart Twitter Sentiment Analysis')
        plt.tight_layout()
        plt.savefig('static/pie_chart.png')
        plt.close(fig)
        ################ Bar Plot ###################
        #Tout d'abord le calcul de la moyenne des sentiments
        pos_mean = np.mean(pos)
        neg_mean = np.mean(neg)
        neutral_mean = np.mean(neutral)
        #creer les tableaux pour les plot
        labels=['Positive','Negative','Neutral']
        length_label = np.arange(len(labels))
        mean_tweets = [pos_mean, neg_mean, neutral_mean]
        #fig
        fig = plt.figure(figsize=(7.2,4.8),dpi=65)
        fig2, ax = plt.subplots(figsize=(7.2,4.8),dpi=65)
        ax.bar(length_label, mean_tweets, align='center', alpha=0.5,color=['blue', 'red', 'green'])
        ax.set_ylabel('Le Nombre de Tweets')
        ax.set_xticks(length_label)
        ax.set_xticklabels(labels)
        ax.set_title('Bar Plot Twitter Sentiment Analysis')
        # Save the figure and show
        plt.tight_layout()
        plt.savefig('static/bar_plot.png')
        plt.close(fig2)
        ################ 2eme BarPlot ###################
        #fig
        n_groups = 3
        # create plot
        fig = plt.figure(figsize=(7.2,4.8),dpi=65)
        fig3, ax = plt.subplots(figsize=(7.2,4.8),dpi=65)
        index = np.arange(0, n_groups * 2, 2)
        #index = np.arange(n_groups)
        bar_width = 0.35
        opacity = 0.8

        rects1 = plt.bar(index, pos_mean, bar_width,alpha=opacity,color='b',label='positive')
        rects2 = plt.bar(index + bar_width, neg_mean, bar_width,alpha=opacity,color='g',label='negative')
        rects3 = plt.bar(index + bar_width* 2, neutral_mean, bar_width,alpha=opacity,color='y',label='neutre')

        plt.xlabel('sentiments')
        plt.ylabel('tweets')
        plt.title('Analysis')
        plt.xticks(index + bar_width, ('A', 'B', 'C'))
        plt.legend()

        plt.tight_layout()
        plt.savefig('static/bar_plot2.png')
        plt.close(fig3)
        #plt.show()
        ################ Line Plot ###################
        #fig
        fig = plt.figure(figsize=(7.2,4.8))
        fig4, ax = plt.subplots(figsize=(7.2,4.8),dpi=65)
        n = 5000
        positive = np.random.normal(pos_mean, pos, n)
        negative = np.random.normal(neg_mean, neg, n)
        neutre = np.random.normal(neutral_mean, neutral, n)
        ax.hist(positive, bins=100, alpha=0.5, label="positive")
        ax.hist(negative, bins=100, alpha=0.5, label="negative")
        ax.hist(neutre,   bins=100, alpha=0.5, label="neutre")
        ax.set_ylabel('Le Nombre de Tweets')
        ax.set_title('Histogram Plot Twitter Sentiment Analysis')
        plt.legend()
        # Save the figure and show
        plt.tight_layout()
        plt.savefig('static/line_plot.png')
        plt.close(fig4)
        ################ Line Plot ###################
        fig = plt.figure(figsize=(7.2,4.8))
        fig5, ax = plt.subplots(figsize=(7.2,4.8),dpi=65)
        pos_line=np.cumsum(np.random.randn(pos,1))
        neg_line=np.cumsum(np.random.randn(neg,1))
        neu_line=np.cumsum(np.random.randn(neutral,1))
        ax.plot(pos_line,color='b',label='positive')
        ax.plot(neg_line,color='g',label='negative')
        ax.plot(neu_line,color='y',label='neutre')
        #data = tweets['created_at']
        #sns.displot(date, bins = 30)
        #sns_plot = sns.pairplot(df, hue='species', height=2.5)
        #sns.displot(penguins, x="flipper_length_mm", kind="kde")
        #fig5 = px.treemap(tweet, path=['words'], values='count',title='Tree Of Unique Positive Words')
        #ax.plot(date,date)
        ax.set_ylabel('Le Nombre de Tweets')
        ax.set_title('Line Plot Twitter Sentiment Analysis')
        plt.legend()
        # Save the figure and show
        plt.tight_layout()
        plt.savefig('static/hist_plot.png')
        plt.close(fig5)

        if global_polarity>0:
            print()
            print("##############################################################################")
            print("Tweets Polarity: Overall Positive")
            print("##############################################################################")
            tw_pol="Overall Positive"
        else:
            print()
            print("##############################################################################")
            print("Tweets Polarity: Overall Negative")
            print("##############################################################################")
            tw_pol="Overall Negative"
        return global_polarity,tw_list,tw_pol,pos,neg,neutral


    def recommending(df, global_polarity,today_stock,mean):
        if today_stock.iloc[-1]['Close'] < mean:
            if global_polarity > 0:
                idea="RISE"
                decision="BUY"
                print()
                print("##############################################################################")
                print("Selon les Predictions du ML, DL et Twitter Sentiment Analyse,une",idea,"dans le",quote,"stock is expected => ce qui implique",decision)
            elif global_polarity <= 0:
                idea="FALL"
                decision="SELL"
                print()
                print("##############################################################################")
                print("Selon les Predictions du ML, DL et Twitter Sentiment Analyse,une",idea,"dans le",quote,"stock is expected => ce qui implique",decision)
        else:
            idea="FALL"
            decision="SELL"
            print()
            print("##############################################################################")
            print("Selon les Predictions du ML, DL et Twitter Sentiment Analyse,une",idea,"dans le",quote,"stock is expected => ce qui implique",decision)
        return idea, decision




    #**************GET DATA ***************************************
    quote=nm
    #
    try:
        get_historical(quote)
    except:
        return render_template('index.html',not_found=True)
    else:
    
        #************** PREPROCESSING ***********************
        df = pd.read_csv(''+quote+'.csv')
        print("##############################################################################")
        print("Today's",quote,"Stock Data: ")
        today_stock=df.iloc[-1:]
        print(today_stock)
        print("##############################################################################")
        df = df.dropna()
        code_list=[]
        for i in range(0,len(df)):
            code_list.append(quote)
        df2=pd.DataFrame(code_list,columns=['Code'])
        df2 = pd.concat([df2, df], axis=1)
        df=df2


        arima_pred, error_arima=ARIMA_ALGO(df)
        lstm_pred, error_lstm=LSTM_ALGO(df)
        df, lr_pred, forecast_set,mean,error_lr=LIN_REG_ALGO(df)
        polarity,tw_list,tw_pol,pos,neg,neutral = retrieving_tweets_polarity(quote)
        
        idea, decision=recommending(df, polarity,today_stock,mean)
        print()
        print("Forecasted Prices for Next 7 days:")
        print(forecast_set)
        today_stock=today_stock.round(2)


        return render_template('results.html',quote=quote,
                               arima_pred=round(arima_pred,2),
                               lstm_pred=round(lstm_pred,2),
                               lr_pred=round(lr_pred,2),
                               open_s=today_stock['Open'].to_string(index=False),
                               close_s=today_stock['Close'].to_string(index=False),
                               adj_close=today_stock['Adj Close'].to_string(index=False),
                               tw_list=tw_list,
                               tw_pol=tw_pol,
                               idea=idea,
                               decision=decision,
                               high_s=today_stock['High'].to_string(index=False),
                               low_s=today_stock['Low'].to_string(index=False),
                               vol=today_stock['Volume'].to_string(index=False),
                               forecast_set=forecast_set,
                               error_lr=round(error_lr,2),error_lstm=round(error_lstm,2),error_arima=round(error_arima,2))
if __name__ == '__main__':
    app.secret_key="super secret key"
    app.run(debug=True)
