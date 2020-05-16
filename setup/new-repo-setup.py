# new-repo-setup
# after setting up a new model repo and pulling bento-mdf as a submodule:
# run in the root dir
# $ python bento-mdf/setup/new-repo-setup.py

# Create .travis.yml from template, put in top-level dir
# Create README.md.content from template
# Create docs dir (if not yet there) - populate with
# - setup/_config.yml
# - setup/assets
# - README.md.content

# variables needed:
# base: basename of the repo - like "icdc-model"
# mdfs: list of the MDFs - like ['icdc-model.yml', 'icdc-model-props.yml']
# readme: README text - for README.md.content
from jinja2 import Environment, FileSystemLoader
from shutil import copytree, copy
import os
import re
import sys

force = '';
if len(sys.argv) > 1:
  force = sys.argv[1]

# basename of repo
base = os.path.basename(os.getcwd())

has_readme = os.path.exists('README.md');
has_model_desc = os.path.isdir('./model-desc');
has_docs = os.path.isdir('./docs');

if not re.match('.*-model$',base) and not len(force):
  print("The base name is '{base}', which doesn't look like a model repo.".format(base=base))
  print("Be sure you're in the top-level directory")
  print("(Run script with argument 'force' to force continuation)")
  if (not re.match('force',force)):
    sys.exit(1)

if not has_readme and not len(force):
  print("The top-level directory should contain a simple README.md.")
  print("(Run script with argument 'force' to force continuation)")
  if (not re.match('force',force)):
    sys.exit(1)

if not has_model_desc:
  print("The top-level directory must contain a subdir 'model-desc'.")
  print("./model-desc should contain the MDF (YAML) files.")
  sys.exit(1)

# list of MDFs
mdfs = [x for x in os.listdir('model-desc') if re.match('.*.ya?ml$',x)]
# heuristic - merge into the yaml with the shortest name
mdfs.sort(key=len)

if not len(mdfs):
  print ("There are no YAML formatted files in ./model-desc.")
  print ("Make sure the MDFs are present there and re-run.")
  sys.exit(1)

# README text
readme = ''

with open("README.md") as f:
  readme = f.read()

print( "Setting up bento-mdf in"+os.getcwd() )

if not has_docs:
  print("Creating subdir ./docs")
  os.mkdir('./docs')

jenv = Environment(
  loader=FileSystemLoader('bento-mdf/setup')
  )
  
print("Populating ./docs")
try:
  copy('./bento-mdf/setup/_config.yml','./docs/_config.yml')
  copytree('./bento-mdf/setup/assets', './docs/assets')
except FileExistsError:
  print("- Not overwriting existing files.")
  print("- Remove ./docs subdir and re-run script to refresh.")

readme_content = open('./docs/README.md.content','w')
print(jenv.get_template('README.md.content.jinja').render(base=base,readme=readme),
        file=readme_content)

print("Creating .travis.yml")
travis = open('./.travis.yml','w')
print(jenv.get_template('.travis.yml.jinja').render(base=base,mdfs=mdfs),
        file=travis)

print("Complete.")
