"""
Motor de Lógica Proposicional
===========================
Cobre:
  1. Equivalência via tabela-verdade
  2. Equivalência via reescrita algébrica
  3. Conversão para FNC (Forma Normal Conjuntiva)
  4. Conversão para FND (Forma Normal Disjuntiva)
  5. SAT solver DPLL em FNC
  6. Verificação de negação entre duas sentenças
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from itertools import product
from typing import Optional
import re

class Op(Enum):
    VAR   = auto()
    NOT   = auto()
    AND   = auto()
    OR    = auto()
    IMP   = auto()
    BIMP  = auto()


@dataclass
class Node:
    op:    Op
    left:  Optional["Node"] = field(default=None, repr=False)
    right: Optional["Node"] = field(default=None, repr=False)
    name:  Optional[str]    = None          # usado apenas para VAR

    def __hash__(self):  return id(self)
    def __eq__(self, o): return self is o


# ─────────────────────────────────────────────
# Parser (descida recursiva, O(n) passagem única)
# Gramática suportada:
#   sentenca      ::= bi-implicacao
#   bi-implicacao ::= implicacao ('<->' implicacao)*
#   implicacao    ::= disjuncao ('->' disjuncao)* (associativo à direita)
#   disjuncao     ::= conjuncao ('|' conjuncao)*
#   conjuncao     ::= unario ('&' unario)*
#   unario        ::= '!' unario | atomo
#   atomo         ::= IDENT | '(' sentenca ')'
# ─────────────────────────────────────────────

_TOKEN = re.compile(r'\s*(<->|->|[A-Za-z_][A-Za-z_0-9]*|[!&|()])|\s+')

def tokenize(src: str) -> list[str]:
    tokens = []
    pos = 0
    while pos < len(src):
        m = _TOKEN.match(src, pos)
        if not m:
            raise SyntaxError(f"Caractere inesperado na posição {pos}: {src[pos]!r}")
        tok = m.group(1)
        if tok:
            tokens.append(tok)
        pos = m.end()
    tokens.append("$EOF$")
    return tokens


class Parser:
    __slots__ = ("_tokens", "_pos")

    def __init__(self, src: str):
        self._tokens = tokenize(src)
        self._pos    = 0

    def _peek(self) -> str:
        return self._tokens[self._pos]

    def _consume(self) -> str:
        tok = self._tokens[self._pos]
        self._pos += 1
        return tok

    def _expect(self, tok: str) -> None:
        got = self._consume()
        if got != tok:
            raise SyntaxError(f"Esperava {tok!r}, mas recebeu {got!r}")

    def parse(self) -> Node:
        node = self._biimplication()
        if self._peek() != "$EOF$":
            raise SyntaxError(f"Token inesperado: {self._peek()!r}")
        return node

    def _biimplication(self) -> Node:
        left = self._implication()
        while self._peek() == "<->":
            self._consume()
            right = self._implication()
            left  = Node(Op.BIMP, left, right)
        return left

    def _implication(self) -> Node:
        left = self._disjunction()
        if self._peek() == "->":
            self._consume()
            right = self._implication()          
            return Node(Op.IMP, left, right)
        return left

    def _disjunction(self) -> Node:
        left = self._conjunction()
        while self._peek() == "|":
            self._consume()
            right = self._conjunction()
            left  = Node(Op.OR, left, right)
        return left

    def _conjunction(self) -> Node:
        left = self._unary()
        while self._peek() == "&":
            self._consume()
            right = self._unary()
            left  = Node(Op.AND, left, right)
        return left

    def _unary(self) -> Node:
        if self._peek() == "!":
            self._consume()
            return Node(Op.NOT, self._unary())
        return self._atom()

    def _atom(self) -> Node:
        tok = self._peek()
        if tok == "(":
            self._consume()
            node = self._biimplication()
            self._expect(")")
            return node
        if re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*', tok):
            self._consume()
            return Node(Op.VAR, name=tok)
        raise SyntaxError(f"Token inesperado: {tok!r}")


def parse(src: str) -> Node:
    return Parser(src).parse()


# ─────────────────────────────────────────────
# Extração de variáveis
# ─────────────────────────────────────────────

def variables(node: Node) -> list[str]:
    seen:  set[str]  = set()
    order: list[str] = []

    def _walk(n: Node) -> None:
        if n.op == Op.VAR:
            if n.name not in seen:
                seen.add(n.name)
                order.append(n.name)
        else:
            if n.left:  _walk(n.left)
            if n.right: _walk(n.right)

    _walk(node)
    return order


# ─────────────────────────────────────────────
# Avaliador
# ─────────────────────────────────────────────

def evaluate(node: Node, assignment: dict[str, bool]) -> bool:
    match node.op:
        case Op.VAR:  return assignment[node.name]
        case Op.NOT:  return not evaluate(node.left, assignment)
        case Op.AND:  return evaluate(node.left, assignment) and evaluate(node.right, assignment)
        case Op.OR:   return evaluate(node.left, assignment) or  evaluate(node.right, assignment)
        case Op.IMP:  return (not evaluate(node.left, assignment)) or evaluate(node.right, assignment)
        case Op.BIMP:
            l = evaluate(node.left,  assignment)
            r = evaluate(node.right, assignment)
            return l == r


# ─────────────────────────────────────────────
# 1.1  Equivalência por tabela-verdade — O(2^n)
# ─────────────────────────────────────────────

def truth_table_equiv(a: Node, b: Node) -> tuple[bool, list[dict]]:
    """
    Retorna (equivalente: bool, contraexemplos: list[dict]).
    A lista de contraexemplos estará vazia se as fórmulas forem equivalentes.
    """
    all_vars = list(dict.fromkeys(variables(a) + variables(b)))
    counterexamples: list[dict] = []

    for values in product([False, True], repeat=len(all_vars)):
        assignment = dict(zip(all_vars, values))
        va = evaluate(a, assignment)
        vb = evaluate(b, assignment)
        if va != vb:
            counterexamples.append({**assignment, "A": va, "B": vb})

    return (len(counterexamples) == 0), counterexamples


def build_truth_table(node: Node) -> tuple[list[str], list[tuple]]:
    """Retorna (cabeçalhos, linhas) para a exibição da tabela."""
    cols = variables(node)
    headers = cols + ["Resultado"]
    rows = []
    for values in product([False, True], repeat=len(cols)):
        assignment = dict(zip(cols, values))
        result = evaluate(node, assignment)
        rows.append(tuple(values) + (result,))
    return headers, rows


# ─────────────────────────────────────────────
# 1.2  Equivalência algébrica via FNN + comparação estrutural
#      Pipeline: eliminar IMP/BIMP → empurrar NOT para dentro (FNN) → ordenar ops comutativos → comparar árvores
# ─────────────────────────────────────────────

def _eliminate_iff(node: Node) -> Node:
    """A <-> B  →  (A -> B) & (B -> A)"""
    if node.op == Op.VAR:
        return node
    l = _eliminate_iff(node.left)  if node.left  else None
    r = _eliminate_iff(node.right) if node.right else None
    if node.op == Op.BIMP:
        return Node(Op.AND,
                    Node(Op.IMP, l, r),
                    Node(Op.IMP, r, l))
    if node.op == Op.IMP:
        return Node(Op.IMP, l, r)
    return Node(node.op, l, r)


def _eliminate_imp(node: Node) -> Node:
    """A -> B  →  !A | B"""
    if node.op == Op.VAR:
        return node
    l = _eliminate_imp(node.left)  if node.left  else None
    r = _eliminate_imp(node.right) if node.right else None
    if node.op == Op.IMP:
        return Node(Op.OR, Node(Op.NOT, l), r)
    return Node(node.op, l, r)


def to_nnf(node: Node) -> Node:
    """Converte para a Forma Normal Negativa (FNN) (sem IMP/BIMP, NOT apenas sobre literais)."""
    node = _eliminate_iff(node)
    node = _eliminate_imp(node)
    return _push_not(node)


def _push_not(node: Node) -> Node:
    match node.op:
        case Op.VAR:
            return node
        case Op.NOT:
            child = node.left
            match child.op:
                case Op.VAR:
                    return node                         # literal — mantém como está
                case Op.NOT:
                    return _push_not(child.left)        # !!A → A
                case Op.AND:
                    return _push_not(Node(Op.OR,
                                         Node(Op.NOT, child.left),
                                         Node(Op.NOT, child.right)))
                case Op.OR:
                    return _push_not(Node(Op.AND,
                                         Node(Op.NOT, child.left),
                                         Node(Op.NOT, child.right)))
                case _:
                    raise ValueError(f"Operador inesperado no NOT: {child.op}")
        case _:
            return Node(node.op,
                        _push_not(node.left),
                        _push_not(node.right))


def _canonical_key(node: Node) -> str:
    """Gera uma string canônica a partir de uma árvore FNN ordenando os operandos comutativos."""
    match node.op:
        case Op.VAR:
            return node.name
        case Op.NOT:
            return f"!{_canonical_key(node.left)}"
        case Op.AND:
            parts = sorted([_canonical_key(node.left), _canonical_key(node.right)])
            return f"({parts[0]}&{parts[1]})"
        case Op.OR:
            parts = sorted([_canonical_key(node.left), _canonical_key(node.right)])
            return f"({parts[0]}|{parts[1]})"
        case _:
            raise ValueError(f"Operador inesperado: {node.op}")


def algebraic_equiv(a: Node, b: Node) -> tuple[bool, str, str]:
    """
    Retorna (equivalente, chave_canonica_A, chave_canonica_B).
    """
    ca = _canonical_key(to_nnf(a))
    cb = _canonical_key(to_nnf(b))
    return ca == cb, ca, cb


# ─────────────────────────────────────────────
# 2.  Conversão para FNC  (distribuição clássica + simplificação)
#     Pior caso O(2^n) para explosão exponencial — aceitável para ferramentas de ensino de lógica.
# ─────────────────────────────────────────────

def to_cnf(node: Node) -> Node:
    """
    Retorna um nó equissatisfatível na FNC.
    Pipeline: FNN → distribuir OR sobre AND repetidamente até estabilizar.
    """
    node = to_nnf(node)
    return _distribute_or(node)


def _distribute_or(node: Node) -> Node:
    match node.op:
        case Op.VAR | Op.NOT:
            return node
        case Op.AND:
            return Node(Op.AND,
                        _distribute_or(node.left),
                        _distribute_or(node.right))
        case Op.OR:
            left  = _distribute_or(node.left)
            right = _distribute_or(node.right)
            if left.op == Op.AND:
                # (A & B) | C  →  (A | C) & (B | C)
                return _distribute_or(Node(Op.AND,
                                           Node(Op.OR, left.left,  right),
                                           Node(Op.OR, left.right, right)))
            if right.op == Op.AND:
                # A | (B & C)  →  (A | B) & (A | C)
                return _distribute_or(Node(Op.AND,
                                           Node(Op.OR, left, right.left),
                                           Node(Op.OR, left, right.right)))
            return Node(Op.OR, left, right)
        case _:
            raise ValueError(f"Operador inesperado: {node.op}")


# ─────────────────────────────────────────────
# 3.  Conversão para FND  (dual da FNC)
# ─────────────────────────────────────────────

def to_dnf(node: Node) -> Node:
    """Distribui AND sobre OR repetidamente até estabilizar."""
    node = to_nnf(node)
    return _distribute_and(node)


def _distribute_and(node: Node) -> Node:
    match node.op:
        case Op.VAR | Op.NOT:
            return node
        case Op.OR:
            return Node(Op.OR,
                        _distribute_and(node.left),
                        _distribute_and(node.right))
        case Op.AND:
            left  = _distribute_and(node.left)
            right = _distribute_and(node.right)
            if left.op == Op.OR:
                # (A | B) & C  →  (A & C) | (B & C)
                return _distribute_and(Node(Op.OR,
                                            Node(Op.AND, left.left,  right),
                                            Node(Op.AND, left.right, right)))
            if right.op == Op.OR:
                # A & (B | C)  →  (A & B) | (A & C)
                return _distribute_and(Node(Op.OR,
                                            Node(Op.AND, left, right.left),
                                            Node(Op.AND, left, right.right)))
            return Node(Op.AND, left, right)
        case _:
            raise ValueError(f"Operador inesperado: {node.op}")


# ─────────────────────────────────────────────
# Auxiliares para extração de cláusulas  (FNC → lista de cláusulas para SAT)
# Cada cláusula é um frozenset de literais com sinal: int positivo = índice da var, negativo = negado
# ─────────────────────────────────────────────

def _collect_conjuncts(node: Node, acc: list[Node]) -> None:
    if node.op == Op.AND:
        _collect_conjuncts(node.left, acc)
        _collect_conjuncts(node.right, acc)
    else:
        acc.append(node)


def _collect_disjuncts(node: Node, acc: list[Node]) -> None:
    if node.op == Op.OR:
        _collect_disjuncts(node.left, acc)
        _collect_disjuncts(node.right, acc)
    else:
        acc.append(node)


def to_clause_set(cnf_node: Node) -> tuple[list[frozenset[int]], list[str]]:
    """
    Retorna (clausulas, nomes_das_vars).
    Cada cláusula é um frozenset de inteiros com sinal (base 1).
    """
    var_index: dict[str, int] = {}
    var_names: list[str]      = []

    def get_idx(name: str) -> int:
        if name not in var_index:
            var_index[name] = len(var_names) + 1
            var_names.append(name)
        return var_index[name]

    def literal(lit_node: Node) -> int:
        if lit_node.op == Op.VAR:
            return get_idx(lit_node.name)
        if lit_node.op == Op.NOT and lit_node.left.op == Op.VAR:
            return -get_idx(lit_node.left.name)
        raise ValueError(f"Não-literal encontrado na cláusula: {lit_node.op}")

    conjuncts: list[Node] = []
    _collect_conjuncts(cnf_node, conjuncts)

    clauses: list[frozenset[int]] = []
    for conj in conjuncts:
        disjuncts: list[Node] = []
        _collect_disjuncts(conj, disjuncts)
        clause = frozenset(literal(d) for d in disjuncts)
        clauses.append(clause)

    return clauses, var_names


# ─────────────────────────────────────────────
# 4.  SAT Solver DPLL  — Pior caso O(2^n)
# ─────────────────────────────────────────────

def dpll_sat(clauses: list[frozenset[int]]) -> Optional[dict[int, bool]]:
    """
    Retorna uma atribuição satisfatória {literal: bool} (índices de var base 1)
    ou None se for INSATISFATÍVEL.
    """
    assignment: dict[int, bool] = {}

    def unit_propagate(cls: list[frozenset[int]]) -> tuple[list[frozenset[int]], bool]:
        changed = True
        while changed:
            changed = False
            units = [c for c in cls if len(c) == 1]
            for unit in units:
                lit = next(iter(unit))
                var, val = abs(lit), lit > 0
                if var in assignment and assignment[var] != val:
                    return cls, True           # ocorreu conflito
                assignment[var] = val
                cls = [c for c in cls if lit not in c]
                cls = [c - {-lit} for c in cls]
                changed = True
        return cls, False

    def pure_literal_elim(cls: list[frozenset[int]]) -> list[frozenset[int]]:
        all_lits: set[int] = set()
        for c in cls: all_lits.update(c)
        for lit in list(all_lits):
            if -lit not in all_lits:
                assignment[abs(lit)] = lit > 0
                cls = [c for c in cls if lit not in c]
        return cls

    def solve(cls: list[frozenset[int]]) -> bool:
        cls, conflict = unit_propagate(cls)
        if conflict: return False
        cls = pure_literal_elim(cls)
        if not cls:        return True                   # todas as cláusulas satisfeitas
        if any(len(c) == 0 for c in cls): return False   # cláusula vazia

        # escolhe o primeiro literal não atribuído
        shortest = min(cls, key=len)
        lit = next(iter(shortest))
        var = abs(lit)

        saved = dict(assignment)
        assignment[var] = lit > 0
        pos_cls = [c for c in cls if lit not in c]
        pos_cls = [c - {-lit} for c in pos_cls]
        if solve(pos_cls): return True

        assignment.clear()
        assignment.update(saved)
        assignment[var] = lit <= 0
        neg_cls = [c for c in cls if -lit not in c]
        neg_cls = [c - {lit} for c in neg_cls]
        return solve(neg_cls)

    sat = solve(list(clauses))
    return assignment if sat else None


def is_satisfiable(node: Node) -> tuple[bool, Optional[dict[str, bool]]]:
    """
    Retorna (satisfativel: bool, modelo: dict[nome_var, bool] | None).
    """
    cnf  = to_cnf(node)
    cls, var_names = to_clause_set(cnf)
    model_idx = dpll_sat(cls)
    if model_idx is None:
        return False, None
    model = {var_names[i - 1]: v for i, v in model_idx.items()}
    # preenche quaisquer variáveis não tocadas pelo DPLL (podem receber qualquer valor)
    for v in variables(node):
        if v not in model:
            model[v] = True
    return True, model


# ─────────────────────────────────────────────
# 5.  Verificação de negação  — A é negação de B se e somente se A ≡ ¬B
#     Usa tabela-verdade para completude; aplica curto-circuito na primeira divergência.
# ─────────────────────────────────────────────

def are_negations(a: Node, b: Node) -> tuple[bool, list[dict]]:
    """
    Retorna (is_negation: bool, counterexamples).
    'a' é a negação de 'b' se e somente se para toda atribuição val(a) = !val(b).
    """
    all_vars = list(dict.fromkeys(variables(a) + variables(b)))
    counterexamples: list[dict] = []

    for values in product([False, True], repeat=len(all_vars)):
        assignment = dict(zip(all_vars, values))
        va = evaluate(a, assignment)
        vb = evaluate(b, assignment)
        if va == vb:  # deveriam diferir para ser uma negação válida
            counterexamples.append({**assignment, "A": va, "B": vb})

    return (len(counterexamples) == 0), counterexamples


# ─────────────────────────────────────────────
# Formatador de exibição (Pretty printer)
# ─────────────────────────────────────────────

_PREC = {Op.BIMP: 0, Op.IMP: 1, Op.OR: 2, Op.AND: 3, Op.NOT: 4, Op.VAR: 5}
_SYM  = {Op.AND: " ∧ ", Op.OR: " ∨ ", Op.IMP: " → ", Op.BIMP: " ↔ "}

def to_str(node: Node, parent_prec: int = -1) -> str:
    prec = _PREC[node.op]
    match node.op:
        case Op.VAR:
            return node.name
        case Op.NOT:
            inner = to_str(node.left, prec)
            if node.left.op not in (Op.VAR, Op.NOT):
                inner = f"({inner})"
            return f"¬{inner}"
        case _:
            sym  = _SYM[node.op]
            expr = to_str(node.left, prec) + sym + to_str(node.right, prec)
            return f"({expr})" if prec < parent_prec else expr