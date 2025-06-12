from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import BrowsingHistory
from datetime import datetime
from django.shortcuts import render,redirect
import openai

from .ml_model import classify_query

from .ml_model import get_cumulative_sentiment_score

from .forms import SignUpForm
from django.contrib import messages

from twilio.rest import Client 

from django.contrib.auth.forms import AuthenticationForm

from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from urllib.parse import quote

from .models import AlertControl
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.db.models import Q
from datetime import timedelta
from decouple import config

@csrf_exempt
def track_url(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        url = data.get('url')
        query = data.get('query', '')
        time_spent = data.get('time_spent', 0)

        mental_state, confidence = classify_query(query)

        BrowsingHistory.objects.create(
            url=url,
            query=query,
            time_spent=time_spent,
            mental_state=mental_state,
            sentiment_score=confidence
        )

        return JsonResponse({'status': 'success', 'mental_state': str(mental_state),
    'confidence': float(confidence)})
    
    return JsonResponse({'status': 'invalid request'})

def dashboard(request):
    history = BrowsingHistory.objects.all().order_by('-timestamp')
    return render(request, 'dashboard.html', {'history': history})

def make_automated_call(to_number):
    account_sid = ''  # Replace with your Twilio Account SID
    auth_token = ''    # Replace with your Twilio Auth Token
    from_number = ''  # Replace with your Twilio number (e.g., '+12065550100')
    twiml_url = "http://demo.twilio.com/docs/voice.xml"

    client = Client(account_sid, auth_token)

    try:
        call = client.calls.create(
            to=to_number,
            from_=from_number,  # your Twilio number
            url=twiml_url
        )
        print("Call initiated:", call.sid)
    except Exception as e:
        print("Twilio call failed:", e)




def sentiment_score_view(request):
    all_queries = BrowsingHistory.objects.values_list('query', flat=True)
    score = get_cumulative_sentiment_score(all_queries)
    return JsonResponse({
        'status': 'success',
        'cumulative_sentiment_score': score
    })

from django.core.mail import send_mail

@login_required(login_url='login')
def sentiment_dashboard(request):
    history = BrowsingHistory.objects.all().order_by('-timestamp')

    # GET parameters
    search_query = request.GET.get('query', '')
    search_date = request.GET.get('date', '')

    if search_query:
        history = history.filter(query__icontains=search_query)

    if search_date:
        parsed_date = parse_date(search_date)
        if parsed_date:
            history = history.filter(timestamp__date=parsed_date)

    filtered_history = history.exclude(mental_state='1')

    control, _ = AlertControl.objects.get_or_create(id=1)
    reset_time = control.reset_timestamp
    now = timezone.now()

    recent_entries = filtered_history.filter(timestamp__gt=reset_time)
    cumulative_score = sum(entry.sentiment_score for entry in recent_entries)

    # Threshold levels
    threshold_email = 10.0
    threshold_sms = 20.0
    threshold_call = 30.0
    email_interval = timedelta(minutes=5)

    recent_negative_queries = BrowsingHistory.objects.filter(
        timestamp__gt=control.reset_timestamp
    ).exclude(mental_state='1').values_list('query', flat=True)

    if (
        control.is_active and 
        cumulative_score > threshold_email and 
        now - control.last_email_sent >= email_interval
    ):
        if recent_negative_queries:
            queries_text = "\n".join(recent_negative_queries)
            prompt = f"""Here are some negative browsing queries:\n{queries_text}\nBased on these, give me personalized mental health advice."""
            encoded_prompt = quote(prompt)
            insight_link = f"https://chat.openai.com/?model=gpt-4&prompt={encoded_prompt}"

            send_mail(
                subject='🚨 Mental Health Alert',
                message=f'''
Cumulative sentiment score has crossed the threshold!

Current score: {cumulative_score}

Want personalized mental health insights based on your recent activity?
Click here: {insight_link}
''',
                from_email = config('FROM_EMAIL'),
                recipient_list = config('RECIPIENT_LIST').split(','),
                fail_silently=False,
            )

            if cumulative_score > threshold_sms:
                print("SMS alert skipped (A2P registration not enabled)")

            print("Triggering automated call...")
            if cumulative_score > threshold_call:
                make_automated_call('')#Replace with the recieveing number

            control.last_email_sent = now
            control.save()
        else:
            print("No negative queries found after last reset.")

    return render(request, 'sentiment_dashboard.html', {
        'history': history,
        'cumulative_score': cumulative_score,
        'request': request  # To access query/date in the template
    })


def home_page(request):
    return render(request, 'home.html')


def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.set_password(form.cleaned_data['password'])
            user.save()
            messages.success(request, "Sign up successful! Please log in.")
            return redirect('login')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect('home_page')  # Or your intended redirect page
        else:
            messages.error(request, "Invalid credentials.")
    else:
        form = AuthenticationForm()

    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('home_page') 

def reset_alerts(request):
    control, _ = AlertControl.objects.get_or_create(pk=1)
    control.reset_timestamp = timezone.now()
    control.last_email_sent = timezone.now()
    control.save()

    # Redirect back to the same page
    return redirect(request.META.get('HTTP_REFERER', 'sentiment_dashboard'))

def stop_alerts(request):
    control, _ = AlertControl.objects.get_or_create(pk=1)
    control.is_active = False
    control.save()
    return redirect('sentiment_dashboard')

@login_required(login_url='login')
def sentiment_visual(request):
    history = BrowsingHistory.objects.all().order_by('-timestamp')
    filtered_history = history.exclude(mental_state='1')

    # Get reset timestamp
    control, _ = AlertControl.objects.get_or_create(id=1)
    reset_time = control.reset_timestamp

    # Apply reset time filter
    recent_entries = filtered_history.filter(timestamp__gt=reset_time)
    cumulative_score = sum(entry.sentiment_score for entry in recent_entries)

    positive_count = 0
    neutral_count = 0
    negative_count = 0

    table_data = []
    for entry in history:  # Show full history in table
        table_data.append({
            'query': entry.query,
            'score': entry.sentiment_score,
            'mental_state': entry.mental_state
        })

        if entry.mental_state == '1':
            if entry.sentiment_score > 0.5:
                positive_count += 1
            else:
                neutral_count += 1
        else:
            negative_count += 1

    # Use only filtered recent entries for visualization
    queries = [entry.query for entry in recent_entries]
    scores = [entry.sentiment_score for entry in recent_entries]
    if sum(scores) < 5:
        msg= "There is no need to worry. Everything seems normal."
    elif 5 <= sum(scores) < 10:
        msg= "There may be early signs of depression. Consider observing closely."
    elif 10 <= sum(scores)< 15:
        msg="There is an accurate chance of depression. Please consider talking to someone."
    elif 15 <= sum(scores) <= 20:
        msg="Definitely depression. Seeking professional help is strongly recommended."
    else:  # score > 20
        msg= "High time alert! Immediate professional intervention is necessary."

    return render(request, 'sentiment_visual.html', {
        'table_data': table_data,
        'queries': queries,
        'scores': scores,
        'cumulative_score': cumulative_score,
        'positive_count': positive_count,
        'neutral_count': neutral_count,
        'negative_count': negative_count,
        'message':msg
    })

@login_required(login_url='login')
def insights_page(request):
    all_queries = BrowsingHistory.objects.values_list('query', flat=True)
    combined_queries = "\n".join(all_queries)

    # Call ChatGPT API
    openai.api_key = 'YOUR_OPENAI_API_KEY'

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful mental health assistant."},
            {"role": "user", "content": f"Give me some mental health insights based on these browsing queries:\n{combined_queries}"}
        ]
    )

    chatgpt_insights = response['choices'][0]['message']['content']

    return render(request, 'insights.html', {'insights': chatgpt_insights})