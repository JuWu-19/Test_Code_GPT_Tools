import inspect
import os
import importlib.util
#from textwrap import cleanoc

def get_module_info(file_path):
    spec = importlib.util.spec_from_file_location("module.name", file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def get_function_details(func):
    sig = inspect.signature(func)
    params = sig.parameters
    inputs = [f"{name}: {param.annotation}" for name, param in params.items()]
    outputs = sig.return_annotation
    return inputs, outputs

def get_class_details(cls):
    methods = inspect.getmembers(cls, predicate=inspect.isfunction)
    properties = [name for name, value in vars(cls).items() if isinstance(value, property)]
    return methods, properties

def analyze_file(file_path):
    print(f"\n{os.path.basename(file_path)}:\n")
    module = get_module_info(file_path)
    for name, obj in inspect.getmembers(module):
        if inspect.isclass(obj):
            print(f"- Class: {name}")
            methods, properties = get_class_details(obj)
            print(f"    - Properties: {properties}")
            for method_name, method in methods:
                inputs, outputs = get_function_details(method)
                print(f"    - Method: {method_name}")
                print(f"        - Inputs: {inputs}")
                print(f"        - Outputs: {outputs}")
        elif inspect.isfunction(obj):
            inputs, outputs = get_function_details(obj)
            print(f"- Function: {name}")
            print(f"    - Inputs: {inputs}")
            print(f"    - Outputs: {outputs}")

files = [
    "core_scheduling.py",
    "data_loading.py",
    "data_results_integrity.py",
    "defect_generation.py",
    "events_managment.py",
    "GUI_main.py",
    "heuristic_rules.py",
    "kpi_calculation.py",
    "main_classes.py",
    "scheduling_main.py",
]

for file in files:
    analyze_file(file)
