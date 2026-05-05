# PropLogic Engine 🧠

Um motor de Lógica Proposicional interativo escrito em Python. Este projeto inclui um avaliador completo de fórmulas lógicas, conversor para formas normais, e um SAT Solver nativo baseado no algoritmo DPLL. Ele vem acompanhado de uma interface de linha de comando (CLI) amigável e colorida para facilitar o uso e o aprendizado.

Ideal para estudantes de Ciência da Computação, Matemática e entusiastas de lógica formal.

---

## ✨ Funcionalidades

O projeto é dividido em um core lógico (`logic_engine.py`) e uma interface iterativa (`menu.py`). Ele suporta as seguintes operações:

* **Tabela-Verdade e Equivalência:** Gera tabelas-verdade completas e verifica a equivalência semântica entre duas proposições ($O(2^n)$).
* **Equivalência Algébrica:** Converte fórmulas para a Forma Normal Negativa (FNN), ordenando operandos comutativos para gerar uma "chave canônica" e comparar estruturas de árvores sintáticas.
* **Conversão para FNC (Forma Normal Conjuntiva):** Transforma qualquer fórmula aplicando distributividade de $\lor$ sobre $\land$.
* **Conversão para FND (Forma Normal Disjuntiva):** Transforma qualquer fórmula aplicando distributividade de $\land$ sobre $\lor$.
* **SAT Solver (DPLL):** Avalia a satisfatibilidade de uma fórmula. Converte internamente para FNC e extrai cláusulas para aplicar o algoritmo DPLL (com propagação unitária e eliminação de literais puros).
* **Verificação de Negação:** Checa de forma rápida se uma fórmula $A$ é a negação exata de uma fórmula $B$.

---

## 📖 Sintaxe Suportada

O parser utiliza recursão à esquerda (*recursive-descent*) em uma única passagem ($O(n)$) e suporta as seguintes operações lógicas, respeitando a precedência padrão:

| Operador | Símbolo no CLI | Exemplo |
| :--- | :---: | :--- |
| **Variável** | Textos livres | `p`, `q`, `var1` |
| **Negação (NOT)** | `!` | `!p` |
| **Conjunção (AND)** | `&` | `p & q` |
| **Disjunção (OR)** | `\|` | `p \| q` |
| **Implicação (IMP)** | `->` | `p -> q` |
| **Bi-implicação (BIMP)** | `<->` | `p <-> q` |

> **Nota:** Parênteses `()` podem ser utilizados livremente para agrupar expressões e alterar a ordem de precedência. Exemplo: `!(p & q) <-> (!p | !q)`

---

## 🚀 Como usar

### Pré-requisitos
* **Python 3.10** ou superior (utiliza `match/case` e tipagem moderna).
* Nenhuma dependência externa/biblioteca adicional é necessária. O projeto utiliza apenas a biblioteca padrão do Python (`re`, `itertools`, `dataclasses`, etc).

### Executando o Menu Interativo

Clone o repositório e execute o arquivo `menu.py` no seu terminal:

```bash
# Clone o repositório
git clone [https://github.com/SEU_USUARIO/NOME_DO_REPOSITORIO.git](https://github.com/SEU_USUARIO/NOME_DO_REPOSITORIO.git)

# Entre na pasta
cd NOME_DO_REPOSITORIO

# Execute a interface
python menu.py