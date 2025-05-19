import os
import sys

sys.path.insert(0, os.path.abspath('../TestingMocks'))



# -- Project information -----------------------------------------------------
project = 'My Simple API Project'
copyright = '2025, Kirill Popov, Anna Sedova'
author = 'Anna Sedova, Kirill Popov'
# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',      # Включает документацию из docstrings
    'sphinx.ext.napoleon',     # Поддержка Google и NumPy стилей docstrings
    'sphinx.ext.todo',         # Поддержка todo-заметок
    'sphinx_rtd_theme',        # Тема Read the Docs
    'autoapi.extension',       # Расширение AutoAPI
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# -- Options for sphinx-autoapi ----------------------------------------------
autoapi_type = 'python'
# Укажите путь к папке(ам) с вашим исходным кодом относительно папки docs/
# Если ваши .py файлы в корне проекта (рядом с папкой docs/):
autoapi_dirs = ['../TestingMocks', '../Alice_and_Fedor']
# Если ваш код в папке src/ (которая на одном уровне с docs/):
# autoapi_dirs = ['../src']
# Если у вас несколько папок, например, сервер в одной, клиент в другой:
# autoapi_dirs = ['../server_code_folder', '../client_code_folder']
autoapi_ignore = ['*/migrations/*', '*/tests/*'] # Игнорировать ненужные папки
autoapi_options = [
    'members',
    'undoc-members',
    # 'private-members', # Раскомментируйте, если нужны приватные члены
    'show-inheritance',
    'show-module-summary',
    'special-members',
]
autoapi_keep_files = False # Не сохранять сгенерированные rst файлы autoapi
autoapi_add_toctree_entry = True # Добавлять сгенерированную документацию в toctree

# -- Options for todo extension ----------------------------------------------
todo_include_todos = True