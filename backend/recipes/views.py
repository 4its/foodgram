from django.shortcuts import redirect


def short_link_view(request, pk):
    return redirect(f'/recipes/{pk}/')
