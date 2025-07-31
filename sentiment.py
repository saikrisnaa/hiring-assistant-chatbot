# sentiment.py

from textblob import TextBlob

def analyze_sentiment(text):
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    if polarity > 0.2:
        return "positive"
    elif polarity < -0.2:
        return "negative"
    else:
        return "neutral"

def get_user_mood(sentiment_trend):
    if sentiment_trend.count("negative") > 2:
        return "seems a bit frustrated"
    elif sentiment_trend.count("positive") > 2:
        return "is upbeat"
    else:
        return "has a neutral approach"

def get_empathy_prefix(sentiment):
    if sentiment == "negative":
        return "I'm here to help, so please don't worry. "
    elif sentiment == "positive":
        return "That's great to hear! "
    else:
        return ""
