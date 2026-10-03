import os
import tempfile
import patoolib
import pandas as pd
from kopyt import Parser, node  # Gunakan `kopyt` sebagai parser AST Kotlin

def manual_max_nesting(body_str):
    """ Menghitung max nesting secara manual dari string kode """
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
    """
    Menghitung Cyclomatic Complexity (CC) secara manual dari string kode.
    """
    cc = 1  # Mulai dari 1 karena setiap metode memiliki setidaknya satu jalur

    # Daftar kata kunci yang menambah CC
    control_keywords = ["if","else", "for", "while", "do", "when", "switch", "case", "try","catch"]

    # Memisahkan kode menjadi baris-baris
    lines = method_code.split("\n")

    for line in method_code.split("\n"):
        stripped = line.strip()
        for strips in stripped.split():
            for keyword in control_keywords:
                if strips.startswith(keyword):
                    cc += 1
    return cc

def is_functional_method(function_body_str):
    # Cek apakah mengandung operasi logika atau kontrol alur
    keywords = ['if', 'for', 'while', 'switch', '+', '-', '*', '/', '%', '=']
    
    # Jika panjang terlalu pendek, kemungkinan hanya return
    if not function_body_str or len(function_body_str.strip()) < 10:
        return False
    
    # Cek apakah ada kata kunci logika
    return any(keyword in function_body_str for keyword in keywords)

def count_WOC(result):
    method_count = 0
    functional_method_count = 0

    class_declaration = result.declarations[0]

    for member in class_declaration.body.members:
        if isinstance(member, node.FunctionDeclaration):
            method_count += 1
            function_body_str = str(member.body) if member.body else ""
            
            if is_functional_method(function_body_str):
                functional_method_count += 1
    
    return functional_method_count / method_count if method_count > 0 else 0

def count_Number_Final_Not_Static_Methods(class_node):
    return sum(1 for member in class_node.body.members 
               if isinstance(member, node.FunctionDeclaration) and 
               "final" in getattr(member, "modifiers", []) and 
               "static" not in getattr(member, "modifiers", []))

def NMCS_counter(class_nodes, method_nodes):
    """menghitung pemanggilan sebuah fungsi pada fungsi lain"""
    function_names = []
    method_count = 0

    for member in class_nodes.body.members:
        if isinstance(member, node.FunctionDeclaration):
            function_name = member.name
            function_names.append(function_name)
    

    for line in method_nodes.split("\n"):
        stripped = line.strip()
        for strips in stripped.split():    
            for keyword in function_names:
                if strips.startswith(keyword):
                    method_count += 1

    return method_count

def split_to_tokens(line):
    tokens = []
    current = ''
    in_string = False
    quote_char = ''
    
    for ch in line:
        if ch in ['"', "'"]:
            if not in_string:
                in_string = True
                quote_char = ch
            elif quote_char == ch:
                in_string = False
                quote_char = ''
            continue

        if in_string:
            continue  # Skip characters inside quotes

        if ch.isalnum() or ch == '_':
            current += ch
        else:
            if current:
                tokens.append(current)
                current = ''
    if current:
        tokens.append(current)
    return tokens

def is_valid_var_name(token):
    """Check if a token is a valid variable name (simple version, no regex)."""
    if not token:
        return False
    if any(c in token for c in "<>-+="):
        return False
    if token[0].isdigit():
        return False
    return token.isidentifier()

def laa_method(class_node, method_node):
    """Menghitung Local Attribute Access (LAA) dari method termasuk parameternya sendiri."""
    class_vars = []     # Variabel yang dideklarasikan di class
    method_params = []   # Parameter method saat ini
    local_access = 0
    param_acces = 0
    
    # Ambil semua properti dalam class
    for member in class_node.members:
        if isinstance(member, node.PropertyDeclaration):
            class_vars.append(member.declaration.name)

    # Ambil semua parameter dari method ini saja
    if isinstance(method_node, node.FunctionDeclaration):
        method_params = [param.name for param in method_node.parameters]

        body_str = str(method_node.body) if method_node.body else ""

        for line in body_str.split("\n"):
            stripped = line.strip()
            tokens = split_to_tokens(stripped)
            for token in tokens:
                if token in class_vars:
                    local_access += 1
                    # print(f"Access class var : {token} in line : {stripped}")
                elif token in method_params:
                    param_acces += 1
                    # print(f"Access method param : {token} in line : {stripped}")

        # LAA = jumlah akses terhadap atribut lokal (class + param) dibagi jumlah total variabel yang mungkin diakses
        total_locals = local_access + param_acces
        print(f"Total accessed: {local_access}, Total locals (class + param): {total_locals}")
        return local_access / total_locals if total_locals else 0

    return 0

def tcc_type(class_node, result):
    """Menghitung TCC (Tight Class Cohession) dari sebuah class."""
    properties = []
    
    class_declaration = result.declarations[0]
    total_method = 0

    if class_node is None:
        return len(properties)
    
    for member in class_node.members:
        if isinstance(member, node.PropertyDeclaration):
            properties.append(member.declaration.name)

    same_proper = []
    
    for member in class_declaration.body.members:
        if isinstance(member, node.FunctionDeclaration):
            total_method += 1
            method_node = str(member.body)

            matched_keyword = False

            for line in method_node.split("\n"):
                stripped = line.strip()
                tokens = split_to_tokens(stripped)
                for token in tokens:
                    if token in properties:
                        same_proper.append({"funct_name": member.name, "keyword": token})
                        matched_keyword = True
            if not matched_keyword:
                same_proper.append({"funct_name": member.name, "keyword": " "})

    # Membuat dictionary: fungsi -> list keyword
    function_keywords = {}
    for item in same_proper:
        func = item["funct_name"]
        keyword = item["keyword"]
        if keyword != " ":  # Abaikan jika keyword kosong
            if func not in function_keywords:
                function_keywords[func] = set()
            function_keywords[func].add(keyword)

    shared_access_count = 0
    functions = list(function_keywords.keys())

    # Bandingkan setiap pasangan fungsi
    for i in range(len(functions)):
        for j in range(i + 1, len(functions)):
            func1 = functions[i]
            func2 = functions[j]
            if function_keywords[func1].intersection(function_keywords[func2]):
                shared_access_count += 1
    
    method_pair_max = total_method*(total_method - 1)/2
    # (Optional) Kalau kamu mau menghitung seperti ini, pastikan jumlah property != 0
    return shared_access_count/method_pair_max if method_pair_max != 0 else 0

def calculate_AMWNAMM(method_function):
    """Menghitung AMWNAMM berdasarkan Cyclometric Complexity."""
    
    cyclo = []
    method_names = []

    for method_name, (cc, _, _, _, _, _) in method_function.items():
        if cc > 0:
            cyclo.append(cc)
            method_names.append(method_name)

    return sum(cyclo) / len(method_names) if cyclo else 0

import traceback
import inspect


def extracted_method(file_path):
    """Ekstrak informasi metode dari file Kotlin."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
        
        parser = Parser(code)
        result = parser.parse()
        package_name = result.package.name if result.package else "Unknown"

        if not result.declarations:
            return [{"Package": package_name, "Class": "Unknown", "Method": "None", "LOC": 0, "Max Nesting": 0, "CC": 0, "WOC": 0,  "count_num_final_not_static_attributes": 0, "NMCS": 0, "LAA": 0, "TCC": 0, "AMWNAMM":0, "Error": "No class declaration found"}]
        
        class_declaration = result.declarations[0]
        class_name = class_declaration.name
        
        if class_declaration.body is None:
            return [{"Package": package_name, "Class": class_name, "Method": "None", "LOC": 0, "Max Nesting": 0, "CC": 0, "WOC": 0, "count_num_final_not_static_attributes": 0, "NMCS": 0, "LAA": 0, "TCC": 0, "AMWNAMM":0, "Error": "Class has no body"}]
        
        datas = []
        method_function = {}
        if hasattr(class_declaration, "body") and hasattr(class_declaration.body, "members"):
            for member in class_declaration.body.members:
                if isinstance(member, node.FunctionDeclaration):
                    function_names = member.name
                    loc_count = str(member.body).count("\n") + 1 if member.body else 0
                    function_body_str = str(member.body)
                    maxnesting = manual_max_nesting(str(member.body)) if member.body else 0
                    cc_value = count_cc_manual(str(member.body)) if member.body else 0
                    #print(f"code method :{method_code}")
                    nmcs_count = NMCS_counter(class_declaration,function_body_str)
                    laa_value = laa_method(class_declaration.body, member)
                    tcc_value = tcc_type(class_declaration.body, result)
                    count_num_final_not_static_attributes_values = count_Number_Final_Not_Static_Methods(class_declaration)        
                    method_function[function_names] = (cc_value, loc_count, maxnesting, nmcs_count, laa_value, tcc_value)

        cc_values = [cc for cc, _, _, _, _, _ in method_function.values()]
        amwnamm_value = calculate_AMWNAMM(method_function)
        woc_values = count_WOC(result)
        
        
        

        for function_names, (cc_value, loc_count, maxnesting, nmcs_count, laa_value, tcc_value) in method_function.items():
                
                    datas.append({
                        "Package": package_name, 
                        "Class": class_name, 
                        "Method": function_names, 
                        "LOC": loc_count, 
                        "Max Nesting": maxnesting, 
                        "CC": cc_value, 
                        "WOC": woc_values, 
                        "count_num_final_not_static_attributes" : count_num_final_not_static_attributes_values,
                        "NMCS": nmcs_count,
                        "LAA": laa_value, 
                        "TCC": tcc_value, 
                        "AMWNAMM": amwnamm_value
                        })
         
        return datas if datas else [{"Package": package_name, "Class": class_name, "Method": "None", "LOC": 0, "Max Nesting": 0, "CC": 0, "WOC": 0, "count_num_final_not_static_attributes": 0, "NMCS": 0, "LAA": 0, "TCC": 0, "AMWNAMM":0, "Error": "No functions found"}]
    
    except Exception as e:
        # get the current stack frame
        tb = traceback.extract_tb(e.__traceback__)
    
        # get the last call in the traceback (where the error occurred)
        last_frame = tb[-1] if tb else None
    
        # default values
        package_name = "UnknownPackage"
        class_name = "UnknownClass"
        method_name = "UnknownMethod"

        if last_frame:
            filename = last_frame.filename
            method_name = last_frame.name

            # Try to guess class name using inspect
            current_frame = inspect.currentframe()
            outer_frames = inspect.getouterframes(current_frame)
            for frame_info in outer_frames:
                if frame_info.function == method_name:
                    class_name = frame_info.frame.f_locals.get('self', '__main__').__class__.__name__
                    break

            # Optional: set package name from filename or module
            package_name = filename.split('/')[-2] if '/' in filename else "Main"

        return [{
            "Package": package_name,
            "Class": class_name,
            "Method": method_name,
            "LOC": "Error",
            "Max Nesting": 0,
            "CC": 0,
            "WOC": 0,
            "Error": str(e)
        }]
    
def detail_report_parse(file):
    """Ekstrak arsip ZIP/RAR dan proses file Kotlin."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file_path = os.path.join(temp_dir, file.name)
        with open(temp_file_path, "wb") as f:
            f.write(file.getbuffer())
        
        try:
            patoolib.extract_archive(temp_file_path, outdir=temp_dir)
            kotlin_files = [os.path.join(root, f) for root, _, files in os.walk(temp_dir) for f in files if f.endswith(".kt")]
            
            package_dict = {}
            for kotlin_file in kotlin_files:
                result = detail_report(kotlin_file)
                if "Packages" in result:
                    for package, details in result["Packages"].items():
                        if package not in package_dict:
                            package_dict[package] = {
                                "File": [],
                                "Class": [],
                                "Method": [],
                                "Property": []
                            }
                        package_dict[package]["File"].append(details["File"])
                        package_dict[package]["Class"].extend(details["Class"])
                        package_dict[package]["Method"].extend(details["Method"])
                        package_dict[package]["Property"].extend(details["Property"])
                elif "error" in result:
                    return result  # return error langsung

            return {"Packages": package_dict}
        except Exception as e:
            return "extract and parser : ", str(e)
    

from pathlib import Path

def detail_report(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()

        parser = Parser(code)
        result = parser.parse()

        package_name = result.package.name if result.package else "Unknown"
        class_declaration = result.declarations[0] if result.declarations else None
        class_name = class_declaration.name if class_declaration else "Unknown"

        methods = []
        properties = []

        if class_declaration and class_declaration.body and hasattr(class_declaration.body, "members"):
            for member in class_declaration.body.members:
                if isinstance(member, node.FunctionDeclaration):
                    methods.append(member.name)
                elif isinstance(member, node.PropertyDeclaration):
                    properties.append(member.declaration.name)

        file_name = Path(file_path).name

        package_dict = {
            package_name: {
                "File": file_name,
                "Class": [class_name],
                "Method": methods,
                "Property": properties
            }
        }

        return {"Packages": package_dict}

    except Exception as e:
        return {"error": f"detail report error: {str(e)}"}
    
def calculate_cognitive_complexity(line):
    # Logika untuk menghitung kompleksitas kognitif
    complexity = 0
    # Memeriksa apakah ada struktur kontrol dalam baris
    if any(
        keyword in line
        for keyword in [
            "if",  # Percabangan jika
            "else",  # Percabangan lain
            "for",  # Perulangan untuk
            "while",  # Perulangan selama
            "do",  # Perulangan do-while
            "when",  # Percabangan ketika
            "switch",  # Percabangan switch
            "case",  # Kasus dalam switch
            "try",  # Blok percobaan
            "catch",  # Menangkap exception
        ]
    ):
        complexity += 1  # Tingkatkan kompleksitas untuk setiap struktur kontrol
    return complexity


def calculate_mcc(line):
    # Logika untuk menghitung kompleksitas siklomatik
    count = 0
    # Memeriksa apakah ada struktur kontrol dalam baris
    if any(
        keyword in line
        for keyword in [
            "if",  # Percabangan jika
            "else",  # Percabangan lain
            "for",  # Perulangan untuk
            "while",  # Perulangan selama
            "do",  # Perulangan do-while
            "when",  # Percabangan ketika
            "switch",  # Percabangan switch
            "case",  # Kasus dalam switch
            "try",  # Blok percobaan
            "catch",  # Menangkap exception
        ]
    ):
        count += 1  # Hitung cabang
    return count

def complexity_report_parse(file):
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file_path = os.path.join(temp_dir, file.name)
        with open(temp_file_path, "wb") as f:
            f.write(file.getbuffer())
        
        try:
            patoolib.extract_archive(temp_file_path, outdir=temp_dir)
            kotlin_files = [os.path.join(root, f) for root, _, files in os.walk(temp_dir) for f in files if f.endswith(".kt")]
            
            
            results = complexity_report(temp_dir)
            
            return results

        except Exception as e:
            return "extract and parser : ", str(e)

def identify_code_smells(lines):
    # Fungsi untuk mengidentifikasi code smells
    smells = 0
    # Memeriksa setiap baris dalam kode
    for line in lines:
        # Contoh smell: metode yang terlalu panjang
        if (
            len(line.strip()) > 100
        ):  # Menghitung jika panjang baris lebih dari 100 karakter
            smells += 1  # Tingkatkan jumlah code smells
    return smells

def complexity_report(directory):
    loc = 0
    sloc = 0
    lloc = 0
    cloc = 0
    cognitive_complexity = 0
    code_smells = 0
    comment_ratio = 0
    mcc_count = 0
    total_code_smells = 0

    try:
        for root, dirs, files_in_dir in os.walk(directory):
            for file in files_in_dir:
                if file.endswith(".kt"):  # Memeriksa file Kotlin
                    file_path = os.path.join(root, file)
                    with open(file_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()  # Membaca semua baris dalam file

                        # Menghitung total baris kode (loc)
                        loc += len(lines)

                        # Menghitung kode sumber (sloc), baris logis (lloc), dan komentar (cloc)
                        for line in lines:
                            stripped_line = (
                                line.strip()
                            )  # Menghapus spasi di awal dan akhir
                            if stripped_line.startswith("//"):
                                cloc += 1  # Menghitung baris komentar
                            elif stripped_line != "":
                                sloc += 1  # Menghitung baris sumber
                                lloc += 1  # Menghitung setiap baris non-kosong sebagai baris logis

                                # Menghitung kompleksitas kognitif dan MCC
                                cognitive_complexity += calculate_cognitive_complexity(
                                    stripped_line
                                )
                                mcc_count += calculate_mcc(stripped_line)

                        # Menghitung total code smells
                        total_code_smells += identify_code_smells(lines)
        # Menghitung metrik
        if lloc > 0:
            comment_ratio = (
                (cloc / sloc) * 100 if sloc > 0 else 0
            )  # Menghitung rasio komentar
            mcc_per_1000_lloc = (
                (mcc_count / (lloc / 1000)) if lloc > 0 else 0
            )  # MCC per 1000 baris logis
            code_smells_per_1000_lloc = (
                (total_code_smells / (lloc / 1000)) if lloc > 0 else 0
            )  # Code smells per 1000 baris logis

        # Mengembalikan hasil laporan kompleksitas
        return {
            "LOC": loc,  # Total baris kode
            "SLOC": sloc,  # Total baris sumber
            "LLOC": lloc,  # Total baris logis
            "CLOC": cloc,  # Total baris komentar
            "Cognitive_Complexity": cognitive_complexity,  # Kompleksitas kognitif
            "Code_Smells": total_code_smells,  # Total code smells
            "Comment_Ratio": comment_ratio,  # Rasio komentar
            "MCC_per_1000_lloc": mcc_per_1000_lloc,  # MCC per 1000 baris logis
            "Code_smells_per_1000_lloc": code_smells_per_1000_lloc,  # Code smells per 1000 baris logis
        }

    except Exception as e:
        return {"error": f"complex report error: {str(e)}"}

        
def extract_and_parse(file):
    """Ekstrak arsip ZIP/RAR dan proses file Kotlin."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file_path = os.path.join(temp_dir, file.name)
        with open(temp_file_path, "wb") as f:
            f.write(file.getbuffer())
        
        try:
            patoolib.extract_archive(temp_file_path, outdir=temp_dir)
            kotlin_files = [os.path.join(root, f) for root, _, files in os.walk(temp_dir) for f in files if f.endswith(".kt")]
            
            results = []
            for kotlin_file in kotlin_files:
                results.extend(extracted_method(kotlin_file))
            
            return pd.DataFrame(results)
        except Exception as e:
            return "extract and parser : ", str(e)
