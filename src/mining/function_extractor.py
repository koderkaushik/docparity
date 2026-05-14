import ast
from dataclasses import dataclass


@dataclass
class FunctionInfo:
    name: str
    code: str
    docstring: str
    full_source: str
    start_line: int
    end_line: int
    args: list[str]
    return_annotation: str | None


def extract_functions(source: str) -> list[FunctionInfo]:
    tree = ast.parse(source)
    functions = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            docstring = ast.get_docstring(node) or ""
            code_lines = source.splitlines()
            # Get code body (excluding docstring)
            if docstring and len(node.body) > 1:
                code = "\n".join(code_lines[node.body[1].lineno - 1:node.body[-1].end_lineno])
            elif node.body:
                code = "\n".join(code_lines[node.body[0].lineno - 1:node.body[-1].end_lineno])
            else:
                code = ""
            full_source = "\n".join(code_lines[node.lineno - 1:(node.end_lineno or node.lineno)])
            args = [a.arg for a in node.args.args if a.arg != "self"]
            ret = ast.unparse(node.returns) if node.returns else None
            functions.append(FunctionInfo(
                name=node.name, code=code, docstring=docstring,
                full_source=full_source, start_line=node.lineno,
                end_line=node.end_lineno or node.lineno, args=args,
                return_annotation=ret,
            ))
    return functions