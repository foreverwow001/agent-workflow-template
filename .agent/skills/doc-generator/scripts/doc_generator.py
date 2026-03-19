# -*- coding: utf-8 -*-
"""
.agent/skills/doc-generator/scripts/doc_generator.py
=====================================
用途：Python 文件自動生成工具
職責：從 Python 檔案中提取 docstring，自動產生 Markdown 格式說明文件
=====================================

使用方式：
    python .agent/skills/doc-generator/scripts/doc_generator.py <file_path>
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import List, Optional


def extract_docstring(node: ast.AST) -> Optional[str]:
    """從 AST 節點中提取 docstring"""
    if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
        if node.body and isinstance(node.body[0], ast.Expr):
            if isinstance(node.body[0].value, ast.Constant):
                value = node.body[0].value.value
                if isinstance(value, str):
                    return value.strip()
    return None


def get_function_signature(node: ast.FunctionDef) -> str:
    """取得函式簽名"""
    args = []
    for arg in node.args.args:
        arg_str = arg.arg
        if arg.annotation:
            arg_str += f": {ast.unparse(arg.annotation)}"
        args.append(arg_str)

    signature = f"{node.name}({', '.join(args)})"
    if node.returns:
        signature += f" -> {ast.unparse(node.returns)}"
    return signature


def generate_markdown(file_path: str) -> str:
    """從 Python 檔案生成 Markdown 文件"""
    path = Path(file_path)

    if not path.exists():
        return f"# 錯誤\n\n檔案不存在：`{file_path}`"

    try:
        content = path.read_text(encoding="utf-8")
        tree = ast.parse(content)
    except SyntaxError as exc:
        return f"# 錯誤\n\n無法解析 Python 檔案：`{str(exc)}`"
    except Exception as exc:
        return f"# 錯誤\n\n讀取檔案失敗：`{str(exc)}`"

    md_lines: List[str] = [f"# {path.name}", ""]

    module_doc = extract_docstring(tree)
    if module_doc:
        md_lines.extend(["## 模組說明", "", module_doc, ""])

    classes: List[ast.ClassDef] = []
    functions: List[ast.FunctionDef] = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            classes.append(node)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(node)

    if classes:
        md_lines.extend(["## 類別 (Classes)", ""])
        for cls in classes:
            md_lines.extend([f"### `{cls.name}`", ""])
            cls_doc = extract_docstring(cls)
            if cls_doc:
                md_lines.extend([cls_doc, ""])

            methods = [node for node in cls.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
            if methods:
                md_lines.extend(["**方法：**", ""])
                for method in methods:
                    signature = get_function_signature(method)
                    method_doc = extract_docstring(method)
                    md_lines.append(f"- `{signature}`")
                    if method_doc:
                        md_lines.append(f"  - {method_doc.split(chr(10))[0]}")
                md_lines.append("")

    if functions:
        md_lines.extend(["## 函式 (Functions)", ""])
        for func in functions:
            signature = get_function_signature(func)
            md_lines.extend([f"### `{signature}`", ""])
            func_doc = extract_docstring(func)
            md_lines.append(func_doc if func_doc else "*（無 docstring）*")
            md_lines.append("")

    if not classes and not functions and not module_doc:
        md_lines.append("*此檔案沒有可提取的 docstring。*")

    return "\n".join(md_lines)


def main(argv: List[str] | None = None) -> int:
    """主程式入口"""
    args = argv or sys.argv
    if len(args) < 2:
        print("# 錯誤")
        print("")
        print("使用方式：`python .agent/skills/doc-generator/scripts/doc_generator.py <file_path>`")
        return 1

    print(generate_markdown(args[1]))
    return 0


__all__ = ["extract_docstring", "get_function_signature", "generate_markdown", "main"]


if __name__ == "__main__":
    raise SystemExit(main())
