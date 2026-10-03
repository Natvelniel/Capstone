import os
import tempfile
import patoolib
import pandas as pd
from kopyt import Parser, node

def manual_max_nesting(body_str):
    indent_levels = []
    max_depth = 0
    for line in body_str.split("\n"):
        stripped = line.strip()
        if stripped.startswith(("if", "try", "for", "catch", "else", "when")):
            indent_levels.append(stripped)
            max_depth = max(max_depth, len(indent_levels))
        elif stripped == "}":
            if indent_levels:
                indent_levels.pop()
    return max_depth

def walk(node, callback):
    if isinstance(node, list):
        for item in node:
            walk(item, callback)
    elif hasattr(node, "__dict__"):
        callback(node)
        for value in vars(node).values():
            walk(value, callback)


def count_atfd(method_node, class_declaration):
    if not isinstance(method_node.body, node.Block):
        return 0

    foreign_accesses = set()

    # Collect current class field names
    current_fields = {
        member.declaration.name
        for member in class_declaration.body.members
        if isinstance(member, node.PropertyDeclaration)
    }

    def collect_foreign_accesses(expr):
        if isinstance(expr, node.PostfixUnaryExpression):
            # Navigate through suffixes, e.g., obj.field or obj.method()
            if isinstance(expr.expression, node.Identifier):
                root_name = expr.expression.value
                if root_name not in current_fields and root_name != "this":
                    foreign_accesses.add(root_name)

            for suffix in expr.suffixes:
                if isinstance(suffix, node.NavigationSuffix):
                    if isinstance(expr.expression, node.Identifier):
                        base = expr.expression.value
                        if base not in current_fields and base != "this":
                            foreign_accesses.add(base)

        elif isinstance(expr, node.Assignment):
            collect_foreign_accesses(expr.value)

        elif isinstance(expr, node.Identifier):
            if expr.value not in current_fields and expr.value != "this":
                foreign_accesses.add(expr.value)

        elif hasattr(expr, "__dict__"):
            for val in vars(expr).values():
                if isinstance(val, node.Node):
                    collect_foreign_accesses(val)
                elif isinstance(val, list) or isinstance(val, tuple):
                    for item in val:
                        if isinstance(item, node.Node):
                            collect_foreign_accesses(item)

    for stmt in method_node.body.sequence:
        collect_foreign_accesses(stmt.statement)

    return len(foreign_accesses)



def count_fdp(method_node, class_declaration):
    if not method_node.body or not isinstance(method_node.body, node.Block):
        return 0

    # Own class field names
    own_fields = {
        member.declaration.name
        for member in class_declaration.body.members
        if isinstance(member, node.PropertyDeclaration)
    }

    foreign_objects = set()

    def visit(n):
        if isinstance(n, node.PostfixUnaryExpression):
            base = n.expression
            if isinstance(base, node.Identifier):
                name = base.value
                if name != "this" and name not in own_fields:
                    foreign_objects.add(name)

        # Recurse into children
        if hasattr(n, "__dict__"):
            for val in vars(n).values():
                if isinstance(val, node.Node):
                    visit(val)
                elif isinstance(val, (list, tuple)):
                    for item in val:
                        if isinstance(item, node.Node):
                            visit(item)

    for stmt in method_node.body.sequence:
        visit(stmt.statement)

    return len(foreign_objects)


def count_nop(method_node):
    return len(getattr(method_node, "parameters", []))

def count_cc_manual(method_code):
    cc = 1
    control_keywords = ["if", "for", "while", "when", "catch", "case"]
    for line in method_code.split("\n"):
        stripped = line.strip()
        if any(stripped.startswith(keyword) for keyword in control_keywords):
            cc += 1
    return cc

def count_rfc(class_declaration):
    method_calls = set()

    for member in class_declaration.body.members:
        if isinstance(member, node.FunctionDeclaration):
            body = getattr(member.body, "sequence", [])
            for stmt in body:
                expr = stmt.statement

                # Handle function calls like someFunction()
                if isinstance(expr, node.PostfixUnaryExpression):
                    if isinstance(expr.expression, node.Identifier):
                        method_calls.add(expr.expression.value)

                # Handle infix calls like a plus b
                elif isinstance(expr, node.InfixFunctionCall):
                    method_calls.add(expr.operator)

    return len(method_calls)


def count_cbo(class_declaration):
    try:
        from kopyt import node

        referenced_classes = set()
        current_class_name = class_declaration.name

        # 1. Check property types (e.g., val something: OtherClass)
        for member in class_declaration.body.members:
            if isinstance(member, node.PropertyDeclaration) and hasattr(member, "type"):
                type_name = str(member.type)
                if type_name != current_class_name:
                    referenced_classes.add(type_name)

        # 2. Check function parameter and return types
        for member in class_declaration.body.members:
            if isinstance(member, node.FunctionDeclaration):

                # Return type
                if hasattr(member, "type") and member.type:
                    return_type = str(member.type)
                    if return_type != current_class_name:
                        referenced_classes.add(return_type)

                # Parameters
                for param in member.parameters:
                    if hasattr(param, "type") and param.type:
                        param_type = str(param.type)
                        if param_type != current_class_name:
                            referenced_classes.add(param_type)

        return len(referenced_classes)
    except Exception as e:
        return f"Error: {str(e)}"



def count_nopa(class_declaration):
    public_count = 0

    for member in class_declaration.body.members:
        if isinstance(member, node.PropertyDeclaration):
            modifiers = [str(mod).lower() for mod in member.modifiers]

            if not modifiers or "public" in modifiers:
                public_count += 1

    return public_count

def count_additional_metrics(classes, methods, packages):
    return {
        "NOPK_project": len(packages),
        "NOCS_project": len(classes),
        "NOM_package": {pkg: len([m for m in methods if m["Package"] == pkg]) for pkg in packages},
    }

def extracted_method(file_path, package_list, class_list, method_list):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
        
        parser = Parser(code)
        result = parser.parse()
        package_name = result.package.name if result.package else "Unknown"
        package_list.add(package_name)
        
        if not result.declarations:
            return []
        
        datas = []
        for class_declaration in result.declarations:
            class_name = class_declaration.name
            class_list.add(class_name)
            
            if class_declaration.body is None:
                continue
            
            rfc_value = count_rfc(class_declaration)
            cbo_value = count_cbo(class_declaration)
            nopa_value = count_nopa(class_declaration)
            
            for member in class_declaration.body.members:
                if isinstance(member, node.FunctionDeclaration):
                    function_name = member.name
                    method_list.append({"Package": package_name, "Class": class_name, "Method": function_name})
                    loc_count = str(member.body).count("\n") + 1 if member.body else 0
                    maxnesting = manual_max_nesting(str(member.body)) if member.body else 0
                    cc_value = count_cc_manual(str(member.body)) if member.body else 0
                    nop_value = count_nop(member)
                    atfd_value = count_atfd(member, class_declaration)
                    fdp_value = count_fdp(member, class_declaration)
                    
                    datas.append({
                        "Package": package_name, "Class": class_name, "Method": function_name,
                        "LOC": loc_count, "Max Nesting": maxnesting, "CC": cc_value,
                        "NOP": nop_value, "ATFD": atfd_value, "RFC": rfc_value,
                        "CBO": cbo_value, "NOPA": nopa_value, "FDP": fdp_value, "Error": "None"
                    })
        return datas
    except Exception as e:
        return [{"Package": "Error", "Class": "Error", "Method": "Error", "LOC": 0, "Max Nesting": 0, "CC": 0, "NOP": 0, "ATFD": 0, "RFC": 0, "CBO": 0, "NOPA": 0, "FDP":0, "Error": str(e)}]

def extract_and_parse(file):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file_path = os.path.join(temp_dir, file.name)
        with open(temp_file_path, "wb") as f:
            f.write(file.getbuffer())
        
        try:
            patoolib.extract_archive(temp_file_path, outdir=temp_dir)
            kotlin_files = [os.path.join(root, f) for root, _, files in os.walk(temp_dir) for f in files if f.endswith(".kt") or f.endswith(".kts")]
            
            results = []
            packages, classes, methods = set(), set(), []
            
            for kotlin_file in kotlin_files:
                results.extend(extracted_method(kotlin_file, packages, classes, methods))
            
            additional_metrics = count_additional_metrics(classes, methods, packages)
            
            df = pd.DataFrame(results)
            df["NOPK_project"] = additional_metrics["NOPK_project"]
            df["NOCS_project"] = additional_metrics["NOCS_project"]
            df["NOM_package"] = df["Package"].map(additional_metrics["NOM_package"])  
            return df
        except Exception as e:
            return str(e)