from django.contrib.auth import authenticate
from django.contrib import messages
from django.shortcuts import render, redirect, reverse


def login(request):
    if request.method == 'GET':
        return render(request, 'login.html')
    user = authenticate(username=request.POST.get("username"), password=request.POST.get("password"))
    if user is not None:
        # the password verified for the user
        if user.is_active:
            messages.info(request, "User is valid, active and authenticated")
            return redirect(reverse('index'))
        else:
            messages.error(request, "The password is valid, but the account has been disabled!")
    else:
        # the authentication system was unable to verify the username and password
        messages.error(request, "The username and password were incorrect.")
    return render(request, 'login.html')


def index(request):
    return render(request, 'index.html')
