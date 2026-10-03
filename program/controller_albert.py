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
                        "number_constructor_DefaultConstructor_methods" : number_constructor_DefaultConstructor_values,
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
