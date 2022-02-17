from cmath import log
from django.shortcuts import render, redirect
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login
from .forms import FeedingForm
from .models import Cat, Toy, Photo
import boto3
import uuid

# Environment Variables
S3_BASE_URL = 'https://s3.us-east-1.amazonaws.com/'
BUCKET = 'cat-collector-jb'


# Create your views here.
def signup(request):
    # handle POST requests (signing up)
    error_message = ''
    if request.method == 'POST':
        # collect form inputs
        form = UserCreationForm(request.POST) # <= fills out the form with the form values from the request
        # validate form inputs
        if form.is_valid():
        # save the new user to the database
            user = form.save()
        # log the user in
            login(request, user)
        # redirect the user to the cats index
            return redirect('index')
        else:
        # if the user form is invalid - show an error message
            error_message = 'Invalid Credentials - Please Try Again'
    # handle GET requests (navigating the user to the signup page)
    # present the user with a fresh signup form
    form = UserCreationForm()
    context = { 'form': form, 'error': error_message }
    return render(request, 'registration/signup.html', context)

def home(request):
    return render(request, 'home.html')

def about(request):
    return render(request, 'about.html')

@login_required
def cats_index(request):
    cats = Cat.objects.filter(user=request.user)
    return render(request, 'cats/index.html', { 'cats': cats })
@login_required
def cats_detail(request, cat_id):
    cat = Cat.objects.get(id=cat_id)
    # can only access the cats a user makes
    if cat.user_id != request.user.id:
        return redirect('index')
    # Get the toys the cat doesn't have
    toys_cat_doesnt_have = Toy.objects.exclude(id__in = cat.toys.all().values_list('id'))
    # instantiate FeedingForm to be rendered in the template
    feeding_form = FeedingForm()
    return render(request, 'cats/detail.html', { 
        'cat': cat, 
        'feeding_form': feeding_form,
        'toys': toys_cat_doesnt_have 
    })

class CatCreate(LoginRequiredMixin, CreateView):
    model = Cat
    fields = ('name', 'breed', 'description', 'age')
    # success_url = '/cats/'
    # template_name = 'cats/cat_form.html' Will move the form to wherever you want

    # This inherited method is called when a valid cat form is being submitted
    def form_valid(self, form):
        # Assign the logged in user (self.request.user)
        form.instance.user = self.request.user # form.instance is the cat
        # Let the CreateView do its job as usual
        return super().form_valid(form)

class CatUpdate(LoginRequiredMixin, UpdateView):
    model = Cat
    fields = ('breed', 'description', 'age')

class CatDelete(LoginRequiredMixin, DeleteView):
    model = Cat
    success_url = '/cats/'




@login_required
def toys_index(request):
    toys = Toy.objects.all()
    return render(request, 'toys/index.html', { 'toys': toys})

@login_required
def toys_detail(request, toy_id):
    toy = Toy.objects.get(id=toy_id)
    return render(request, 'toys/detail.html', { 'toy': toy })

class ToyCreate(LoginRequiredMixin, CreateView):
    model = Toy
    fields = '__all__'

class ToyUpdate(LoginRequiredMixin, UpdateView):
    model = Toy
    fields = '__all__'

class ToyDelete(LoginRequiredMixin, DeleteView):
    model = Toy
    success_url = '/toys/'



@login_required
def add_feeding(request, cat_id):
  # create the ModelForm using the data in request.POST
  form = FeedingForm(request.POST)
  # validate the form
  if form.is_valid():
    # don't save the form to the db until it
    # has the cat_id assigned
    new_feeding = form.save(commit=False)
    new_feeding.cat_id = cat_id
    new_feeding.save()
  return redirect('detail', cat_id=cat_id)


@login_required
def assoc_toy(request, cat_id, toy_id):
    Cat.objects.get(id=cat_id).toys.add(toy_id)
    return redirect('detail', cat_id=cat_id)


@login_required
def add_photo(request, cat_id):
    # collect the file asset from the request
    photo_file = request.FILES.get('photo-file', None)
    # check if file is present
    if photo_file:
        # create a reference to the s3 service from boto3
        s3 = boto3.client('s3')
        # create a unique identifier for each photo asset
        key = uuid.uuid4().hex[:6] + photo_file.name[photo_file.name.rfind('.'):]
        try:
            # attempt to upload image to AWS
            s3.upload_fileobj(photo_file, BUCKET, key)
            # build the full url string
            url = f"{S3_BASE_URL}{BUCKET}/{key}"
            # create an in-memory reference to a photo model instance
            photo = Photo(url=url, cat_id=cat_id)
            # save the instance to the database
            photo.save()
        except Exception as error:
            print('**********')
            print('An error has occurred with s3')
            print(error)
            print('**********')
    return redirect('detail', cat_id=cat_id)