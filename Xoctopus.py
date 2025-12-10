import sys
import os
import subprocess
import click            # requirements.txt
import colorama
from tqdm import tqdm   # requirements.txt

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
os.environ["ZIMMERMAN_TOOLS_PATH"] = '/mnt/c/tools/' 

def run_module(module, os_name):
    print(f"Runnning module: {module}")
    subprocess.run([sys.executable, f"{module}.py"], check=True, cwd=f"{BASE_DIR}/modules/{os_name}/{module}")
    print(colorama.Style.RESET_ALL, end='')

def update_modules(os_name):
    module_names = os.listdir(f"{BASE_DIR}/modules/{os_name}/")
    # Далее тут будет проверка на валидность модулей.
    return module_names 

'''
run_analyze() is a function, for analyze one triage
''' 
def run_analyze(os_name, p, t):
    #Переменная среды для передачи subrocess пути к триажу
    os.environ["TRIAGE_PATH"] = t
    module_names = update_modules(os_name) 
    if not p: 
        for module in module_names:
            run_module(module, os_name)
    elif p in module_names:
        run_module(p, os_name)
    else:
        print(f'module with name {p} undefined')

def lin_or_win(triage_path):
    if os.path.exists(f'{triage_path}/[root]/'):
        return 'lin'
    elif os.path.exists(f'{triage_path}/Target/'):
        return 'win'
    return None

@click.version_option("0.1.0", prog_name="Xoctopus")
@click.command(no_args_is_help=True)
@click.option('-t', default=None, help='Path to triage (target)')
@click.option('-p', default=None, help='Use specific plugin plugin_name')
@click.option('-c', default=None, is_flag=True, help='Use current directory (Xoctopus.py/../) for analyze many triages')
def main(t, p, c):
    
    if c:
        potential_triages = [f'{BASE_DIR}/../{triage_dir}' \
                                for triage_dir in os.listdir(f'{BASE_DIR}/../')]
        triages = {}

        #filter unsuitable items
        for path in potential_triages:
            os_name = lin_or_win(path) 
            if os_name is not None:
                triages[path] = os_name

        for path in tqdm(triages.keys()):
            run_analyze(triages[path], p, path)
    
    elif t:
        os_name = lin_or_win(t)
        os.environ["TRIAGE_NAME"] = t.split('/')[-1]
        with open(f"{BASE_DIR}/cache/latest.conf", "w") as latest:
            latest.write(t) 
        run_analyze(os_name, p, t)
    else:
        if os.listdir(f"{BASE_DIR}/cache/") == []:
            click.echo('Please specify -t or -c parametr')
            sys.exit()
        else:
            with open(f"{BASE_DIR}/cache/latest.conf", "r") as latest:
                t = latest.readline()
                run_analyze(os_name, p, t)

if __name__ == "__main__":
    main()
