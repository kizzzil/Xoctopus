import sys
import os
import subprocess
import click

BASE_DIR = os.path.dirname(os.path.realpath(__file__))

def run_module(module):
    print(f"Runnning module: {module}")
    subprocess.run([sys.executable, f"{module}.py"], check=True, cwd=f"{BASE_DIR}/modules/{module}")

def update_modules():
    module_names = os.listdir(f"{BASE_DIR}/modules/")
    # Далее тут будет проверка на валидность модулей.
    return module_names 

@click.version_option("0.0.1", prog_name="Xoctopus")
@click.command()
@click.option('-t', help='Path to triage (target)')
def main(t):
    if not t:
        click.echo('Please specify -t parametr')
        sys.exit()
    #Переменная среды для передачи subrocess пути к триажу
    os.environ["TRIAGE"] = t
    module_names = update_modules() 
    for module in module_names:
        run_module(module)

if __name__ == "__main__":
    main()

