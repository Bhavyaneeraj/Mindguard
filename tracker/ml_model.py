import joblib
import re

# Load the model and vectorizer
model = joblib.load('tracker/saved_model/logistic_regression_model.pkl')
vectorizer = joblib.load('tracker/saved_model/tfidf_vectorizer.pkl')

# Text cleaning function
def clean_text(text):
    text = re.sub(r'[^\w\s]', '', text.lower())
    return text

# Prediction function
def classify_query(text):
    cleaned = clean_text(text)
    vectorized = vectorizer.transform([cleaned])
    prediction = model.predict(vectorized)[0]
    probabilities = model.predict_proba(vectorized)[0]
    max_prob = max(probabilities)

    return prediction, round(max_prob, 2)


from textblob import TextBlob

def get_cumulative_sentiment_score(queries):
    if not queries:
        return 0.0
    
    total_score = 0
    for q in queries:
        blob = TextBlob(q)
        total_score += blob.sentiment.polarity  # ranges from -1 (negative) to 1 (positive)

    normalized_score = (total_score + len(queries)) / (2 * len(queries))  # Normalize to [0, 1]
    return round(normalized_score, 2)

