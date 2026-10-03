import os
import tempfile
import patoolib
import pandas as pd
from kopyt import Parser, node

# ====================== UTIL: EKSTRAK KODE ========================
def extract_companion_block(code: str) -> list[str]:
    lines = code.splitlines()
    inside = False
    brace_count = 0
    block_lines = []

    for line in lines:
        stripped = line.strip()
        if not inside and stripped.startswith("companion object"):
            inside = True
            brace_count += stripped.count("{") - stripped.count("}")
            block_lines.append(stripped)
        elif inside:
            brace_count += stripped.count("{") - stripped.count("}")
            block_lines.append(stripped)
            if brace_count == 0:
                break
    return block_lines

# ===================== HITUNG JUMLAH FUN ===========================
def number_fun_methods(class_decl) -> int:
    code_lines = str(class_decl).splitlines()
    count = 0
    inside_companion = False
    brace_count = 0

    for line in code_lines:
        stripped = line.strip()
        if not inside_companion and stripped.startswith("companion object"):
            inside_companion = True
            brace_count += stripped.count("{") - stripped.count("}")
            continue
        elif inside_companion:
            brace_count += stripped.count("{") - stripped.count("}")
            if brace_count == 0:
                inside_companion = False
            continue

        if "fun" in stripped and "abstract fun" not in stripped and "final fun" not in stripped:
            count += 1

    return count

def number_static_methods(class_decl) -> int:
    block = extract_companion_block(str(class_decl))
    return sum(1 for line in block if "fun" in line and "final fun" not in line)

def number_final_static_methods(class_decl) -> int:
    block = extract_companion_block(str(class_decl))
    return sum(1 for line in block if "final fun" in line)

def number_abstract_methods(class_decl) -> int:
    return sum(1 for line in str(class_decl).splitlines() if "abstract fun" in line)

def number_final_methods(class_decl) -> int:
    lines = str(class_decl).splitlines()
    inside_companion = False
    brace_depth = 0
    count = 0

    for line in lines:
        stripped = line.strip()
        if not inside_companion and stripped.startswith("companion object"):
            inside_companion = True
            brace_depth += stripped.count("{") - stripped.count("}")
            continue
        if inside_companion:
            brace_depth += stripped.count("{") - stripped.count("}")
            if brace_depth == 0:
                inside_companion = False
            continue
        if "final fun" in stripped:
            count += 1
    return count

def number_not_final_static_methods(class_decl) -> int:
    return number_static_methods(class_decl)

def number_not_final_not_static_methods(class_decl) -> int:
    return number_abstract_methods(class_decl) + number_fun_methods(class_decl)

def number_not_abstract_not_final_methods(class_decl) -> int:
    return number_fun_methods(class_decl) + number_static_methods(class_decl)

# ====================== STATIC CHECK ==============================
def is_static_method(member, in_companion=False) -> int:
    # Debug info
    # print(f"[DEBUG is_static_method] Method: {getattr(member, 'name', 'Unknown')}, Modifiers: {getattr(member, 'modifiers', None)}, In companion: {in_companion}")
    if isinstance(member, node.FunctionDeclaration):
        modifiers = member.modifiers or []
        if in_companion:
            if "final" in modifiers:
                return 0
            else:
                return 1
    return 0

# ====================== GET STATIC METHODS DARI FILE ===============
def get_companion_methods(file_path: str) -> list[str]:
    with open(file_path, "r", encoding="utf-8") as f:
        code = f.read()

    parser = Parser(code)
    result = parser.parse()

    if not result.declarations:
        return []

    class_decl = result.declarations[0]
    methods = []

    for member in class_decl.body.members:
        if isinstance(member, node.ObjectDeclaration) and member.modifiers and "companion" in member.modifiers:
            for comp_member in member.body.members:
                if isinstance(comp_member, node.FunctionDeclaration):
                    methods.append(comp_member.name)

    return methods

# ====================== EXTRACT METHOD UTAMA =======================
def extracted_method(file_path: str) -> list[dict]:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()

        parser = Parser(code)
        result = parser.parse()
        package_name = result.package.name if result.package else "Unknown"

        if not result.declarations:
            return [{
                "Package": package_name,
                "Class": "Unknown",
                "Method": "None",
                "Abstract Methods": 0,
                "Final Methods": 0,
                "Static Methods": 0,
                "Final Static Methods": 0,
                "Not Final Static Methods": 0,
                "Not Final Not Static Methods": 0,
                "Not Abstract Not Final Methods": 0,
                "isStatic_method": 0,
                "Error": "No class declaration found",
            }]

        class_decl = result.declarations[0]
        class_name = class_decl.name
        
        final_count = number_final_methods(class_decl)
        abstract_count = number_abstract_methods(class_decl)
        static_count = number_static_methods(class_decl)
        final_static_count = number_final_static_methods(class_decl)
        not_final_static_count = number_not_final_static_methods(class_decl)
        not_final_not_static_count = number_not_final_not_static_methods(class_decl)
        not_abstract_not_final_count = number_not_abstract_not_final_methods(class_decl)

        data_rows = []
        companion_found_by_kopyt = False

        for member in class_decl.body.members:
            if isinstance(member, node.FunctionDeclaration):
                print(f"[DEBUG] Function '{member.name}', Modifiers: {member.modifiers}")
                data_rows.append({
                    "Package": package_name,
                    "Class": class_name,
                    "Method": member.name,
                    "Abstract Methods": abstract_count,
                    "Final Methods": final_count,
                    "Static Methods": static_count,
                    "Final Static Methods": final_static_count,
                    "Not Final Static Methods": not_final_static_count,
                    "Not Final Not Static Methods": not_final_not_static_count,
                    "Not Abstract Not Final Methods": not_abstract_not_final_count,
                    "isStatic_method": is_static_method(member, in_companion=False),
                })

            elif isinstance(member, node.ObjectDeclaration):
                print(f"[DEBUG] ObjectDeclaration name: '{member.name}', Modifiers: {member.modifiers}")
                if member.name == "Companion" or (member.modifiers and "companion" in member.modifiers):
                    companion_found_by_kopyt = True
                    for comp_member in member.body.members:
                        if isinstance(comp_member, node.FunctionDeclaration):
                            print(f"[DEBUG] Companion Function '{comp_member.name}', Modifiers: {comp_member.modifiers}")
                            data_rows.append({
                                "Package": package_name,
                                "Class": class_name,
                                "Method": comp_member.name,
                                "Abstract Methods": abstract_count,
                                "Final Methods": final_count,
                                "Static Methods": static_count,
                                "Final Static Methods": final_static_count,
                                "Not Final Static Methods": not_final_static_count,
                                "Not Final Not Static Methods": not_final_not_static_count,
                                "Not Abstract Not Final Methods": not_abstract_not_final_count,
                                "isStatic_method": is_static_method(comp_member, in_companion=True),
                            })

        if not companion_found_by_kopyt:
            print("[DEBUG] Companion object tidak ditemukan oleh kopyt, ekstrak manual...")
            companion_lines = extract_companion_block(code)
            for line in companion_lines:
                if "fun " in line:
                    method_name = line.split("fun")[1].split("(")[0].strip()
                    data_rows.append({
                        "Package": package_name,
                        "Class": class_name,
                        "Method": method_name,
                        "Abstract Methods": abstract_count,
                        "Final Methods": final_count,
                        "Static Methods": static_count,
                        "Final Static Methods": final_static_count,
                        "Not Final Static Methods": not_final_static_count,
                        "Not Final Not Static Methods": not_final_not_static_count,
                        "Not Abstract Not Final Methods": not_abstract_not_final_count,
                        "isStatic_method": 0,
                    })

        return data_rows

    except Exception as e:
        return [{
            "Package": "Error",
            "Class": "Error",
            "Method": "Error",
            "Abstract Methods": 0,
            "Final Methods": 0,
            "Static Methods": 0,
            "Final Static Methods": 0,
            "Not Final Static Methods": 0,
            "Not Final Not Static Methods": 0,
            "Not Abstract Not Final Methods": 0,
            "isStatic_method": 0,
            "Error": str(e),
        }]

# ====================== EXTRACT RAR FILE ===========================
def extract_and_parse(file):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file_path = os.path.join(temp_dir, file.name)
        with open(temp_file_path, "wb") as f:
            f.write(file.getbuffer())

        try:
            patoolib.extract_archive(temp_file_path, outdir=temp_dir)

            kotlin_files = []
            for root, _, files in os.walk(temp_dir):
                for f in files:
                    if f.endswith(".kt") or f.endswith(".kts"):
                        kotlin_files.append(os.path.join(root, f))

            results = []
            for kotlin_file in kotlin_files:
                results.extend(extracted_method(kotlin_file))

            return pd.DataFrame(results)

        except Exception as e:
            return str(e)
