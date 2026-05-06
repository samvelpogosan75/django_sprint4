from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import CommentForm, PostForm, ProfileEditForm
from .models import Category, Comment, Post

User = get_user_model()

POSTS_PER_PAGE = 10


def _base_post_queryset():
    return (
        Post.objects
        .select_related('author', 'category', 'location')
        .annotate(comment_count=Count('comments'))
    )


def _get_post_or_404_for_user(request, post_id):
    post = get_object_or_404(_base_post_queryset(), pk=post_id)
    now = timezone.now()
    if (
        post.pub_date > now
        or not post.is_published
        or (post.category and not post.category.is_published)
    ) and request.user != post.author:
        raise Http404
    return post


def index(request):
    post_list = (
        _base_post_queryset()
        .filter(
            is_published=True,
            pub_date__lte=timezone.now(),
            category__is_published=True,
        )
        .order_by('-pub_date')
    )

    paginator = Paginator(post_list, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'blog/index.html',
        {'page_obj': page_obj},
    )


def post_detail(request, id):
    post = _get_post_or_404_for_user(request, id)

    comments = (
        post.comments
        .select_related('author')
        .order_by('created_at')
    )

    form = CommentForm()

    return render(
        request,
        'blog/detail.html',
        {
            'post': post,
            'comments': comments,
            'form': form,
        },
    )


def category_posts(request, category_slug):
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True,
    )

    post_list = (
        _base_post_queryset()
        .filter(
            category=category,
            is_published=True,
            pub_date__lte=timezone.now(),
        )
        .order_by('-pub_date')
    )

    paginator = Paginator(post_list, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'blog/category.html',
        {
            'category': category,
            'page_obj': page_obj,
        },
    )


def profile(request, username):
    profile_user = get_object_or_404(User, username=username)

    if request.user == profile_user:
        post_list = (
            _base_post_queryset()
            .filter(author=profile_user)
            .order_by('-pub_date')
        )
    else:
        post_list = (
            _base_post_queryset()
            .filter(
                author=profile_user,
                is_published=True,
                category__is_published=True,
                pub_date__lte=timezone.now(),
            )
            .order_by('-pub_date')
        )

    paginator = Paginator(post_list, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'blog/profile.html',
        {
            'profile': profile_user,
            'page_obj': page_obj,
        },
    )


@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileEditForm(
            request.POST,
            instance=request.user,
        )
        if form.is_valid():
            form.save()
            return redirect(
                'blog:profile',
                username=request.user.username,
            )
    else:
        form = ProfileEditForm(instance=request.user)

    return render(
        request,
        'blog/user.html',
        {'form': form},
    )


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()

    return render(
        request,
        'registration/registration_form.html',
        {'form': form},
    )


@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect(
                'blog:profile',
                username=request.user.username,
            )
    else:
        form = PostForm()

    return render(
        request,
        'blog/create.html',
        {'form': form},
    )


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)

    if request.user != post.author:
        return redirect('blog:post_detail', id=post_id)

    if request.method == 'POST':
        form = PostForm(
            request.POST,
            request.FILES,
            instance=post,
        )
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', id=post_id)
    else:
        form = PostForm(instance=post)

    return render(
        request,
        'blog/create.html',
        {'form': form},
    )


@login_required
def post_delete(request, post_id):
    post = get_object_or_404(Post, pk=post_id)

    if request.user != post.author and not request.user.is_staff:
        return redirect('blog:post_detail', id=post_id)

    if request.method == 'POST':
        post.delete()
        return redirect('blog:index')

    return render(
        request,
        'blog/create.html',
        {'form': PostForm(instance=post)},
    )


@login_required
def add_comment(request, post_id):
    post = _get_post_or_404_for_user(request, post_id)

    if request.method != 'POST':
        return redirect('blog:post_detail', id=post_id)

    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()

    return redirect('blog:post_detail', id=post_id)


@login_required
def edit_comment(request, post_id, comment_id):
    comment = get_object_or_404(
        Comment,
        pk=comment_id,
        post_id=post_id,
    )

    if request.user != comment.author and not request.user.is_staff:
        return redirect('blog:post_detail', id=post_id)

    if request.method == 'POST':
        form = CommentForm(
            request.POST,
            instance=comment,
        )
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', id=post_id)
    else:
        form = CommentForm(instance=comment)

    return render(
        request,
        'blog/comment.html',
        {
            'form': form,
            'comment': comment,
        },
    )


@login_required
def delete_comment(request, post_id, comment_id):
    comment = get_object_or_404(
        Comment,
        pk=comment_id,
        post_id=post_id,
    )

    if request.user != comment.author and not request.user.is_staff:
        return redirect('blog:post_detail', id=post_id)

    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', id=post_id)

    return render(
        request,
        'blog/comment.html',
        {'comment': comment},
    )
