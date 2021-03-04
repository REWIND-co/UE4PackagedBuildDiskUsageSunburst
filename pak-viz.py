#! /usr/bin/env python

"""
SYNOPSIS

    ./pak-viz.py --help

    ./pak-viz.py ExampleBuild my-dest-dir

    ./pak-viz.py ExampleBuild my-dest-dir --unreal_pak U:/bin/UnrealPak.exe

DESCRIPTION

Accepts an input and output directory.

Within the input directory, searches for an `.obb` or `.apk` file. In the case of the latter, searches
for an .obb as `assets/.obb.png` and process if found.

An `.pak` file is sought in the `.obb` 's `/ProjectName/Content/Paks/`, and if found, is processed through
`UnrealPak.exe`, and then a JSON tree is created of the directory structure, and added to a
d3 sunburst visualisation, which is then saved to the specified destination directory as `pak-viz.html`

"""

import argparse
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

EXTRACTED_OBB_DIR = tempfile.mkdtemp()
EXTRACTED_PAK_DIR = tempfile.mkdtemp()
EXTRACTED_APK_DIR = tempfile.mkdtemp()

HTML_FILENAME = 'pak-viz.html'
HTML_DATA_PLACEHOLDER = 'const root = {};'
HTML_BUILD_DIRECTORY_PLACEHOLDER = '<STRONG>Build Directory: </STRONG><br/>'
HTML_TOTAL_BUILD_SIZE_PLACEHOLDER = ''

parser = argparse.ArgumentParser(
    description="Visualise the filesystem of a UE4 pak file")

parser.add_argument("input", type=str, help="Directory of the build to scan")

parser.add_argument("output", type=str,
                    help="Destination directory for the generated file")

parser.add_argument("--unreal_pak", type=str, default="UnrealPak.exe",
                    help="Path to UnrealPak.exe - defaults to just the filename")

args = parser.parse_args()

input_location = os.path.abspath(args.input)
output_dir = os.path.abspath(args.output)
html_dest_path = output_dir + os.sep + HTML_FILENAME


def main():
    if (not(os.path.isdir(input_location))):
        print('Supplied input directory not found: ' + input_location)
        sys.exit(1)

    if (not(os.path.isdir(output_dir))):
        os.mkdir(output_dir)

    obb_file_path = get_obb_file_path(input_location)

    if obb_file_path: # Android build
        with zipfile.ZipFile(obb_file_path, 'r') as zipObj:
            zipObj.extractall(EXTRACTED_OBB_DIR)
        pak_path = find_pak_path(EXTRACTED_OBB_DIR)
    else: # Windows build
        pak_path = find_pak_path(input_location)
        
    if not(pak_path):
        print("Unable to find an apk, obb or windows pak file\n")
        sys.exit(-9)
    
    subprocess.run([args.unreal_pak, pak_path, '-extract', EXTRACTED_PAK_DIR])

    theTree = tree(EXTRACTED_PAK_DIR)

    create_file(theTree)
    
    shutil.copyfile('rewind_banner.png', output_dir + os.sep + 'rewind_banner.png')

    print('\nFinished after writing ' + html_dest_path)


def tree(dir):
    match = re.search('([^/\\\\]+)[/\\\\]*$', dir)
    label = match.group(0)

    if dir == EXTRACTED_PAK_DIR:
        label = 'Package'

    branch = {
        "name": label,
        "children": []
    }

    for file in os.listdir(dir):
        path = dir + os.sep + file
        if os.path.isdir(path):
            branch["children"].append(tree(path))
        else:
            branch["children"].append(
                {"name": file, "size": os.path.getsize(path)})

    return branch


def create_file(theTree):
    with open(HTML_FILENAME) as html_file:
        html = html_file.read()

    html = html.replace(HTML_DATA_PLACEHOLDER, "const root = " +
                        json.dumps(theTree) + ";")
                        
    html = html.replace(HTML_BUILD_DIRECTORY_PLACEHOLDER, 
        '<STRONG>Build Directory: </STRONG>' + input_location +  '<br/>')

    if os.path.isfile(html_dest_path):
        os.remove(html_dest_path)

    with open(html_dest_path, 'w') as combined_file:
        combined_file.write(html)


def get_obb_path_from_apk(apk_path):
    with zipfile.ZipFile(apk_path, 'r') as zipObj:
        zipObj.extractall(EXTRACTED_APK_DIR)
    obb_path = EXTRACTED_APK_DIR + os.sep + 'assets' + os.sep + 'main.obb.png'
    if not(os.path.isfile(obb_path)):
        sys.stderr.write(
            'Did not find assets/.obb.png in ' + apk_path + '\n')
        obb_path = ''
    return obb_path


def get_obb_file_path(input_path):
    obb_file_path = ''
    
    print('searching ' + input_path)

    if os.path.isfile(input_path):
        obb_file_path = find_input_file(input_path)
    else:
        for element in os.listdir(input_path):
            print('- ' + element)
            full_element_path = input_path + os.sep + element
            if os.path.isfile(full_element_path):
                obb_file_path = find_input_file(full_element_path)
            else:
                obb_file_path = get_obb_file_path(full_element_path)
                
            if obb_file_path:
                break

    return obb_file_path

def find_input_file(path):
    obb_file_path = ''
    if os.path.isfile(path):
        if re.search('\\.apk$', path):
            obb_file_path = get_obb_path_from_apk(path)
            if obb_file_path:
                print('Extracting .obb.png from apk', path)
        elif re.search('\\.obb$', path):
            obb_file_path = path
            print('Found an obb outside of an apk', path)

    return obb_file_path

def find_pak_path(obb_dir):
    pak_path = ''
    for root, dirs, files in os.walk(obb_dir):
        for file in files:
            if file.endswith(".pak"):
                pak_path = os.path.join(root, file)

    if pak_path:
        print('Using pak file', pak_path)
        
    return pak_path

main()
