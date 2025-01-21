from django.shortcuts import redirect
from django.urls import reverse


def short_link_view(request, pk):
    url = reverse(f'/recipes/{pk}')
    print(url)
    return redirect(url)
