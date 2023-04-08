import ast
import copy
import astunparse
import random
import string
import sys
import os
import glob
from importlib.util import find_spec
import keyword

def get_skip_modules(path):
    # Check if the input path is a file or a directory
    is_file = os.path.isfile(path)

    if is_file:
        directory = os.path.dirname(path)
        filenames = [os.path.basename(path)]
    else:
        directory = path
        filenames = os.listdir(directory)

    # Get the absolute path of the directory
    abs_directory = os.path.abspath(directory)

    # Add the directory to the start of sys.path so that Python will search it first
    sys.path.insert(0, abs_directory)

    # Initialize a list to store the imported module names
    imported_modules = []

    # Include all the built-in modules explicitly
    # Get the list of built-in module names
    module_names = sys.builtin_module_names
    # Print each module name
    for name in module_names:
        if not name.startswith('_'):
            imported_modules.append(name)
    builtin_modules = copy.copy(imported_modules)

    # Iterate over all Python files in the directory or the single file
    local_filenames = []
    for filename in filenames:
        if filename.endswith('.py'):
            local_filenames.append(filename[:-3])
            # Parse the AST of the Python file
            with open(os.path.join(abs_directory, filename), 'r') as f:
                tree = ast.parse(f.read())

            # Extract the imported module names from the AST
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported_modules += [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    imported_modules += [node.module + '.' + alias.name for alias in node.names]

    # Remove duplicates and sort the list of imported modules
    imported_modules = sorted(set(imported_modules))

    # Remove the directory from sys.path so that it is not searched anymore
    sys.path.remove(abs_directory)

    # Filter the list of imported modules to exclude modules in the directory and duplicates
    # print(f"local file names: {local_filenames}")
    nonlocal_modules = []
    for module in set(imported_modules):
        modulename = module.split('.')[0]
        if modulename not in local_filenames:
            nonlocal_modules.append(modulename)
    return nonlocal_modules


class Obfuscator(ast.NodeTransformer):
    def __init__(self, modules_to_skip=None):
        self.names_map = {}
        self.modules_to_skip = modules_to_skip or []
        self.builtin_names = set(dir(__builtins__))
        self.args_with_defaults = set()  # Add this line

    def _random_name(self):
        while True:
            name = ''.join(random.choices(string.ascii_letters, k=8))
            if name not in self.names_map.values() and name not in keyword.kwlist:
                return name

    def visit_FunctionDef(self, node):
        new_args = []
        default_values_start_index = len(node.args.args) - len(node.args.defaults)

        for i, arg in enumerate(node.args.args):
            # Check if the argument has a default value
            has_default_value = i >= default_values_start_index

            if has_default_value:
                self.args_with_defaults.add(arg.arg)

            # Obfuscate argument names only if they don't have default values
            if not has_default_value and arg.arg not in self.names_map:
                self.names_map[arg.arg] = self._random_name()

            # Only use the names_map for arguments without default values
            new_arg_id = self.names_map.get(arg.arg) if not has_default_value else arg.arg
            new_arg = ast.arg(arg=new_arg_id, annotation=arg.annotation)
            new_args.append(new_arg)

        node.args.args = new_args
        return self.generic_visit(node)

    def visit_Name(self, node):
        if isinstance(node.ctx, (ast.Store, ast.Load, ast.Del)):
            if node.id in self.names_map:
                node.id = self.names_map[node.id]
            elif isinstance(node.ctx, (ast.Store)) and not node.id.startswith('__') and \
            not keyword.iskeyword(node.id) and node.id not in self.builtin_names and \
            node.id not in self.modules_to_skip and node.id not in self.args_with_defaults:
                self.names_map[node.id] = self._random_name()
                node.id = self.names_map[node.id]
        return node

    def visit_ClassDef(self, node):
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                item.is_class_method = True
        return self.generic_visit(node)
    
    def visit_Import(self, node):
        return node

    def visit_ImportFrom(self, node):
        new_names = []
        for alias in node.names:
            if alias.name in self.names_map:
                new_names.append(ast.alias(name=self.names_map[alias.name], asname=None))
            else:
                new_names.append(alias)
        node.names = new_names
        return node

    def obfuscate(self, source_code):
        # Generate AST for the file and build the global names map
        tree = ast.parse(source_code)
        self.visit(tree)

        # Generate obfuscated code from the updated tree
        obfuscated_code = astunparse.unparse(tree)
        return obfuscated_code


def obfuscate_file_or_directory(path, modules_to_skip=None):
    is_file = os.path.isfile(path)

    if is_file:
        python_files = [path]
        directory = os.path.dirname(path)
    else:
        directory = path
        python_files = glob.glob(os.path.join(directory, "*.py"))

    # Create the obfuscated_src directory if it doesn't exist
    obfuscated_src_dir = os.path.join(directory, "obfuscated_src")
    os.makedirs(obfuscated_src_dir, exist_ok=True)

    obfuscator = Obfuscator(modules_to_skip)

    for python_file in python_files:
        with open(python_file, "r") as file:
            source_code = file.read()

        # Obfuscate the code using the obfuscator
        obfuscated_code = obfuscator.obfuscate(source_code)

        # Save the obfuscated code in the obfuscated_src directory
        obfuscated_file = os.path.join(obfuscated_src_dir, os.path.basename(python_file))
        with open(obfuscated_file, "w") as file:
            file.write(obfuscated_code)

        print(f"Obfuscated {python_file} -> {obfuscated_file}")

    return obfuscator.names_map


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python cipherpy.py <path>")
        sys.exit(1)

    path = sys.argv[1]
    modules_to_skip = get_skip_modules(path)
    modules_to_skip = list(set(modules_to_skip))
    print(f"modules to skip: {modules_to_skip}")
    names_map = obfuscate_file_or_directory(path, modules_to_skip=modules_to_skip)
    # print(f"names_map: {names_map}")