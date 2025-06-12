from setuptools import setup

setup(
    name='auto-prdgen',
    version='0.1.0',
    py_modules=['prd_creator', 'prompts', 'config', 'ui_utils'],
    install_requires=[
        'google-generativeai',
        'python-dotenv',
        'colorama>=0.4.4',
    ],
    entry_points={
        'console_scripts': [
            'auto-prdgen = prd_creator:main',
        ],
    },
    author='Hesham Salama',
    author_email='hesham.salama@rub.de',
    description='A CLI tool to automatically generate Product Requirements Documents (PRDs) using a Large Language Model (LLM).',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/HeshamFS/auto-prdgen',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)