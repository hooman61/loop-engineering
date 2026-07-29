from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
DOCUMENTATION_ROOTS = ("docs", "loops", "templates")


def _owned_markdown_files() -> list[Path]:
    """Return Markdown sources owned by this repository.

    The workspace may contain disposable inspected products and generated
    dependency trees.  Their documentation is not part of this project's
    quality boundary and must not influence its documentation tests.
    """

    files = [REPOSITORY_ROOT / "README.md", REPOSITORY_ROOT / "AGENTS.md"]
    for directory in DOCUMENTATION_ROOTS:
        files.extend(sorted((REPOSITORY_ROOT / directory).rglob("*.md")))
    return [path for path in files if path.is_file()]


class DocumentationQualityTests(unittest.TestCase):
    def test_public_python_api_has_docstrings(self) -> None:
        missing: list[str] = []
        for path in sorted((REPOSITORY_ROOT / "src").rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            if ast.get_docstring(tree) is None:
                missing.append(f"{path.relative_to(REPOSITORY_ROOT)}: module")
            for node in tree.body:
                public_nodes = (
                    ast.ClassDef,
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                )
                if isinstance(node, public_nodes):
                    missing_docstring = ast.get_docstring(node) is None
                    if not node.name.startswith("_") and missing_docstring:
                        missing.append(
                            f"{path.relative_to(REPOSITORY_ROOT)}:{node.lineno} "
                            f"{node.name}"
                        )
        self.assertEqual(missing, [], "Missing docstrings:\n" + "\n".join(missing))

    def test_local_markdown_links_resolve(self) -> None:
        broken: list[str] = []
        markdown_files = [REPOSITORY_ROOT / "README.md"]
        markdown_files.extend(sorted((REPOSITORY_ROOT / "docs").rglob("*.md")))
        markdown_files.extend(sorted((REPOSITORY_ROOT / "loops").rglob("*.md")))
        for path in markdown_files:
            text = path.read_text(encoding="utf-8")
            for match in MARKDOWN_LINK.finditer(text):
                target = match.group(1).strip().strip("<>").split("#", 1)[0]
                if not target or "://" in target or target.startswith("mailto:"):
                    continue
                resolved = (path.parent / target).resolve()
                if not resolved.exists():
                    broken.append(
                        f"{path.relative_to(REPOSITORY_ROOT)} -> {target}"
                    )
        self.assertEqual(broken, [], "Broken links:\n" + "\n".join(broken))

    def test_markdown_fences_are_balanced(self) -> None:
        unbalanced: list[str] = []
        for path in _owned_markdown_files():
            count = sum(
                1
                for line in path.read_text(encoding="utf-8").splitlines()
                if line.startswith("```")
            )
            if count % 2:
                unbalanced.append(str(path.relative_to(REPOSITORY_ROOT)))
        self.assertEqual(
            unbalanced, [], "Unbalanced code fences:\n" + "\n".join(unbalanced)
        )

    def test_documentation_scope_excludes_inspected_products(self) -> None:
        paths = [
            path.relative_to(REPOSITORY_ROOT)
            for path in _owned_markdown_files()
        ]

        self.assertTrue(paths)
        self.assertFalse(any(path.parts[0] == "targets" for path in paths))
        self.assertFalse(any("node_modules" in path.parts for path in paths))


if __name__ == "__main__":
    unittest.main()
