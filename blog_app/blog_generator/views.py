from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

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