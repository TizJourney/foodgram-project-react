from django.shortcuts import render
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required

from django.core.paginator import Paginator

from django.shortcuts import get_object_or_404, redirect, render

from django.db.models import Q, Count

from .models import Recipe, Subscriber

from .forms import RecipeForm

RECIPE_PER_PAGE = 10


def _prepare_recipe_content(post_query, page_number, request):

    user = request.user if request.user.is_authenticated else None

    filter_query = Q()
    filter_context = {
        'breakfast': request.GET.get('breakfast', '1'),
        'lunch': request.GET.get('lunch', '1'),
        'dinner': request.GET.get('dinner', '1'),
    }
    if filter_context['breakfast'] is not '0':
        filter_query.add(Q(breakfast_tag=True), Q.OR)

    if filter_context['lunch'] is not '0':
        filter_query.add(Q(lunch_tag=True), Q.OR)

    if filter_context['dinner'] is not '0':
        filter_query.add(Q(dinner_tag=True), Q.OR)

    extended_query = post_query.filter(filter_query)

    if user is not None:
        favoriedQuery = Q(favorite_by_users__user=user)
        extended_query = (
            extended_query
            .annotate(isFavoried=Count('favorite_by_users', filter=favoriedQuery))
        )

    paginator = Paginator(extended_query, RECIPE_PER_PAGE)
    page = paginator.get_page(page_number)
    return {
        'page': page,
        'paginator': paginator,
        'filter': filter_context
    }


def index(request):
    page_number = request.GET.get('page')

    recipe_query = (
        Recipe.objects
        .all()
    )

    context = _prepare_recipe_content(
        recipe_query,
        page_number,
        request
    )
    context['title'] = 'Рецепты'

    return render(
        request,
        'recipes/recipes.html',
        context
    )


@login_required
def favorite(request):
    page_number = request.GET.get('page')

    recipe_query = (
        Recipe
        .objects
        .filter(favorite_by_users__user=request.user)

    )

    context = _prepare_recipe_content(
        recipe_query,
        page_number,
        request
    )

    context['title'] = 'Избранное'

    return render(
        request,
        'recipes/recipes.html',
        context
    )


def recipe_view(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    isFavoried = request.user and recipe.favorite_by_users.filter(
        user=request.user).exists()
    isSubscribed = request.user and recipe.author.subscribed_by_user.filter(
        subscriber=request.user).exists()

    context = {
        'recipe': recipe,
        'isFavoried': isFavoried,
        'isSubscribed': isSubscribed,
    }
    return render(request, 'recipes/singlePage.html', context)


@login_required
def new_recipe(request):
    if request.method == 'POST':
        form = RecipeForm(request.POST, files=request.FILES or None)
        if form.is_valid():
            form.instance.author = request.user
            form.save()
            return redirect('index')

        return render(
            request,
            'recipes/new.html',
            {'form': form}
        )

    form = RecipeForm()
    return render(request, 'recipes/new.html', {'form': form})
