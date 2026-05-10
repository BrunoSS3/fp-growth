import re
from pathlib import Path
from collections import Counter
from math import ceil
from itertools import combinations

import pandas as pd


class NoFPTree:
    def __init__(self, item, contador, pai):
        self.item = item
        self.contador = contador
        self.pai = pai
        self.filhos = {}
        self.proximo_no = None

    def incrementar(self, quantidade=1):
        self.contador += quantidade


def limpar_nome_item(item):
    item = str(item).lower()
    item = item.strip()
    item = re.sub(r"\s+", " ", item)
    return item


def separar_itens(valor):
    valor = str(valor)
    itens = re.split(r";|\|", valor)

    itens_limpos = []

    for item in itens:
        item_limpo = limpar_nome_item(item)

        if item_limpo != "":
            itens_limpos.append(item_limpo)

    return itens_limpos


def carregar_dataset(caminho_arquivo):
    caminho = Path(caminho_arquivo)
    extensao = caminho.suffix.lower()

    if extensao == ".csv":
        return pd.read_csv(caminho)

    if extensao in [".xlsx", ".xls"]:
        return pd.read_excel(caminho)

    raise ValueError("Formato não suportado.")


def preparar_transacoes(caminho_arquivo, coluna_lista_itens):
    df = carregar_dataset(caminho_arquivo)

    df.columns = [coluna.strip().lower() for coluna in df.columns]
    coluna_lista_itens = coluna_lista_itens.lower()

    if coluna_lista_itens not in df.columns:
        raise ValueError(f"A coluna '{coluna_lista_itens}' não existe no dataset.")

    transacoes = []

    for valor in df[coluna_lista_itens].dropna():
        itens = separar_itens(valor)
        itens_unicos = sorted(set(itens))

        if itens_unicos:
            transacoes.append(itens_unicos)

    return transacoes


def mostrar_resumo_transacoes(transacoes):
    print(f"Total de transações: {len(transacoes)}")

    total_itens = sum(len(transacao) for transacao in transacoes)
    print(f"Total de itens nas transações: {total_itens}")

    produtos_unicos = set()

    for transacao in transacoes:
        for item in transacao:
            produtos_unicos.add(item)

    print(f"Total de produtos únicos: {len(produtos_unicos)}")

    print("\nExemplos de transações:")

    for transacao in transacoes[:5]:
        print(transacao)


def contar_frequencia_itens(transacoes):
    frequencia_itens = Counter()

    for transacao in transacoes:
        for item in transacao:
            frequencia_itens[item] += 1

    return frequencia_itens


def mostrar_itens_mais_frequentes(frequencia_itens, limite=20):
    print("\nItens mais frequentes:")

    for item, frequencia in frequencia_itens.most_common(limite):
        print(f"{item}: {frequencia}")


def calcular_suporte_minimo_absoluto(total_transacoes, min_support):
    if 0 < min_support < 1:
        return ceil(total_transacoes * min_support)

    return int(min_support)


def filtrar_itens_por_suporte(frequencia_itens, total_transacoes, min_support):
    suporte_minimo_absoluto = calcular_suporte_minimo_absoluto(
        total_transacoes,
        min_support
    )

    itens_frequentes = {}

    for item, frequencia in frequencia_itens.items():
        if frequencia >= suporte_minimo_absoluto:
            itens_frequentes[item] = frequencia

    return itens_frequentes, suporte_minimo_absoluto


def mostrar_resumo_suporte(itens_frequentes, suporte_minimo_absoluto):
    print(f"\nSuporte mínimo absoluto: {suporte_minimo_absoluto}")
    print(f"Total de itens frequentes: {len(itens_frequentes)}")


def ordenar_transacoes_por_frequencia(transacoes, itens_frequentes):
    transacoes_ordenadas = []

    for transacao in transacoes:
        itens_validos = []

        for item in transacao:
            if item in itens_frequentes:
                itens_validos.append(item)

        itens_ordenados = sorted(
            itens_validos,
            key=lambda item: (-itens_frequentes[item], item)
        )

        if itens_ordenados:
            transacoes_ordenadas.append(itens_ordenados)

    return transacoes_ordenadas


def criar_header_table(itens_frequentes):
    header_table = {}

    itens_ordenados = sorted(
        itens_frequentes.items(),
        key=lambda item: (-item[1], item[0])
    )

    for item, frequencia in itens_ordenados:
        header_table[item] = {
            "frequencia": frequencia,
            "primeiro_no": None,
            "ultimo_no": None
        }

    return header_table


def criar_filho(no_pai, item, quantidade):
    no_filho = NoFPTree(item, quantidade, no_pai)
    no_pai.filhos[item] = no_filho
    return no_filho


def atualizar_header_table(item, novo_no, header_table):
    if header_table[item]["primeiro_no"] is None:
        header_table[item]["primeiro_no"] = novo_no
        header_table[item]["ultimo_no"] = novo_no
    else:
        header_table[item]["ultimo_no"].proximo_no = novo_no
        header_table[item]["ultimo_no"] = novo_no


def inserir_transacao_na_arvore(transacao, raiz, header_table, quantidade=1):
    no_atual = raiz

    for item in transacao:
        if item in no_atual.filhos:
            no_atual.filhos[item].incrementar(quantidade)
        else:
            novo_no = criar_filho(no_atual, item, quantidade)
            atualizar_header_table(item, novo_no, header_table)

        no_atual = no_atual.filhos[item]


def construir_fp_tree(transacoes_ordenadas, itens_frequentes):
    raiz = NoFPTree(None, 1, None)
    header_table = criar_header_table(itens_frequentes)

    for transacao in transacoes_ordenadas:
        inserir_transacao_na_arvore(transacao, raiz, header_table)

    return raiz, header_table


def contar_nos_arvore(no):
    total = 1

    for filho in no.filhos.values():
        total += contar_nos_arvore(filho)

    return total


def mostrar_resumo_fp_tree(raiz, header_table):
    total_nos = contar_nos_arvore(raiz) - 1

    print("\nResumo da FP-Tree:")
    print(f"Total de nós: {total_nos}")
    print(f"Itens na header table: {len(header_table)}")


def obter_caminho_prefixo(no):
    caminho = []
    no_atual = no.pai

    while no_atual is not None and no_atual.item is not None:
        caminho.append(no_atual.item)
        no_atual = no_atual.pai

    caminho.reverse()
    return caminho


def obter_base_condicional(item, header_table):
    base_condicional = []
    no_atual = header_table[item]["primeiro_no"]

    while no_atual is not None:
        caminho = obter_caminho_prefixo(no_atual)

        if caminho:
            base_condicional.append((caminho, no_atual.contador))

        no_atual = no_atual.proximo_no

    return base_condicional


def contar_frequencia_condicional(base_condicional):
    frequencia = Counter()

    for caminho, quantidade in base_condicional:
        for item in caminho:
            frequencia[item] += quantidade

    return frequencia


def construir_fp_tree_condicional(base_condicional, suporte_minimo_absoluto):
    frequencia_condicional = contar_frequencia_condicional(base_condicional)

    itens_frequentes_condicionais = {}

    for item, frequencia in frequencia_condicional.items():
        if frequencia >= suporte_minimo_absoluto:
            itens_frequentes_condicionais[item] = frequencia

    if not itens_frequentes_condicionais:
        return None, None

    header_table_condicional = criar_header_table(itens_frequentes_condicionais)
    raiz_condicional = NoFPTree(None, 1, None)

    for caminho, quantidade in base_condicional:
        caminho_filtrado = []

        for item in caminho:
            if item in itens_frequentes_condicionais:
                caminho_filtrado.append(item)

        caminho_ordenado = sorted(
            caminho_filtrado,
            key=lambda item: (-itens_frequentes_condicionais[item], item)
        )

        if caminho_ordenado:
            inserir_transacao_na_arvore(
                caminho_ordenado,
                raiz_condicional,
                header_table_condicional,
                quantidade
            )

    return raiz_condicional, header_table_condicional


def minerar_fp_tree(header_table, suporte_minimo_absoluto, sufixo=None, itemsets=None):
    if sufixo is None:
        sufixo = set()

    if itemsets is None:
        itemsets = {}

    itens_ordenados = sorted(
        header_table.items(),
        key=lambda item: (item[1]["frequencia"], item[0])
    )

    for item, dados in itens_ordenados:
        novo_itemset = set(sufixo)
        novo_itemset.add(item)

        itemsets[frozenset(novo_itemset)] = dados["frequencia"]

        base_condicional = obter_base_condicional(item, header_table)

        raiz_condicional, header_table_condicional = construir_fp_tree_condicional(
            base_condicional,
            suporte_minimo_absoluto
        )

        if header_table_condicional is not None:
            minerar_fp_tree(
                header_table_condicional,
                suporte_minimo_absoluto,
                novo_itemset,
                itemsets
            )

    return itemsets


def gerar_subconjuntos(itemset):
    itemset = sorted(itemset)
    subconjuntos = []

    for tamanho in range(1, len(itemset)):
        for combinacao in combinations(itemset, tamanho):
            subconjuntos.append(frozenset(combinacao))

    return subconjuntos


def calcular_suporte(suporte_absoluto, total_transacoes):
    return suporte_absoluto / total_transacoes


def gerar_regras_associacao(itemsets_frequentes, total_transacoes, min_confidence):
    regras = []

    for itemset, suporte_itemset_abs in itemsets_frequentes.items():
        if len(itemset) < 2:
            continue

        subconjuntos = gerar_subconjuntos(itemset)

        for antecedente in subconjuntos:
            consequente = itemset - antecedente

            if not consequente:
                continue

            suporte_antecedente_abs = itemsets_frequentes.get(antecedente)
            suporte_consequente_abs = itemsets_frequentes.get(consequente)

            if not suporte_antecedente_abs or not suporte_consequente_abs:
                continue

            suporte = calcular_suporte(
                suporte_itemset_abs,
                total_transacoes
            )

            suporte_antecedente = calcular_suporte(
                suporte_antecedente_abs,
                total_transacoes
            )

            suporte_consequente = calcular_suporte(
                suporte_consequente_abs,
                total_transacoes
            )

            confianca = suporte / suporte_antecedente
            lift = confianca / suporte_consequente

            if confianca >= min_confidence:
                regras.append({
                    "antecedente": tuple(sorted(antecedente)),
                    "consequente": tuple(sorted(consequente)),
                    "suporte": suporte,
                    "confianca": confianca,
                    "lift": lift
                })

    return regras


def mostrar_itemsets_frequentes(itemsets, limite=20):
    print("\nItemsets frequentes:")

    itemsets_ordenados = sorted(
        itemsets.items(),
        key=lambda item: (-item[1], sorted(item[0]))
    )

    for itemset, suporte in itemsets_ordenados[:limite]:
        print(f"{set(itemset)}: {suporte}")


def formatar_itemset(itemset):
    return " + ".join(itemset)


def mostrar_regras(regras, limite=20):
    df_regras = pd.DataFrame(regras)

    if df_regras.empty:
        print("\nNenhuma regra encontrada.")
        return

    df_regras = df_regras.sort_values(
        by=["lift", "confianca", "suporte"],
        ascending=False
    )

    df_regras["antecedente"] = df_regras["antecedente"].apply(formatar_itemset)
    df_regras["consequente"] = df_regras["consequente"].apply(formatar_itemset)

    df_regras["recomendacao"] = df_regras.apply(
        lambda linha: (
            f"Quem compra '{linha['antecedente']}' "
            f"também costuma comprar '{linha['consequente']}'"
        ),
        axis=1
    )

    df_regras["suporte"] = df_regras["suporte"].round(4)
    df_regras["confianca"] = df_regras["confianca"].round(4)
    df_regras["lift"] = df_regras["lift"].round(4)

    colunas = [
        "recomendacao",
        "suporte",
        "confianca",
        "lift"
    ]

    print("\nRegras de associação encontradas:")
    print(df_regras[colunas].head(limite).to_string(index=False))


if __name__ == "__main__":
    min_support = 0.005
    min_confidence = 0.3

    transacoes = preparar_transacoes(
        caminho_arquivo="vendas_dataset.csv",
        coluna_lista_itens="descricao_produtos"
    )

    mostrar_resumo_transacoes(transacoes)

    frequencia_itens = contar_frequencia_itens(transacoes)

    mostrar_itens_mais_frequentes(frequencia_itens)

    itens_frequentes, suporte_minimo_absoluto = filtrar_itens_por_suporte(
        frequencia_itens,
        len(transacoes),
        min_support
    )

    mostrar_resumo_suporte(itens_frequentes, suporte_minimo_absoluto)

    transacoes_ordenadas = ordenar_transacoes_por_frequencia(
        transacoes,
        itens_frequentes
    )

    raiz, header_table = construir_fp_tree(
        transacoes_ordenadas,
        itens_frequentes
    )

    mostrar_resumo_fp_tree(raiz, header_table)

    itemsets_frequentes = minerar_fp_tree(
        header_table,
        suporte_minimo_absoluto
    )

    mostrar_itemsets_frequentes(itemsets_frequentes)

    regras = gerar_regras_associacao(
        itemsets_frequentes,
        len(transacoes),
        min_confidence
    )

    mostrar_regras(regras)