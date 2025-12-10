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
    if os.path.exists(f'{triage_path}/[root]/') or \
            os.path.exists(f'{triage_path}/chkrootkit/'):
        return 'lin'
    elif os.path.exists(f'{triage_path}/Target/'):
        return 'win'
    return None

@click.version_option("0.1.0", prog_name="Xoctopus")
@click.command(no_args_is_help=True)
@click.option('-t', '--triage', default=None, help='Path to triage (target)')
@click.option('-p', '--plugin', default=None, help='Use specific plugin plugin_name')
@click.option('-c', '--current',default=None, is_flag=True, help='Use current directory (Xoctopus.py/../) for analyze many triages')
@click.option('-m', '--many-triage-dir', default=None, help='Path to triage (target)')

def main(triage, plugin, current, many_triage_dir):

    if current or many_triage_dir:
        if current:
            potential_triages = [f'{BASE_DIR}/../{triage_dir}' \
                                    for triage_dir in os.listdir(f'{BASE_DIR}/../')]
        else:
            potential_triages = [f'{many_triage_dir}/{dir}' 
                                    for dir in os.listdir(many_triage_dir)]
        triages = {}

        #filter unsuitable items
        for path in potential_triages:
            os_name = lin_or_win(path) 
            if os_name is not None:
                triages[path] = os_name

        for path in tqdm(triages.keys()):
            run_analyze(triages[path], plugin, path)
    
    elif triage:
        os_name = lin_or_win(t)
        os.environ["TRIAGE_NAME"] = triage.split('/')[-1]
        with open(f"{BASE_DIR}/cache/latest.conf", "w") as latest:
            latest.write(triage) 
        run_analyze(os_name, plugin, triage)
    else:
        if os.listdir(f"{BASE_DIR}/cache/") == []:
            click.echo('Please specify -t or -c parametr')
            sys.exit()
        else:
            with open(f"{BASE_DIR}/cache/latest.conf", "r") as latest:
                triage = latest.readline()
                run_analyze(os_name, plugin, triage)

if __name__ == "__main__":
    main()
