from django.shortcuts import redirect


def short_link_view(request, pk):
    print(redirect(f'/recipes/{pk}'))
    return redirect(f'/recipes/{pk}')
