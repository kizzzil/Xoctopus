import sys
import os
import subprocess
import click            # requirements.txt
import colorama
from tqdm import tqdm   # requirements.txt

help_epilog = '''
##DEFAULT MODULES##\b\n
NAME\t\tDESCRIPTION\n
bodytime\tparse and convert bodytime timestamp to human readable view\n
'''

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
os.environ["ZIMMERMAN_TOOLS_PATH"] = '/mnt/c/tools/' 

def run_module(module_name, type_module, os_name):
    file_path = f"{BASE_DIR}/modules/{type_module}/{os_name}/{module_name}"
    if os.path.exists(file_path):
        print(f"Runnning module: {module_name}")
        subprocess.run([sys.executable, f"{module_name}.py"], check=True, cwd=file_path)
        print(colorama.Style.RESET_ALL, end='')

def update_modules(os_name):
    parsers = os.listdir(f"{BASE_DIR}/modules/parsers/{os_name}/")
    analyzators = os.listdir(f"{BASE_DIR}/modules/analyzators/{os_name}/")
    summaryzators = os.listdir(f"{BASE_DIR}/modules/summaryzators/{os_name}/")
    return (parsers, analyzators, summaryzators) 

'''
run_analyze() is a function, for analyze one triage
''' 
def run_parse_and_analyze(os_name, p, t, do_all, modules):
    #Переменная среды для передачи subrocess пути к триажу
    os.environ["TRIAGE_PATH"] = t
    parsers, analyzators, summarizators = modules[os_name]
    
    if not p: 
        for module in parsers:
            run_module(module, 'parsers', os_name)
        if do_all is not None:
            for module in analyzators:
                run_module(module, 'analyzators', os_name)
    elif os.path.exists(f'{BASE_DIR}/modules/{p}'):
        type_module, os_name, module_name = p.split('/')
        run_module(module_name, type_module, os_name)
    else:
        print(f'module with name {p} undefined')

def run_summarize(modules, p):
    ### summarize for lin
    _, _, summaryzators_lin = modules['lin']

    if p:
        type_module, _ ,module_name = p.split('/')
        run_module(module_name, 'summaryzators', 'lin')
    else:
        for module_name in summaryzators_lin:
            run_module(module_name, 'summaryzators', 'lin')

    ### summmarize for win

    _, _, summaryzators_win = modules['win']

    if p:
        type_module, _, module_name = p.split('/')
        run_module(module_name, 'summaryzators', 'win')
    else:
        for module_name in summaryzators_lin:
            run_module(module_name, 'summaryzators', 'win')

def lin_or_win(triage_path):
    if os.path.exists(f'{triage_path}/[root]/') or \
            os.path.exists(f'{triage_path}/chkrootkit/'):
        return 'lin'
    elif os.path.exists(f'{triage_path}/Target/'):
        return 'win'
    return None

@click.version_option("0.1.0", prog_name="Xoctopus")
@click.command(no_args_is_help=True, epilog=help_epilog)
@click.option('-t', '--triage', default=None, help='Path to triage (target)')
@click.option('-p', '--plugin', default=None, help='Use specific plugin(module) example "parsers/bodytime"')
@click.option('-c', '--current',default=None, is_flag=True, help='Use current directory for analyze many triages')
@click.option('-m', '--many-triage-dir', default=None, help='Path to dir with many triages')
@click.option('-s', '--summarize', default=None, is_flag=True, help='Use current directory for analyze many triages')
@click.option('-a', '--do-all', default=None, is_flag=True, help='Just do it all' )
@click.option('--parse', '--only-parse', default=None, is_flag=True, help='Just only parse' )

def main(triage, plugin, current, many_triage_dir, summarize, do_all, parse):
    
    modules = {'lin' : update_modules('lin'), 'win' : update_modules('win')}
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
            run_parse_and_analyze(triages[path], plugin, path, do_all, modules)
        
        if summarize or do_all:
            os.environ['TRIAGE_PATHES'] = ";".join([ f'{x},{triages[x]}' for x in triages.keys()])  
            print('### RUN SUMMARYZATORS###')
            run_summarize(modules, plugin)

    elif triage:
        os_name = lin_or_win(triage)
        os.environ["TRIAGE_NAME"] = triage.split('/')[-1]
        with open(f"{BASE_DIR}/cache/latest.conf", "w") as latest:
            latest.write(triage) 
        run_parse_and_analyze(os_name, plugin, triage, do_all, modules)
    else:
        if os.listdir(f"{BASE_DIR}/cache/") == []:
            click.echo('Please specify -t or -c parametr')
            sys.exit()
        else:
            with open(f"{BASE_DIR}/cache/latest.conf", "r") as latest:
                triage = latest.readline()
                run_parse_and_analyze(os_name, p, t, do_all, modules)

if __name__ == "__main__":
    main()
