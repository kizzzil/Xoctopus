import sys
import os
import subprocess
import click
import colorama

BASE_DIR = os.path.dirname(os.path.realpath(__file__))

def run_module(module):
    print(f"Runnning module: {module}")
    subprocess.run([sys.executable, f"{module}.py"], check=True, cwd=f"{BASE_DIR}/modules/{module}")
    print(colorama.Style.RESET_ALL, end='')

def update_modules():
    module_names = os.listdir(f"{BASE_DIR}/modules/")
    # Далее тут будет проверка на валидность модулей.
    return module_names 

@click.version_option("0.0.1", prog_name="Xoctopus")
@click.command()
@click.option('-t', default=None, help='Path to triage (target)')
@click.option('-p', default=None, help='Use specific plugin plugin_name')
def main(t, p):
    if not t:
        if os.listdir(f"{BASE_DIR}/cache/") == []:
            click.echo('Please specify -t parametr')
            sys.exit()
        else:
            with open(f"{BASE_DIR}/cache/latest.conf", "r") as latest:
                t = latest.readline()

    else:
        os.environ["TRIAGE_NAME"] = t.split('/')[-1]
        with open(f"{BASE_DIR}/cache/latest.conf", "w") as latest:
            latest.write(t)
     
    #Переменная среды для передачи subrocess пути к триажу
    os.environ["TRIAGE_PATH"] = t
    module_names = update_modules() 
    if not p: 
        for module in module_names:
            run_module(module)
    elif p in module_names:
        run_module(p)
    else:
        print(f'module with name {p} undefined')

if __name__ == "__main__":
    main()

