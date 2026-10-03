import os
import tempfile
import patoolib
import pandas as pd
import re
from kopyt import Parser, node

def count_clnamm(method_code):
    """
    Menghitung CLNAMM (Class Level Non-Accessor/Mutator Methods).
    Return 1 kalau method bukan getter/setter, 0 kalau iya.
    """
    code = method_code.strip()
    # Kotlin getter/setter biasanya bukan explicit function, tapi bisa pake "get" dan "set" prefix juga
    if code.startswith("get ") or code.startswith("set "):
        return 0
    # Cek juga jika ada override property getter/setter, contoh: get() = ...
    is_getter = re.match(r'get\s*\(\)\s*=', code) or re.match(r'get\s*{', code)
    is_setter = re.match(r'set\s*\(\w+\)\s*{', code)
    if is_getter or is_setter:
        return 0
    return 1

def count_cint(method_code):
    """
    Coupling Intensity: hitung jumlah objek/class berbeda yang dipanggil methodnya.
    """
    matches = re.findall(r'(\w+)\.', method_code)
    filtered = [m for m in matches if m not in ('this', 'super')]
    return len(set(filtered))

def count_memcl(method_code):
    """Menghitung Mean Method Chain Length (MeMCL)."""
    chains = [len(call.split(".")) for call in method_code.split() if "." in call]
    return sum(chains) / len(chains) if chains else 0

def count_cdisp(method_code):
    """
    Coupling Dispersion: rasio kelas unik yang digunakan terhadap total pemanggilan method.
    """
    matches = re.findall(r'(\w+)\.', method_code)
    filtered = [m for m in matches if m not in ('this', 'super')]
    total_usages = len(filtered)
    unique_usages = len(set(filtered))
    if total_usages == 0:
        return 0.0
    return unique_usages / total_usages

# kurang NOII, NOAM, NOCS

def count_nom(class_declaration):
    """
    Number of Methods (NOM).
    """
    return sum(1 for member in class_declaration.body.members if isinstance(member, node.FunctionDeclaration))

def count_nmo(class_declaration):
    """
    Number of Methods Overridden (NMO).
    """
    count = 0
    for member in class_declaration.body.members:
        if isinstance(member, node.FunctionDeclaration):
            if member.modifiers and "override" in member.modifiers:
                count += 1
    return count

def extracted_method(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()

        parser = Parser(code)
        result = parser.parse()

        package_name = result.package.name if result.package else "Unknown"
        all_classes = [decl for decl in result.declarations if isinstance(decl, node.ClassDeclaration)]

        if not all_classes:
            return [{"Package": package_name, "Class": "Unknown", "Method": "None", "CLNAMM": 0, "CINT": 0, "MeMCL": 0,
                     "CDISP": 0, "NOII": 0, "NOAM": 0, "NOCS": 0, "NOM": 0, "NMO": 0}]

        datas = []

        for class_declaration in all_classes:
            class_name = class_declaration.name
            noii = count_noii(class_declaration)
            noam = count_noam(class_declaration)
            nocs = count_nocs(class_declaration, all_classes)
            nom = count_nom(class_declaration)
            nmo = count_nmo(class_declaration)

            for member in class_declaration.body.members:
                if isinstance(member, node.FunctionDeclaration):
                    method_code = str(member.body) if member.body else ""
                    clnamm = count_clnamm(method_code)
                    cint = count_cint(method_code)
                    memcl = count_memcl(method_code)
                    cdisp = count_cdisp(method_code)

                    datas.append({
                        "Package": package_name,
                        "Class": class_name,
                        "Method": member.name,
                        "CLNAMM": clnamm,
                        "CINT": cint,
                        "MeMCL": memcl,
                        "CDISP": cdisp,
                        "NOII": noii,
                        "NOAM": noam,
                        "NOCS": nocs,
                        "NOM": nom,
                        "NMO": nmo
                    })

        if not datas:
            datas.append({"Package": package_name, "Class": class_name, "Method": "None", "CLNAMM": 0, "CINT": 0, "MeMCL": 0,
                          "CDISP": 0, "NOII": noii, "NOAM": noam, "NOCS": nocs, "NOM": nom, "NMO": nmo})

        return datas

    except Exception as e:
        return [{"Package": "Error", "Class": "Error", "Method": "Error", "CLNAMM": 0, "CINT": 0, "MeMCL": 0,
                 "CDISP": 0, "NOII": 0, "NOAM": 0, "NOCS": 0, "NOM": 0, "NMO": 0, "Error": str(e)}]

def extract_and_parse(file):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file_path = os.path.join(temp_dir, file.name)
        with open(temp_file_path, "wb") as f:
            f.write(file.getbuffer())

        try:
            patoolib.extract_archive(temp_file_path, outdir=temp_dir)
            kotlin_files = [os.path.join(root, f) for root, _, files in os.walk(temp_dir)
                            for f in files if f.endswith(".kt") or f.endswith(".kts")]

            results = []
            for kotlin_file in kotlin_files:
                results.extend(extracted_method(kotlin_file))

            return pd.DataFrame(results)
        except Exception as e:
            return str(e)