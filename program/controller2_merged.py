# ======= Begin: controller albert.py =======
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
    control_keywords = ["if", "for", "while", "when", "catch", "case"]

    # Memisahkan kode menjadi baris-baris
    lines = method_code.split("\n")

    for line in lines:
        stripped = line.strip()
        # Menghitung struktur kontrol
        for keyword in control_keywords:
            if stripped.startswith(keyword):
                cc += 1  # Setiap struktur kontrol menambah CC
    return cc

def count_woc(cc_values):
    """Menghitung Weighted Operations Count (WOC)."""
    total_CC = sum(cc_values)
    return [cc / total_CC if total_CC else 0 for cc in cc_values]

def count_num_final_not_static_attributes(file_path):
    """Count the number of final non-static attributes in a Kotlin project."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
        
        parser = Parser(code)
        result = parser.parse()

        if not result.declarations:
            return 0
        
        attribute_count = 0

        for declaration in result.declarations:
            if isinstance(declaration, node.ClassDeclaration):
                # print(f"Class: {declaration.name}")
                for member in declaration.body.members:
                    if isinstance(member, node.PropertyDeclaration):
                        # Extract the property name from the declaration or value
                        property_name = None
                        if hasattr(member, "declaration") and hasattr(member.declaration, "name"):
                            property_name = member.declaration.name
                        elif hasattr(member, "value") and hasattr(member.value, "name"):
                            property_name = member.value.name
                        else:
                            # Fallback: Try to extract the name from the string representation
                            property_str = str(member)
                            if "var" in property_str or "val" in property_str:
                                property_name = property_str.split()[1].split(":")[0].strip()
                        
                        if property_name:
                            # print(f"Property: {property_name}")
                            
                            # Check if the property is final (either declared with 'val' or not marked as 'open')
                            is_final = ("val" in str(member) or "open" not in getattr(member, "modifiers", []))
                            
                            # Check if the property is not static (not in companion object and not top-level)
                            is_not_static = not any(isinstance(parent, node.CompanionObject) for parent in getattr(member, "parents", [])) and "static" not in getattr(member, "modifiers", [])
                            
                            if is_final and is_not_static:
                                print(f"Final non-static property: {property_name}")
                                attribute_count += 1
        
        return attribute_count
    
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return 0

def count_num_static_not_final_attributes(file_path):
    """Count the number of static but not final attributes in a Kotlin project."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
        
        parser = Parser(code)
        result = parser.parse()

        if not result.declarations:
            return 0
        
        attribute_count = 0

        for declaration in result.declarations:
            if isinstance(declaration, node.ClassDeclaration):
                print(f"Class: {declaration.name}")
                for member in declaration.body.members:
                    if isinstance(member, node.CompanionObject):
                        # Check properties inside the companion object
                        for companion_member in member.body.members:
                            if isinstance(companion_member, node.PropertyDeclaration):
                                # Extract the property name
                                property_name = None
                                if hasattr(companion_member, "declaration") and hasattr(companion_member.declaration, "name"):
                                    property_name = companion_member.declaration.name
                                elif hasattr(companion_member, "value") and hasattr(companion_member.value, "name"):
                                    property_name = companion_member.value.name
                                else:
                                    # Fallback: Try to extract the name from the string representation
                                    property_str = str(companion_member)
                                    if "var" in property_str or "val" in property_str:
                                        property_name = property_str.split()[1].split(":")[0].strip()
                                
                                if property_name:
                                    print(f"Property: {property_name}")
                                    
                                    # Check if the property is not final (marked as 'open' or declared with 'var')
                                    is_not_final = "open" in getattr(companion_member, "modifiers", []) or "var" in str(companion_member)
                                    
                                    if is_not_final:
                                        print(f"Static non-final property: {property_name}")
                                        attribute_count += 1
        
        return attribute_count
    
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return 0

def number_public_visibility_methods(file_path):
    """Count the number of public visibility methods in a Kotlin project."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
        
        parser = Parser(code)
        result = parser.parse()

        if not result.declarations:
            return 0
        
        public_method_count = 0

        for declaration in result.declarations:
            if isinstance(declaration, node.ClassDeclaration):
                print(f"Class: {declaration.name}")
                for member in declaration.body.members:
                    if isinstance(member, node.FunctionDeclaration):
                        # Check if the method is public (no visibility modifier or explicitly marked as 'public')
                        modifiers = getattr(member, "modifiers", [])
                        is_public = "private" not in modifiers and "protected" not in modifiers and "internal" not in modifiers
                        
                        if is_public:
                            print(f"Public method: {member.name}")
                            public_method_count += 1
        
        return public_method_count
    
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return 0


def number_private_visibility_methods(file_path):
    """Count the number of private visibility methods in a Kotlin project."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
        
        parser = Parser(code)
        result = parser.parse()

        if not result.declarations:
            return 0
        
        private_method_count = 0

        for declaration in result.declarations:
            if isinstance(declaration, node.ClassDeclaration):
                print(f"Class: {declaration.name}")
                for member in declaration.body.members:
                    if isinstance(member, node.FunctionDeclaration):
                        # Check if the method is private
                        modifiers = getattr(member, "modifiers", [])
                        is_private = "private" in modifiers
                        
                        if is_private:
                            print(f"Private method: {member.name}")
                            private_method_count += 1
        
        return private_method_count
    
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return 0

def number_protected_visibility_methods(file_path):
    """Count the number of protected visibility methods in a Kotlin project."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
        
        parser = Parser(code)
        result = parser.parse()

        if not result.declarations:
            return 0
        
        protected_method_count = 0

        for declaration in result.declarations:
            if isinstance(declaration, node.ClassDeclaration):
                print(f"Class: {declaration.name}")
                for member in declaration.body.members:
                    if isinstance(member, node.FunctionDeclaration):
                        # Check if the method is protected
                        modifiers = getattr(member, "modifiers", [])
                        is_protected = "protected" in modifiers
                        
                        if is_protected:
                            print(f"Protected method: {member.name}")
                            protected_method_count += 1
        
        return protected_method_count
    
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return 0


def number_package_visibility_methods(file_path):
    """Count the number of package visibility methods in a Kotlin project."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
        
        parser = Parser(code)
        result = parser.parse()

        if not result.declarations:
            return 0
        
        package_method_count = 0

        for declaration in result.declarations:
            if isinstance(declaration, node.ClassDeclaration):
                print(f"Class: {declaration.name}")
                for member in declaration.body.members:
                    if isinstance(member, node.FunctionDeclaration):
                        # Check if the method has package visibility (no explicit visibility modifier)
                        modifiers = getattr(member, "modifiers", [])
                        is_package_visibility = (
                            "public" not in modifiers and
                            "private" not in modifiers and
                            "protected" not in modifiers and
                            "internal" not in modifiers
                        )

                        if is_package_visibility:
                            print(f"Package visibility method: {member.name}")
                            package_method_count += 1

        return package_method_count
    
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return 0

def number_standard_design_methods(file_path):
    """Count the number of standard design pattern methods in a Kotlin project."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
        
        parser = Parser(code)
        result = parser.parse()

        if not result.declarations:
            return 0
        
        design_method_count = 0
        design_pattern_indicators = {
            # Factory pattern indicators
            'create', 'make', 'newInstance', 'of', 'from',
            # Builder pattern indicators
            'build', 'builder', 'construct', 'assemble',
            # Singleton pattern indicators
            'getInstance', 'instance',
            # Other common patterns
            'clone', 'copy', 'parse', 'load', 'save'
        }

        for declaration in result.declarations:
            if isinstance(declaration, node.ClassDeclaration):
                print(f"Class: {declaration.name}")
                for member in declaration.body.members:
                    if isinstance(member, node.FunctionDeclaration):
                        method_name = member.name.lower()
                        
                        # Check if method name matches any design pattern indicator
                        if any(indicator in method_name for indicator in design_pattern_indicators):
                            print(f"Design method: {member.name}")
                            design_method_count += 1
                        
                        # Check for factory methods by return type
                        if hasattr(member, 'return_type') and member.return_type:
                            return_type = str(member.return_type)
                            if 'factory' in return_type.lower() or 'companion' in str(member.parents).lower():
                                print(f"Factory method: {member.name}")
                                design_method_count += 1
        
        return design_method_count
    
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return 0

def number_constructor_DefaultConstructor_methods(file_path):
    """Count the number of default constructors in a Kotlin project using AST parsing."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
        
        parser = Parser(code)
        result = parser.parse()
        
        default_constructors = 0
        
        for declaration in result.declarations:
            # Skip if not a class declaration or if it's an object declaration
            if not isinstance(declaration, node.ClassDeclaration) or isinstance(declaration, node.ObjectDeclaration):
                continue
            
            # Skip abstract classes
            if hasattr(declaration, 'modifiers') and 'abstract' in declaration.modifiers:
                continue
                
            has_any_constructor = False
            class_body = getattr(declaration, 'class_body', None)
            
            # Check primary constructor in class header
            primary_constructor = getattr(declaration, 'primary_constructor', None)
            if primary_constructor:
                has_any_constructor = True
                
                # Check if the primary constructor has no parameters
                value_parameters = getattr(primary_constructor, 'value_parameters', [])
                if not value_parameters:
                    default_constructors += 1
            
            # Check for secondary constructors in class body
            if class_body:
                for member in getattr(class_body, 'declarations', []):
                    if isinstance(member, node.Constructor):
                        has_any_constructor = True
                        
                        # Check if the secondary constructor has no parameters
                        value_parameters = getattr(member, 'value_parameters', [])
                        if not value_parameters:
                            default_constructors += 1
            
            # If no constructors found and class is not abstract or object, 
            # it has an implicit default constructor
            if not has_any_constructor:
                default_constructors += 1
        
        return default_constructors
    
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return 0

def extracted_method(file_path):
    """Ekstrak informasi metode dari file Kotlin."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
        
        parser = Parser(code)
        result = parser.parse()
        package_name = result.package.name if result.package else "Unknown"

        if not result.declarations:
            return [{"Package": package_name, "Class": "Unknown", "Method": "None", "LOC": 0, "Max Nesting": 0, "CC": 0, "WOC": 0, "Error": "No class declaration found"}]
        
        class_declaration = result.declarations[0]
        class_name = class_declaration.name
        
        if class_declaration.body is None:
            return [{"Package": package_name, "Class": class_name, "Method": "None", "LOC": 0, "Max Nesting": 0, "CC": 0, "WOC": 0, "Error": "Class has no body"}]
        
        datas = []
        method_function = {}
        for member in class_declaration.body.members:
            if isinstance(member, node.FunctionDeclaration):
                function_names = member.name
                loc_count = str(member.body).count("\n") + 1 if member.body else 0
                maxnesting = manual_max_nesting(str(member.body)) if member.body else 0
                cc_value = count_cc_manual(str(member.body)) if member.body else 0

                
                method_function[function_names] = (cc_value, loc_count, maxnesting)

        cc_values = [cc for cc, _, _ in method_function.values()]
        woc_values = count_woc(cc_values)
        count_num_final_not_static_attributes_values = count_num_final_not_static_attributes(file_path)
        num_static_not_final_attributes_values = count_num_static_not_final_attributes(file_path)
        number_public_visibility_methods_values = number_public_visibility_methods(file_path)
        number_private_visibility_methods_values = number_private_visibility_methods(file_path)
        number_protected_visibility_methods_values = number_protected_visibility_methods(file_path)
        number_package_visibility_methods_values = number_package_visibility_methods(file_path)
        number_standard_design_methods_values = number_standard_design_methods(file_path)
        number_constructor_DefaultConstructor_values = number_constructor_DefaultConstructor_methods(file_path)

        for (function_names, (cc_value, loc_count, maxnesting)), woc in zip(method_function.items(), woc_values):
                
                    datas.append({
                        "Package": package_name,
                        "Class": class_name,
                        "Method": function_names,
                        "LOC": loc_count,
                        "Max Nesting": maxnesting,
                        "CC": cc_value,
                        "WOC": woc,
                        "count_num_final_not_static_attributes" : count_num_final_not_static_attributes_values,
                        "num_static_not_final_attributes" : num_static_not_final_attributes_values,
                        "number_public_visibility_methods" : number_public_visibility_methods_values,
                        "number_private_visibility_methods" : number_private_visibility_methods_values,
                        "number_protected_visibility_methods" : number_protected_visibility_methods_values,
                        "number_package_visibility_methods" : number_package_visibility_methods_values,
                        "number_standard_design_methods" : number_standard_design_methods_values,
                        "number_constructor_DefaultConstructor_methods" : number_constructor_DefaultConstructor_values
                        })
        
        return datas if datas else [{"Package": package_name, "Class": class_name, "Method": "None", "LOC": 0, "Max Nesting": 0, "CC": 0, "WOC": 0,"Error": "No functions found"}]
    
    except Exception as e:
        return [{"Package": "Error", "Class": "Error", "Method": "Error", "LOC": "Error", "Max Nesting": 0, "CC": 0, "WOC": 0, "Error": str(e)}]

def extract_and_parse(file):
    """Ekstrak arsip ZIP/RAR dan proses file Kotlin."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file_path = os.path.join(temp_dir, file.name)
        with open(temp_file_path, "wb") as f:
            f.write(file.getbuffer())
        
        try:
            patoolib.extract_archive(temp_file_path, outdir=temp_dir)
            kotlin_files = [os.path.join(root, f) for root, _, files in os.walk(temp_dir) for f in files if f.endswith(".kt") or f.endswith(".kts")]
            
            results = []
            for kotlin_file in kotlin_files:
                results.extend(extracted_method(kotlin_file))
            
            return pd.DataFrame(results)
        except Exception as e:
            return str(e)

# def test_default_constructor_detection(file_path):
#     """Test the default constructor detection on a specific file."""
#     count = number_constructor_DefaultConstructor_methods(file_path)
#     print(f"\nAnalyzing file: {os.path.basename(file_path)}")
#     print(f"Number of default constructors found: {count}")
    
#     # Read and parse the file to show class details
#     with open(file_path, "r", encoding="utf-8") as f:
#         code = f.read()
    
#     parser = Parser(code)
#     result = parser.parse()
    
#     print("\nClasses found:")
#     for declaration in result.declarations:
#         if isinstance(declaration, node.ClassDeclaration):
#             print(f"\nClass: {declaration.name}")
#             if hasattr(declaration, 'modifiers'):
#                 print(f"Modifiers: {declaration.modifiers}")
            
#             primary_constructor = getattr(declaration, 'primary_constructor', None)
#             if primary_constructor:
#                 params = getattr(primary_constructor, 'value_parameters', [])
#                 print(f"Primary constructor found with {len(params)} parameters")
#             else:
#                 print("No primary constructor (implicit default constructor)")
                
#             class_body = getattr(declaration, 'class_body', None)
#             if class_body:
#                 secondary_constructors = [m for m in getattr(class_body, 'declarations', []) 
#                                        if isinstance(m, node.Constructor)]
#                 if secondary_constructors:
#                     print(f"Secondary constructors found: {len(secondary_constructors)}")
#                 else:
#                     print("No secondary constructors")
                    
#     return count


# ======= Begin: controller angk 19.py =======
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

# ======= Begin: controller henry.py =======
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
    print(f"[DEBUG is_static_method] Method: {getattr(member, 'name', 'Unknown')}, Modifiers: {getattr(member, 'modifiers', None)}, In companion: {in_companion}")
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

        abstract_count = number_abstract_methods(class_decl)
        final_count = number_final_methods(class_decl)
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


# ======= Begin: controller indarto.py =======
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

# ======= Begin: controller jason.py =======
import os
import tempfile
import patoolib
import pandas as pd
from kopyt import Parser, node
import re 

def manual_max_nesting(code):
    indent_stack = []
    max_depth = 0
    for line in code.split("\n"):
        line = line.strip()
        if line.startswith(("if", "for", "while", "catch", "when", "try", "else")):
            indent_stack.append(line)
            max_depth = max(max_depth, len(indent_stack))
        elif line == "}":
            if indent_stack:
                indent_stack.pop()
    return max_depth

def count_cc_manual(code):
    cc = 1
    control_keywords = ["if", "for", "while", "when", "catch", "case"]
    for line in code.split("\n"):
        line = line.strip()
        for kw in control_keywords:
            if line.startswith(kw):
                cc += 1
    return cc

def count_woc(cc_values):
    total = sum(cc_values)
    return [cc / total if total > 0 else 0 for cc in cc_values]

def count_mamcl(code):
    max_chain = 0
    lines = code.splitlines()
    for line in lines:
        line = line.strip()
        if not line or line.startswith(("//", "/*", "*", "*/")):
            continue
            
        # Cari semua chain method calls dalam satu baris
        current_chain = 0
        parts = line.split(".")
        if len(parts) > 1:
            # Mulai dari index 1 karena index 0 adalah objek
            for part in parts[1:]:
                # Check if it's a method call (contains parentheses)
                if "(" in part and ")" in part:
                    current_chain += 1
                else:
                    # Reset if not a method call, as the chain is broken
                    current_chain = 0
                    break # Stop processing this line as chain is broken
        max_chain = max(max_chain, current_chain)
    return max_chain


def count_cm_method(method_code, all_methods_in_file):
    """Count Coupling between Methods (CM)"""
    count = 0
    method_lines = method_code.splitlines()
    
    for method_name in all_methods_in_file:
        # We need to make sure we are looking for actual calls, not just substrings
        # and not the method itself if it's currently being analyzed.
        # This is a heuristic. A full AST-based approach would be more robust.
        
        # Avoid counting the method itself as coupling with itself
        # This check is heuristic and might miss cases.
        # Example: if method 'foo' calls 'this.foo()', it would still be counted by simple string match.
        # For simplicity, we assume 'method_name' is usually unique enough here.
        
        for line in method_lines:
            line = line.strip()
            if not line or line.startswith(("//", "/*", "*", "*/")):
                continue
                
            # A more robust check for method calls.
            # Look for "methodName(" or "methodName ("
            # This avoids matching if "methodName" is just part of a variable name.
            if re.search(r'\b' + re.escape(method_name) + r'\s*\(', line):
                count += 1
                break  # Count once per distinct method called within the current method
    return count


def count_loc_type(class_code):
    return class_code.count("\n") + 1


def count_locnamm_type(class_decl):
    count = 0
    if hasattr(class_decl, 'body') and class_decl.body and hasattr(class_decl.body, 'members'):
        for member in class_decl.body.members:
            if isinstance(member, node.FunctionDeclaration):
                # Check if it's a non-accessor method
                if not member.name.startswith(("get", "set", "is")):
                    count += str(member.body).count("\n") + 1 if member.body else 0
    return count

def count_cfnamm_type(class_decl):
    methods = []
    if hasattr(class_decl, 'body') and class_decl.body and hasattr(class_decl.body, 'members'):
        for m in class_decl.body.members:
            if isinstance(m, node.FunctionDeclaration) and not m.name.startswith(("get", "set", "is")):
                methods.append(m.name)
    coupled = 0
    if hasattr(class_decl, 'body') and class_decl.body and hasattr(class_decl.body, 'members'):
        for m in class_decl.body.members:
            if isinstance(m, node.FunctionDeclaration) and m.name in methods:
                body = str(m.body)
                # Check for calls to other non-accessor methods within the same class
                if any(other_method_name != m.name and re.search(r'\b' + re.escape(other_method_name) + r'\s*\(', body) for other_method_name in methods):
                    coupled += 1
    return coupled / len(methods) if methods else 0

def count_noav_class(class_decl):
    count = 0
    # Ensure class_decl.body and class_decl.body.members exist
    if hasattr(class_decl, 'body') and class_decl.body and hasattr(class_decl.body, 'members'):
        for member in class_decl.body.members:
            # Only count property/variable declarations at the class level
            if isinstance(member, node.PropertyDeclaration):


                count += 1  # Increment for each class-level property
            # Also check for VariableDeclaration, but typically not used for class-level in Kopyt
            elif hasattr(node, 'VariableDeclaration') and isinstance(member, node.VariableDeclaration):
                # Not incrementing count here, as class-level variables are usually PropertyDeclaration
                pass 
    return count  # Total number of class-level attributes (properties/fields)  # Total number of class-level attributes (properties/fields)

def count_noav(class_node, method_code, method_node=None):
    """
    Menghitung NOAV (Number of Attributes Accessed in a Method) dengan benar.
    1. Kumpulkan semua nama atribut (property/field) dari class (termasuk companion object jika ada).
    2. Kumpulkan semua nama atribut yang diakses di method (this.<var>, super.<var>, atau akses langsung <var>).
    3. Exclude variabel lokal dan parameter method dari akses langsung.
    4. Intersect kedua set.
    5. Return jumlah hasil irisan.
    """
    declared_vars = set()

    # 1. Kumpulkan semua nama atribut dari class (PropertyDeclaration dan VariableDeclaration)
    if hasattr(class_node, 'body') and hasattr(class_node.body, 'members'):
        for member in class_node.body.members:
            # PropertyDeclaration (val/var property)
            if isinstance(member, node.PropertyDeclaration):
                if hasattr(member, 'declaration') and hasattr(member.declaration, 'name'):
                    declared_vars.add(member.declaration.name)
                elif hasattr(member, 'name'):
                    declared_vars.add(member.name)
            # VariableDeclaration (jarang, tapi bisa saja)
            elif isinstance(member, node.VariableDeclaration):
                if hasattr(member, 'name'):
                    declared_vars.add(member.name)
            # Companion object property (hanya jika object declaration bernama 'Companion')
            elif isinstance(member, node.ObjectDeclaration) and getattr(member, 'name', None) == "Companion":
                if hasattr(member, 'body') and hasattr(member.body, 'members'):
                    for submember in member.body.members:
                        if isinstance(submember, node.PropertyDeclaration):
                            if hasattr(submember, 'declaration') and hasattr(submember.declaration, 'name'):
                                declared_vars.add(submember.declaration.name)
                            elif hasattr(submember, 'name'):
                                declared_vars.add(submember.name)
                        elif isinstance(submember, node.VariableDeclaration):
                            if hasattr(submember, 'name'):
                                declared_vars.add(submember.name)

    # 2. Kumpulkan semua nama variable yang diakses di method_code
    accessed_vars = set()
    # this.<var>
    accessed_vars.update(re.findall(r'\bthis\.([a-zA-Z_][a-zA-Z0-9_]*)\b', method_code))
    # super.<var>
    accessed_vars.update(re.findall(r'\bsuper\.([a-zA-Z_][a-zA-Z0-9_]*)\b', method_code))

    # 3. Exclude variabel lokal dan parameter method dari akses langsung
    local_vars = set()
    param_vars = set()
    if method_node and hasattr(method_node, 'parameters'):
        for param in method_node.parameters:
            if hasattr(param, 'name'):
                param_vars.add(param.name)
    # Cari variabel lokal (val/var di dalam body method)
    for match in re.finditer(r'\b(?:val|var)\s+([a-zA-Z_][a-zA-Z0-9_]*)', method_code):
        local_vars.add(match.group(1))

    # akses langsung (bukan didahului titik/angka/huruf/underscore, dan bukan method call)
    for match in re.finditer(r'(?<![\w\.])([a-zA-Z_][a-zA-Z0-9_]*)\b', method_code):
        varname = match.group(1)
        idx = match.end()
        after = method_code[idx:idx+1]
        if after == '(':
            continue
        # Exclude keyword, angka, parameter, dan variabel lokal
        keywords = {
            "if", "for", "while", "when", "catch", "case", "else", "return", "val", "var", "fun",
            "true", "false", "null", "override", "private", "public", "protected", "internal", "class",
            "object", "interface", "companion", "constructor", "init", "super", "this", "in", "is", "as","do", "try", "finally", "throw", "typeof", "sealed", "data", "lateinit"
        }
        if varname in keywords or varname.isdigit() or varname in param_vars or varname in local_vars:
            continue
        accessed_vars.add(varname)

    # 4. Intersect
    intersected = declared_vars & accessed_vars

    # 5. Return jumlah hasil irisan
    return len(intersected)

def get_class_properties(class_node):
    """
    Ambil semua nama property/field dari class_node.
    """
    props = set()
    if hasattr(class_node, 'body') and hasattr(class_node.body, 'members'):
        for member in class_node.body.members:
            if isinstance(member, node.PropertyDeclaration):
                if hasattr(member, 'declaration') and hasattr(member.declaration, 'name'):
                    props.add(member.declaration.name)
                elif hasattr(member, 'name'):
                    props.add(member.name)
    return props

def noav_method(class_node, method_node):
    """
    Menghitung jumlah atribut class yang diakses di seluruh body fungsi (NOAV), 
    tanpa tergantung pada nama method/parameter/lokal.
    Perbaikan: juga menghitung akses via this.<prop> dan akses langsung pada baris yang mengandung method call.
    """
    # Ambil semua property class
    class_props = set()
    if hasattr(class_node, 'body') and hasattr(class_node.body, 'members'):
        for member in class_node.body.members:
            if isinstance(member, node.PropertyDeclaration):
                if hasattr(member, 'declaration') and hasattr(member.declaration, 'name'):
                    class_props.add(member.declaration.name)
                elif hasattr(member, 'name'):
                    class_props.add(member.name)

    # Ambil semua nama yang tidak boleh dihitung (parameter dan variabel lokal)
    param_vars = set()
    if hasattr(method_node, 'parameters'):
        for param in method_node.parameters:
            if hasattr(param, 'name'):
                param_vars.add(param.name)
    local_vars = set()
    body_str = str(method_node.body) if hasattr(method_node, 'body') and method_node.body else ""
    for match in re.finditer(r'\b(?:val|var)\s+([a-zA-Z_][a-zA-Z0-9_]*)', body_str):
        local_vars.add(match.group(1))

    accessed = set()
    # Cek akses this.<prop> dan super.<prop>
    for prop in class_props:
        if prop in param_vars or prop in local_vars:
            continue
        # Cek akses this.<prop>
        if re.search(r'\bthis\.' + re.escape(prop) + r'\b', body_str):
            accessed.add(prop)
        # Cek akses super.<prop>
        if re.search(r'\bsuper\.' + re.escape(prop) + r'\b', body_str):
            accessed.add(prop)
        # Cek akses langsung (bukan bagian dari kata lain, bukan param/lokal)
        # Perbaikan: hitung juga jika property dipakai dalam method call, assignment, atau argumen
        # Contoh: unregisterReceiver(mMessageReceiver)
        if re.search(r'\b' + re.escape(prop) + r'\b', body_str):
            accessed.add(prop)
    return len(accessed)


def extracted_method(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
        parser = Parser(code)
        result = parser.parse()

        # Extract package name from AST or fallback to 'UNKNOWN'
        if hasattr(result, 'package') and result.package:
            package_name = result.package.name if hasattr(result.package, 'name') else str(result.package)
        else:
            package_name = "UNKNOWN"
        # --- PACKAGE-LEVEL METRICS ---
        declarations = result.declarations if hasattr(result, 'declarations') else []
        class_decls = [n for n in declarations if isinstance(n, node.ClassDeclaration)]
        interface_decls = [n for n in declarations if isinstance(n, node.InterfaceDeclaration)]
        function_decls = [n for n in declarations if isinstance(n, node.FunctionDeclaration)]

        # --- PACKAGE-LEVEL METRICS ---
        nomnamm_package = sum(1 for f in function_decls if not f.name.startswith(("get", "set", "is")))
        for c in class_decls:
            if hasattr(c, 'body') and c.body and hasattr(c.body, 'members'):
                for m in c.body.members:
                    if isinstance(m, node.FunctionDeclaration) and not m.name.startswith(("get", "set", "is")):
                        nomnamm_package += 1
        noi_package = len(interface_decls)
        loc_package = code.count("\n") + 1

        # Simpan metrik package-level dalam dictionary berdasarkan package_name
        package_metrics_map = {
            package_name: {
                'NOMNAMM_Package': nomnamm_package,
                'NOI_Package': noi_package,
                'LOC_Package': loc_package
            }
        }

        # Kumpulkan semua nama method di file untuk CM calculation
        all_methods_in_file = [f.name for f in function_decls if not f.name.startswith(("get", "set", "is"))]
        for c in class_decls:
            if hasattr(c, 'body') and c.body and hasattr(c.body, 'members'):
                for m in c.body.members:
                    if isinstance(m, node.FunctionDeclaration) and not m.name.startswith(("get", "set", "is")):
                        all_methods_in_file.append(m.name)

        datas = []

        for class_decl in class_decls:
            if not class_decl.body:
                continue

            class_name = class_decl.name
            loc_type = count_loc_type(str(class_decl))
            locnamm_type = count_locnamm_type(class_decl)
            cfnamm_type = count_cfnamm_type(class_decl)

            noav_class_val = count_noav_class(class_decl)

            methods_cc = []
            methods_info = []
            for member in class_decl.body.members:
                if isinstance(member, node.FunctionDeclaration):
                    name = member.name
                    body = str(member.body) if member.body else ""

                    cc = count_cc_manual(body)
                    loc = body.count("\n") + 1 if body else 0
                    max_nest = manual_max_nesting(body)
                    mamcl = count_mamcl(body)
                    cm = count_cm_method(body, all_methods_in_file)
                    # Ganti pemanggilan NOAV ke noav_method
                    noav_method_val = noav_method(class_decl, member)

                    methods_cc.append(cc)
                    methods_info.append((name, cc, loc, max_nest, mamcl, noav_method_val, cm))

            woc_values = count_woc(methods_cc)

            # Ambil metrik package-level dari dictionary
            pkg_metrics = package_metrics_map.get(package_name, {'NOMNAMM_Package': 0, 'NOI_Package': 0, 'LOC_Package': 0})

            for i, (name, cc, loc, nest, mamcl, noav_method_val, cm) in enumerate(methods_info):
                woc = woc_values[i] if i < len(woc_values) else 0
                # Method kolom: hanya nama method saja (tanpa gabungan NOAV)
                datas.append({
                    "Package": package_name,
                    "Class": class_name,
                    "Method": name,  # hanya nama method
                    "LOC": loc,
                    "Max Nesting": nest,
                    "CC": cc,
                    "WOC": woc,
                    "MaMCL": mamcl,
                    "NOAV": noav_method_val,  # NOAV tetap individual per baris
                    "CM": cm,
                    "LOC_type": loc_type,
                    "LOCNAMM_type": locnamm_type,
                    "CFNAMM_type": cfnamm_type,
                    "NOMNAMM_Package": pkg_metrics['NOMNAMM_Package'],
                    "NOI_Package": pkg_metrics['NOI_Package'],
                    "LOC_package": pkg_metrics['LOC_Package']
                })

        # Tambahkan fungsi top-level ke dalam hasil
        pkg_metrics = package_metrics_map.get(package_name, {'NOMNAMM_Package': 0, 'NOI_Package': 0, 'LOC_Package': 0})
        for func in function_decls:
            body = str(func.body) if func.body else ""
            cc = count_cc_manual(body)
            loc = body.count("\n") + 1 if func.body else 0
            max_nest = manual_max_nesting(body)
            mamcl = count_mamcl(body)
            # Hitung NOAV dengan fungsi baru, class_node None untuk top-level
            noav_method_val = 0
            cm = count_cm_method(body, all_methods_in_file)
            
            datas.append({
                "Package": package_name,
                "Class": "TopLevel",
                "Method": func.name,
                "LOC": loc,
                "Max Nesting": max_nest,
                "CC": cc,
                "WOC": 1 if cc > 0 else 0,
                "MaMCL": mamcl,
                "NOAV": noav_method_val, 
                "CM": cm,
                "LOC_type": 0,
                "LOCNAMM_type": 0,
                "CFNAMM_type": 0,
                "NOMNAMM_Package": pkg_metrics['NOMNAMM_Package'],
                "NOI_Package": pkg_metrics['NOI_Package'],
                "LOC_package": pkg_metrics['LOC_Package']
            })

        return datas if datas else [{
            "Package": package_name, "Class": "None", "Method": "None",
            "LOC": 0, "Max Nesting": 0, "CC": 0, "WOC": 0,
            "MaMCL": 0, "NOAV": 0, "CM": 0,
            "LOC_type": 0, "LOCNAMM_type": 0, "CFNAMM_type": 0,
            "NOMNAMM_Package": nomnamm_package, "NOI_Package": noi_package, 
            "LOC_package": loc_package, "Error": "No functions found"
        }]
    except Exception as e:
        return [{
            "Package": "Error", "Class": "Error", "Method": "Error",
            "LOC": "Error", "Max Nesting": 0, "CC": 0, "WOC": 0,
            "MaMCL": 0, "NOAV": 0, "CM": 0,
            "LOC_type": 0, "LOCNAMM_type": 0, "CFNAMM_type": 0,
            "NOMNAMM_Package": 0, "NOI_Package": 0, "LOC_package": 0, 
            "Error": str(e)
        }]


def extract_and_parse(file):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file_path = os.path.join(temp_dir, file.name)
        try:
            # Tulis file ke temporary directory
            with open(temp_file_path, "wb") as f:
                f.write(file.getbuffer())

            # Ekstrak arsip
            patoolib.extract_archive(temp_file_path, outdir=temp_dir)
            
            # Cari semua file Kotlin
            kotlin_files = [
                os.path.join(root, f)
                for root, _, files in os.walk(temp_dir)
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
                    "MaMCL": 0,
                    "NOAV": 0,
                    "CM": 0,
                    "LOC_type": 0,
                    "LOCNAMM_type": 0,
                    "CFNAMM_type": 0,
                    "NOMNAMM_Package": 0,
                    "NOI_Package": 0,
                    "LOC_package": 0,
                    "Error": "No Kotlin files found in archive"
                }])

            results = []
            file_package_map = {}  # file_path -> package_name
            file_code_map = {}     # file_path -> code string

            # Pass 1: Kumpulkan hasil per file dan mapping file ke package
            for kotlin_file in kotlin_files:
                try:
                    with open(kotlin_file, "r", encoding="utf-8") as f:
                        code = f.read()
                    parser = Parser(code)
                    result = parser.parse()
                    if hasattr(result, 'package') and result.package:
                        package_name = result.package.name if hasattr(result.package, 'name') else str(result.package)
                    else:
                        package_name = "UNKNOWN"
                    file_package_map[kotlin_file] = package_name
                    file_code_map[kotlin_file] = code
                    file_result = extracted_method(kotlin_file)
                    if file_result:
                        results.extend(file_result)
                except Exception as file_error:
                    results.append({
                        "Package": "Error",
                        "Class": "Error",
                        "Method": kotlin_file,
                        "LOC": "Error",
                        "Max Nesting": 0,
                        "CC": 0,
                        "WOC": 0,
                        "MaMCL": 0,
                        "NOAV": 0,
                        "CM": 0,
                        "LOC_type": 0,
                        "LOCNAMM_type": 0,
                        "CFNAMM_type": 0,
                        "NOMNAMM_Package": 0,
                        "NOI_Package": 0,
                        "LOC_package": 0,
                        "Error": str(file_error)
                    })

            # Pass 2: Hitung ulang metrik package-level secara agregat
            # Kumpulkan semua file per package
            package_files = {}
            for file_path, pkg in file_package_map.items():
                package_files.setdefault(pkg, []).append(file_path)

            # Hitung metrik package-level agregat
            package_metrics_map = {}
            for pkg, files in package_files.items():
                all_code = ""
                all_functions = 0
                all_interfaces = 0
                for file_path in files:
                    code = file_code_map[file_path]
                    all_code += code + "\n"
                    parser = Parser(code)
                    result = parser.parse()
                    declarations = result.declarations if hasattr(result, 'declarations') else []
                    class_decls = [n for n in declarations if isinstance(n, node.ClassDeclaration)]
                    interface_decls = [n for n in declarations if isinstance(n, node.InterfaceDeclaration)]
                    function_decls = [n for n in declarations if isinstance(n, node.FunctionDeclaration)]
                    all_functions += sum(1 for f in function_decls if not f.name.startswith(("get", "set", "is")))
                    for c in class_decls:
                        if hasattr(c, 'body') and c.body and hasattr(c.body, 'members'):
                            for m in c.body.members:
                                if isinstance(m, node.FunctionDeclaration) and not m.name.startswith(("get", "set", "is")):
                                    all_functions += 1
                    all_interfaces += len(interface_decls)
                loc_package = all_code.count("\n") + 1
                package_metrics_map[pkg] = {
                    'NOMNAMM_Package': all_functions,
                    'NOI_Package': all_interfaces,
                    'LOC_Package': loc_package
                }

            # Update semua baris di results dengan metrik package-level agregat
            for row in results:
                pkg = row.get("Package", "UNKNOWN")
                pkg_metrics = package_metrics_map.get(pkg, {'NOMNAMM_Package': 0, 'NOI_Package': 0, 'LOC_Package': 0})
                row["NOMNAMM_Package"] = pkg_metrics['NOMNAMM_Package']
                row["NOI_Package"] = pkg_metrics['NOI_Package']
                row["LOC_package"] = pkg_metrics['LOC_Package']

            df = pd.DataFrame(results)

            # --- PATCH: Update NOAV agar semua method dengan nama sama dapat total NOAV seluruh project ---
            # HAPUS/COMMENT PATCH INI AGAR NOAV TIDAK DIJUMLAHKAN
            # noav_sum_by_method = df.groupby("Method")["NOAV"].sum().to_dict()
            # df["NOAV"] = df["Method"].map(noav_sum_by_method)
            # --- END PATCH ---

            # Tambahkan baris total
            numeric_columns = ['LOC', 'Max Nesting', 'CC', 'WOC', 'MaMCL', 'NOAV', 'CM', 
                                'LOC_type', 'LOCNAMM_type', 'CFNAMM_type', 'NOMNAMM_Package', 
                                'NOI_Package', 'LOC_package']
            
            # Konversi kolom 'LOC' ke numerik, ganti 'Error' dengan 0
            df['LOC'] = pd.to_numeric(df['LOC'].replace('Error', 0))
            
            # Hitung total
            totals = df[numeric_columns].sum()
            
            # Buat baris total
            total_row = pd.DataFrame([{
                'Package': 'TOTAL',
                'Class': '',
                'Method': '',
                **totals,
                'Error': ''
            }])
            
            # Gabungkan DataFrame asli dengan baris total
            df = pd.concat([df, total_row], ignore_index=True)
            
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
                "MaMCL": 0,
                "NOAV": 0,
                "CM": 0,
                "LOC_type": 0,
                "LOCNAMM_type": 0,
                "CFNAMM_type": 0,
                "NOMNAMM_Package": 0,
                "NOI_Package": 0,
                "LOC_package": 0,
                "Error": f"Archive extraction error: {str(e)}"
            }])

# ======= Begin: controller patrik.py =======
import os
import tempfile
import patoolib
import pandas as pd
from kopyt import Parser, node
from kopyt.node import ClassDeclaration  # Perhatikan perubahan di sini

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

def count_noi(directory):
    noi_count = 0
    kotlin_files = [os.path.join(root, f) for root, _, files in os.walk(directory) for f in files if f.endswith(".kt") or f.endswith(".kts")]
    for file_path in kotlin_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()
            parser = Parser(code)
            result = parser.parse()
            for declaration in result.declarations:
                if isinstance(declaration, node.InterfaceDeclaration):
                    noi_count += 1
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
    return noi_count

def count_nom(directory):
    nom_count = 0
    kotlin_files = [os.path.join(root, f) for root, _, files in os.walk(directory) for f in files if f.endswith(".kt") or f.endswith(".kts")]
    for file_path in kotlin_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()
            parser = Parser(code)
            result = parser.parse()
            for declaration in result.declarations:
                if hasattr(declaration, "body") and declaration.body:
                    for member in declaration.body.members:
                        if isinstance(member, node.FunctionDeclaration):
                            nom_count += 1
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
    return nom_count

def count_nomnamm(directory):
    nomnamm_count = 0
    kotlin_files = [os.path.join(root, f) for root, _, files in os.walk(directory) for f in files if f.endswith(".kt") or f.endswith(".kts")]
    for file_path in kotlin_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()
            parser = Parser(code)
            result = parser.parse()
            for declaration in result.declarations:
                if hasattr(declaration, "body") and declaration.body:
                    for member in declaration.body.members:
                        if isinstance(member, node.FunctionDeclaration):
                            if not (member.name.startswith("get") or member.name.startswith("set")):
                                nomnamm_count += 1
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
    return nomnamm_count

def count_noc_type(directory, include_external_classes=True):
    import os
    from kopyt import Parser
    from kopyt.node import ClassDeclaration, InterfaceDeclaration
    
    classes = {}  # {class_name: [superclasses]}
    all_classes = set()
    external_classes = set()  # For tracking external superclasses

    kotlin_files = [
        os.path.join(root, f) 
        for root, _, files in os.walk(directory) 
        for f in files if f.endswith(".kt") or f.endswith(".kts")
    ]

    for file_path in kotlin_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()
            
            parser = Parser(code)
            kotlin_file = parser.parse()
            
            for decl in kotlin_file.declarations:
                if isinstance(decl, ClassDeclaration) or isinstance(decl, InterfaceDeclaration):
                    class_name = decl.name
                    all_classes.add(class_name)
                    
                    super_types = []
                    
                    # Process supertypes to find inheritance relationships
                    if hasattr(decl, 'supertypes') and decl.supertypes:
                        for supertype in decl.supertypes:
                            super_name = None
                            
                            # Extract the name from the supertype structure
                            # For constructor invocations (class inheritance with parentheses)
                            if hasattr(supertype, 'delegate') and hasattr(supertype.delegate, 'invoker'):
                                if hasattr(supertype.delegate.invoker, 'sequence') and supertype.delegate.invoker.sequence:
                                    super_name = supertype.delegate.invoker.sequence[0].name
                            
                            # For direct type references (interface implementation)
                            elif hasattr(supertype, 'delegate') and hasattr(supertype.delegate, 'sequence'):
                                if supertype.delegate.sequence:
                                    super_name = supertype.delegate.sequence[0].name
                            
                            if super_name:
                                super_types.append(super_name)
                                print(f"Found inheritance relationship: {class_name} extends/implements {super_name}")
                                
                                # Track external superclasses (not declared in your code)
                                if super_name not in all_classes:
                                    external_classes.add(super_name)
                    
                    classes[class_name] = super_types
                    
        except Exception as e:
            print(f"Error parsing {file_path}: {str(e)}")

    # Add external classes to tracking if requested
    if include_external_classes:
        for ext_class in external_classes:
            all_classes.add(ext_class)

    # Initialize NOC count
    class_hierarchy = {cls: 0 for cls in all_classes}

    # Count subclass relationships
    for class_name, super_types in classes.items():
        for super_type in super_types:
            simple_super_type = super_type.split('.')[-1]  # Handle qualified names
            
            if simple_super_type in class_hierarchy:
                class_hierarchy[simple_super_type] += 1
                print(f"Inheritance counted: {simple_super_type} now has {class_hierarchy[simple_super_type]} children")
            else:
                print(f"Warning: Superclass '{simple_super_type}' not found in tracked classes")

    return class_hierarchy

# Function to calculate WMC for a single class
def calculate_wmc_for_class(class_declaration):
    """Calculate WMC (Weighted Methods per Class) for a single class declaration"""
    if class_declaration.body is None:
        return 0
        
    wmc_value = 0
    for member in class_declaration.body.members:
        if isinstance(member, node.FunctionDeclaration):
            # Calculate complexity for this function
            cc_value = count_cc_manual(str(member.body)) if member.body else 0
            wmc_value += cc_value
            
    return wmc_value

def calculate_wmcnamm_type(class_declaration):
    """
    Calculate WMCNAMM_type (Weighted Methods per Class for Non-Accessor/Mutator Methods)
    This metric calculates the sum of cyclomatic complexity of non-accessor/non-mutator methods in a class
    """
    if class_declaration.body is None:
        return 0
    
    total_cc = 0
    
    # Identifikasi semua properti/atribut kelas untuk menentukan accessor/mutator methods
    class_properties = set()
    for member in class_declaration.body.members:
        if isinstance(member, node.PropertyDeclaration) or isinstance(member, node.VariableDeclaration):
            if hasattr(member, 'name'):
                class_properties.add(member.name)
    
    # Iterasi melalui semua metode kelas
    for member in class_declaration.body.members:
        if isinstance(member, node.FunctionDeclaration):
            # Skip jika metode tidak memiliki body
            if member.body is None:
                continue
            
            function_name = member.name
            function_body = str(member.body)
            
            # Cek apakah metode adalah accessor/mutator
            is_accessor_mutator = False
            
            # Pola nama untuk accessor/mutator: get*, set*, is*, has*
            if (function_name.startswith("get") or function_name.startswith("set") or 
                function_name.startswith("is") or function_name.startswith("has")):
                
                # Cek lebih lanjut berdasarkan konten dan nama properti
                property_name = ""
                if function_name.startswith("get"):
                    property_name = function_name[3:].lower()
                elif function_name.startswith("set"):
                    property_name = function_name[3:].lower()
                elif function_name.startswith("is"):
                    property_name = function_name[2:].lower()
                elif function_name.startswith("has"):
                    property_name = function_name[3:].lower()
                
                # Cari properti yang sesuai (case insensitive)
                for prop in class_properties:
                    if prop.lower() == property_name:
                        # Periksa apakah body metode sederhana (hanya return atau assignment)
                        # Ini adalah heuristik sederhana untuk menentukan accessor/mutator
                        body_lines = function_body.strip().split("\n")
                        is_simple = len(body_lines) <= 3  # Metode sederhana biasanya 1-3 baris
                        
                        if is_simple:
                            # Cek pola return/assignment
                            has_return_or_assign = any("return" in line or "=" in line for line in body_lines)
                            if has_return_or_assign:
                                is_accessor_mutator = True
                                break
            
            # Jika bukan accessor/mutator, hitung kompleksitasnya
            if not is_accessor_mutator:
                # Hitung kompleksitas siklomat metode
                cc_value = count_cc_manual(function_body)
                total_cc += cc_value
    
    return total_cc

def calculate_amw_type(class_declaration):
    """
    Calculate AMW_type (Average Method Weight)
    This metric calculates the average cyclomatic complexity of methods in a class
    """
    if class_declaration.body is None:
        return 0
    
    method_cc_values = []
    
    # Iterasi melalui semua metode kelas
    for member in class_declaration.body.members:
        if isinstance(member, node.FunctionDeclaration):
            # Skip jika metode tidak memiliki body
            if member.body is None:
                continue
            
            # Hitung kompleksitas siklomat metode
            function_body = str(member.body)
            cc_value = count_cc_manual(function_body)
            method_cc_values.append(cc_value)
    
    # Hitung rata-rata kompleksitas
    if method_cc_values:
        return sum(method_cc_values) / len(method_cc_values)
    else:
        return 0  # Jika tidak ada metode, kembalikan 0

def count_nocs_package(directory):
    """
    Calculate NOCS_package (Number of Classes in a Package)
    This metric counts the number of classes in each package
    
    Returns a dictionary mapping package names to their class counts
    """
    # Dictionary untuk menyimpan jumlah kelas per package
    package_class_counts = {}
    
    # Temukan semua file Kotlin dalam direktori
    kotlin_files = [os.path.join(root, f) for root, _, files in os.walk(directory) 
                  for f in files if f.endswith(".kt") or f.endswith(".kts")]
    
    for file_path in kotlin_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()
            parser = Parser(code)
            result = parser.parse()
            
            # Dapatkan nama paket
            package_name = result.package.name if result.package else "default"
            
            # Hitung jumlah kelas dalam file ini
            class_count = sum(1 for decl in result.declarations if isinstance(decl, node.ClassDeclaration))
            
            # Update jumlah kelas untuk paket ini
            if package_name in package_class_counts:
                package_class_counts[package_name] += class_count
            else:
                package_class_counts[package_name] = class_count
                
        except Exception:
            # Jika file tidak dapat di-parse, lanjutkan ke file berikutnya
            continue
    
    return package_class_counts

def calculate_lcom5(class_declaration):
    """
    Calculate LCOM5 (Lack of Cohesion in Methods) 
    Uses a simplified approach based on method body similarity
    """
    if class_declaration.body is None:
        return 0
    
    # Collect all methods with bodies
    methods = []
    for member in class_declaration.body.members:
        if isinstance(member, node.FunctionDeclaration) and member.body is not None:
            methods.append(member)
    
    # Need at least 2 methods for LCOM5 calculation
    if len(methods) < 2:
        return 0
    
    # Calculate method pairs and their similarity
    total_pairs = 0
    cohesive_pairs = 0
    
    for i in range(len(methods)):
        for j in range(i + 1, len(methods)):
            total_pairs += 1
            
            # Get method bodies as strings (same way as your other metrics)
            body1 = str(methods[i].body) if methods[i].body else ""
            body2 = str(methods[j].body) if methods[j].body else ""
            
            if body1 and body2:
                # Split into tokens and find common meaningful tokens
                tokens1 = set(body1.split())
                tokens2 = set(body2.split())
                
                # Remove common programming constructs
                common_keywords = {
                    'if', 'else', 'for', 'while', 'return', 'var', 'val', 'fun', 
                    'this', 'null', 'true', 'false', 'it', 'when', 'is', 'as',
                    '{', '}', '(', ')', '[', ']', ';', ',', '.', '=', '+', '-', 
                    '*', '/', '&&', '||', '!', '<', '>', '<=', '>=', '==', '!=',
                    'private', 'public', 'protected', 'internal', 'override'
                }
                
                # Filter out keywords and short tokens
                meaningful_tokens1 = {token for token in tokens1 
                                    if token not in common_keywords and len(token) > 2}
                meaningful_tokens2 = {token for token in tokens2 
                                    if token not in common_keywords and len(token) > 2}
                
                # Check if methods share meaningful tokens (indicating shared attributes/functionality)
                shared_tokens = meaningful_tokens1 & meaningful_tokens2
                if len(shared_tokens) > 0:
                    cohesive_pairs += 1
    
    if total_pairs == 0:
        return 0
    
    # LCOM5 = 1 - (cohesive pairs / total pairs)
    # Higher values indicate lower cohesion
    lcom5 = 1 - (cohesive_pairs / total_pairs)
    
    # Ensure result is between 0 and 1
    return max(0.0, min(1.0, lcom5))

def extracted_method(file_path, noi_count, nom_count, nomnamm_count, nocs_package_counts):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
        parser = Parser(code)
        result = parser.parse()
        package_name = result.package.name if result.package else "Unknown"
        
        # Dapatkan NOCS_package untuk paket ini
        nocs_package = nocs_package_counts.get(package_name, 0)
        
        if not result.declarations:
            return [{"Package": package_name, "Class": "Unknown", "Method": "None", "LOC": 0, "Max Nesting": 0, 
                    "CC": 0, "WOC": 0, "NOI": noi_count, "NOM": nom_count, "NOMNAMM": nomnamm_count, 
                    "NOC_type": 0, "WMC_type": 0, "LCOM5": 0, "WMCNAMM_type": 0, "AMW_type": 0,
                    "NOCS_package": nocs_package, "Error": "No class declaration found"}]
        
        # Get NOC_type mapping for the directory
        directory = os.path.dirname(file_path)
        noc_type_mapping = count_noc_type(directory)
        
        datas = []
        for class_declaration in result.declarations:
            if not isinstance(class_declaration, node.ClassDeclaration):
                continue
                
            class_name = class_declaration.name
            noc_type = noc_type_mapping.get(class_name, 0)
            # Calculate WMC for this class
            wmc_type = calculate_wmc_for_class(class_declaration)
            # Calculate LCOM5 for this class
            lcom5_value = calculate_lcom5(class_declaration)
            # Calculate WMCNAMM_type for this class
            wmcnamm_type = calculate_wmcnamm_type(class_declaration)
            # Calculate AMW_type for this class
            amw_type = calculate_amw_type(class_declaration)
            
            if class_declaration.body is None:
                datas.append({"Package": package_name, "Class": class_name, "Method": "None", "LOC": 0, 
                            "Max Nesting": 0, "CC": 0, "WOC": 0, "NOI": noi_count, "NOM": nom_count, 
                            "NOMNAMM": nomnamm_count, "NOC_type": noc_type, "WMC_type": wmc_type, 
                            "LCOM5": lcom5_value, "WMCNAMM_type": wmcnamm_type, "AMW_type": amw_type,
                            "NOCS_package": nocs_package, "Error": "Class has no body"})
                continue
                
            method_function = {}
            for member in class_declaration.body.members:
                if isinstance(member, node.FunctionDeclaration):
                    function_names = member.name
                    loc_count = str(member.body).count("\n") + 1 if member.body else 0
                    maxnesting = manual_max_nesting(str(member.body)) if member.body else 0
                    cc_value = count_cc_manual(str(member.body)) if member.body else 0
                    method_function[function_names] = (cc_value, loc_count, maxnesting)
                    
            cc_values = [cc for cc, _, _ in method_function.values()]
            woc_values = count_woc(cc_values)
            
            for (function_names, (cc_value, loc_count, maxnesting)), woc in zip(method_function.items(), woc_values):
                datas.append({"Package": package_name, "Class": class_name, "Method": function_names, 
                             "LOC": loc_count, "Max Nesting": maxnesting, "CC": cc_value, "WOC": woc, 
                             "NOI": noi_count, "NOM": nom_count, "NOMNAMM": nomnamm_count, 
                             "NOC_type": noc_type, "WMC_type": wmc_type, "LCOM5": lcom5_value, 
                             "WMCNAMM_type": wmcnamm_type, "AMW_type": amw_type, "NOCS_package": nocs_package})
                
            if not method_function:
                datas.append({"Package": package_name, "Class": class_name, "Method": "None", "LOC": 0, 
                            "Max Nesting": 0, "CC": 0, "WOC": 0, "NOI": noi_count, "NOM": nom_count, 
                            "NOMNAMM": nomnamm_count, "NOC_type": noc_type, "WMC_type": wmc_type, 
                            "LCOM5": lcom5_value, "WMCNAMM_type": wmcnamm_type, "AMW_type": amw_type,
                            "NOCS_package": nocs_package, "Error": "No functions found"})
                
        return datas if datas else [{"Package": package_name, "Class": "Unknown", "Method": "None", "LOC": 0, 
                                   "Max Nesting": 0, "CC": 0, "WOC": 0, "NOI": noi_count, "NOM": nom_count, 
                                   "NOMNAMM": nomnamm_count, "NOC_type": 0, "WMC_type": 0, "LCOM5": 0, 
                                   "WMCNAMM_type": 0, "AMW_type": 0, "NOCS_package": nocs_package,
                                   "Error": "No class declarations found"}]
    except Exception as e:
        return [{"Package": "Error", "Class": "Error", "Method": "Error", "LOC": "Error", 
                "Max Nesting": 0, "CC": 0, "WOC": 0, "NOI": noi_count, "NOM": nom_count, 
                "NOMNAMM": nomnamm_count, "NOC_type": 0, "WMC_type": 0, "LCOM5": 0, 
                "WMCNAMM_type": 0, "AMW_type": 0, "NOCS_package": 0, "Error": str(e)}]

def extract_and_parse(file):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file_path = os.path.join(temp_dir, file.name)
        with open(temp_file_path, "wb") as f:
            f.write(file.getbuffer())
        try:
            patoolib.extract_archive(temp_file_path, outdir=temp_dir)
            noi_count = count_noi(temp_dir)
            nom_count = count_nom(temp_dir)
            nomnamm_count = count_nomnamm(temp_dir)
            
            # Hitung NOCS_package
            nocs_package_counts = count_nocs_package(temp_dir)
            
            results = []
            for kotlin_file in [os.path.join(root, f) for root, _, files in os.walk(temp_dir) 
                              for f in files if f.endswith(".kt") or f.endswith(".kts")]:
                file_results = extracted_method(kotlin_file, noi_count, nom_count, nomnamm_count, nocs_package_counts)
                results.extend(file_results)
            return pd.DataFrame(results)
        except Exception as e:
            return str(e)

# ======= Begin: controller danta.py =======
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
        'private_attributes': 0,
        'protected_attributes': 0,
        'package_visible_attributes': 0,
        'final_attributes': 0,
        'static_attributes': 0,
        'final_static_attributes': 0,
        'not_final_not_static_attributes': 0
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
                                        class_counts['private_attributes'] += 1
                                    elif is_protected:
                                        class_counts['protected_attributes'] += 1
                                    elif not modifiers or is_internal:
                                        class_counts['package_visible_attributes'] += 1

                                    class_counts['static_attributes'] += 1
                                    if is_final:
                                        class_counts['final_attributes'] += 1
                                        class_counts['final_static_attributes'] += 1
                                    elif 'var' in str(companion_member):
                                        class_counts['not_final_not_static_attributes'] += 1

                        elif isinstance(member, node.PropertyDeclaration):
                            modifiers = getattr(member, 'modifiers', [])
                            is_private = 'private' in modifiers
                            is_protected = 'protected' in modifiers
                            is_internal = 'internal' in modifiers
                            is_final = 'val' in str(member)
                            # static detection removed

                            if is_private:
                                class_counts['private_attributes'] += 1
                            elif is_protected:
                                class_counts['protected_attributes'] += 1
                            elif not modifiers or is_internal:
                                class_counts['package_visible_attributes'] += 1

                            if is_final:
                                class_counts['final_attributes'] += 1
                            # static detection removed
                            elif not is_final and 'var' in str(member):
                                class_counts['not_final_not_static_attributes'] += 1
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


# ======= Begin: controller adit.py =======
import os
import tempfile
import patoolib
import pandas as pd
from kopyt import Parser, node
from typing import Set # Import Set untuk type hinting

def count_nomnamm_type(class_declaration):
    """
    Menghitung jumlah metode yang bukan accessor/mutator (NOMNAMM_type).
    Lebih akurat dengan memfilter berdasarkan body method yang hanya mengakses properti.
    """
    if not hasattr(class_declaration, 'body') or class_declaration.body is None:
        return 0
        
    nomnamm_count = 0

    class_properties = set()

    # Ambil semua nama property untuk deteksi akses di getter/setter
    for member in class_declaration.body.members:
        if isinstance(member, node.PropertyDeclaration):
            decl = getattr(member, 'declaration', None)
            if isinstance(decl, node.VariableDeclaration):
                class_properties.add(decl.name)
            elif isinstance(decl, node.MultiVariableDeclaration):
                for var in decl.sequence:
                    class_properties.add(var.name)

    for member in class_declaration.body.members:
        if isinstance(member, node.FunctionDeclaration):
            function_name = member.name
            body = str(member.body) if member.body else ""

            # Skip constructor (same name as class)
            if function_name == class_declaration.name:
                continue

            # Strip whitespace and remove line breaks
            clean_body = body.replace("\n", "").strip()

            # Possible accessor/mutator detection
            is_accessor = (
                function_name.startswith("get") or function_name.startswith("is")
            ) and any(prop in clean_body for prop in class_properties)

            is_mutator = (
                function_name.startswith("set") and any(f"{prop} =" in clean_body for prop in class_properties)
            )

            if not (is_accessor or is_mutator):
                nomnamm_count += 1

    return nomnamm_count

def count_noa_type(class_declaration):
    """Menghitung jumlah atribut dalam sebuah kelas (NOA_type)."""
    if not hasattr(class_declaration, 'body') or class_declaration.body is None:
        return 0
        
    attribute_count = 0
    for member in class_declaration.body.members:
        if isinstance(member, node.PropertyDeclaration) or \
           (isinstance(member, node.VariableDeclaration) and not hasattr(member, 'function')):
            attribute_count += 1
    return attribute_count

def count_nim_type(class_declaration):
    """
    Menghitung jumlah metode yang diwariskan dari kelas induk (NIM_type).
    """
    if not hasattr(class_declaration, 'body') or class_declaration.body is None:
        return 0
        
    # In Kotlin, inherited methods come from:
    # 1. Superclass (Any class by default)
    # 2. Interfaces
    # This is a simplified approach that counts overridden methods
        
    nim_count = 0
        
    for member in class_declaration.body.members:
        if isinstance(member, node.FunctionDeclaration):
            # Check if the method has 'override' modifier
            if hasattr(member, 'modifiers') and member.modifiers:
                for modifier in member.modifiers:
                    if str(modifier).strip() == 'override':
                        nim_count += 1
                        break
        
    return nim_count

def count_atfd(method_node, class_declaration):
    """
    Counts Access to Foreign Data (ATFD) for a single method by traversing the AST.
    """
    if not hasattr(method_node, 'body') or not isinstance(method_node.body, node.Block):
        return 0

    foreign_accesses = set()

    # Collect current class field names robustly
    current_fields = set()
    if hasattr(class_declaration, 'body') and class_declaration.body is not None:
        for member in class_declaration.body.members:
            if isinstance(member, node.PropertyDeclaration):
                decl = getattr(member, 'declaration', None)
                if isinstance(decl, node.VariableDeclaration):
                    current_fields.add(decl.name)
                elif isinstance(decl, node.MultiVariableDeclaration):
                    for var in decl.sequence:
                        current_fields.add(var.name)

    def collect_foreign_accesses(expr):
        if expr is None:
            return
            
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

        elif hasattr(expr, "_dict_"):
            for val in vars(expr).values():
                if isinstance(val, node.Node):
                    collect_foreign_accesses(val)
                elif isinstance(val, (list, tuple)):
                    for item in val:
                        if isinstance(item, node.Node):
                            collect_foreign_accesses(item)

    # Iterate through statements in the method body
    if hasattr(method_node.body, 'sequence') and method_node.body.sequence is not None:
        for stmt in method_node.body.sequence:
            if hasattr(stmt, 'statement'):
                collect_foreign_accesses(stmt.statement)
    
    return len(foreign_accesses)

def count_fanout_method(method_body: str, class_methods=None) -> int:
    """
    Refined FANOUT_method metric:
    Count unique external class or method calls from a method body.

    Args:
        method_body (str): Method code as string.
        class_methods (set): Optional, names of own class methods to exclude from count.

    Returns:
        int: Number of unique external class or method calls.
    """
    if not method_body:
        return 0

    external_calls = set()
    class_methods = class_methods or set()

    lines = method_body.split('\n')

    for line in lines:
        line = line.strip()

        if not line or line.startswith('//') or line.startswith('/*'):
            continue

        # Case 1: object.method() or safe-call obj?.method()
        if '.' in line and '(' in line:
            segments = line.replace('?.', '.').split('.')
            for i in range(len(segments) - 1):
                receiver = segments[i].strip().split(' ')[-1]
                method_part = segments[i + 1].split('(')[0].strip()

                if receiver not in ('this', 'super', ''):
                    external_calls.add(f"{receiver}.{method_part}")

        # Case 2: direct method calls (no dot)
        elif '(' in line:
            candidate = line.split('(')[0].strip()
            if candidate and candidate not in class_methods:
                external_calls.add(candidate)

    return len(external_calls)

def count_atld_method(method_node, class_fields):
    attributes_accessed = set()
    local_variables = set()

    # Step 1: parameters as locals
    if hasattr(method_node, 'parameters'):
        for param in method_node.parameters:
            if hasattr(param, 'name'):
                local_variables.add(param.name)

    # Step 2: fallback to body text scan
    body_text = str(method_node.body) if method_node.body else ""

    # Detect class attributes used
    for field in class_fields:
        if field in body_text:
            attributes_accessed.add(field)

    # Detect locals by looking for `val` / `var` declarations
    for line in body_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("val ") or stripped.startswith("var "):
            parts = stripped.split()
            if len(parts) >= 2:
                var_name = parts[1].split("=")[0].strip()
                if var_name.isidentifier():
                    local_variables.add(var_name)

    # Final calculation
    local_count = len(local_variables)
    attr_count = len(attributes_accessed)

    return round(attr_count / local_count, 2) if local_count > 0 else float(attr_count)

def count_cfnamm_method(class_declaration):
    """
    Menghitung CFNAMM_method per method: 
    berapa banyak metode non-AM lain yang dipanggil oleh masing-masing method.
    """
    if not hasattr(class_declaration, 'body') or class_declaration.body is None:
        return {}

    methods = {}
    class_properties = set()

    # 1. Kumpulkan semua properti
    for member in class_declaration.body.members:
        if isinstance(member, node.PropertyDeclaration):
            decl = member.declaration
            if isinstance(decl, node.VariableDeclaration):
                class_properties.add(decl.name)
            elif isinstance(decl, node.MultiVariableDeclaration):
                for var in decl.sequence:
                    class_properties.add(var.name)

    # 2. Ambil method non-AM
    for member in class_declaration.body.members:
        if isinstance(member, node.FunctionDeclaration):
            function_name = member.name
            if function_name == class_declaration.name:
                continue

            body_str = str(member.body) if member.body else ""
            clean_body = body_str.replace('\n', '').strip()

            is_accessor = (
                function_name.startswith("get") or function_name.startswith("is")
            ) and any(prop in clean_body for prop in class_properties)

            is_mutator = (
                function_name.startswith("set") and any(f"{prop} =" in clean_body for prop in class_properties)
            )

            if not (is_accessor or is_mutator):
                methods[function_name] = body_str

    if not methods:
        return {}

    method_names = set(methods.keys())
    cfnamm_per_method = {}

    # 3. Untuk tiap method, hitung coupling terhadap method lain
    for method_name, body_str in methods.items():
        calls = 0
        for other in method_names:
            if other != method_name and f"{other}(" in body_str:
                calls += 1
        max_possible = len(method_names) - 1
        ratio = round(calls / max_possible, 2) if max_possible > 0 else 0.0
        cfnamm_per_method[method_name] = ratio

    return cfnamm_per_method

# KAMUS UNTUK PERKIRAAN DIT BERBASIS NAMA KELAS
# Nilai ini adalah perkiraan dan bisa Anda sesuaikan/tambahkan.
PREDEFINED_DIT_MAP = {
    # Android Core & AppCompat
    "Object": 0,
    "Any": 0,
    "Context": 1,
    "Application": 2,
    "Activity": 2,
    "Fragment": 1,
    "Service": 2,
    "BroadcastReceiver": 1,
    "ContentProvider": 2,
    "ViewModel": 1,
    "LiveData": 1,
    "RecyclerView": 2,
    "Adapter": 2, # RecyclerView.Adapter
    "ViewHolder": 1, # RecyclerView.ViewHolder
    
    # AppCompat & Material
    "AppCompatActivity": 3,
    "FragmentActivity": 2,
    "MaterialAlertDialogBuilder": 2,
    "DialogFragment": 2,
    "BottomSheetDialogFragment": 3,
    
    # Coroutines
    "CoroutineScope": 1,
    
    # Common Java
    "Exception": 1,
    "RuntimeException": 2,
    "Thread": 1,
}

def count_dit_by_name(class_declaration) -> int:
    """
    Memperkirakan DIT berdasarkan nama superclass menggunakan kamus yang telah ditentukan.
    """
    if not hasattr(class_declaration, 'supertypes') or not class_declaration.supertypes:
        return 0

    max_depth = 0
    
    for supertype_node in class_declaration.supertypes:
        parent_name = None
        delegate = getattr(supertype_node, 'delegate', None)
        
        if isinstance(delegate, node.ConstructorInvocation):
            parent_name = str(delegate.invoker)
        elif isinstance(delegate, node.UserType):
            parent_name = str(delegate)

        if parent_name:
            # Hapus generic types jika ada (e.g., "Adapter<MyViewHolder>" -> "Adapter")
            clean_parent_name = parent_name.split('<')[0]
            
            # Cek di kamus
            if clean_parent_name in PREDEFINED_DIT_MAP:
                depth = 1 + PREDEFINED_DIT_MAP[clean_parent_name]
            else:
                # Jika tidak ada di kamus, anggap DIT-nya 1
                depth = 1
            
            if depth > max_depth:
                max_depth = depth

    # Jika tidak ada superclass yang dikenali, tapi ada supertypes, default ke 1
    if max_depth == 0 and class_declaration.supertypes:
        return 1
        
    return max_depth

def count_fanout_type(class_declaration, fanout_method_values):
    """
    Menghitung FANOUT_type dengan menjumlahkan semua FANOUT_method dalam sebuah kelas.
    
    Args:
        class_declaration: Deklarasi kelas dari parser kopyt
        fanout_method_values: Dictionary yang berisi nilai FANOUT_method per method
        
    Returns:
        int: Total FANOUT_type (sum of all FANOUT_method in the class)
    """
    if not hasattr(class_declaration, 'body') or class_declaration.body is None:
        return 0
        
    # Jika class_declaration adalah kelas yang valid, jumlahkan semua FANOUT_method-nya
    total_fanout = 0
    for member in class_declaration.body.members:
        if isinstance(member, node.FunctionDeclaration):
            method_name = member.name
            total_fanout += fanout_method_values.get(method_name, 0)
    
    return total_fanout

def extracted_method(file_path):
    """
    Ekstrak informasi metode dan metrik dari satu file Kotlin.
    Fungsi ini lengkap dan menangani berbagai kasus.
    """
    results_for_file = []
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
        
        parser = Parser(code)
        ast = parser.parse()

        package_name = ast.package.name if ast.package else "Unknown"

        # Kasus 1: File tidak memiliki deklarasi kelas sama sekali
        if not ast.declarations:
            results_for_file.append({
                "Package": package_name, 
                "Class": "No Class Found", 
                "Method": "None", 
                "LOC": len(code.splitlines()), 
                "NOMNAMM_type": 0, "NOA_type": 0, "NIM_type": 0,
                "ATFD_type": 0, "DIT_type": 0, "FANOUT_type": 0,
                "FANOUT_method": 0, "ATLD_method": 0.0, "CFNAMM_method": 0.0,
                "Error": "No class declarations in file"
            })
            return results_for_file

        # Iterasi melalui semua deklarasi di file
        for class_declaration in ast.declarations:
            # Hanya proses deklarasi kelas, abaikan fungsi atau properti top-level
            if not isinstance(class_declaration, node.ClassDeclaration):
                continue

            class_name = class_declaration.name
            
            # --- Perhitungan Metrik Tingkat Kelas ---
            dit_total = count_dit_by_name(class_declaration)
            
            # Default values
            nomnamm_total = 0
            noa_total = 0
            nim_total = 0
            cfnamm_results = {}
            fanout_method_values = {}
            atfd_method_values = {}
            class_fields = set()

            # Kasus 2: Kelas tidak punya body
            if not hasattr(class_declaration, 'body') or class_declaration.body is None:
                results_for_file.append({
                    "Package": package_name, "Class": class_name, "Method": "None", "LOC": 0,
                    "NOMNAMM_type": 0, "NOA_type": 0, "NIM_type": 0,
                    "ATFD_type": 0, "DIT_type": dit_total, "FANOUT_type": 0,
                    "FANOUT_method": 0, "ATLD_method": 0.0, "CFNAMM_method": 0.0,
                    "Error": "Class has no body"
                })
                continue

            # Hitung metrik jika kelas punya body
            nomnamm_total = count_nomnamm_type(class_declaration)
            noa_total = count_noa_type(class_declaration)
            nim_total = count_nim_type(class_declaration)
            cfnamm_results = count_cfnamm_method(class_declaration)

            # Kumpulkan properti kelas untuk perhitungan ATLD
            for member in class_declaration.body.members:
                if isinstance(member, node.PropertyDeclaration):
                    decl = member.declaration
                    if isinstance(decl, node.VariableDeclaration):
                        class_fields.add(decl.name)
                    elif isinstance(decl, node.MultiVariableDeclaration):
                        for var in decl.sequence:
                            class_fields.add(var.name)

            # --- Perhitungan Metrik Tingkat Method ---
            method_found_in_class = False
            for member in class_declaration.body.members:
                if isinstance(member, node.FunctionDeclaration):
                    method_found_in_class = True
                    function_name = member.name
                    body_str = str(member.body) if member.body else ""
                    
                    loc_count = body_str.count('\n') + 1 if body_str else 0
                    fanout_value = count_fanout_method(body_str, {m.name for m in class_declaration.body.members if isinstance(m, node.FunctionDeclaration)})
                    atld_value = count_atld_method(member, class_fields)
                    cfnamm_value = cfnamm_results.get(function_name, 0.0)
                    atfd_value = count_atfd(member, class_declaration)
                    
                    fanout_method_values[function_name] = fanout_value
                    atfd_method_values[function_name] = atfd_value

                    results_for_file.append({
                        "Package": package_name,
                        "Class": class_name,
                        "Method": function_name,
                        "LOC": loc_count,
                        "NOMNAMM_type": nomnamm_total,
                        "NOA_type": noa_total,
                        "NIM_type": nim_total,
                        "ATFD_type": 0,  # Placeholder
                        "DIT_type": dit_total,
                        "FANOUT_type": 0,  # Placeholder
                        "FANOUT_method": fanout_value,
                        "ATLD_method": atld_value,
                        "CFNAMM_method": cfnamm_value,
                        "Error": ""
                    })

            # --- Finalisasi Metrik Tingkat Kelas ---
            fanout_type_total = sum(fanout_method_values.values())
            atfd_type_total = sum(atfd_method_values.values())

            # Kasus 3: Kelas punya body tapi tidak punya method
            if not method_found_in_class:
                class_loc = len(str(class_declaration.body).splitlines()) if class_declaration.body else 0
                results_for_file.append({
                    "Package": package_name, "Class": class_name, "Method": "None", "LOC": class_loc,
                    "NOMNAMM_type": nomnamm_total, "NOA_type": noa_total, "NIM_type": nim_total,
                    "ATFD_type": atfd_type_total, "DIT_type": dit_total, "FANOUT_type": fanout_type_total,
                    "FANOUT_method": 0, "ATLD_method": 0.0, "CFNAMM_method": 0.0,
                    "Error": "No methods found in class"
                })
            else:
                # Update placeholder ATFD_type dan FANOUT_type di setiap baris
                for row in results_for_file:
                    if row["Class"] == class_name:
                        row["FANOUT_type"] = fanout_type_total
                        row["ATFD_type"] = atfd_type_total

    except Exception as e:
        # Menangani error fatal saat parsing file
        results_for_file.append({
            "Package": "Error", "Class": os.path.basename(file_path), "Method": "Error", "LOC": 0,
            "NOMNAMM_type": 0, "NOA_type": 0, "NIM_type": 0,
            "ATFD_type": 0, "DIT_type": 0, "FANOUT_type": 0,
            "FANOUT_method": 0, "ATLD_method": 0.0, "CFNAMM_method": 0.0,
            "Error": f"Fatal parsing error: {str(e)}"
        })

    return results_for_file

def extract_and_parse(file):
    """Ekstrak arsip ZIP/RAR dan proses file Kotlin."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file_path = os.path.join(temp_dir, file.name)
        with open(temp_file_path, "wb") as f:
            f.write(file.getbuffer())
        
        try:
            patoolib.extract_archive(temp_file_path, outdir=temp_dir)
            kotlin_files = [os.path.join(root, f) for root, _, files in os.walk(temp_dir) for f in files if f.endswith(".kt") or f.endswith(".kts")]
            
            results = []
            for kotlin_file in kotlin_files:
                results.extend(extracted_method(kotlin_file))
            
            return pd.DataFrame(results)
        except Exception as e:
            # Jika ekstraksi arsip gagal atau tidak ada file Kotlin yang ditemukan
            return pd.DataFrame([{
                "Package": "Error",
                "Class": "Error",
                "Method": "Error",
                "LOC": 0,
                "NOMNAMM_type": 0,
                "NOA_type": 0,
                "NIM_type": 0,
                "ATFD_type": 0,
                "DIT_type": 0,
                "FANOUT_type": 0,
                "FANOUT_method": 0,
                "ATLD_method": 0,
                "CFNAMM_method": 0.0,
                "ATFD_method": 0,
                "Error": f"Archive extraction or file search failed: {str(e)}"
            }])

# ======= Begin: controller2.py =======
import os
import tempfile
import patoolib
import pandas as pd
from kopyt import Parser, node  # Gunakan `kopyt` sebagai parser AST Kotlin
import traceback
import inspect

def count_noi(directory):
    noi_count = 0
    kotlin_files = [os.path.join(root, f) for root, _, files in os.walk(directory) for f in files if f.endswith(".kt") or f.endswith(".kts")]
    for file_path in kotlin_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()
            parser = Parser(code)
            result = parser.parse()
            for declaration in result.declarations:
                if isinstance(declaration, node.InterfaceDeclaration):
                    noi_count += 1
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
    return noi_count

def count_nom(directory):
    nom_count = 0
    kotlin_files = [os.path.join(root, f) for root, _, files in os.walk(directory) for f in files if f.endswith(".kt") or f.endswith(".kts")]
    for file_path in kotlin_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()
            parser = Parser(code)
            result = parser.parse()
            for declaration in result.declarations:
                if hasattr(declaration, "body") and declaration.body:
                    for member in declaration.body.members:
                        if isinstance(member, node.FunctionDeclaration):
                            nom_count += 1
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
    return nom_count

def count_nomnamm(directory):
    nomnamm_count = 0
    kotlin_files = [os.path.join(root, f) for root, _, files in os.walk(directory) for f in files if f.endswith(".kt") or f.endswith(".kts")]
    for file_path in kotlin_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()
            parser = Parser(code)
            result = parser.parse()
            for declaration in result.declarations:
                if hasattr(declaration, "body") and declaration.body:
                    for member in declaration.body.members:
                        if isinstance(member, node.FunctionDeclaration):
                            if not (member.name.startswith("get") or member.name.startswith("set")):
                                nomnamm_count += 1
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
    return nomnamm_count

def count_noc_type(directory, include_external_classes=True):
    import os
    from kopyt import Parser
    from kopyt.node import ClassDeclaration, InterfaceDeclaration
    
    classes = {}  # {class_name: [superclasses]}
    all_classes = set()
    external_classes = set()  # For tracking external superclasses

    kotlin_files = [
        os.path.join(root, f) 
        for root, _, files in os.walk(directory) 
        for f in files if f.endswith(".kt") or f.endswith(".kts")
    ]

    for file_path in kotlin_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()
            
            parser = Parser(code)
            kotlin_file = parser.parse()
            
            for decl in kotlin_file.declarations:
                if isinstance(decl, ClassDeclaration) or isinstance(decl, InterfaceDeclaration):
                    class_name = decl.name
                    all_classes.add(class_name)
                    
                    super_types = []
                    
                    # Process supertypes to find inheritance relationships
                    if hasattr(decl, 'supertypes') and decl.supertypes:
                        for supertype in decl.supertypes:
                            super_name = None
                            
                            # Extract the name from the supertype structure
                            # For constructor invocations (class inheritance with parentheses)
                            if hasattr(supertype, 'delegate') and hasattr(supertype.delegate, 'invoker'):
                                if hasattr(supertype.delegate.invoker, 'sequence') and supertype.delegate.invoker.sequence:
                                    super_name = supertype.delegate.invoker.sequence[0].name
                            
                            # For direct type references (interface implementation)
                            elif hasattr(supertype, 'delegate') and hasattr(supertype.delegate, 'sequence'):
                                if supertype.delegate.sequence:
                                    super_name = supertype.delegate.sequence[0].name
                            
                            if super_name:
                                super_types.append(super_name)
                                print(f"Found inheritance relationship: {class_name} extends/implements {super_name}")
                                
                                # Track external superclasses (not declared in your code)
                                if super_name not in all_classes:
                                    external_classes.add(super_name)
                    
                    classes[class_name] = super_types
                    
        except Exception as e:
            print(f"Error parsing {file_path}: {str(e)}")

    # Add external classes to tracking if requested
    if include_external_classes:
        for ext_class in external_classes:
            all_classes.add(ext_class)

    # Initialize NOC count
    class_hierarchy = {cls: 0 for cls in all_classes}

    # Count subclass relationships
    for class_name, super_types in classes.items():
        for super_type in super_types:
            simple_super_type = super_type.split('.')[-1]  # Handle qualified names
            
            if simple_super_type in class_hierarchy:
                class_hierarchy[simple_super_type] += 1
                print(f"Inheritance counted: {simple_super_type} now has {class_hierarchy[simple_super_type]} children")
            else:
                print(f"Warning: Superclass '{simple_super_type}' not found in tracked classes")

    return class_hierarchy
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

def count_mamcl(code):
    max_chain = 0
    lines = code.splitlines()
    for line in lines:
        line = line.strip()
        if not line or line.startswith(("//", "/*", "*", "*/")):
            continue
            
        # Cari semua chain method calls dalam satu baris
        current_chain = 0
        parts = line.split(".")
        if len(parts) > 1:
            # Mulai dari index 1 karena index 0 adalah objek
            for part in parts[1:]:
                # Check if it's a method call (contains parentheses)
                if "(" in part and ")" in part:
                    current_chain += 1
                else:
                    # Reset if not a method call, as the chain is broken
                    current_chain = 0
                    break # Stop processing this line as chain is broken
        max_chain = max(max_chain, current_chain)
    return max_chain


def count_cm_method(method_code, all_methods_in_file):
    """Count Coupling between Methods (CM)"""
    count = 0
    method_lines = method_code.splitlines()
    
    for method_name in all_methods_in_file:
        # We need to make sure we are looking for actual calls, not just substrings
        # and not the method itself if it's currently being analyzed.
        # This is a heuristic. A full AST-based approach would be more robust.
        
        # Avoid counting the method itself as coupling with itself
        # This check is heuristic and might miss cases.
        # Example: if method 'foo' calls 'this.foo()', it would still be counted by simple string match.
        # For simplicity, we assume 'method_name' is usually unique enough here.
        
        for line in method_lines:
            line = line.strip()
            if not line or line.startswith(("//", "/*", "*", "*/")):
                continue
                
            # A more robust check for method calls.
            # Look for "methodName(" or "methodName ("
            # This avoids matching if "methodName" is just part of a variable name.
            if re.search(r'\b' + re.escape(method_name) + r'\s*\(', line):
                count += 1
                break  # Count once per distinct method called within the current method
    return count


def count_loc_type(class_code):
    return class_code.count("\n") + 1


def count_locnamm_type(class_decl):
    count = 0
    if hasattr(class_decl, 'body') and class_decl.body and hasattr(class_decl.body, 'members'):
        for member in class_decl.body.members:
            if isinstance(member, node.FunctionDeclaration):
                # Check if it's a non-accessor method
                if not member.name.startswith(("get", "set", "is")):
                    count += str(member.body).count("\n") + 1 if member.body else 0
    return count

def count_cfnamm_type(class_decl):
    methods = []
    if hasattr(class_decl, 'body') and class_decl.body and hasattr(class_decl.body, 'members'):
        for m in class_decl.body.members:
            if isinstance(m, node.FunctionDeclaration) and not m.name.startswith(("get", "set", "is")):
                methods.append(m.name)
    coupled = 0
    if hasattr(class_decl, 'body') and class_decl.body and hasattr(class_decl.body, 'members'):
        for m in class_decl.body.members:
            if isinstance(m, node.FunctionDeclaration) and m.name in methods:
                body = str(m.body)
                # Check for calls to other non-accessor methods within the same class
                if any(other_method_name != m.name and re.search(r'\b' + re.escape(other_method_name) + r'\s*\(', body) for other_method_name in methods):
                    coupled += 1
    return coupled / len(methods) if methods else 0

def noav_method(class_node, method_node):
    """
    Menghitung jumlah atribut class yang diakses di seluruh body fungsi (NOAV), 
    tanpa tergantung pada nama method/parameter/lokal.
    Perbaikan: juga menghitung akses via this.<prop> dan akses langsung pada baris yang mengandung method call.
    """
    # Ambil semua property class
    class_props = set()
    if hasattr(class_node, 'body') and hasattr(class_node.body, 'members'):
        for member in class_node.body.members:
            if isinstance(member, node.PropertyDeclaration):
                if hasattr(member, 'declaration') and hasattr(member.declaration, 'name'):
                    class_props.add(member.declaration.name)
                elif hasattr(member, 'name'):
                    class_props.add(member.name)

    # Ambil semua nama yang tidak boleh dihitung (parameter dan variabel lokal)
    param_vars = set()
    if hasattr(method_node, 'parameters'):
        for param in method_node.parameters:
            if hasattr(param, 'name'):
                param_vars.add(param.name)
    local_vars = set()
    body_str = str(method_node.body) if hasattr(method_node, 'body') and method_node.body else ""
    for match in re.finditer(r'\b(?:val|var)\s+([a-zA-Z_][a-zA-Z0-9_]*)', body_str):
        local_vars.add(match.group(1))

    accessed = set()
    # Cek akses this.<prop> dan super.<prop>
    for prop in class_props:
        if prop in param_vars or prop in local_vars:
            continue
        # Cek akses this.<prop>
        if re.search(r'\bthis\.' + re.escape(prop) + r'\b', body_str):
            accessed.add(prop)
        # Cek akses super.<prop>
        if re.search(r'\bsuper\.' + re.escape(prop) + r'\b', body_str):
            accessed.add(prop)
        # Cek akses langsung (bukan bagian dari kata lain, bukan param/lokal)
        # Perbaikan: hitung juga jika property dipakai dalam method call, assignment, atau argumen
        # Contoh: unregisterReceiver(mMessageReceiver)
        if re.search(r'\b' + re.escape(prop) + r'\b', body_str):
            accessed.add(prop)
    return len(accessed)

# Function to calculate WMC for a single class
def calculate_wmc_for_class(class_declaration):
    """Calculate WMC (Weighted Methods per Class) for a single class declaration"""
    if class_declaration.body is None:
        return 0
        
    wmc_value = 0
    for member in class_declaration.body.members:
        if isinstance(member, node.FunctionDeclaration):
            # Calculate complexity for this function
            cc_value = count_cc_manual(str(member.body)) if member.body else 0
            wmc_value += cc_value
            
    return wmc_value

def calculate_wmcnamm_type(class_declaration):
    """
    Calculate WMCNAMM_type (Weighted Methods per Class for Non-Accessor/Mutator Methods)
    This metric calculates the sum of cyclomatic complexity of non-accessor/non-mutator methods in a class
    """
    if class_declaration.body is None:
        return 0
    
    total_cc = 0
    
    # Identifikasi semua properti/atribut kelas untuk menentukan accessor/mutator methods
    class_properties = set()
    for member in class_declaration.body.members:
        if isinstance(member, node.PropertyDeclaration) or isinstance(member, node.VariableDeclaration):
            if hasattr(member, 'name'):
                class_properties.add(member.name)
    
    # Iterasi melalui semua metode kelas
    for member in class_declaration.body.members:
        if isinstance(member, node.FunctionDeclaration):
            # Skip jika metode tidak memiliki body
            if member.body is None:
                continue
            
            function_name = member.name
            function_body = str(member.body)
            
            # Cek apakah metode adalah accessor/mutator
            is_accessor_mutator = False
            
            # Pola nama untuk accessor/mutator: get*, set*, is*, has*
            if (function_name.startswith("get") or function_name.startswith("set") or 
                function_name.startswith("is") or function_name.startswith("has")):
                
                # Cek lebih lanjut berdasarkan konten dan nama properti
                property_name = ""
                if function_name.startswith("get"):
                    property_name = function_name[3:].lower()
                elif function_name.startswith("set"):
                    property_name = function_name[3:].lower()
                elif function_name.startswith("is"):
                    property_name = function_name[2:].lower()
                elif function_name.startswith("has"):
                    property_name = function_name[3:].lower()
                
                # Cari properti yang sesuai (case insensitive)
                for prop in class_properties:
                    if prop.lower() == property_name:
                        # Periksa apakah body metode sederhana (hanya return atau assignment)
                        # Ini adalah heuristik sederhana untuk menentukan accessor/mutator
                        body_lines = function_body.strip().split("\n")
                        is_simple = len(body_lines) <= 3  # Metode sederhana biasanya 1-3 baris
                        
                        if is_simple:
                            # Cek pola return/assignment
                            has_return_or_assign = any("return" in line or "=" in line for line in body_lines)
                            if has_return_or_assign:
                                is_accessor_mutator = True
                                break
            
            # Jika bukan accessor/mutator, hitung kompleksitasnya
            if not is_accessor_mutator:
                # Hitung kompleksitas siklomat metode
                cc_value = count_cc_manual(function_body)
                total_cc += cc_value
    
    return total_cc

def calculate_amw_type(class_declaration):
    """
    Calculate AMW_type (Average Method Weight)
    This metric calculates the average cyclomatic complexity of methods in a class
    """
    if class_declaration.body is None:
        return 0
    
    method_cc_values = []
    
    # Iterasi melalui semua metode kelas
    for member in class_declaration.body.members:
        if isinstance(member, node.FunctionDeclaration):
            # Skip jika metode tidak memiliki body
            if member.body is None:
                continue
            
            # Hitung kompleksitas siklomat metode
            function_body = str(member.body)
            cc_value = count_cc_manual(function_body)
            method_cc_values.append(cc_value)
    
    # Hitung rata-rata kompleksitas
    if method_cc_values:
        return sum(method_cc_values) / len(method_cc_values)
    else:
        return 0  # Jika tidak ada metode, kembalikan 0

def count_nocs_package(directory):
    """
    Calculate NOCS_package (Number of Classes in a Package)
    This metric counts the number of classes in each package
    
    Returns a dictionary mapping package names to their class counts
    """
    # Dictionary untuk menyimpan jumlah kelas per package
    package_class_counts = {}
    
    # Temukan semua file Kotlin dalam direktori
    kotlin_files = [os.path.join(root, f) for root, _, files in os.walk(directory) 
                  for f in files if f.endswith(".kt") or f.endswith(".kts")]
    
    for file_path in kotlin_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()
            parser = Parser(code)
            result = parser.parse()
            
            # Dapatkan nama paket
            package_name = result.package.name if result.package else "default"
            
            # Hitung jumlah kelas dalam file ini
            class_count = sum(1 for decl in result.declarations if isinstance(decl, node.ClassDeclaration))
            
            # Update jumlah kelas untuk paket ini
            if package_name in package_class_counts:
                package_class_counts[package_name] += class_count
            else:
                package_class_counts[package_name] = class_count
                
        except Exception:
            # Jika file tidak dapat di-parse, lanjutkan ke file berikutnya
            continue
    
    return package_class_counts

def calculate_lcom5(class_declaration):
    """
    Calculate LCOM5 (Lack of Cohesion in Methods) 
    Uses a simplified approach based on method body similarity
    """
    if class_declaration.body is None:
        return 0
    
    # Collect all methods with bodies
    methods = []
    for member in class_declaration.body.members:
        if isinstance(member, node.FunctionDeclaration) and member.body is not None:
            methods.append(member)
    
    # Need at least 2 methods for LCOM5 calculation
    if len(methods) < 2:
        return 0
    
    # Calculate method pairs and their similarity
    total_pairs = 0
    cohesive_pairs = 0
    
    for i in range(len(methods)):
        for j in range(i + 1, len(methods)):
            total_pairs += 1
            
            # Get method bodies as strings (same way as your other metrics)
            body1 = str(methods[i].body) if methods[i].body else ""
            body2 = str(methods[j].body) if methods[j].body else ""
            
            if body1 and body2:
                # Split into tokens and find common meaningful tokens
                tokens1 = set(body1.split())
                tokens2 = set(body2.split())
                
                # Remove common programming constructs
                common_keywords = {
                    'if', 'else', 'for', 'while', 'return', 'var', 'val', 'fun', 
                    'this', 'null', 'true', 'false', 'it', 'when', 'is', 'as',
                    '{', '}', '(', ')', '[', ']', ';', ',', '.', '=', '+', '-', 
                    '*', '/', '&&', '||', '!', '<', '>', '<=', '>=', '==', '!=',
                    'private', 'public', 'protected', 'internal', 'override'
                }
                
                # Filter out keywords and short tokens
                meaningful_tokens1 = {token for token in tokens1 
                                    if token not in common_keywords and len(token) > 2}
                meaningful_tokens2 = {token for token in tokens2 
                                    if token not in common_keywords and len(token) > 2}
                
                # Check if methods share meaningful tokens (indicating shared attributes/functionality)
                shared_tokens = meaningful_tokens1 & meaningful_tokens2
                if len(shared_tokens) > 0:
                    cohesive_pairs += 1
    
    if total_pairs == 0:
        return 0
    
    # LCOM5 = 1 - (cohesive pairs / total pairs)
    # Higher values indicate lower cohesion
    lcom5 = 1 - (cohesive_pairs / total_pairs)
    
    # Ensure result is between 0 and 1
    return max(0.0, min(1.0, lcom5))

def extracted_method(file_path, noi_count, nom_count, nomnamm_count, nocs_package_counts):
    """Ekstrak informasi metode dari file Kotlin tanpa metrik LOC, Max Nesting, CC, dan WOC."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
        
        parser = Parser(code)
        result = parser.parse()
        package_name = result.package.name if result.package else "Unknown"

        nocs_package = nocs_package_counts.get(package_name, 0)

        declarations = result.declarations if hasattr(result, 'declarations') else []
        class_decls = [n for n in declarations if isinstance(n, node.ClassDeclaration)]
        interface_decls = [n for n in declarations if isinstance(n, node.InterfaceDeclaration)]
        function_decls = [n for n in declarations if isinstance(n, node.FunctionDeclaration)]

        # --- PACKAGE-LEVEL METRICS ---
        nomnamm_package = sum(1 for f in function_decls if not f.name.startswith(("get", "set", "is")))
        for c in class_decls:
            if hasattr(c, 'body') and c.body and hasattr(c.body, 'members'):
                for m in c.body.members:
                    if isinstance(m, node.FunctionDeclaration) and not m.name.startswith(("get", "set", "is")):
                        nomnamm_package += 1
        noi_package = len(interface_decls)
        loc_package = code.count("\n") + 1

        # Simpan metrik package-level dalam dictionary berdasarkan package_name
        package_metrics_map = {
            package_name: {
                'NOMNAMM_Package': nomnamm_package,
                'NOI_Package': noi_package,
                'LOC_Package': loc_package
            }
        }

        # Kumpulkan semua nama method di file untuk CM calculation
        all_methods_in_file = [f.name for f in function_decls if not f.name.startswith(("get", "set", "is"))]
        for c in class_decls:
            if hasattr(c, 'body') and c.body and hasattr(c.body, 'members'):
                for m in c.body.members:
                    if isinstance(m, node.FunctionDeclaration) and not m.name.startswith(("get", "set", "is")):
                        all_methods_in_file.append(m.name)

        if not result.declarations:
            return [{
                "Package": package_name,
                "Class": "Unknown",
                "Method": "None",
                "NOI": noi_count,
                "NOM": nom_count,
                "NOMNAMM": nomnamm_count,
                "NOC_type": 0,
                "WMC_type": 0,
                "LCOM5": 0,
                "WMCNAMM_type": 0,
                "AMW_type": 0,
                "NOCS_package": nocs_package,
                "Error": "No class declaration found"
            }]
        
        class_declaration = result.declarations[0]
        class_name = class_declaration.name
        
        if class_declaration.body is None:
            return [{
                "Package": package_name,
                "Class": class_name,
                "Method": "None",
                "NOI": noi_count,
                "NOM": nom_count,
                "NOMNAMM": nomnamm_count,
                "NOC_type": 0,
                "WMC_type": 0,
                "LCOM5": 0,
                "WMCNAMM_type": 0,
                "AMW_type": 0,
                "NOCS_package": nocs_package,
                "Error": "Class has no body"
            }]

        directory = os.path.dirname(file_path)
        noc_type_mapping = count_noc_type(directory)

        datas = []
        for class_declaration in result.declarations:
            if not isinstance(class_declaration, node.ClassDeclaration):
                continue
                
            class_name = class_declaration.name
            noc_type = noc_type_mapping.get(class_name, 0)
            wmc_type = calculate_wmc_for_class(class_declaration)
            lcom5_value = calculate_lcom5(class_declaration)
            wmcnamm_type = calculate_wmcnamm_type(class_declaration)
            amw_type = calculate_amw_type(class_declaration)

            if class_declaration.body is None:
                datas.append({
                    "Package": package_name,
                    "Class": class_name,
                    "Method": "None",
                    "NOI": noi_count,
                    "NOM": nom_count,
                    "NOMNAMM": nomnamm_count,
                    "NOC_type": noc_type,
                    "WMC_type": wmc_type,
                    "LCOM5": lcom5_value,
                    "WMCNAMM_type": wmcnamm_type,
                    "AMW_type": amw_type,
                    "NOCS_package": nocs_package,
                    "Error": "Class has no body"
                })
                continue

            for member in class_declaration.body.members:
                if isinstance(member, node.FunctionDeclaration):
                    datas.append({
                        "Package": package_name,
                        "Class": class_name,
                        "Method": member.name,
                        "NOI": noi_count,
                        "NOM": nom_count,
                        "NOMNAMM": nomnamm_count,
                        "NOC_type": noc_type,
                        "WMC_type": wmc_type,
                        "LCOM5": lcom5_value,
                        "WMCNAMM_type": wmcnamm_type,
                        "AMW_type": amw_type,
                        "NOCS_package": nocs_package
                    })

            if not datas:
                datas.append({
                    "Package": package_name,
                    "Class": class_name,
                    "Method": "None",
                    "NOI": noi_count,
                    "NOM": nom_count,
                    "NOMNAMM": nomnamm_count,
                    "NOC_type": noc_type,
                    "WMC_type": wmc_type,
                    "LCOM5": lcom5_value,
                    "WMCNAMM_type": wmcnamm_type,
                    "AMW_type": amw_type,
                    "NOCS_package": nocs_package,
                    "Error": "No functions found"
                })

        return datas if datas else [{
            "Package": package_name,
            "Class": "Unknown",
            "Method": "None",
            "NOI": noi_count,
            "NOM": nom_count,
            "NOMNAMM": nomnamm_count,
            "NOC_type": 0,
            "WMC_type": 0,
            "LCOM5": 0,
            "WMCNAMM_type": 0,
            "AMW_type": 0,
            "NOCS_package": nocs_package,
            "Error": "No class declarations found"
        }]
    
    except Exception as e:
        return [{
            "Package": "UnknownPackage",
            "Class": "UnknownClass",
            "Method": "UnknownMethod",
            "NOI": noi_count,
            "NOM": nom_count,
            "NOMNAMM": nomnamm_count,
            "NOC_type": 0,
            "WMC_type": 0,
            "LCOM5": 0,
            "WMCNAMM_type": 0,
            "AMW_type": 0,
            "NOCS_package": 0,
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
            noi_count = count_noi(temp_dir)
            nom_count = count_nom(temp_dir)
            nomnamm_count = count_nomnamm(temp_dir)
            # Hitung NOCS_package
            nocs_package_counts = count_nocs_package(temp_dir)
            results = []
            for kotlin_file in kotlin_files:
                file_results = extracted_method(kotlin_file, noi_count, nom_count, nomnamm_count, nocs_package_counts)
                results.extend(file_results)
            
            return pd.DataFrame(results)
        except Exception as e:
            return "extract and parser : ", str(e)


