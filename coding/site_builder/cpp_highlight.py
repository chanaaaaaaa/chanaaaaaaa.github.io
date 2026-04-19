# -*- coding: utf-8 -*-
"""C++ 語法高亮、略過 #pragma。"""
import html


def strip_pragma_lines(code: str) -> str:
    """建置 HTML 時略過所有 `#pragma ...` 行（不寫入題解頁程式碼區塊）。"""
    out = []
    for line in code.splitlines(keepends=True):
        if line.lstrip().startswith("#pragma"):
            continue
        out.append(line)
    return "".join(out)


def highlight_cpp(code: str) -> str:
    """
    建置時進行 C++ 語法高亮，輸出 Prism 相容的 token class，
    無需依賴 JavaScript，確保顏色一定顯示。
    """
    tokens = []
    i = 0
    n = len(code)

    def esc(s):
        return html.escape(s)

    CPP_KEYWORDS = {
        "alignas", "alignof", "asm", "auto", "bool", "break", "case", "catch",
        "char", "class", "const", "constexpr", "const_cast", "continue", "decltype",
        "default", "delete", "do", "double", "dynamic_cast", "else", "enum",
        "explicit", "export", "extern", "false", "float", "for", "friend", "goto",
        "if", "inline", "int", "long", "mutable", "namespace", "new", "noexcept",
        "nullptr", "operator", "override", "private", "protected", "public",
        "register", "reinterpret_cast", "return", "short", "signed", "sizeof",
        "static", "static_assert", "static_cast", "struct", "switch", "template",
        "this", "thread_local", "throw", "true", "try", "typedef", "typeid",
        "typename", "union", "unsigned", "using", "virtual", "void", "volatile",
        "wchar_t", "while", "co_await", "co_return", "co_yield", "concept",
        "consteval", "constinit", "import", "module", "requires",
    }

    while i < n:
        if code[i] == '"':
            j = i + 1
            while j < n and (code[j] != '"' or (j > 0 and code[j - 1] == "\\")):
                if code[j] == "\\":
                    j += 2
                else:
                    j += 1
            if j < n:
                j += 1
            tokens.append(f'<span class="token string">{esc(code[i:j])}</span>')
            i = j
            continue
        if code[i] == "'":
            j = i + 1
            while j < n and (code[j] != "'" or (j > 0 and code[j - 1] == "\\")):
                if code[j] == "\\":
                    j += 2
                else:
                    j += 1
            if j < n:
                j += 1
            tokens.append(f'<span class="token string">{esc(code[i:j])}</span>')
            i = j
            continue
        if i + 1 < n and code[i : i + 2] == "/*":
            j = code.find("*/", i + 2)
            j = j + 2 if j >= 0 else n
            tokens.append(f'<span class="token comment">{esc(code[i:j])}</span>')
            i = j
            continue
        if i + 1 < n and code[i : i + 2] == "//":
            j = code.find("\n", i + 2)
            j = n if j < 0 else j
            tokens.append(f'<span class="token comment">{esc(code[i:j])}</span>')
            i = j
            continue
        if code[i] == "#" and (i == 0 or code[i - 1] == "\n"):
            j = i + 1
            while j < n and code[j] in " \t":
                j += 1
            while j < n and (code[j].isalnum() or code[j] in "_"):
                j += 1
            tokens.append(f'<span class="token directive">{esc(code[i:j])}</span>')
            i = j
            continue
        if code[i].isdigit():
            j = i
            while j < n and (code[j].isdigit() or code[j] in ".xXaAbBcCdDeEfF"):
                j += 1
            tokens.append(f'<span class="token number">{esc(code[i:j])}</span>')
            i = j
            continue
        if code[i].isalpha() or code[i] == "_":
            j = i
            while j < n and (code[j].isalnum() or code[j] == "_"):
                j += 1
            word = code[i:j]
            if word in CPP_KEYWORDS:
                tokens.append(f'<span class="token keyword">{esc(word)}</span>')
            else:
                tokens.append(esc(word))
            i = j
            continue
        tokens.append(esc(code[i]))
        i += 1

    return "".join(tokens)
