from django.http import FileResponse


def make_file(request, ingredients):
    output = 'Список покупок\n\n'
    output += '\n'.join(
        [f'{ingredient["ingredient__name"]}'
         f' ({ingredient["ingredient__measurement_unit"]})'
         f' - {ingredient["amount"]}'
         for ingredient in ingredients
         ]
    )
    response = FileResponse(
        output, as_attachment=True,
        filename=f'{request.user.username}_список_покупок.txt'
    )
    response['Content-Type'] = 'text/plain'
    return response
