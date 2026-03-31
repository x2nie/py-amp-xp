import re


def lex(text):
    lines = text.split("\n")
    result = []
    skips = -1 # soon changed. needed by python unittest to allow indented code

    for i, line in enumerate(lines):
        if not line.strip():
            continue

        if skips <= 0:
            skips = len(line) - len(line.lstrip())

        # remove comment after "
        line = re.sub(r'".*$', '', line)

        indent = ( -skips + len(re.match(r'^\s*', line).group(0))) // 4
        raw = line.strip()

        if raw.startswith('@'):
            parts = raw[1:].split()
            result.append({
                "phase": "lex",
                "kind": "Decorator",
                "name": parts[0],
                "args": parts[1:],
                "indent": indent,
                "line": i + 1
            })
            continue

        tokens = []
        for v in raw.split():
            try:
                tokens.append(int(v))
            except ValueError:
                tokens.append(v)

        result.append({
            "phase": "lex",
            "kind": "Words",
            "tokens": tokens,
            "indent": indent,
            "line": i + 1
        })

    return result


def structure(tokens):
    root = {"type": "file", "children": []}
    active_decorator = None
    stack = []

    for t in tokens:
        if t["kind"] == "Decorator":
            node = {
                "type": t["name"],
                "subject": None,
                "args": t["args"][:] if t["name"] == "include" else [],
                "children": [],
                "line": t["line"],
            }
            root["children"].append(node)
            active_decorator = node
            stack = [{"indent": t["indent"], "node": node}]
            continue

        if not active_decorator:
            continue

        if active_decorator["type"] == "include" and t["indent"] == 1:
            active_decorator["args"].extend(t["tokens"])
            continue

        if (
            active_decorator["subject"] is None and
            t["indent"] == stack[0]["indent"]
        ):
            toks = t["tokens"][:]
            active_decorator["subject"] = toks.pop(0)
            active_decorator["args"] = toks
            continue

        while stack and t["indent"] <= stack[-1]["indent"]:
            stack.pop()

        parent = stack[-1]["node"] if stack else active_decorator

        node = {
            "kind": "Words",
            "tokens": t["tokens"],
            "line": t["line"],
            "children": []
        }

        parent["children"].append(node)
        stack.append({"indent": t["indent"], "node": node})

    return root


def declarative(tree):
    registry = {}
    output = {
        "type": "file",
        "children": [],
        "registry": registry
    }

    for node in tree["children"]:
        if node["type"] == "type":
            schema = {}
            for w in node["children"]:
                key, *types = w["tokens"]
                schema[key] = types
            registry[node["subject"]] = schema

        elif node["type"] == "skin":
            output["children"].append(node)

        elif node["type"] == "include":
            paths = []

            # subject (multiline style)
            if node.get("subject"):
                paths.append(node["subject"])

            # args (kalau suatu saat dipakai lagi)
            paths.extend(node.get("args", []))

            # children (kalau indent style dipakai)
            for w in node.get("children", []):
                paths.extend(w.get("tokens", []))

            output["children"].append({
                "type": "include",
                "children": paths
            })

        else:
            output["children"].append({
                "type": node["type"],
                "subject": node.get("subject"),
                "args": node.get("args", []),
                "line": node.get("line"),
                "children": node.get("children", [])
            })

    return output


def collect_types(ast):
    return ast.get("registry", {})


def resolve(ast, registry):
    new_children = []

    for node in ast.get("children", []):
        errs = []
        t = node.get("type")

        if t in ("include", "skin"):
            new_children.append(node)
            continue

        schema = registry.get(t)
        if not schema:
            # continue  # atau nanti bisa jadi error
            errs.append({
                "message": f"Unknown type: {t}",
                "foo": 1,
                "line": node.get("line")
            })
            new_children.append({
                "type": t,
                "name": node.get("subject"),
                "props": {},
                "children": [],
                "errors": errs
            })
            continue

        parts = [node.get("subject")] + node.get("args", [])
        name = parts[0]

        props = {}
        i = 1
        while i < len(parts):
            key = parts[i]
            i += 1
            arity = len(schema.get(key, []))

            if key not in schema:
                errs.append({
                    "message": f"Unknown property: {key}",
                    "foo": 3,
                    "line": node.get("line")
                })
                continue

            if i + arity > len(parts):
                errs.append({
                    "message": f"Missing value for {key}",
                    "line": node.get("line")
                })
                break

            props[key] = parts[i:i + arity]
            i += arity

        children = []
        for w in node.get("children", []):
            toks = w.get("tokens", [])
            if not toks:
                continue

            target = toks[0]

            p = {}
            child_errs = []
            i = 1
            while i < len(toks):
                key = toks[i]
                i += 1
                arity = len(schema.get(key, []))

                if key not in schema:
                    child_errs.append({
                        "message": f"Unknown property: {key}",
                        "foo": 2,
                        "line": w.get("line")
                    })
                    continue

                if i + arity > len(toks):
                    child_errs.append({
                        "message": f"Missing value for {key}",
                        "line": w.get("line")
                    })
                    break

                p[key] = toks[i:i + arity]
                i += arity

            children.append({
                "type": t + ".child",
                "target": target,
                "props": p,
                "errors": child_errs,
                "children": []
            })

        new_children.append({
            "type": t,
            "name": name,
            "props": props,
            "children": children,
            "schema": schema,
            "errors": errs
        })

    ast["children"] = new_children
    return ast

def resolve_include(ast, loader, visited=None):
    """
    dependency resolver.
    loader(path) -> text
    """

    if visited is None:
        visited = set()

    new_children = []

    for node in ast.get("children", []):
        if node.get("type") == "include":
            for path in node.get("children", []):
                if path in visited:
                    raise Exception(f"Circular include detected: {path}")

                visited.add(path)

                text = loader(path)

                sub_ast = declarative(structure(lex(text)))
                sub_ast = resolve_include(sub_ast, loader, visited)

                # 🔥 merge registry
                ast["registry"].update(sub_ast.get("registry", {}))

                # 🔥 merge children
                new_children.extend(sub_ast.get("children", []))

        else:
            new_children.append(node)

    ast["children"] = new_children
    return ast