from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class Symbol:
    name: str
    symbol_type: str
    kind: str
    scope: str
    line: Optional[int] = None


class SymbolTable:
    def __init__(self):
        self.scopes: List[Dict[str, Symbol]] = []
        self.scope_names: List[str] = []
        self.all_scopes: List[Dict[str, object]] = []

    def enter_scope(self, scope_name: str):
        scope = {}

        self.scopes.append(scope)
        self.scope_names.append(scope_name)

        self.all_scopes.append({
            "name": scope_name,
            "symbols": scope,
        })

    def exit_scope(self):
        if self.scopes:
            self.scopes.pop()
            self.scope_names.pop()

    def declare(
        self,
        name: str,
        symbol_type: str,
        kind: str,
        line: Optional[int] = None,
    ) -> Symbol:
        if not self.scopes:
            self.enter_scope("global")

        current_scope = self.scopes[-1]
        scope_name = self.scope_names[-1]

        symbol = Symbol(
            name=name,
            symbol_type=symbol_type,
            kind=kind,
            scope=scope_name,
            line=line,
        )

        current_scope[name] = symbol

        return symbol

    def lookup(self, name: str) -> Optional[Symbol]:
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]

        return None

    def current_scope(self) -> Optional[str]:
        if not self.scope_names:
            return None

        return self.scope_names[-1]

    def get_all_symbols(self) -> List[Symbol]:
        symbols = []

        for scope_data in self.all_scopes:
            symbols.extend(scope_data["symbols"].values())

        return symbols