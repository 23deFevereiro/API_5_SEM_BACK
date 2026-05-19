from math import ceil


def normalizar_pagina(page):
    return max(int(page), 1)


def calcular_paginacao(total_items, page, page_size):
    total_pages = ceil(total_items / page_size) if total_items > 0 else 1
    start = (page - 1) * page_size
    end = start + page_size
    return total_pages, start, end