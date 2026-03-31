import re


def lex(text):
    lines = text.split("\n")
    result = []

    for i, line in enumerate(lines):
        if not line.strip():
            continue

        # remove comment after "
        line = re.sub(r'".*$', '', line)

        indent = len(re.match(r'^\s*', line).group(0)) // 4
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
                "children": []
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
            output["children"].append({
                "type": node["type"],
                "children": node["args"]
            })

        else:
            schema = registry.get(node["type"])
            if not schema:
                continue

            # parts = re.split(r"\s+", str(node["subject"]))
            parts = [node["subject"]] + node.get("args", [])
            name = parts[0]

            props = {}
            i = 1
            while i < len(parts):
                key = parts[i]
                i += 1
                arity = len(schema.get(key, []))

                if arity > 0:
                    # props[key] = list(map(int, parts[i:i + arity]))
                    props[key] = parts[i:i + arity]
                i += arity

            children = []
            for w in node["children"]:
                toks = w["tokens"]
                target = toks[0]

                p = {}
                i = 1
                while i < len(toks):
                    key = toks[i]
                    i += 1
                    arity = len(schema.get(key, []))

                    if arity > 0:
                        p[key] = toks[i:i + arity]
                    i += arity

                children.append({
                    "type": node["type"] + ".child",
                    "target": target,
                    "props": p,
                    "children": []
                })

            output["children"].append({
                "type": node["type"],
                "name": name,
                "props": props,
                "children": children
            })

    return output


def collect_types(ast):
    return ast.get("registry", {})


def resolve(ast, registry):
    for node in ast.get("children", []):
        if node.get("type") != "type":
            node["schema"] = registry.get(node["type"])
    return ast