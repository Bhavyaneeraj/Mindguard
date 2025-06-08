import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
import pickle

dataset = pd.read_csv(r'C:\Users\Bannu\Desktop\browser_tracker\sentiment-analysis-for-mental-health-Combined Data.csv')

texts = dataset['statement'].fillna("").astype(str)  
labels = dataset['status']

label_names = labels.unique().tolist()
label2id = {label: i for i, label in enumerate(label_names)}
id2label = {i: label for label, i in label2id.items()}
labels = labels.map(label2id)


train_texts, val_texts, train_labels, val_labels = train_test_split(texts, labels, test_size=0.2, random_state=42)


vectorizer = TfidfVectorizer(max_features=10000, ngram_range=(1, 2))
train_features = vectorizer.fit_transform(train_texts)
val_features = vectorizer.transform(val_texts)

classifier = LogisticRegression(max_iter=1000)
classifier.fit(train_features, train_labels)

val_predictions = classifier.predict(val_features)

accuracy = accuracy_score(val_labels, val_predictions)
print(f"Model Accuracy: {accuracy:.4f}")

with open("saved_model/logistic_regression_model.pkl", "wb") as model_file:
    pickle.dump(classifier, model_file)

with open("saved_model/tfidf_vectorizer.pkl", "wb") as vectorizer_file:
    pickle.dump(vectorizer, vectorizer_file)

print("✅ Model training complete and saved in 'saved_model/'")
