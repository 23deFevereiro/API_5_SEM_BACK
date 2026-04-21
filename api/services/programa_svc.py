from django.db.models import F

from ..models import Programa

def listar_programas(search=''):
    programas = Programa.objects.all()
    if search:
        programas = programas.filter(nome_programa__icontains=search)

    return list(programas.values('id', nome=F('nome_programa')))