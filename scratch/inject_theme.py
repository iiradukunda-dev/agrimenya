import glob
import os

for file in glob.glob('pages/*.py'):
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'from utils.theme import load_theme' not in content:
        content = content.replace('import streamlit as st', 'import streamlit as st\nfrom utils.theme import load_theme', 1)
        content = content.replace('layout="wide")', 'layout="wide")\nload_theme()', 1)
        content = content.replace("layout='wide')", "layout='wide')\nload_theme()", 1)
        
        with open(file, 'w', encoding='utf-8') as f:
            f.write(content)
