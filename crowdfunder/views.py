from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from crowdfunder.forms import LoginForm
from .models import *
from .forms import *

def home(request):
    return render(request, 'index.html', {
        'projects': Project.objects.all().order_by('-id')[:9]
    })

def profile(request, user_id):
    user = User.objects.get(id=user_id)
    owned_projects = user.projects.all()
    # backed_projects = [d.project for d in user.donations.all()]
    funded_count = [p.met_goal for p in owned_projects].count(True)
    donations = user.donations.all()

    return render(request, "profile.html", {
        'user': user,
        'owned_projects': owned_projects,
        'donations': donations,
        'funded_count': funded_count,
    })

def login_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('')
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            pw = form.cleaned_data['password']
            user = authenticate(username=username, password=pw)
            if user is not None:
                login(request, user)
                return HttpResponseRedirect('')
            else:
                form.add_error('username', 'Login failed')
    else:
        form = LoginForm()
    context = {'title': 'Log in', 'form': form}
    http_response = render(request, 'login.html', context)
    return HttpResponse(http_response)

def logout_view(request):
    logout(request)
    return HttpResponseRedirect('')

def signup(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('')
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return HttpResponseRedirect('')
    else:
        form = UserCreationForm()
    html_response =  render(request, 'signup.html', {'title': 'Sign up', 'form': form})
    return HttpResponse(html_response)
    
def project_detail(request, id):
    project = get_object_or_404(Project, pk=id)
    existing_donation = project.donations.filter(user=request.user)

    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            new_comment = form.save()
            return redirect('project_detail', id=id)
    else:
        form = CommentForm(initial={'user': request.user, 'project':project})

    context = {'project': project, 'existing_donation': existing_donation, 'form': form}
    return render(request, 'project_detail.html', context)

@login_required
def create_project(request):
    form = CreateProject(request.POST)
    if form.is_valid():
        new_project = form.instance
        new_project.user = request.user
        new_project.save()
        return HttpResponseRedirect("/")
    else:
        html_string = render(request, 'create_project.html', {'title': 'Create a new project', 'form': CreateProject(request.POST)})
        return HttpResponse(html_string)
        form = CreateProject()

    context = {'form': form}
    return render(request, 'create_project.html', context)

@login_required
def donate(request, id):
    project = get_object_or_404(Project, pk=id)

    if request.method == "POST":
        form = MakeDonation(request.POST)
        if form.is_valid():
            new_donation = form.save()
            project.update_total_funded()
            project.update_total_backers()
            return redirect('project_detail', id=id)
    else:
        form = MakeDonation(initial={'user': request.user, 'project':project})

    context = {'form': form, 'project': project}
    return render(request, 'make_donation.html', context)
    
def profile_view(request):
    context = {'profiles': Profile.objects.all()}
    response = render(request, 'profile.html', context)
    return HttpResponse(response)

def category(request, cat):
    category_projects = get_list_or_404(Project, category=cat)
    context = {'category': cat, 'projects': category_projects}
    return render(request, 'category_list.html', context)

def projects_by_owner(request, id):
    owner = get_object_or_404(User, pk=id)
    context = {'owner': owner}
    return render(request, 'owner_projects.html', context)

def search_results(request):
    query = request.GET["query"]
    search_results = (Project.objects.filter(title__icontains=query))
    context = {"projects": search_results, "query": query}
    return render(request, "search_results.html", context)
    
