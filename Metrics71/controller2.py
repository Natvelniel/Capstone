import os
import tempfile
import patoolib
import pandas as pd
from kopyt import Parser, node

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
        atfd_total = 0
        for member in class_declaration.body.members:
            if isinstance(member, node.FunctionDeclaration):
                function_names = member.name
                loc_count = str(member.body).count("\n") + 1 if member.body else 0
                
                #print(f"code method :{method_code}")
            
        
                
        datas.append({"Package": package_name, "Class": class_name, "Method": function_names, "LOC": loc_count,})
         
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