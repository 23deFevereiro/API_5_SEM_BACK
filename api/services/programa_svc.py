from ..models import Programa

def listar_programas(search=''):
    programas = Programa.objects.all()
    if search:
        programas = programas.filter(nome_programa__icontains=search)
        
    response = []
    for programa in programas:
        response.append({
            'id': programa.id,
            'nome': programa.nome_programa,
        })
        
    return response