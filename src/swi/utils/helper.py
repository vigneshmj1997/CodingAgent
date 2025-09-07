import os

def get_folder_tree(root_dir, ignore_dirs=None, prefix=""):
    if ignore_dirs is None:
        ignore_dirs = {"node_modules", ".git", ".build", "__pycache__", ".venv", ".idea"}

    tree_str = ""

    try:
        entries = sorted(os.listdir(root_dir))
    except PermissionError:
        return prefix + "🚫 [Permission Denied]\n"

    for index, entry in enumerate(entries):
        path = os.path.join(root_dir, entry)
        connector = "├── " if index < len(entries) - 1 else "└── "

        if os.path.isdir(path):
            if entry in ignore_dirs:
                continue
            tree_str += prefix + connector + entry + "/\n"
            extension = "│   " if index < len(entries) - 1 else "    "
            tree_str += get_folder_tree(path, ignore_dirs, prefix + extension)
        else:
            tree_str += prefix + connector + entry + "\n"

    return tree_str


if __name__ == "__main__":
    root_path = "."  # change to the folder you want
    structure = root_path + "/\n" + get_folder_tree(root_path)
    print(structure)
