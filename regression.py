#extra stuff needed for regression model
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression 

self.data['SMA_METRIC'] = self.data['SMA_LONG'] - self.data['SMA_SHORT']
self.data['BB_METRIC'] = self.data['BB_UPPER'] - self.data['BB_LOWER']

self.data['PNL'] = self.data['Open'] - self.data['Close']
self.data['PNL'] = ((self.data['PNL'].div(self.data['PNL'].abs())).add(1)).div(2)
#this will either be positive or negative
#not sure how this will work with regression model but needs testing

X = [self.data['BOLLINGER_METRIC'], self.data['SMA_METRIC']]
y = self.data['PNL']

X_train, X_test, y_train, y_test = train_test_split(X,y,test_size=0.25,random_state=16)
self.logreg = LogisticRegression(random_state=16)
self.logreg.fit(X_train, y_train)

#then use in the part that uses the indicators:
self.prediction = self.logreg.predict(self.data['BB_METRIC'], self.data['SMA_METRIC'])

#then self.prediction will have the values, will probably need to test which one 
#either self.prediction[0] or self.prediciton[1]
