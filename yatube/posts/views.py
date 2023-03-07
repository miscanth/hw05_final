from django.shortcuts import render, get_object_or_404
from .models import Post, Group, Follow, User
from .forms import PostForm, CommentForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from .utils import paginate
from django.views.decorators.cache import cache_page


@cache_page(20, key_prefix='index_page')
def index(request):
    """Заглавная траница с выводом всех постов"""
    posts = Post.objects.select_related('group', 'author')
    page_obj = paginate(posts, request)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    """Страница группы/сообщества с выводом всех постов (по группе)"""
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related('author')
    page_obj = paginate(posts, request)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


@login_required
def post_create(request):
    """Страница создания нового поста"""
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if request.method == 'POST':
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', post.author)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    """Страница редактирования поста"""
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    context = {
        'form': form,
        'post': post,
        'is_edit': True,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    """Страница с формой добаления комментария"""
    # Получаем пост
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        # Create Comment object but don't save to database yet
        comment = form.save(commit=False)
        comment.author = request.user
        # Assign the current post to the comment
        comment.post = post
        # Save the comment to the database
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


def post_detail(request, post_id):
    """Страница просмотра отдельного поста по id"""
    form = CommentForm(request.POST or None)
    post = get_object_or_404(Post, pk=post_id)
    context = {
        'post': post,
        'comments': post.comments.all(),
        'form': form,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def follow_index(request):
    """Страница просмотра постов авторов,
    на которых подписан текущий пользователь.
    """
    posts = Post.objects.filter(author__following__user=request.user)
    page_obj = paginate(posts, request)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    # Подписаться на автора
    following = get_object_or_404(User, username=username)
    if request.user.username != username:
        Follow.objects.get_or_create(
            user=request.user,
            author=following
        )
        return redirect('posts:profile', username=username)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    # Дизлайк, отписка
    following_author = get_object_or_404(User, username=username)
    if request.user.username != username:
        follow = Follow.objects.filter(
            user=request.user,
            author=following_author,
        ).first()
        if follow:
            follow.delete()
    return redirect('posts:profile', username=username)


def profile(request, username):
    """Страница просмотра профайла автора с выводом всех постов (по автору)"""
    author = get_object_or_404(User, username=username)
    posts = author.posts.select_related('group')
    page_obj = paginate(posts, request)
    following = request.user.is_authenticated and Follow.objects.filter(
        user=request.user,
        author=request.user,
    ).exists()
    followers = Follow.objects.filter(author=author, is_deleted=False)
    followers_count = followers.count()
    context = {
        'author': author,
        'page_obj': page_obj,
        'following': following,
        'followers_count': followers_count,
    }
    return render(request, 'posts/profile.html', context)
