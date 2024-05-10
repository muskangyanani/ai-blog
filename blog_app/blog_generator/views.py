from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse 
import json
from pytube import YouTube # type: ignore
from django.conf import settings
import os
import assemblyai as aai # type: ignore
import openai # type: ignore
from dotenv import load_dotenv
from .models import BlogPost
load_dotenv()

# Create your views here.
@login_required
def index(request):
  return render(request, 'index.html')

def user_login(request):
  if request.method == 'POST':
    username = request.POST['username']
    password = request.POST['password']
    user = authenticate(request, username=username, password=password)
    if user is not None:
      login(request, user)
      return redirect('/')
    else:
      error_messages = 'Invalid username or password. Please try again.'
      return render(request, 'login.html', {'error_messages': error_messages})
  return render(request, 'login.html')

def user_signup(request):
  if request.method == 'POST':
    username = request.POST['username']
    email = request.POST['email']
    password = request.POST['password']
    confirm_password = request.POST['confirm_password']
    if password == confirm_password:
      try:
        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()
        login(request, user)
        return redirect('/')
      except:
        error_messages = 'Username already exists. Please try another one.'
        return render(request, 'signup.html', {'error_messages': error_messages}) 
    else:
      error_messages = 'Passwords do not match. Please try again.'
      return render(request, 'signup.html', {'error_messages': error_messages})
  return render(request, 'signup.html')

def user_logout(request):
  logout(request)
  return redirect('/')

@csrf_exempt
def generate_blog(request):
  if request.method == 'POST':
    try:
      data = json.loads(request.body)
      yt_link = data['link']
    except (KeyError, json.JSONDecodeError):
      return JsonResponse({'error': 'Invalid data sent'}, status=400)

    # get yt title
    title = yt_title(yt_link)

    # get transcript
    transcription = get_transcription(yt_link)
    if not transcription:
      return JsonResponse({'error': " Failed to get transcript"}, status=500)

    # use OpenAI to generate the blog
    blog_content = generate_blog_from_transcription(transcription)
    if not blog_content:
      return JsonResponse({'error': " Failed to generate blog article"}, status=500)

    new_blog = BlogPost.objects.create(
      user=request.user,
      youtube_title=title,
      youtube_link=yt_link,
      generated_content=blog_content
    )
    new_blog.save()
    return JsonResponse({'title': title, 'content': blog_content})
  else:
    return JsonResponse({'error': 'Invalid request method'}, status=405)

def yt_title(link):
  yt = YouTube(link)
  title = yt.title
  return title

def download_audio(link):
  print('Downloading audio....')
  yt = YouTube(link)
  video = yt.streams.filter(only_audio=True).first()
  out_file = video.download(output_path=settings.MEDIA_ROOT)
  base, ext = os.path.splitext(out_file)
  new_file = base + '.mp3'
  os.rename(out_file, new_file)
  return new_file

def get_transcription(link):
  print('Getting transcription from AssemblyAI....')
  audio_file = download_audio(link)
  aai.settings.api_key = os.getenv('ASSEMBLYAI_API_KEY')

  transcriber = aai.Transcriber()
  transcript = transcriber.transcribe(audio_file)

  return transcript.text

def generate_blog_from_transcription(transcription):
  print('Generating blog from openAI....')
  openai.api_key = os.getenv('OPENAI_API_KEY')
  prompt = f"Based on the following transcript from a YouTube video, write a comprehensive blog article, write it based on the transcript, but dont make it look like a youtube video, make it look like a proper blog article:\n\n{transcription}\n\nArticle:"

  response = openai.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": prompt}],
    max_tokens=1000
  )
  generated_blog = response.choices[0].message.content
  return generated_blog


def blog_list(request):
  blog_articles = BlogPost.objects.filter(user=request.user)
  return render(request, "all-blogs.html", {'blog_articles': blog_articles})


def blog_detail(request, pk):
  blog_article_detail = BlogPost.objects.get(id=pk)
  if request.user == blog_article_detail.user:
    return render(request, 'blog-details.html',{'blog_article_detail': blog_article_detail})
  else:
    return redirect('/')
    