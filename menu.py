
from logic_engine import (
    parse, to_str, variables,
    truth_table_equiv, algebraic_equiv,
    to_cnf, to_dnf,
    is_satisfiable,
    are_negations,
    build_truth_table,
)

# ── Formatação ────────────────────────────────────────────────────────────────

VERDE   = "\033[92m"
VERMELHO= "\033[91m"
AMARELO = "\033[93m"
AZUL    = "\033[94m"
CINZA   = "\033[90m"
BOLD    = "\033[1m"
RESET   = "\033[0m"

def cor(texto, c):       return f"{c}{texto}{RESET}"
def titulo(texto):       print(f"\n{BOLD}{AZUL}{'─'*50}{RESET}")  ; print(f"{BOLD}{AZUL}  {texto}{RESET}") ; print(f"{BOLD}{AZUL}{'─'*50}{RESET}")
def secao(texto):        print(f"\n{AMARELO}{BOLD}{texto}{RESET}")
def ok(texto):           print(f"  {VERDE}✓{RESET}  {texto}")
def erro(texto):         print(f"  {VERMELHO}✗{RESET}  {texto}")
def info(texto):         print(f"  {CINZA}{texto}{RESET}")

def exibir_formula(rotulo, node):
    print(f"  {CINZA}{rotulo}:{RESET}  {BOLD}{to_str(node)}{RESET}")

# ── Entrada segura ────────────────────────────────────────────────────────────

def ler_formula(prompt):
    while True:
        raw = input(f"\n  {AMARELO}→{RESET} {prompt}: ").strip()
        if not raw:
            erro("Entrada vazia. Tente novamente.")
            continue
        try:
            node = parse(raw)
            exibir_formula("Lida como", node)
            return node
        except SyntaxError as e:
            erro(f"Erro de sintaxe: {e}")
            info("Exemplo válido: p -> q   |   !(p & q)   |   p <-> q")

def pausar():
    input(f"\n  {CINZA}[Enter para continuar]{RESET}")

# ── Tabela-verdade visual ─────────────────────────────────────────────────────

def imprimir_tabela(headers, rows, destacar_col=None):
    col_w = max(len(h) for h in headers) + 2
    col_w = max(col_w, 7)

    header_line = "  " + "  ".join(h.center(col_w) for h in headers)
    print(f"\n{BOLD}{header_line}{RESET}")
    print("  " + "─" * (col_w * len(headers) + 2 * len(headers)))

    for row in rows:
        cells = []
        for i, val in enumerate(row):
            label = "V" if val else "F"
            if i == len(row) - 1 or (destacar_col and headers[i] == destacar_col):
                label = cor(label.center(col_w), VERDE if val else VERMELHO)
            else:
                label = label.center(col_w)
            cells.append(label)
        print("  " + "  ".join(cells))

# ── Tarefas ───────────────────────────────────────────────────────────────────

def tarefa_equivalencia_tt():
    titulo("1 · Equivalência por Tabela-Verdade")
    info("Sintaxe: ! (NOT)   & (AND)   | (OR)   -> (→)   <-> (↔)")
    a = ler_formula("Fórmula A")
    b = ler_formula("Fórmula B")

    equiv, contraexemplos = truth_table_equiv(a, b)

    secao("Tabela-Verdade Combinada")
    all_vars = list(dict.fromkeys(variables(a) + variables(b)))
    from itertools import product as iproduct
    from logic_engine import evaluate
    headers = all_vars + ["A", "B"]
    rows = []
    for vals in iproduct([False, True], repeat=len(all_vars)):
        asgn = dict(zip(all_vars, vals))
        rows.append(vals + (evaluate(a, asgn), evaluate(b, asgn)))
    imprimir_tabela(headers, rows)

    secao("Resultado")
    if equiv:
        ok(f"{BOLD}As fórmulas SÃO equivalentes.{RESET}")
    else:
        erro(f"{BOLD}As fórmulas NÃO são equivalentes.{RESET}")
        print(f"  {len(contraexemplos)} contraexemplo(s) encontrado(s):")
        for cex in contraexemplos[:5]:
            vals = {k: ("V" if v else "F") for k, v in cex.items()}
            print(f"    {CINZA}{vals}{RESET}")


def tarefa_equivalencia_alg():
    titulo("2 · Equivalência Algébrica")
    info("Normaliza ambas para FNN e compara chaves canônicas.")
    a = ler_formula("Fórmula A")
    b = ler_formula("Fórmula B")

    equiv, chave_a, chave_b = algebraic_equiv(a, b)

    secao("Passos")
    from logic_engine import to_nnf
    info(f"FNN de A : {to_str(to_nnf(a))}")
    info(f"Chave A  : {chave_a}")
    info(f"FNN de B : {to_str(to_nnf(b))}")
    info(f"Chave B  : {chave_b}")

    secao("Resultado")
    if equiv:
        ok(f"{BOLD}As fórmulas SÃO equivalentes.{RESET}  (chaves idênticas)")
    else:
        erro(f"{BOLD}As fórmulas NÃO são equivalentes.{RESET}  (chaves diferentes)")


def tarefa_cnf():
    titulo("3 · Conversão para FNC (Forma Normal Conjuntiva)")
    info("Pipeline: eliminar ↔ → eliminar → → empurrar ¬ → distribuir ∨ sobre ∧")
    node = ler_formula("Fórmula")

    from logic_engine import to_nnf
    nnf  = to_nnf(node)
    cnf  = to_cnf(node)

    secao("Transformação")
    exibir_formula("Original", node)
    exibir_formula("FNN     ", nnf)
    exibir_formula("FNC     ", cnf)

    secao("Verificação semântica")
    equiv, _ = truth_table_equiv(node, cnf)
    if equiv:
        ok("FNC é semanticamente equivalente à fórmula original.")
    else:
        erro("Divergência detectada (reporte como bug).")


def tarefa_dnf():
    titulo("4 · Conversão para FND (Forma Normal Disjuntiva)")
    info("Pipeline: eliminar ↔ → eliminar → → empurrar ¬ → distribuir ∧ sobre ∨")
    node = ler_formula("Fórmula")

    from logic_engine import to_nnf
    nnf  = to_nnf(node)
    dnf  = to_dnf(node)

    secao("Transformação")
    exibir_formula("Original", node)
    exibir_formula("FNN     ", nnf)
    exibir_formula("FND     ", dnf)

    secao("Verificação semântica")
    equiv, _ = truth_table_equiv(node, dnf)
    if equiv:
        ok("FND é semanticamente equivalente à fórmula original.")
    else:
        erro("Divergência detectada (reporte como bug).")


def tarefa_sat():
    titulo("5 · SAT Solver (DPLL)")
    info("Converte para FNC e aplica o algoritmo DPLL com propagação unitária.")
    node = ler_formula("Fórmula")

    cnf = to_cnf(node)
    exibir_formula("FNC usada", cnf)

    sat, modelo = is_satisfiable(node)

    secao("Resultado")
    if sat:
        ok(f"{BOLD}SATISFATÍVEL{RESET}")
        secao("Modelo satisfatório")
        for var, val in sorted(modelo.items()):
            simbolo = cor("V  (True) ", VERDE) if val else cor("F  (False)", VERMELHO)
            print(f"    {BOLD}{var}{RESET}  =  {simbolo}")
        secao("Verificação")
        from logic_engine import evaluate
        ok(f"evaluate(fórmula, modelo) = {evaluate(node, modelo)}")
    else:
        erro(f"{BOLD}INSATISFATÍVEL{RESET}  — nenhuma atribuição satisfaz a fórmula.")


def tarefa_negacao():
    titulo("6 · Verificação de Negação")
    info("A é negação de B se val(A) ≠ val(B) para toda atribuição.")
    a = ler_formula("Fórmula A")
    b = ler_formula("Fórmula B")

    is_neg, contraexemplos = are_negations(a, b)

    secao("Tabela-Verdade")
    all_vars = list(dict.fromkeys(variables(a) + variables(b)))
    from itertools import product as iproduct
    from logic_engine import evaluate
    headers = all_vars + ["A", "B"]
    rows = []
    for vals in iproduct([False, True], repeat=len(all_vars)):
        asgn = dict(zip(all_vars, vals))
        rows.append(vals + (evaluate(a, asgn), evaluate(b, asgn)))
    imprimir_tabela(headers, rows)

    secao("Resultado")
    if is_neg:
        ok(f"{BOLD}A É a negação de B.{RESET}  (val(A) ≠ val(B) em todas as linhas)")
    else:
        erro(f"{BOLD}A NÃO é a negação de B.{RESET}  ({len(contraexemplos)} linha(s) com val(A) = val(B))")


# ── Menu principal ────────────────────────────────────────────────────────────

MENU = [
    ("1", "Verificar equivalência — Tabela-Verdade",   tarefa_equivalencia_tt),
    ("2", "Verificar equivalência — Algébrica",        tarefa_equivalencia_alg),
    ("3", "Converter para FNC",                        tarefa_cnf),
    ("4", "Converter para FND",                        tarefa_dnf),
    ("5", "SAT Solver (satisfatibilidade)",            tarefa_sat),
    ("6", "Verificar negação entre duas fórmulas",     tarefa_negacao),
    ("0", "Sair",                                      None),
]

def exibir_menu():
    print(f"\n{BOLD}{AZUL}╔══════════════════════════════════════════╗")
    print(f"║           Lógica Proposicional           ║")
    print(f"╚══════════════════════════════════════════╝{RESET}")
    print()
    for chave, descricao, _ in MENU:
        if chave == "0":
            print(f"  {CINZA}[{chave}]{RESET}  {CINZA}{descricao}{RESET}")
        else:
            print(f"  {AMARELO}[{chave}]{RESET}  {descricao}")
    print()
    info("Sintaxe: p, q, r... | ! & | -> <->  | parênteses livres")


def main():
    opcoes = {chave: fn for chave, _, fn in MENU}

    while True:
        exibir_menu()
        escolha = input(f"  {BOLD}Escolha uma opção: {RESET}").strip()

        if escolha not in opcoes:
            erro(f"Opção inválida: '{escolha}'. Escolha entre: {', '.join(opcoes)}")
            pausar()
            continue

        if escolha == "0":
            print(f"\n{CINZA}Encerrando. Até mais!{RESET}\n")
            break

        try:
            opcoes[escolha]()
        except KeyboardInterrupt:
            print(f"\n  {CINZA}Operação cancelada.{RESET}")

        pausar()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{CINZA}Saindo...{RESET}\n")