from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post

User = get_user_model()


def paginator_for_all(data_for_paginator, request):
    post_on_page = 10
    paginator = Paginator(data_for_paginator, post_on_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return {
        'paginator': paginator,
        'page_number': page_number,
        'page_obj': page_obj,
    }


def index(request):
    posts = Post.objects.all()
    title = 'Это главная страница проекта Yatube'
    context = {
        'posts': posts,
        'title': title,
    }
    context.update(paginator_for_all(posts, request))
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    title = 'Здесь будет информация о группах проекта Yatube'
    context = {
        'group': group,
        'posts': posts,
        'title': title,
    }
    context.update(paginator_for_all(posts, request))
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_author = Post.objects.filter(author=author)
    title = f' Профиль пользователя {author.get_full_name()}'
    following = request.user.is_authenticated and Follow.objects.filter(
        user=request.user,
        author__username=username).exists()
    context = {
        'author': author,
        'post_author': post_author,
        'title': title,
        'following': following,
    }
    context.update(paginator_for_all(post_author, request))
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post_list = Post.objects.get(pk=post_id)
    title = 'Подробнее о посте'
    form = CommentForm(request.POST or None)
    comments = post_list.comments.all()
    is_edit = True
    context = {
        'post_list': post_list,
        'title': title,
        'form': form,
        'comments': comments,
        'is_edit': is_edit,
    }
    return render(request, 'posts/post_detail.html', context)


def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if not request.method == 'POST':
        return render(request, 'posts/create_post.html', {'form': form})
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {'form': form})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:profile', request.user.username)


def post_edit(request, post_id):
    post_data = Post.objects.get(pk=post_id)
    form = PostForm(instance=post_data, files=request.FILES or None,)
    is_edit = True
    if request.method == 'POST':
        form = PostForm(request.POST, instance=post_data)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            form.save()
            return redirect('posts:post_detail', post_id)
    context = {
        'form': form,
        'is_edit': is_edit,
    }
    return render(
        request, 'posts/create_post.html', context
    )


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    posts_author = Post.objects.filter(
        author__following__user=request.user
    )
    title = 'Страница с избранными авторами'
    paginator = Paginator(posts_author, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {
        'title': title,
        'paginator': paginator,
        'page': page,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    follow_user = get_object_or_404(User, username=username)
    if request.user != follow_user:
        Follow.objects.get_or_create(user=request.user, author=follow_user)
    return redirect('posts:profile', username=username)
# @login_required
# def profile_follow(request, username):
#     user = request.user
#     author = User.objects.get(username=username)
#     is_follower = Follow.objects.filter(user=user, author=author)
#     if user != author and not is_follower.exists():
#         Follow.objects.create(user=user, author=author)
#     return redirect('posts:profile', username=author)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    is_follower = Follow.objects.filter(user=request.user, author=author)
    if is_follower.exists():
        is_follower.delete()
    return redirect('posts:profile', username=username)
# @login_required
# def profile_follow(request, username):
#     follow_author = get_object_or_404(User, username=username)
#     if request.user != follow_author:
#         Follow.objects.get_or_create(
#             user=request.user,
#             author=follow_author,
#         )
#     return redirect('posts:profile', username=username)


# @login_required
# def profile_unfollow(request, username):
#     unfollow_author = get_object_or_404(User, username=username)
#     get_object_or_404(
#         Follow,
#         user=request.user,
#         author=unfollow_author
#     ).delete()
#     return redirect('posts:profile', username=username)
