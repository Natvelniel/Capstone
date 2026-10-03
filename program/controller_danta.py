import os
import tempfile
import re
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


def count_cc_manual(method_code):
    cc = 1
    control_keywords = ["if", "for", "while", "when", "catch", "case"]
    lines = method_code.split("\n")
    for line in lines:
        stripped = line.strip()
        for keyword in control_keywords:
            if stripped.startswith(keyword):
                cc += 1
    return cc


def count_woc(cc_values):
    total_CC = sum(cc_values)
    return [cc / total_CC if total_CC else 0 for cc in cc_values]


def count_loc_project(kotlin_files):
    total_loc = 0
    for file_path in kotlin_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    stripped = line.strip()
                    if stripped and not stripped.startswith("//"):
                        total_loc += 1
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
    return total_loc


def attach_parents(node_obj, parent=None):
    if isinstance(node_obj, list):
        for child in node_obj:
            attach_parents(child, parent)
    elif hasattr(node_obj, '__dict__'):
        node_obj.parent = parent
        for attr in node_obj.__dict__.values():
            attach_parents(attr, node_obj)

def is_static(result):
    static = 0
    temp = []
    class_decl = result.declarations[0]

    lines = str(class_decl).split("\n")
    inside_companion = False
    brace_count = 0

    for token in lines:
        tokens = token.lstrip()
        if not inside_companion and tokens.startswith("companion object"):
            inside_companion = True

        if inside_companion:
            temp.append(tokens)
            brace_count += tokens.count("{")
            brace_count -= tokens.count("}")

            if brace_count == 0:
                inside_companion = False

    for line in temp:
        if line.startswith("fun"):
            static = 1

    return static

def count_attributes_in_project(kotlin_files):
    from collections import defaultdict
    class_attribute_counts = defaultdict(lambda: {
        'number_private_visibility_attributes': 0,
        'number_protected_visibility_attributes': 0,
        'number_package_visibility_attributes': 0,
        'num_final_attributes': 0,
        'num_static_attributes': 0,
        'num_final_static_attributes': 0,
        'num_not_final_not_static_attributes': 0
    })

    for file_path in kotlin_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()
            parser = Parser(code)
            result = parser.parse()
            attach_parents(result)

            for declaration in result.declarations:
                if isinstance(declaration, node.ClassDeclaration) and declaration.body:
                    class_name = declaration.name
                    class_counts = class_attribute_counts[class_name]

                    for member in declaration.body.members:
                        if isinstance(member, node.CompanionObject) and member.body:
                            for companion_member in member.body.members:
                                if isinstance(companion_member, node.PropertyDeclaration):
                                    modifiers = getattr(companion_member, 'modifiers', [])
                                    is_private = 'private' in modifiers
                                    is_protected = 'protected' in modifiers
                                    is_internal = 'internal' in modifiers
                                    is_final = 'val' in str(companion_member)

                                    if is_private:
                                        class_counts['number_private_visibility_attributes'] += 1
                                    elif is_protected:
                                        class_counts['number_protected_visibility_attributes'] += 1
                                    elif not modifiers or is_internal:
                                        class_counts['number_package_visibility_attributes'] += 1

                                    class_counts['num_static_attributes'] += 1
                                    if is_final:
                                        class_counts['num_final_attributes'] += 1
                                        class_counts['num_final_static_attributes'] += 1
                                    elif 'var' in str(companion_member):
                                        class_counts['num_not_final_not_static_attributes'] += 1

                        elif isinstance(member, node.PropertyDeclaration):
                            modifiers = getattr(member, 'modifiers', [])
                            is_private = 'private' in modifiers
                            is_protected = 'protected' in modifiers
                            is_internal = 'internal' in modifiers
                            is_final = 'val' in str(member)
                            # static detection removed

                            if is_private:
                                class_counts['number_private_visibility_attributes'] += 1
                            elif is_protected:
                                class_counts['number_protected_visibility_attributes'] += 1
                            elif not modifiers or is_internal:
                                class_counts['number_package_visibility_attributes'] += 1

                            if is_final:
                                class_counts['num_final_attributes'] += 1
                            # static detection removed
                            elif not is_final and 'var' in str(member):
                                class_counts['num_not_final_not_static_attributes'] += 1
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")

    return dict(class_attribute_counts)

def extracted_method(file_path, project_attributes):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()

        parser = Parser(code)
        result = parser.parse()
        attach_parents(result)

        package_name = result.package.name if result.package else "Unknown"
        datas = []

        global_static_flag = is_static(result)

        for declaration in result.declarations:
            if not isinstance(declaration, (node.ClassDeclaration, node.ObjectDeclaration)):
                continue

            class_name = declaration.name
            class_counts = project_attributes.get(class_name, {})

            if declaration.body is None:
                datas.append({
                    "Package": package_name,
                    "Class": class_name,
                    "Method": "None",
                    "LOC": 0,
                    "Max Nesting": 0,
                    "CC": 0,
                    "WOC": 0,
                    "isStatic": global_static_flag,
                    "Static Methods Count": 0,
                    **class_counts,
                    "Error": "Class/Object has no body"
                })
                continue

            method_function = {}
            static_count = 0

            for member in declaration.body.members:
                if isinstance(member, node.FunctionDeclaration):
                    function_name = member.name
                    loc_count = str(member.body).count("\n") + 1 if member.body else 0
                    maxnesting = manual_max_nesting(str(member.body)) if member.body else 0
                    cc_value = count_cc_manual(str(member.body)) if member.body else 0
                    # static detection removed
                    is_static_method = 0

                    method_function[function_name] = (cc_value, loc_count, maxnesting, is_static_method)

            cc_values = [cc for cc, _, _, _ in method_function.values()]
            woc_values = count_woc(cc_values) if cc_values else []

            for (function_name, (cc_value, loc_count, maxnesting, is_static_method)), woc in zip(method_function.items(), woc_values):
                datas.append({
                    "Package": package_name,
                    "Class": class_name,
                    "Method": function_name,
                    "LOC": loc_count,
                    "Max Nesting": maxnesting,
                    "CC": cc_value,
                    "WOC": woc,
                    "Static Methods Count": static_count,
                    "isStatic": global_static_flag,
                    **class_counts
                })

        if not datas:
            datas.append({
                "Package": package_name,
                "Class": "Unknown",
                "Method": "None",
                "LOC": 0,
                "Max Nesting": 0,
                "CC": 0,
                "WOC": 0,
                "isStatic": global_static_flag,
                "Static Methods Count": 0,
                **project_attributes.get("Unknown", {}),
                "Error": "No functions found"
            })

        return datas

    except Exception as e:
        return [{
            "Package": "Error",
            "Class": "Error",
            "Method": "Error",
            "LOC": "Error",
            "Max Nesting": 0,
            "CC": 0,
            "WOC": 0,
            "isStatic": 0,
            "Static Methods Count": 0,
            **project_attributes.get("Error", {}),
            "Error": str(e)
        }]

def extract_and_parse(file):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file_path = os.path.join(temp_dir, file.name)
        with open(temp_file_path, "wb") as f:
            f.write(file.getbuffer())

        try:
            patoolib.extract_archive(temp_file_path, outdir=temp_dir)
            kotlin_files = [
                os.path.join(root, f) for root, _, files in os.walk(temp_dir)
                for f in files if f.endswith(".kt") or f.endswith(".kts")
            ]

            if not kotlin_files:
                return pd.DataFrame([{
                    "Package": "Error",
                    "Class": "Error",
                    "Method": "Error",
                    "LOC": "Error",
                    "Max Nesting": 0,
                    "CC": 0,
                    "WOC": 0,
                    "isStatic": 0,
                    "LOC_project": 0,
                    "Static Methods Count": 0,
                    "Error": "No Kotlin files found"
                }])

            loc_project = count_loc_project(kotlin_files)
            project_attributes = count_attributes_in_project(kotlin_files)

            results = []
            for kotlin_file in kotlin_files:
                file_results = extracted_method(kotlin_file, project_attributes)
                for result in file_results:
                    result["LOC_project"] = loc_project
                results.extend(file_results)

            df = pd.DataFrame(results)

            return df
        except Exception as e:
            return pd.DataFrame([{
                "Package": "Error",
                "Class": "Error",
                "Method": "Error",
                "LOC": "Error",
                "Max Nesting": 0,
                "CC": 0,
                "WOC": 0,
                "isStatic": 0,
                "LOC_project": 0,
                "Static Methods Count": 0,
                "Error": str(e)
            }])
