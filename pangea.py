#!/usr/bin/env python3
"""Pangea 1.0 — one language for people, machines, and minds.

Reference interpreter. Standard library only.
Usage:
    python pangea.py program.pangaea   run a program
    python pangea.py                   open the interactive REPL
    python pangea.py --check file      check a program without running it
    python pangea.py --help            show help
"""

import difflib
import os
import subprocess
import sys
import time

VERSION = "1.2.0"
MAX_LOOP = 100000

# ---------------------------------------------------------------------------
# Errors — always in plain words, always with a line number.
# ---------------------------------------------------------------------------

class PangeaError(Exception):
    def __init__(self, message, line=None):
        self.message = message
        self.line = line
        super().__init__(message)

    def __str__(self):
        if self.line is not None:
            return "Line %s: %s" % (self.line, self.message)
        return self.message


class ReturnSignal(Exception):
    def __init__(self, value):
        self.value = value


class StopProgram(Exception):
    pass


# ---------------------------------------------------------------------------
# Lexer
# ---------------------------------------------------------------------------

KEYWORDS = {
    "let", "say", "ask", "if", "elif", "else", "end", "while", "for", "in",
    "to", "return", "link", "as", "speak", "send", "receive", "broadcast",
    "from", "and", "or", "not", "is", "yes", "no", "nothing", "stop", "read",
    "save", "grant", "revoke", "admin", "check", "room", "delete", "run",
    "list", "all",
}

MULTI_OPS = ("==", "!=", "<=", ">=")
SINGLE_OPS = set("+-*/%^=<>(),[]{}:")


class Token(object):
    __slots__ = ("kind", "value", "line")

    def __init__(self, kind, value, line):
        self.kind = kind
        self.value = value
        self.line = line

    def __repr__(self):
        return "Token(%s, %r, %s)" % (self.kind, self.value, self.line)


def tokenize(source):
    tokens = []
    i = 0
    line = 1
    n = len(source)
    while i < n:
        ch = source[i]
        if ch in " \t\r":
            i += 1
            continue
        if ch == "#":
            while i < n and source[i] != "\n":
                i += 1
            continue
        if ch == "\n":
            tokens.append(Token("NL", "\n", line))
            line += 1
            i += 1
            continue
        if ch.isdigit():
            start = i
            seen_dot = False
            while i < n and (source[i].isdigit() or (source[i] == "." and not seen_dot)):
                if source[i] == ".":
                    seen_dot = True
                i += 1
            text = source[start:i]
            try:
                value = float(text) if seen_dot else int(text)
            except ValueError:
                raise PangeaError("'%s' is not a number I understand." % text, line)
            tokens.append(Token("NUM", value, line))
            continue
        if ch == '"':
            i += 1
            out = []
            while i < n and source[i] != '"':
                c = source[i]
                if c == "\\" and i + 1 < n:
                    nxt = source[i + 1]
                    mapping = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}
                    if nxt in mapping:
                        out.append(mapping[nxt])
                        i += 2
                        continue
                if c == "\n":
                    raise PangeaError("A piece of text was never closed with a quote.", line)
                out.append(c)
                i += 1
            if i >= n:
                raise PangeaError("A piece of text was never closed with a quote.", line)
            i += 1
            tokens.append(Token("STR", "".join(out), line))
            continue
        if ch.isalpha() or ch == "_":
            start = i
            while i < n and (source[i].isalnum() or source[i] == "_"):
                i += 1
            word = source[start:i]
            if word in KEYWORDS:
                tokens.append(Token("KW", word, line))
            else:
                tokens.append(Token("IDENT", word, line))
            continue
        two = source[i:i + 2]
        if two in MULTI_OPS:
            tokens.append(Token("OP", two, line))
            i += 2
            continue
        if ch in SINGLE_OPS:
            tokens.append(Token("OP", ch, line))
            i += 1
            continue
        raise PangeaError("I don't understand the character '%s'." % ch, line)
    tokens.append(Token("EOF", None, line))
    return tokens


# ---------------------------------------------------------------------------
# Parser — recursive descent. AST nodes are tuples: (kind, line, ...).
# ---------------------------------------------------------------------------

class Parser(object):
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self, offset=0):
        idx = min(self.pos + offset, len(self.tokens) - 1)
        return self.tokens[idx]

    def advance(self):
        tok = self.tokens[self.pos]
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return tok

    def at_kw(self, word):
        t = self.peek()
        return t.kind == "KW" and t.value == word

    def at_op(self, op):
        t = self.peek()
        return t.kind == "OP" and t.value == op

    def expect_op(self, op):
        t = self.peek()
        if t.kind == "OP" and t.value == op:
            return self.advance()
        raise PangeaError("I expected '%s' here." % op, t.line)

    def expect_kw(self, word):
        t = self.peek()
        if t.kind == "KW" and t.value == word:
            return self.advance()
        raise PangeaError("I expected the word '%s' here." % word, t.line)

    def expect_ident(self):
        t = self.peek()
        if t.kind == "IDENT":
            return self.advance().value
        raise PangeaError("I expected a name here.", t.line)

    def skip_nl(self):
        while self.peek().kind == "NL":
            self.advance()

    def parse_program(self):
        stmts = self.parse_stmts(set())
        if self.peek().kind != "EOF":
            raise PangeaError("I expected the program to end here.", self.peek().line)
        return stmts

    def parse_stmts(self, terminators):
        stmts = []
        while True:
            self.skip_nl()
            t = self.peek()
            if t.kind == "EOF":
                break
            if t.kind == "KW" and t.value in terminators:
                break
            stmt = self.parse_stmt()
            stmts.append(stmt)
            t = self.peek()
            if t.kind == "NL":
                continue
            if t.kind == "EOF":
                break
            if t.kind == "KW" and t.value in terminators:
                continue
            raise PangeaError(
                "I expected this line to end here.", t.line)
        return stmts

    def parse_stmt(self):
        t = self.peek()
        line = t.line
        if t.kind == "KW":
            word = t.value
            if word == "let":
                self.advance()
                name = self.expect_ident()
                self.expect_op("=")
                expr = self.parse_expr()
                return ("let", line, name, expr)
            if word == "say":
                self.advance()
                return ("say", line, self.parse_expr())
            if word == "if":
                return self.parse_if()
            if word == "while":
                self.advance()
                cond = self.parse_expr()
                self.expect_op(":")
                self.skip_nl()
                body = self.parse_stmts({"end"})
                self.expect_kw("end")
                return ("while", line, cond, body)
            if word == "for":
                self.advance()
                var = self.expect_ident()
                self.expect_kw("in")
                expr = self.parse_expr()
                self.expect_op(":")
                self.skip_nl()
                body = self.parse_stmts({"end"})
                self.expect_kw("end")
                return ("for", line, var, expr, body)
            if word == "to":
                self.advance()
                name = self.expect_ident()
                self.expect_op("(")
                params = []
                if not self.at_op(")"):
                    params.append(self.expect_ident())
                    while self.at_op(","):
                        self.advance()
                        params.append(self.expect_ident())
                self.expect_op(")")
                self.expect_op(":")
                self.skip_nl()
                body = self.parse_stmts({"end"})
                self.expect_kw("end")
                return ("func", line, name, params, body)
            if word == "return":
                self.advance()
                if self.peek().kind == "NL" or self.peek().kind == "EOF" \
                        or (self.peek().kind == "KW" and self.peek().value == "end"):
                    return ("return", line, None)
                return ("return", line, self.parse_expr())
            if word == "link":
                self.advance()
                name = self.expect_ident()
                self.expect_kw("as")
                kind = self.expect_ident()
                return ("link", line, name, kind)
            if word == "speak":
                self.advance()
                self.expect_kw("as")
                name = self.expect_ident()
                return ("speak", line, name)
            if word == "send":
                self.advance()
                expr = self.parse_expr()
                self.expect_kw("to")
                target = self.expect_ident()
                return ("send", line, expr, target)
            if word == "broadcast":
                self.advance()
                return ("broadcast", line, self.parse_expr())
            if word == "save":
                self.advance()
                expr = self.parse_expr()
                self.expect_kw("to")
                path = self.parse_expr()
                return ("save", line, expr, path)
            if word == "stop":
                self.advance()
                return ("stop", line)
            if word == "grant":
                self.advance()
                self.expect_kw("admin")
                self.expect_kw("to")
                return ("grant", line, self.parse_admin_target())
            if word == "revoke":
                self.advance()
                self.expect_kw("admin")
                self.expect_kw("from")
                return ("revoke", line, self.parse_admin_target())
            if word == "check":
                self.advance()
                return ("check", line, self.parse_expr())
            if word == "no":
                if self.peek(1).kind == "KW" and self.peek(1).value == "room":
                    self.advance()
                    self.advance()
                    return ("noroom", line, True)
            if word == "room":
                self.advance()
                return ("noroom", line, False)
            if word == "delete":
                self.advance()
                return ("delete", line, self.parse_expr())
        # An expression on its own (usually a function call).
        expr = self.parse_expr()
        return ("expr", line, expr)

    def parse_admin_target(self):
        # One agent, all agents, or all agents of one kind.
        t = self.peek()
        if t.kind == "KW" and t.value == "all":
            self.advance()
            if self.peek().kind == "IDENT" and self.peek().value in ("ai", "human", "computer"):
                return ("all", self.advance().value)
            return ("all", None)
        return ("one", self.expect_ident())

    def parse_if(self):
        line = self.peek().line
        self.expect_kw("if")
        branches = []
        cond = self.parse_expr()
        self.expect_op(":")
        self.skip_nl()
        body = self.parse_stmts({"elif", "else", "end"})
        branches.append((cond, body))
        else_body = None
        while self.at_kw("elif"):
            self.advance()
            cond = self.parse_expr()
            self.expect_op(":")
            self.skip_nl()
            body = self.parse_stmts({"elif", "else", "end"})
            branches.append((cond, body))
        if self.at_kw("else"):
            self.advance()
            self.expect_op(":")
            self.skip_nl()
            else_body = self.parse_stmts({"end"})
        self.expect_kw("end")
        return ("if", line, branches, else_body)

    # -- expressions, lowest precedence first ------------------------------
    def parse_expr(self):
        return self.parse_or()

    def parse_or(self):
        line = self.peek().line
        left = self.parse_and()
        while self.at_kw("or"):
            self.advance()
            right = self.parse_and()
            left = ("binop", line, "or", left, right)
        return left

    def parse_and(self):
        line = self.peek().line
        left = self.parse_not()
        while self.at_kw("and"):
            self.advance()
            right = self.parse_not()
            left = ("binop", line, "and", left, right)
        return left

    def parse_not(self):
        line = self.peek().line
        if self.at_kw("not"):
            self.advance()
            return ("unop", line, "not", self.parse_not())
        return self.parse_comparison()

    def parse_comparison(self):
        line = self.peek().line
        left = self.parse_add()
        while True:
            if self.peek().kind == "OP" and self.peek().value in ("==", "!=", "<", "<=", ">", ">="):
                op = self.advance().value
            elif self.at_kw("is"):
                self.advance()
                if self.at_kw("not"):
                    self.advance()
                    op = "!="
                else:
                    op = "=="
            else:
                break
            right = self.parse_add()
            left = ("binop", line, op, left, right)
        return left

    def parse_add(self):
        line = self.peek().line
        left = self.parse_mul()
        while self.peek().kind == "OP" and self.peek().value in ("+", "-"):
            op = self.advance().value
            right = self.parse_mul()
            left = ("binop", line, op, left, right)
        return left

    def parse_mul(self):
        line = self.peek().line
        left = self.parse_power()
        while self.peek().kind == "OP" and self.peek().value in ("*", "/", "%"):
            op = self.advance().value
            right = self.parse_power()
            left = ("binop", line, op, left, right)
        return left

    def parse_power(self):
        line = self.peek().line
        left = self.parse_unary()
        if self.at_op("^"):
            self.advance()
            right = self.parse_power()
            left = ("binop", line, "^", left, right)
        return left

    def parse_unary(self):
        line = self.peek().line
        if self.at_op("-"):
            self.advance()
            return ("unop", line, "-", self.parse_unary())
        return self.parse_postfix()

    def parse_postfix(self):
        line = self.peek().line
        node = self.parse_primary()
        while self.at_op("["):
            self.advance()
            index = self.parse_expr()
            self.expect_op("]")
            node = ("index", line, node, index)
        return node

    def parse_primary(self):
        t = self.peek()
        line = t.line
        if t.kind == "NUM":
            self.advance()
            return ("num", line, t.value)
        if t.kind == "STR":
            self.advance()
            return ("str", line, t.value)
        if t.kind == "OP" and t.value == "(":
            self.advance()
            expr = self.parse_expr()
            self.expect_op(")")
            return expr
        if t.kind == "OP" and t.value == "[":
            self.advance()
            elems = []
            if not self.at_op("]"):
                elems.append(self.parse_expr())
                while self.at_op(","):
                    self.advance()
                    elems.append(self.parse_expr())
            self.expect_op("]")
            return ("list", line, elems)
        if t.kind == "OP" and t.value == "{":
            self.advance()
            pairs = []
            if not self.at_op("}"):
                key = self.parse_map_key()
                self.expect_op(":")
                value = self.parse_expr()
                pairs.append((key, value))
                while self.at_op(","):
                    self.advance()
                    key = self.parse_map_key()
                    self.expect_op(":")
                    value = self.parse_expr()
                    pairs.append((key, value))
            self.expect_op("}")
            return ("map", line, pairs)
        if t.kind == "KW":
            word = t.value
            if word == "yes":
                self.advance()
                return ("bool", line, True)
            if word == "no":
                self.advance()
                return ("bool", line, False)
            if word == "nothing":
                self.advance()
                return ("nothing", line)
            if word == "ask":
                self.advance()
                if self.peek().kind in ("NL", "EOF") or \
                        (self.peek().kind == "KW" and self.peek().value in ("end", "elif", "else")):
                    return ("ask", line, ("str", line, ""))
                return ("ask", line, self.parse_add())
            if word == "receive":
                self.advance()
                self.expect_kw("from")
                name = self.expect_ident()
                return ("receive", line, name)
            if word == "read":
                self.advance()
                if self.at_op("("):
                    self.advance()
                    arg = self.parse_add()
                    self.expect_op(")")
                    return ("call", line, "read", [arg])
                return ("call", line, "read", [self.parse_add()])
            if word == "run":
                self.advance()
                return ("run", line, self.parse_add())
            if word == "list":
                self.advance()
                if self.at_op("("):
                    self.advance()
                    arg = self.parse_add()
                    self.expect_op(")")
                    return ("call", line, "list", [arg])
                return ("call", line, "list", [self.parse_add()])
        if t.kind == "IDENT":
            self.advance()
            name = t.value
            if self.at_op("("):
                self.advance()
                args = []
                if not self.at_op(")"):
                    args.append(self.parse_expr())
                    while self.at_op(","):
                        self.advance()
                        args.append(self.parse_expr())
                self.expect_op(")")
                return ("call", line, name, args)
            return ("var", line, name)
        raise PangeaError("I did not understand this part of the line.", line)

    def parse_map_key(self):
        t = self.peek()
        if t.kind == "STR":
            self.advance()
            return t.value
        if t.kind == "IDENT":
            self.advance()
            return t.value
        raise PangeaError("A map key must be a word or a piece of text.", t.line)


def parse_source(source):
    return Parser(tokenize(source)).parse_program()


# ---------------------------------------------------------------------------
# Values — how Pangea shows them to a human.
# ---------------------------------------------------------------------------

def format_value(value):
    if value is None:
        return "nothing"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if value == int(value):
            return str(int(value))
        return str(value)
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "[" + ", ".join(format_container(v) for v in value) + "]"
    if isinstance(value, dict):
        parts = []
        for k in value:
            parts.append('"%s": %s' % (k, format_container(value[k])))
        return "{" + ", ".join(parts) + "}"
    if isinstance(value, PangeaFunction):
        return "function %s" % value.name
    return str(value)


def format_container(value):
    if isinstance(value, str):
        return '"%s"' % value
    return format_value(value)


def expr_text(node):
    # Render an expression back into readable Pangea, for check messages.
    kind = node[0]
    if kind == "num":
        return format_value(node[2])
    if kind == "str":
        return '"%s"' % node[2]
    if kind == "bool":
        return "yes" if node[2] else "no"
    if kind == "nothing":
        return "nothing"
    if kind == "var":
        return node[2]
    if kind == "list":
        return "[" + ", ".join(expr_text(e) for e in node[2]) + "]"
    if kind == "map":
        return "{" + ", ".join("%s: %s" % (k, expr_text(v)) for k, v in node[2]) + "}"
    if kind == "index":
        return "%s[%s]" % (expr_text(node[2]), expr_text(node[3]))
    if kind == "unop":
        if node[2] == "not":
            return "not " + expr_text(node[3])
        return "-" + expr_text(node[3])
    if kind == "binop":
        return "%s %s %s" % (expr_text(node[3]), node[2], expr_text(node[4]))
    if kind == "call":
        return "%s(%s)" % (node[2], ", ".join(expr_text(a) for a in node[3]))
    if kind == "ask":
        return "ask %s" % expr_text(node[2])
    if kind == "receive":
        return "receive from %s" % node[2]
    if kind == "run":
        return "run %s" % expr_text(node[2])
    return "?"


def type_name(value):
    if value is None:
        return "nothing"
    if isinstance(value, bool):
        return "yes-no"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "text"
    if isinstance(value, list):
        return "list"
    if isinstance(value, dict):
        return "map"
    if isinstance(value, PangeaFunction):
        return "function"
    return "value"


def truthy(value):
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return len(value) > 0
    if isinstance(value, (list, dict)):
        return len(value) > 0
    return True


def values_equal(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a == b
    if type(a) is not type(b):
        return False
    return a == b


# ---------------------------------------------------------------------------
# Environment — names live in nested scopes.
# ---------------------------------------------------------------------------

class Env(object):
    def __init__(self, parent=None):
        self.vars = {}
        self.parent = parent

    def define(self, name, value):
        self.vars[name] = value

    def get(self, name, line=None):
        env = self
        while env is not None:
            if name in env.vars:
                return env.vars[name]
            env = env.parent
        names = self.all_names()
        hint = ""
        close = difflib.get_close_matches(name, names, n=1)
        if close:
            hint = " Did you mean '%s'?" % close[0]
        raise PangeaError("I don't know the name '%s'.%s" % (name, hint), line)

    def all_names(self):
        names = set(self.vars)
        env = self.parent
        while env is not None:
            names.update(env.vars)
            env = env.parent
        return sorted(names)


class PangeaFunction(object):
    def __init__(self, name, params, body, closure):
        self.name = name
        self.params = params
        self.body = body
        self.closure = closure


# ---------------------------------------------------------------------------
# Interpreter
# ---------------------------------------------------------------------------

class Interpreter(object):
    def __init__(self):
        self.global_env = Env()
        self.agents = {"me": "program"}
        self.room = []
        self.speaker = "me"
        self.admins = set()
        self.strict = False
        self.stats = {"statements": 0, "checks": 0, "commands": 0, "retries": 0}
        self.builtins = {
            "len": self._len,
            "type": self._type,
            "str": self._str,
            "num": self._num,
            "upper": self._upper,
            "lower": self._lower,
            "abs": self._abs,
            "round": self._round,
            "range": self._range,
            "keys": self._keys,
            "push": self._push,
            "pop": self._pop,
            "inbox": self._inbox,
            "now": self._now,
            "read": self._read,
            "admins": self._admins,
            "list": self._list,
        }

    # -- builtins -----------------------------------------------------------
    def _need(self, args, count, name, line):
        if len(args) != count:
            raise PangeaError(
                "'%s' needs %d value(s), but got %d." % (name, count, len(args)), line)

    def _len(self, args, line):
        self._need(args, 1, "len", line)
        v = args[0]
        if isinstance(v, (str, list, dict)):
            return len(v)
        raise PangeaError("'len' works on text, lists, and maps — not %s." % type_name(v), line)

    def _type(self, args, line):
        self._need(args, 1, "type", line)
        return type_name(args[0])

    def _str(self, args, line):
        self._need(args, 1, "str", line)
        return format_value(args[0])

    def _num(self, args, line):
        self._need(args, 1, "num", line)
        v = args[0]
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return v
        if isinstance(v, str):
            try:
                return float(v) if "." in v else int(v)
            except ValueError:
                raise PangeaError("'%s' is not a number." % v, line)
        raise PangeaError("'num' needs text or a number.", line)

    def _upper(self, args, line):
        self._need(args, 1, "upper", line)
        if not isinstance(args[0], str):
            raise PangeaError("'upper' needs text.", line)
        return args[0].upper()

    def _lower(self, args, line):
        self._need(args, 1, "lower", line)
        if not isinstance(args[0], str):
            raise PangeaError("'lower' needs text.", line)
        return args[0].lower()

    def _abs(self, args, line):
        self._need(args, 1, "abs", line)
        if not isinstance(args[0], (int, float)) or isinstance(args[0], bool):
            raise PangeaError("'abs' needs a number.", line)
        return abs(args[0])

    def _round(self, args, line):
        self._need(args, 1, "round", line)
        if not isinstance(args[0], (int, float)) or isinstance(args[0], bool):
            raise PangeaError("'round' needs a number.", line)
        return int(round(args[0]))

    def _range(self, args, line):
        if len(args) == 1:
            start, stop = 0, args[0]
        elif len(args) == 2:
            start, stop = args
        else:
            raise PangeaError("'range' needs 1 or 2 numbers.", line)
        if not all(isinstance(a, int) and not isinstance(a, bool) for a in (start, stop)):
            raise PangeaError("'range' needs whole numbers.", line)
        return list(range(start, stop))

    def _keys(self, args, line):
        self._need(args, 1, "keys", line)
        if not isinstance(args[0], dict):
            raise PangeaError("'keys' needs a map.", line)
        return list(args[0].keys())

    def _push(self, args, line):
        self._need(args, 2, "push", line)
        if not isinstance(args[0], list):
            raise PangeaError("'push' needs a list first.", line)
        args[0].append(args[1])
        return args[0]

    def _pop(self, args, line):
        self._need(args, 1, "pop", line)
        if not isinstance(args[0], list):
            raise PangeaError("'pop' needs a list.", line)
        if not args[0]:
            raise PangeaError("That list is empty — there is nothing to take off.", line)
        return args[0].pop()

    def _inbox(self, args, line):
        self._need(args, 0, "inbox", line)
        return ["%s: %s" % (m["from"], format_value(m["text"]))
                for m in self.room if m["to"] == self.speaker]

    def _now(self, args, line):
        self._need(args, 0, "now", line)
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    def _read(self, args, line):
        self._need(args, 1, "read", line)
        path = args[0]
        if not isinstance(path, str):
            raise PangeaError("'read' needs the name of a file, as text.", line)
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            raise PangeaError("I could not find the file '%s'." % path, line)
        except OSError as e:
            raise PangeaError("I could not read the file '%s' (%s)." % (path, e), line)

    def _admins(self, args, line):
        self._need(args, 0, "admins", line)
        return sorted(self.admins)

    def _list(self, args, line):
        self._need(args, 1, "list", line)
        path = args[0]
        if not isinstance(path, str):
            raise PangeaError("'list' needs the name of a folder, as text.", line)
        try:
            return sorted(os.listdir(path))
        except FileNotFoundError:
            raise PangeaError("I could not find the folder '%s'." % path, line)
        except (OSError, NotADirectoryError) as e:
            raise PangeaError("I could not list the folder '%s' (%s)." % (path, e), line)

    # -- running ------------------------------------------------------------
    def run(self, stmts, env=None):
        env = env or self.global_env
        for stmt in stmts:
            self.exec_stmt(stmt, env)

    def exec_stmt(self, stmt, env):
        kind = stmt[0]
        line = stmt[1]
        try:
            self.stats["statements"] += 1
            if kind == "let":
                env.define(stmt[2], self.eval_expr(stmt[3], env))
            elif kind == "say":
                print(format_value(self.eval_expr(stmt[2], env)))
            elif kind == "expr":
                self.eval_expr(stmt[2], env)
            elif kind == "if":
                for cond, body in stmt[2]:
                    if truthy(self.eval_expr(cond, env)):
                        self.run(body, env)
                        break
                else:
                    if stmt[3] is not None:
                        self.run(stmt[3], env)
            elif kind == "while":
                count = 0
                while truthy(self.eval_expr(stmt[2], env)):
                    count += 1
                    if count > MAX_LOOP:
                        raise PangeaError(
                            "This loop ran %d times. It might never stop, so I stopped it." % MAX_LOOP, line)
                    self.run(stmt[3], env)
            elif kind == "for":
                items = self.eval_expr(stmt[3], env)
                if isinstance(items, str):
                    items = list(items)
                if not isinstance(items, list):
                    raise PangeaError(
                        "'for' needs a list to walk through, not %s." % type_name(items), line)
                for item in items:
                    env.define(stmt[2], item)
                    self.run(stmt[4], env)
            elif kind == "func":
                env.define(stmt[2], PangeaFunction(stmt[2], stmt[3], stmt[4], env))
            elif kind == "return":
                value = None
                if stmt[2] is not None:
                    value = self.eval_expr(stmt[2], env)
                raise ReturnSignal(value)
            elif kind == "link":
                name, agent_kind = stmt[2], stmt[3]
                if agent_kind not in ("human", "ai", "computer"):
                    raise PangeaError(
                        "An agent must be a 'human', an 'ai', or a 'computer' — not '%s'." % agent_kind, line)
                self.agents[name] = agent_kind
            elif kind == "speak":
                name = stmt[2]
                if name != "me" and name not in self.agents:
                    raise PangeaError(
                        "I don't know the agent '%s'. Link them first: link %s as ai" % (name, name), line)
                self.speaker = name
            elif kind == "send":
                text = self.eval_expr(stmt[2], env)
                target = stmt[3]
                if target != "me" and target not in self.agents:
                    raise PangeaError(
                        "'send' needs a linked agent. '%s' is not linked yet." % target, line)
                self.room.append({"from": self.speaker, "to": target, "text": text})
            elif kind == "broadcast":
                text = self.eval_expr(stmt[2], env)
                for name in self.agents:
                    if name != self.speaker:
                        self.room.append({"from": self.speaker, "to": name, "text": text})
            elif kind == "save":
                text = format_value(self.eval_expr(stmt[2], env))
                path = self.eval_expr(stmt[3], env)
                if not isinstance(path, str):
                    raise PangeaError("'save' needs the name of a file, as text.", line)
                try:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(text)
                except OSError as e:
                    raise PangeaError("I could not write to the file '%s' (%s)." % (path, e), line)
            elif kind == "stop":
                raise StopProgram()
            elif kind == "grant":
                self._grant(stmt[2], True, line)
            elif kind == "revoke":
                self._grant(stmt[2], False, line)
            elif kind == "check":
                self.stats["checks"] += 1
                if not truthy(self.eval_expr(stmt[2], env)):
                    raise PangeaError(
                        "Check failed: %s was not true." % expr_text(stmt[2]), line)
            elif kind == "noroom":
                self.strict = stmt[2]
            elif kind == "delete":
                self._require_admin(line)
                path = self.eval_expr(stmt[2], env)
                if not isinstance(path, str):
                    raise PangeaError("'delete' needs the name of a file, as text.", line)
                try:
                    os.remove(path)
                except FileNotFoundError:
                    raise PangeaError("I could not find the file '%s'." % path, line)
                except OSError as e:
                    raise PangeaError("I could not delete the file '%s' (%s)." % (path, e), line)
        except PangeaError as e:
            if e.line is None:
                e.line = line
            raise

    def _require_admin(self, line):
        if self.speaker not in self.admins:
            raise PangeaError(
                "Only an admin agent can do that. A human can grant admin first: grant admin to %s" % self.speaker, line)

    def _grant(self, target, give, line):
        if self.speaker != "me" and self.agents.get(self.speaker) != "human":
            raise PangeaError(
                "Only a human can grant or revoke admin access. Speak as a human first.", line)
        mode, value = target
        if mode == "one":
            if value != "me" and value not in self.agents:
                raise PangeaError(
                    "I don't know the agent '%s'. Link them first: link %s as ai" % (value, value), line)
            if give:
                self.admins.add(value)
            else:
                self.admins.discard(value)
        else:
            for agent_name, agent_kind in self.agents.items():
                if value is None or agent_kind == value:
                    if give:
                        self.admins.add(agent_name)
                    else:
                        self.admins.discard(agent_name)

    def eval_expr(self, node, env):
        kind = node[0]
        line = node[1]
        try:
            if kind == "num" or kind == "str":
                return node[2]
            if kind == "bool":
                return node[2]
            if kind == "nothing":
                return None
            if kind == "var":
                return env.get(node[2], line)
            if kind == "list":
                return [self.eval_expr(e, env) for e in node[2]]
            if kind == "map":
                return {k: self.eval_expr(v, env) for k, v in node[2]}
            if kind == "index":
                obj = self.eval_expr(node[2], env)
                idx = self.eval_expr(node[3], env)
                return self._index(obj, idx, line)
            if kind == "ask":
                prompt = self.eval_expr(node[2], env)
                text = format_value(prompt)
                try:
                    return input(text + " " if text else "")
                except EOFError:
                    return ""
            if kind == "receive":
                name = node[2]
                for i, m in enumerate(self.room):
                    if m["from"] == name and m["to"] == self.speaker:
                        del self.room[i]
                        return m["text"]
                return None
            if kind == "run":
                cmd = self.eval_expr(node[2], env)
                if not isinstance(cmd, str):
                    raise PangeaError("'run' needs a command, as text.", line)
                self._require_admin(line)
                return self._run_command(cmd, line)
            if kind == "unop":
                value = self.eval_expr(node[3], env)
                if node[2] == "not":
                    return not truthy(value)
                if node[2] == "-":
                    if not isinstance(value, (int, float)) or isinstance(value, bool):
                        raise PangeaError("You can only put a minus sign on a number.", line)
                    return -value
            if kind == "binop":
                return self._binop(node, env)
            if kind == "call":
                return self._call(node[2], node[3], env, line)
            raise PangeaError("I don't know how to run this part.", line)
        except PangeaError as e:
            if e.line is None:
                e.line = line
            raise

    def _run_command(self, cmd, line):
        # In no-room mode a failed command is retried up to 3 times.
        attempts = 3 if self.strict else 1
        self.stats["commands"] += 1
        last_error = ""
        for attempt in range(attempts):
            try:
                proc = subprocess.run(cmd, shell=True, capture_output=True,
                                      text=True, timeout=30)
            except subprocess.TimeoutExpired:
                last_error = "The command took too long (more than 30 seconds)."
                if attempt + 1 < attempts:
                    self.stats["retries"] += 1
                    continue
                raise PangeaError(last_error, line)
            if proc.returncode == 0:
                return proc.stdout.rstrip("\n")
            last_error = proc.stderr.strip() or \
                ("The command stopped with exit code %d." % proc.returncode)
            if attempt + 1 < attempts:
                self.stats["retries"] += 1
                continue
            raise PangeaError("The command '%s' failed: %s" % (cmd, last_error), line)
        raise PangeaError("The command '%s' failed: %s" % (cmd, last_error), line)

    def _index(self, obj, idx, line):
        if isinstance(obj, list):
            if not isinstance(idx, int) or isinstance(idx, bool):
                raise PangeaError("A list needs a whole number to pick a position.", line)
            try:
                return obj[idx]
            except IndexError:
                raise PangeaError("That list has no position %d." % idx, line)
        if isinstance(obj, dict):
            if idx not in obj:
                raise PangeaError("That map has no entry called '%s'." % idx, line)
            return obj[idx]
        if isinstance(obj, str):
            if not isinstance(idx, int) or isinstance(idx, bool):
                raise PangeaError("Text needs a whole number to pick a letter.", line)
            try:
                return obj[idx]
            except IndexError:
                raise PangeaError("That text has no letter %d." % idx, line)
        raise PangeaError("You can only pick from a list, a map, or text.", line)

    def _binop(self, node, env):
        _, line, op, left_node, right_node = node
        if op == "and":
            left = self.eval_expr(left_node, env)
            if not truthy(left):
                return left
            return self.eval_expr(right_node, env)
        if op == "or":
            left = self.eval_expr(left_node, env)
            if truthy(left):
                return left
            return self.eval_expr(right_node, env)
        left = self.eval_expr(left_node, env)
        right = self.eval_expr(right_node, env)
        if op == "+":
            if isinstance(left, (int, float)) and isinstance(right, (int, float)) \
                    and not isinstance(left, bool) and not isinstance(right, bool):
                return left + right
            if isinstance(left, str) and isinstance(right, str):
                return left + right
            if isinstance(left, list) and isinstance(right, list):
                return left + right
            raise PangeaError(
                "You cannot add %s and %s." % (type_name(left), type_name(right)), line)
        if op in ("-", "*", "/", "%", "^"):
            if not (isinstance(left, (int, float)) and isinstance(right, (int, float))) \
                    or isinstance(left, bool) or isinstance(right, bool):
                raise PangeaError(
                    "'%s' needs two numbers." % op, line)
            if op == "-":
                return left - right
            if op == "*":
                return left * right
            if op == "/":
                if right == 0:
                    raise PangeaError("You cannot divide by zero.", line)
                return left / right
            if op == "%":
                if right == 0:
                    raise PangeaError("You cannot divide by zero.", line)
                return left % right
            if op == "^":
                return left ** right
        if op in ("==", "!=", "<", "<=", ">", ">="):
            if op == "==":
                return values_equal(left, right)
            if op == "!=":
                return not values_equal(left, right)
            if isinstance(left, (int, float)) and isinstance(right, (int, float)) \
                    and not isinstance(left, bool) and not isinstance(right, bool):
                if op == "<":
                    return left < right
                if op == "<=":
                    return left <= right
                if op == ">":
                    return left > right
                return left >= right
            if isinstance(left, str) and isinstance(right, str):
                if op == "<":
                    return left < right
                if op == "<=":
                    return left <= right
                if op == ">":
                    return left > right
                return left >= right
            raise PangeaError(
                "You cannot compare %s and %s with '%s'." % (type_name(left), type_name(right), op), line)
        raise PangeaError("I don't know the operation '%s'." % op, line)

    def _call(self, name, arg_nodes, env, line):
        args = [self.eval_expr(a, env) for a in arg_nodes]
        try:
            fn = env.get(name, line)
        except PangeaError:
            fn = None
        if isinstance(fn, PangeaFunction):
            if len(args) != len(fn.params):
                raise PangeaError(
                    "'%s' needs %d value(s), but got %d." % (name, len(fn.params), len(args)), line)
            call_env = Env(fn.closure)
            for param, value in zip(fn.params, args):
                call_env.define(param, value)
            try:
                self.run(fn.body, call_env)
            except ReturnSignal as ret:
                return ret.value
            return None
        if fn is not None:
            raise PangeaError("'%s' is not something you can call." % name, line)
        if name in self.builtins:
            return self.builtins[name](args, line)
        names = env.all_names() + sorted(self.builtins)
        hint = ""
        close = difflib.get_close_matches(name, names, n=1)
        if close:
            hint = " Did you mean '%s'?" % close[0]
        raise PangeaError("I don't know anything called '%s'.%s" % (name, hint), line)


# ---------------------------------------------------------------------------
# Running programs and the REPL
# ---------------------------------------------------------------------------

HELP = """Pangea %s — one language for people, machines, and minds.

Usage:
  pangea program.pangaea    run a program
  pangea                    open the interactive REPL
  pangea --check file       check a program without running it
  pangea --help             show this help

Learn more in PANGEA.md.
""" % VERSION


def run_file(path, interp):
    try:
        with open(path, "r", encoding="utf-8") as f:
            source = f.read()
    except FileNotFoundError:
        print("I could not find the file '%s'." % path)
        return 1
    except OSError as e:
        print("I could not read the file '%s' (%s)." % (path, e))
        return 1
    try:
        stmts = parse_source(source)
    except PangeaError as e:
        print(str(e))
        return 1
    try:
        interp.run(stmts)
    except StopProgram:
        pass
    except PangeaError as e:
        print(str(e))
        return 1
    if interp.strict:
        s = interp.stats
        print("No-room report: %d statements ran, %d checks passed, %d commands ran, %d retries, 0 errors."
              % (s["statements"], s["checks"], s["commands"], s["retries"]))
    return 0


def repl(interp):
    print("Pangea %s — one language for people, machines, and minds." % VERSION)
    print("Type a statement. Type 'stop' to leave. Blocks end with 'end'.")
    buffer = []
    depth = 0
    openers = ("if", "while", "for", "to")
    while True:
        prompt = "pangea> " if depth == 0 else "...     "
        try:
            line = input(prompt)
        except EOFError:
            print()
            break
        except KeyboardInterrupt:
            print()
            break
        stripped = line.strip()
        if depth == 0 and stripped in ("stop", "exit", "quit"):
            break
        first = stripped.split(" ", 1)[0] if stripped else ""
        if first in openers:
            depth += 1
        elif first == "end" and depth > 0:
            depth -= 1
        buffer.append(line)
        if depth > 0:
            continue
        source = "\n".join(buffer)
        buffer = []
        if not source.strip():
            continue
        try:
            stmts = parse_source(source)
        except PangeaError as e:
            print(str(e))
            continue
        try:
            interp.run(stmts)
        except PangeaError as e:
            print(str(e))
        except StopProgram:
            break


def main(argv):
    if len(argv) >= 2 and argv[1] in ("--help", "-h", "help"):
        print(HELP)
        return 0
    if len(argv) >= 2 and argv[1] == "--version":
        print("Pangea " + VERSION)
        return 0
    if len(argv) >= 3 and argv[1] == "--check":
        path = argv[2]
        try:
            with open(path, "r", encoding="utf-8") as f:
                source = f.read()
        except FileNotFoundError:
            print("I could not find the file '%s'." % path)
            return 1
        try:
            stmts = parse_source(source)
        except PangeaError as e:
            print(str(e))
            return 1
        print("OK — %d statement(s), no errors." % len(stmts))
        return 0
    interp = Interpreter()
    if len(argv) >= 2:
        return run_file(argv[1], interp)
    repl(interp)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
