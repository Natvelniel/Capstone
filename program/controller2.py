import os
import tempfile
import patoolib
import pandas as pd
import re # untuk NOII type
from kopyt import Parser, node  # Gunakan `kopyt` sebagai parser AST Kotlin
from .controller_albert import *
from .controller_henry import *
from .controller_jason import *
from .controller_danta import *

from .controller_indarto import *
from .controller_patrik import *
from .controller_adit import *
from .controller import *

def get_class_properties(class_node):
    props = set()
    if hasattr(class_node, 'body') and hasattr(class_node.body, 'members'):
        for member in class_node.body.members:
            if isinstance(member, node.PropertyDeclaration):
                if hasattr(member, 'declaration') and hasattr(member.declaration, 'name'):
                    props.add(member.declaration.name)
                elif hasattr(member, 'name'):
                    props.add(member.name)
    return props

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

def count_memcl(method_code):
    """Menghitung Mean Method Chain Length (MeMCL)."""
    chains = [len(call.split(".")) for call in method_code.split() if "." in call]
    return sum(chains) / len(chains) if chains else 0

def count_nom_main(directory):
    nom_count = 0
    kotlin_files = [os.path.join(root, f) for root, _, files in os.walk(directory) for f in files if f.endswith(".kt")]
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

def count_noi_main(directory):
    noi_count = 0
    kotlin_files = [os.path.join(root, f) for root, _, files in os.walk(directory) for f in files if f.endswith(".kt")]
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

def count_nomnamm_main(directory):
    nomnamm_count = 0
    kotlin_files = [os.path.join(root, f) for root, _, files in os.walk(directory) for f in files if f.endswith(".kt")]
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

def count_nocs_package_main(directory):
    """
    Calculate NOCS_package (Number of Classes in a Package)
    This metric counts the number of classes in each package
    
    Returns a dictionary mapping package names to their class counts
    """
    # Dictionary untuk menyimpan jumlah kelas per package
    package_class_counts = {}
    
    # Temukan semua file Kotlin dalam direktori
    kotlin_files = [os.path.join(root, f) for root, _, files in os.walk(directory) 
                  for f in files if f.endswith(".kt")]
    
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


def extracted_method(file_path, project_attributes,  package_list, class_list, method_list, noi_count, nom_count, nomnamm_count, nocs_package_counts):
    data = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()

        parser = Parser(code)
        result = parser.parse()
        package_name = result.package.name if result.package else "Unknown"
        package_list.add(package_name)
        
        # Dapatkan NOCS_package untuk paket ini
        nocs_package = nocs_package_counts.get(package_name, 0)

        fanout_method_values = {}
        atfd_method_values = {}

        directory = os.path.dirname(file_path)
        noc_type_mapping = count_noc_type(directory)

        # deklarasi metrik tingkat class

        count_num_final_not_static_attributes_values = count_num_final_not_static_attributes(file_path)
        num_static_not_final_attributes_values = count_num_static_not_final_attributes(file_path)
        number_public_visibility_methods_values = number_public_visibility_methods(file_path)
        number_private_visibility_methods_values = number_private_visibility_methods(file_path)
        number_protected_visibility_methods_values = number_protected_visibility_methods(file_path)
        number_package_visibility_methods_values = number_package_visibility_methods(file_path)
        number_standard_design_methods_values = number_standard_design_methods(file_path)
        number_constructor_DefaultConstructor_values = number_constructor_DefaultConstructor_methods(file_path)

        count_noii_type_value = count_NOII_type(code)

        class_decls = [d for d in result.declarations if isinstance(d, node.ClassDeclaration)]

        for class_decl in class_decls:
            # deklarasi metrik tingkat class
            class_name = class_decl.name
            class_props = get_class_properties(class_decl)
            all_methods = [m.name for m in class_decl.body.members if isinstance(m, node.FunctionDeclaration)]
            nom = count_nom(class_decl)
            nmo = count_nmo(class_decl)
            class_list.add(class_name)

            class_counts = project_attributes.get(class_name, {})

            final_count = number_final_methods(class_decl)
            abstract_count = number_abstract_methods(class_decl)
            static_count = number_static_methods(class_decl)
            final_static_count = number_final_static_methods(class_decl)
            not_final_static_count = number_not_final_static_methods(class_decl)
            not_final_not_static_count = number_not_final_not_static_methods(class_decl)
            not_abstract_not_final_count = number_not_abstract_not_final_methods(class_decl)

            cfnamm_results = {}
            clnamm_results = {}

            cfnamm_results = count_cfnamm_method(class_decls)
            
            # ARGO
            clnamm_results = count_CLNAMM_method(class_decl)
            count_noam_value = count_noam_type(class_decl)
            count_nocs_type_value = count_nocs_type(class_decl)
            number_constructor_NotDefaultConstructor_values = number_constructor_NotDefaultConstructor_methods(file_path)

            noc_type = noc_type_mapping.get(class_name, 0)
            # Calculate WMC for this class
            wmc_type = calculate_wmc_for_class(class_decl)
            # Calculate LCOM5 for this class
            lcom5_value = calculate_lcom5(class_decl)
            # Calculate WMCNAMM_type for this class
            wmcnamm_type = calculate_wmcnamm_type(class_decl)
            # Calculate AMW_type for this class
            amw_type = calculate_amw_type(class_decl)

            declarations = result.declarations if hasattr(result, 'declarations') else []
            class_decls = [n for n in declarations if isinstance(n, node.ClassDeclaration)]
            tcc_value = tcc_type(class_decl.body, result)
            method_function = {}
            woc_values = count_WOC(result)
            # count_num_final_not_static_methods_values = count_Number_Final_Not_Static_Methods(class_decl)

            all_methods_dict = {
                m.name: m for m in class_decl.body.members if isinstance(m, node.FunctionDeclaration)
            }
            
            companion_found_by_kopyt = False
            for method in class_decl.body.members:
                if not isinstance(method, node.FunctionDeclaration):
                    continue
                # deklarasi metrik tingkat method
                method_name = method.name
                method_list.append({"Package": package_name, "Class": class_name, "Method": method_name})
                method_body = str(method.body) if method.body else ""
                atfd_method = count_atfd(method, class_decl)
                fanout_method = count_fanout_method(method_body, set(all_methods))
                cfnamm_value = cfnamm_results.get(method_name, 0.0)
                clnamm_value = clnamm_results.get(method_name, 0.0)
                fanout_method_values[method_name] = fanout_method
                atfd_method_values[method_name] = atfd_method
                loc_method = str(method.body).count("\n") + 1 if method.body else 0
                cc_value = count_cc_manual(str(method.body)) if method.body else 0
                maxnesting = manual_max_nesting(str(method.body)) if method.body else 0
                nmcs_count = NMCS_counter(class_decl,str(method.body))
                laa_value = laa_method(class_decl.body, method)
                tcc_value = tcc_type(class_decl.body, result)
                method_function[method_name] = (cc_value, loc_method, maxnesting, nmcs_count, laa_value, tcc_value)
                cint_value = count_CINT_method(method, class_decl)
                cdisp_value = count_CDISP_method(method, class_decl)

                row = {
                    # output dari metrik
                    "Package": package_name,
                    "Class": class_name,
                    "Method": method_name,
                    # ARGO
                    "CYCLO_method": cc_value,
                    "NOLV_method": count_nolv(str(method.body)),
                    "CLNAMM_method": clnamm_value,
                    "CINT_method": cint_value,
                    "CDISP_method": cdisp_value,
                    "NOII_type": count_noii_type_value,
                    "NOAM_type": count_noam_value,
                    "NOCS_type": count_nocs_type_value,
                    "number_constructor_NotDefaultConstructor": number_constructor_NotDefaultConstructor_values,

                    "LOC_method": loc_method,
                    "MAXNESTING_method": maxnesting,
                    "CC_method": cc_value,
                    "NMCS_method": nmcs_count,
                    "LAA_method": laa_value,
                    "CM_method": count_cm_method(method_body, all_methods),
                    "NOAV_method": noav_method(class_decl, method),
                    "ATFD_method": atfd_method,
                    "FANOUT_method": fanout_method,
                    "ATLD_method": count_atld_method(method, class_props),
                    "MaMCL_method": count_mamcl(method_body),
                    "MeMCL_method": count_memcl(method_body),
                    "NOP_method": count_nop(method),
                    "FDP_method": count_fdp(method, class_decl),
                    "CFNAMM_method": cfnamm_value,
                    "Number_Final_Not_Static_Methods": count_Number_Final_Not_Static_Methods(class_decl),
                    "TCC_type": tcc_value,
                    "WOC_type": woc_values,
                    "LOC_type": count_loc_type(str(class_decl)),
                    "LOCNAMM_type": count_locnamm_type(class_decl),
                    "CFNAMM_type": count_cfnamm_type(class_decl),
                    
                    "NOMNAMM_type": count_nomnamm_type(class_decl),
                    "NOA_type": count_noa_type(class_decl),
                    "NIM_type": count_nim_type(class_decl),
                    "DIT_type": count_dit_by_name(class_decl),
                    "NOPA_type": count_nopa(class_decl),
                    "CBO_type": count_cbo(class_decl),
                    "RFC_type": count_rfc(class_decl),
                    "isStatic_type": is_static(result),
                    **class_counts,  # Menambahkan atribut dari project_attributes
                    "NOC_type": noc_type,
                    "WMC_type": wmc_type,
                    "LCOM5_type": lcom5_value,
                    "WMCNAMM_type": wmcnamm_type,
                    "AMW_type": amw_type,
                    "NOM_type": nom,
                    "NMO_type": nmo,

                    "num_final_not_static_attributes": count_num_final_not_static_attributes_values,
                    "num_static_not_final_attributes": num_static_not_final_attributes_values,
                    "number_public_visibility_methods": number_public_visibility_methods_values,
                    "number_private_visibility_methods": number_private_visibility_methods_values,
                    "number_protected_visibility_methods": number_protected_visibility_methods_values, 
                    "number_package_visibility_methods": number_package_visibility_methods_values,
                    "number_standard_design_methods": number_standard_design_methods_values,
                    "number_constructor_DefaultConstructor_methods": number_constructor_DefaultConstructor_values,
                    "number_final_methods": final_count,
                    "number_abstract_methods": abstract_count,
                    "number_static_methods": static_count,
                    "number_final_static_methods": final_static_count,
                    "number_not_final_static_methods": not_final_static_count,
                    "number_not_final_not_static_methods": not_final_not_static_count,
                    "number_not_abstract_not_final_methods": not_abstract_not_final_count,

                    "NOI_project": noi_count,
                    "NOM_project": nom_count,
                    "NOMNAMM_project": nomnamm_count,
                    "NOCS_package": nocs_package,
                    "isStatic_method": is_static_method(str(method), str(class_decl))
                    
                }

                data.append(row)
                
                # masih belum keluar output untuk companion object
                if isinstance(method, node.ObjectDeclaration):
                    if method.name == "Companion" or (method.modifiers and "companion" in method.modifiers):
                        companion_found_by_kopyt = True
                        for comp_member in method.body.members:
                            if isinstance(comp_member, node.FunctionDeclaration):
                                row.update({
                                    #output dari metrik jika ada didalam companion object
                                    "Package": package_name,
                                    "class": class_name,
                                    "method": comp_member.name,
                                    # ARGO
                                    "CYCLO_method": cc_value,
                                    "NOLV_method": count_nolv(str(method.body)),
                                    "CLNAMM_method": clnamm_value,
                                    "CINT_method": cint_value,
                                    "CDISP_method": cdisp_value,
                                    "NOII_type": count_noii_type_value,
                                    "NOAM_type": count_noam_value,
                                    "NOCS_type": count_nocs_type_value,
                                    "number_constructor_NotDefaultConstructor": number_constructor_NotDefaultConstructor_values,

                                    "LOC_method": loc_method,
                                    "MAXNESTING_method": maxnesting,
                                    "CC_method": cc_value,
                                    "NMCS_method": nmcs_count,
                                    "LAA_method": laa_value,
                                    "CM_method": count_cm_method(method_body, all_methods),
                                    "NOAV_method": noav_method(class_decl, method),
                                    "ATFD_method": atfd_method,
                                    "FANOUT_method": fanout_method,
                                    "ATLD_method": count_atld_method(method, class_props),
                                    "MaMCL_method": count_mamcl(method_body),
                                    "MeMCL_method": count_memcl(method_body),
                                    "NOP_method": count_nop(method),
                                    "FDP_method": count_fdp(method, class_decl),
                                    "CFNAMM_method": cfnamm_value,
                                    
                                    "Number_Final_Not_Static_Methods": count_Number_Final_Not_Static_Methods(class_decl),
                                    "TCC_type": tcc_value,
                                    "WOC_type": woc_values,
                                    "LOC_type": count_loc_type(str(class_decl)),
                                    "LOCNAMM_type": count_locnamm_type(class_decl),
                                    "CFNAMM_type": count_cfnamm_type(class_decl),
                                    
                                    "NOMNAMM_type": count_nomnamm_type(class_decl),
                                    "NOA_type": count_noa_type(class_decl),
                                    "NIM_type": count_nim_type(class_decl),
                                    "DIT_type": count_dit_by_name(class_decl),
                                    "NOPA_type": count_nopa(class_decl),
                                    "CBO_type": count_cbo(class_decl),
                                    "RFC_type": count_rfc(class_decl),
                                    "isStatic_type": is_static(result),
                                    **class_counts,  # Menambahkan atribut dari project_attributes
                                    "NOC_type": noc_type,
                                    "WMC_type": wmc_type,
                                    "LCOM5_type": lcom5_value,
                                    "WMCNAMM_type": wmcnamm_type,
                                    "AMW_type": amw_type,
                                    "NOM_type": nom,
                                    "NMO_type": nmo,

                                    "num_final_not_static_attributes": count_num_final_not_static_attributes_values,
                                    "num_static_not_final_attributes": num_static_not_final_attributes_values,
                                    "number_public_visibility_methods": number_public_visibility_methods_values,
                                    "number_private_visibility_methods": number_private_visibility_methods_values,
                                    "number_protected_visibility_methods": number_protected_visibility_methods_values, 
                                    "number_package_visibility_methods": number_package_visibility_methods_values,
                                    "number_standard_design_methods": number_standard_design_methods_values,
                                    "number_constructor_DefaultConstructor_methods": number_constructor_DefaultConstructor_values,
                                    "number_final_methods": final_count,
                                    "number_abstract_methods": abstract_count,
                                    "number_static_methods": static_count,
                                    "number_final_static_methods": final_static_count,
                                    "number_not_final_static_methods": not_final_static_count,
                                    "number_not_final_not_static_methods": not_final_not_static_count,
                                    "number_not_abstract_not_final_methods": not_abstract_not_final_count,

                                    "NOI_project": noi_count,
                                    "NOM_project": nom_count,
                                    "NOMNAMM_project": nomnamm_count,
                                    "NOCS_package": nocs_package,
                                    "isStatic_method": is_static_method(str(comp_member), str(class_decl))
                                })
                #                 print(f"Companion object method found: {comp_member.name} in {file_path}")
                        
            atfd_type = sum(atfd_method_values.values())
            fanout_type = sum(fanout_method_values.values())
            amwnamm_value = calculate_AMWNAMM(method_function)
            
            for rows in data:
                rows.update({
                    "ATFD_type": atfd_type,
                    "FANOUT_type": fanout_type,
                    "AMWNAMM_type": calculate_AMWNAMM(method_function),
                    })
            
        if not companion_found_by_kopyt:
            companion_lines = extract_companion_block(code)
            for line in companion_lines:
                if "fun"  in line:
                    method_name = line.split("fun")[1].split("(")[0].strip()
                    row.update({
                        # output dari metrik jika ada didalam companion object
                        "Package": package_name,
                        "Class": class_name,
                        "Method": method_name,
                        # ARGO
                        "CYCLO_method": cc_value,
                        "NOLV_method": count_nolv(str(method.body)),
                        "CLNAMM_method": clnamm_value,
                        "CINT_method": cint_value,
                        "CDISP_method": cdisp_value,
                        "NOII_type": count_noii_type_value,
                        "NOAM_type": count_noam_value,
                        "NOCS_type": count_nocs_type_value,
                        "number_constructor_NotDefaultConstructor": number_constructor_NotDefaultConstructor_values,

                        "LOC_method": loc_method,
                        "MAXNESTING_method": maxnesting,
                        "CC_method": cc_value,
                        "NMCS_method": nmcs_count,
                        "LAA_method": laa_value,
                        "CM_method": count_cm_method(method_body, all_methods),
                        "NOAV_method": noav_method(class_decl, method),
                        "ATFD_method": atfd_method,
                        "FANOUT_method": fanout_method,
                        "ATLD_method": count_atld_method(method, class_props),
                        "MaMCL_method": count_mamcl(method_body),
                        "MeMCL_method": count_memcl(method_body),
                        "NOP_method": count_nop(method),
                        "FDP_method": count_fdp(method, class_decl),
                        "CFNAMM_method": cfnamm_value,
                        
                        "Number_Final_Not_Static_Methods": count_Number_Final_Not_Static_Methods(class_decl),
                        "TCC_type": tcc_value,
                        "WOC_type": woc_values,
                        "LOC_type": count_loc_type(str(class_decl)),
                        "LOCNAMM_type": count_locnamm_type(class_decl),
                        "CFNAMM_type": count_cfnamm_type(class_decl),
                        
                        "NOMNAMM_type": count_nomnamm_type(class_decl),
                        "NOA_type": count_noa_type(class_decl),
                        "NIM_type": count_nim_type(class_decl),
                        "DIT_type": count_dit_by_name(class_decl),
                        "NOPA_type": count_nopa(class_decl),
                        "CBO_type": count_cbo(class_decl),
                        "RFC_type": count_rfc(class_decl),
                        "isStatic_type": is_static(result),
                        **class_counts,  # Menambahkan atribut dari project_attributes
                        "NOC_type": noc_type,
                        "WMC_type": wmc_type,
                        "LCOM5_type": lcom5_value,
                        "WMCNAMM_type": wmcnamm_type,
                        "AMW_type": amw_type,
                        "NOM_type": nom,
                        "NMO_type": nmo,

                        "num_final_not_static_attributes": count_num_final_not_static_attributes_values,
                        "num_static_not_final_attributes": num_static_not_final_attributes_values,
                        "number_public_visibility_methods": number_public_visibility_methods_values,
                        "number_private_visibility_methods": number_private_visibility_methods_values,
                        "number_protected_visibility_methods": number_protected_visibility_methods_values, 
                        "number_package_visibility_methods": number_package_visibility_methods_values,
                        "number_standard_design_methods": number_standard_design_methods_values,
                        "number_constructor_DefaultConstructor_methods": number_constructor_DefaultConstructor_values,
                        "number_final_methods": final_count,
                        "number_abstract_methods": abstract_count,
                        "number_static_methods": static_count,
                        "number_final_static_methods": final_static_count,
                        "number_not_final_static_methods": not_final_static_count,
                        "number_not_final_not_static_methods": not_final_not_static_count,
                        "number_not_abstract_not_final_methods": not_abstract_not_final_count,

                        "NOI_project": noi_count,
                        "NOM_project": nom_count,
                        "NOMNAMM_project": nomnamm_count,
                        "NOCS_package": nocs_package,
                        "isStatic_method": 1
                    })
    except Exception as e:
        print(f"[ERROR] {file_path}: {e}")

    return data

def extract_and_parse(file):
    """Ekstrak arsip ZIP/RAR dan proses file Kotlin."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file_path = os.path.join(temp_dir, file.name)
        with open(temp_file_path, "wb") as f:
            f.write(file.getbuffer())
        
        try:
            patoolib.extract_archive(temp_file_path, outdir=temp_dir)
            
            noi_count = count_noi_main(temp_dir)
            nom_count = count_nom_main(temp_dir)
            nomnamm_count = count_nomnamm_main(temp_dir)
            kotlin_files = [os.path.join(root, f) for root, _, files in os.walk(temp_dir) for f in files if f.endswith(".kt")]
            
            # Hitung NOCS_package
            nocs_package_counts = count_nocs_package(temp_dir)
            

            loc_project = count_loc_project(kotlin_files)
            project_attributes = count_attributes_in_project(kotlin_files)

            file_package_map = {}
            file_code_map = {}

            

            results = []
            packages, classes, methods = set(), set(), []

            for kotlin_file in kotlin_files:
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
                file_result = extracted_method(kotlin_file, project_attributes, packages, classes, methods, noi_count, nom_count, nomnamm_count, nocs_package_counts)
                if file_result:
                    results.extend(file_result)

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

            for row in results:
                pkg = row.get("Package", "UNKNOWN")
                pkg_metrics = package_metrics_map.get(pkg, {'NOMNAMM_Package': 0, 'NOI_Package': 0, 'LOC_Package': 0})
                row["NOMNAMM_Package"] = pkg_metrics['NOMNAMM_Package']
                row["NOI_Package"] = pkg_metrics['NOI_Package']
                row["LOC_package"] = pkg_metrics['LOC_Package']

            additional_metrics = count_additional_metrics(classes, methods, packages)
            

            df = pd.DataFrame(results)
            df["NOPK_project"] = additional_metrics["NOPK_project"]
            df["NOCS_project"] = additional_metrics["NOCS_project"]
            df["NOM_package"] = df["Package"].map(additional_metrics["NOM_package"])
            df["LOC_project"] = loc_project
            
            return df
        except Exception as e:
            return f"extract_and_parse error: {e}"
        
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

# ================================== ARGO =====================================

# def count_NOLV_method
def count_nolv(block_str):
    """
    Menghitung jumlah deklarasi variabel lokal di dalam string tubuh method
    berdasarkan keberadaan kata kunci 'val' atau 'var' di awal baris atau setelah indentasi.

    Args:
        block_str (str): String representasi dari isi blok method (str(method.body))

    Returns:
        int: Jumlah variabel lokal (val/var)
    """
    count = 0
    lines = block_str.splitlines()
    
    for line in lines:
        stripped = line.strip()
        
        # Abaikan baris kosong dan komentar
        if not stripped or stripped.startswith("//") or stripped.startswith("/*"):
            continue
        
        # Cek apakah baris dimulai dengan 'val' atau 'var'
        if stripped.startswith("val ") or stripped.startswith("var "):
            count += 1
        # Atau jika val/var muncul setelah indentasi (misal dalam if, when)
        elif " val " in stripped or " var " in stripped:
            # Optional: pastikan dia tidak dalam komentar akhir baris
            comment_index = stripped.find("//")
            check_str = stripped if comment_index == -1 else stripped[:comment_index]
            if " val " in check_str or " var " in check_str:
                count += 1

    return count

# def count_CLNAMM_method count_called_local_not_accessor_or_mutator
def count_CLNAMM_method(class_declaration):
    """
    Hitung CLNAMM: jumlah method NON-AM lokal yang dipanggil oleh masing-masing method NON-AM.
    """

    if not hasattr(class_declaration, 'body') or class_declaration.body is None:
        return {}

    non_am_methods = {}  # method_name: body_str
    all_methods_am_status = {}  # method_name: is_accessor_or_mutator
    class_properties = set()

    # 1. Kumpulkan properti class (misal: "value")
    for member in class_declaration.body.members:
        if isinstance(member, node.PropertyDeclaration):
            decl = member.declaration
            if isinstance(decl, node.VariableDeclaration):
                class_properties.add(decl.name)
            elif isinstance(decl, node.MultiVariableDeclaration):
                for var in decl.sequence:
                    class_properties.add(var.name)

    # 2. Identifikasi method dan tentukan apakah AM atau bukan
    for member in class_declaration.body.members:
        if isinstance(member, node.FunctionDeclaration):
            method_name = member.name
            is_am = False

            if member.body:
                body_str = str(member.body)
                body_clean = body_str.replace('\n', '').strip()

                # Sederhanakan logika AM: berdasarkan nama saja
                if method_name.startswith(("get", "is", "set")):
                    is_am = True

            all_methods_am_status[method_name] = is_am

            if not is_am:
                non_am_methods[method_name] = body_str

    # 3. Hitung CLNAMM: hanya pemanggilan method lokal yang bukan AM
    clnamm_per_method = {}
    for method_name, body_str in non_am_methods.items():
        count = 0
        for target_name, is_am in all_methods_am_status.items():
            if target_name == method_name or is_am:
                continue
            if f"{target_name}(" in body_str:
                count += 1
        clnamm_per_method[method_name] = count

    return clnamm_per_method

# def count_CINT_method
def count_CINT_method(method, class_decl):
    local_methods = {
        m.name for m in class_decl.body.members
        if isinstance(m, node.FunctionDeclaration)
    }

    if not method.body:
        return 0

    body_str = str(method.body)
    
    # Naif: ambil kata2 setelah titik (.)
    called_methods = set()
    lines = body_str.splitlines()
    for line in lines:
        line = line.strip()
        if "." in line and "(" in line:
            parts = line.split(".")
            if len(parts) > 1:
                right_part = parts[1]
                method_name = right_part.split("(")[0].strip()
                if method_name and method_name not in local_methods:
                    called_methods.add(method_name)

    return len(called_methods)

def count_CINTforCDISP_method(method, class_decl):
    local_methods = {
        m.name for m in class_decl.body.members
        if isinstance(m, node.FunctionDeclaration)
    }

    if not method.body:
        return set(), set()

    body_str = str(method.body)
    
    external_calls = set()
    external_classes = set()

    lines = body_str.splitlines()
    for line in lines:
        line = line.strip()
        if "." in line and "(" in line:
            parts = line.split(".")
            if len(parts) > 1:
                class_name = parts[0].strip()  # bagian sebelum titik
                right_part = parts[1]
                method_name = right_part.split("(")[0].strip()
                if method_name and method_name not in local_methods:
                    external_calls.add(f"{class_name}.{method_name}")
                    external_classes.add(class_name)

    return external_calls, external_classes

# def count_CDISP_method
def count_CDISP_method(method, class_decl):
    # Asumsi: count_cint sudah tersedia dan mengembalikan tuple (external_calls, external_classes)
    external_calls, external_classes = count_CINTforCDISP_method(method, class_decl)

    cint_value = len(external_calls)
    if cint_value == 0:
        return 0.0
    
    cdisp_value = len(external_classes) / cint_value
    return round(cdisp_value, 4)  # pembulatan opsional

def count_NOII_type(code):
    """
    Menghitung jumlah interface yang diimplementasikan dari string kode Kotlin class.
    """
    class_decl_match = re.search(r'class\s+\w+\s*:\s*([^({]+)', code)
    if class_decl_match:
        supertypes = class_decl_match.group(1)
        interfaces = [iface.strip() for iface in supertypes.split(',') if iface.strip()]
        return len(interfaces)
    return 0

# def count_NOAM_type
def count_noam_type(class_decl):
    count = 0
    for member in class_decl.body.members:
        if isinstance(member, node.FunctionDeclaration):
            method_name = member.name
            # Getter biasa: getX atau isX
            if method_name.startswith("get") or method_name.startswith("is"):
                count += 1
            # Setter: setX
            elif method_name.startswith("set"):
                count += 1
    return count

# def count_NOCS_type
def count_nocs_type(class_decl):
    count = 1  # Hitung class itu sendiri
    for member in class_decl.body.members:
        if isinstance(member, node.ClassDeclaration):
            count += 1
    return count

# def count_number_constructor_NotDefaultConstructor_methods
def number_constructor_NotDefaultConstructor_methods(file_path: str) -> int:
    with open(file_path, "r", encoding="utf-8") as f:
        code = f.read()

    # Cari semua constructor
    pattern = r'constructor\s*\((.*?)\)'
    all_constructors = re.findall(pattern, code)

    # Hitung hanya constructor yang punya parameter (bukan default)
    non_default_constructors = [c for c in all_constructors if c.strip()]
    return len(non_default_constructors)