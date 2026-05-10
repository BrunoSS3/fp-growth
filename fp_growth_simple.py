import re
from collections import Counter
from math import ceil
from itertools import combinations

import pandas as pd


class NoArvore:
    def __init__(self, item, quantidade, pai):
        self.item = item
        self.quantidade = quantidade
        self.pai = pai
        self.filhos = {}
        self.proximo = None

    def aumentar(self, quantidade):
        self.quantidade += quantidade


def limpar_item(item):
    item = str(item).lower().strip()
    item = re.sub(r"\s+", " ", item)
    return item


def carregar_transacoes(caminho_csv, coluna_produtos):
    df = pd.read_csv(caminho_csv)
    df.columns = [coluna.strip().lower() for coluna in df.columns]

    coluna_produtos = coluna_produtos.lower()

    if coluna_produtos not in df.columns:
        raise ValueError(f"A coluna '{coluna_produtos}' não existe.")

    transacoes = []

    for texto_produtos in df[coluna_produtos].dropna():
        produtos = re.split(r";|\|", str(texto_produtos))
        produtos_limpos = []

        for produto in produtos:
            produto_limpo = limpar_item(produto)

            if produto_limpo != "":
                produtos_limpos.append(produto_limpo)

        produtos_unicos = sorted(set(produtos_limpos))

        if produtos_unicos:
            transacoes.append(produtos_unicos)

    return transacoes


def contar_itens(transacoes):
    contador = Counter()

    for transacao in transacoes:
        for item in transacao:
            contador[item] += 1

    return contador


def filtrar_itens_frequentes(contagem_itens, total_transacoes, suporte_minimo):
    if 0 < suporte_minimo < 1:
        suporte_minimo_abs = ceil(total_transacoes * suporte_minimo)
    else:
        suporte_minimo_abs = int(suporte_minimo)

    itens_frequentes = {}

    for item, quantidade in contagem_itens.items():
        if quantidade >= suporte_minimo_abs:
            itens_frequentes[item] = quantidade

    return itens_frequentes, suporte_minimo_abs


def ordenar_transacoes(transacoes, itens_frequentes):
    transacoes_ordenadas = []

    for transacao in transacoes:
        itens_validos = []

        for item in transacao:
            if item in itens_frequentes:
                itens_validos.append(item)

        itens_validos.sort(key=lambda item: (-itens_frequentes[item], item))

        if itens_validos:
            transacoes_ordenadas.append(itens_validos)

    return transacoes_ordenadas


def criar_tabela_itens(itens_frequentes):
    tabela = {}

    for item, quantidade in itens_frequentes.items():
        tabela[item] = {
            "quantidade": quantidade,
            "primeiro_no": None
        }

    return tabela


def ligar_no_na_tabela(item, novo_no, tabela_itens):
    primeiro_no = tabela_itens[item]["primeiro_no"]

    if primeiro_no is None:
        tabela_itens[item]["primeiro_no"] = novo_no
        return

    no_atual = primeiro_no

    while no_atual.proximo is not None:
        no_atual = no_atual.proximo

    no_atual.proximo = novo_no


def inserir_transacao(transacao, raiz, tabela_itens, quantidade=1):
    no_atual = raiz

    for item in transacao:
        if item in no_atual.filhos:
            no_atual.filhos[item].aumentar(quantidade)
        else:
            novo_no = NoArvore(item, quantidade, no_atual)
            no_atual.filhos[item] = novo_no
            ligar_no_na_tabela(item, novo_no, tabela_itens)

        no_atual = no_atual.filhos[item]


def construir_fp_tree(transacoes_ordenadas, itens_frequentes):
    raiz = NoArvore(None, 0, None)
    tabela_itens = criar_tabela_itens(itens_frequentes)

    for transacao in transacoes_ordenadas:
        inserir_transacao(transacao, raiz, tabela_itens)

    return raiz, tabela_itens


def pegar_caminho_ate_raiz(no):
    caminho = []
    no_atual = no.pai

    while no_atual is not None and no_atual.item is not None:
        caminho.append(no_atual.item)
        no_atual = no_atual.pai

    caminho.reverse()
    return caminho


def criar_base_condicional(item, tabela_itens):
    base_condicional = []
    no_atual = tabela_itens[item]["primeiro_no"]

    while no_atual is not None:
        caminho = pegar_caminho_ate_raiz(no_atual)

        if caminho:
            base_condicional.append((caminho, no_atual.quantidade))

        no_atual = no_atual.proximo

    return base_condicional


def construir_arvore_condicional(base_condicional, suporte_minimo_abs):
    contagem = Counter()

    for caminho, quantidade in base_condicional:
        for item in caminho:
            contagem[item] += quantidade

    itens_frequentes = {}

    for item, quantidade in contagem.items():
        if quantidade >= suporte_minimo_abs:
            itens_frequentes[item] = quantidade

    if not itens_frequentes:
        return None, None

    raiz, tabela_itens = construir_fp_tree([], itens_frequentes)

    for caminho, quantidade in base_condicional:
        caminho_filtrado = []

        for item in caminho:
            if item in itens_frequentes:
                caminho_filtrado.append(item)

        caminho_filtrado.sort(key=lambda item: (-itens_frequentes[item], item))

        if caminho_filtrado:
            inserir_transacao(caminho_filtrado, raiz, tabela_itens, quantidade)

    return raiz, tabela_itens


def minerar_fp_growth(tabela_itens, suporte_minimo_abs, itemset_base=None, itemsets=None):
    if itemset_base is None:
        itemset_base = set()

    if itemsets is None:
        itemsets = {}

    itens = sorted(
        tabela_itens.items(),
        key=lambda item: (item[1]["quantidade"], item[0])
    )

    for item, dados in itens:
        novo_itemset = set(itemset_base)
        novo_itemset.add(item)

        itemsets[frozenset(novo_itemset)] = dados["quantidade"]

        base_condicional = criar_base_condicional(item, tabela_itens)

        _, tabela_condicional = construir_arvore_condicional(
            base_condicional,
            suporte_minimo_abs
        )

        if tabela_condicional is not None:
            minerar_fp_growth(
                tabela_condicional,
                suporte_minimo_abs,
                novo_itemset,
                itemsets
            )

    return itemsets


def gerar_regras(itemsets, total_transacoes, confianca_minima, lift_minimo=1):
    regras = []

    for itemset, suporte_itemset_abs in itemsets.items():
        if len(itemset) < 2:
            continue

        itens = sorted(itemset)

        for tamanho in range(1, len(itens)):
            for combinacao in combinations(itens, tamanho):
                antecedente = frozenset(combinacao)
                consequente = itemset - antecedente

                suporte_antecedente_abs = itemsets.get(antecedente)
                suporte_consequente_abs = itemsets.get(consequente)

                if suporte_antecedente_abs is None or suporte_consequente_abs is None:
                    continue

                suporte = suporte_itemset_abs / total_transacoes
                confianca = suporte_itemset_abs / suporte_antecedente_abs

                suporte_consequente = suporte_consequente_abs / total_transacoes
                lift = confianca / suporte_consequente

                if confianca >= confianca_minima and lift >= lift_minimo:
                    regras.append({
                        "antecedente": " + ".join(sorted(antecedente)),
                        "consequente": " + ".join(sorted(consequente)),
                        "suporte": suporte,
                        "confianca": confianca,
                        "lift": lift,
                        "recomendacao": (
                            f"Quem compra '{' + '.join(sorted(antecedente))}' "
                            f"também costuma comprar '{' + '.join(sorted(consequente))}'"
                        )
                    })

    return regras


def mostrar_resumo(transacoes, itens_frequentes, suporte_minimo_abs, itemsets, regras):
    print(f"Total de transações: {len(transacoes)}")
    print(f"Suporte mínimo absoluto: {suporte_minimo_abs}")
    print(f"Total de itens frequentes: {len(itens_frequentes)}")
    print(f"Total de itemsets frequentes: {len(itemsets)}")
    print(f"Total de regras encontradas: {len(regras)}")


def mostrar_regras(regras, limite=20):
    if not regras:
        print("\nNenhuma regra encontrada.")
        return

    df = pd.DataFrame(regras)

    df = df.sort_values(
        by=["lift", "confianca", "suporte"],
        ascending=False
    )

    df["suporte"] = df["suporte"].round(4)
    df["confianca"] = df["confianca"].round(4)
    df["lift"] = df["lift"].round(4)

    print("\nPrincipais recomendações:")
    print(
        df[
            ["recomendacao", "suporte", "confianca", "lift"]
        ].head(limite).to_string(index=False)
    )


if __name__ == "__main__":
    caminho_csv = "vendas_dataset.csv"
    coluna_produtos = "descricao_produtos"

    suporte_minimo = 0.005
    confianca_minima = 0.3
    lift_minimo = 1

    transacoes = carregar_transacoes(caminho_csv, coluna_produtos)

    contagem_itens = contar_itens(transacoes)

    itens_frequentes, suporte_minimo_abs = filtrar_itens_frequentes(
        contagem_itens,
        len(transacoes),
        suporte_minimo
    )

    transacoes_ordenadas = ordenar_transacoes(transacoes, itens_frequentes)

    raiz, tabela_itens = construir_fp_tree(
        transacoes_ordenadas,
        itens_frequentes
    )

    itemsets = minerar_fp_growth(
        tabela_itens,
        suporte_minimo_abs
    )

    regras = gerar_regras(
        itemsets,
        len(transacoes),
        confianca_minima,
        lift_minimo
    )

    mostrar_resumo(
        transacoes,
        itens_frequentes,
        suporte_minimo_abs,
        itemsets,
        regras
    )

    mostrar_regras(regras)
    