import sys
import os
import subprocess
import click            # requirements.txt
import colorama
from tqdm import tqdm   # requirements.txt

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
MODULE_TYPES = ('parsers', 'analyzators', 'summaryzators')
DEFAULT_ZIMMERMAN_PATH = '/mnt/c/tools/'

# Модули, завершившиеся с ошибкой: (модуль, триаж, код возврата)
failed_modules = []

def list_modules(type_module, os_name):
    path = f"{BASE_DIR}/modules/{type_module}/{os_name}"
    if not os.path.isdir(path):
        return []
    return sorted(m for m in os.listdir(path) if os.path.isfile(f'{path}/{m}/{m}.py'))

def build_epilog():
    lines = ['\b', 'AVAILABLE MODULES (use with -p):']
    for type_module in MODULE_TYPES:
        for os_name in ('lin', 'win'):
            lines.extend(f'  {type_module}/{os_name}/{m}' for m in list_modules(type_module, os_name))
    return '\n'.join(lines)

def run_module(module_name, type_module, os_name, env):
    file_path = f"{BASE_DIR}/modules/{type_module}/{os_name}/{module_name}"
    if not os.path.isfile(f'{file_path}/{module_name}.py'):
        return
    print(f"Running module: {module_name}", flush=True)
    try:
        subprocess.run([sys.executable, f"{module_name}.py"], check=True, cwd=file_path, env=env)
    except subprocess.CalledProcessError as e:
        # Ошибка одного модуля не должна останавливать обработку остальных
        failed_modules.append((f'{type_module}/{os_name}/{module_name}', env.get('TRIAGE_NAME', '-'), e.returncode))
        print(colorama.Fore.RED + f'Module {module_name}: FAILED (exit code {e.returncode})')
    print(colorama.Style.RESET_ALL, end='')

'''
run_parse_and_analyze() is a function, for analyze one triage
'''
def run_parse_and_analyze(triage, plugin, do_all):
    os_name = triage['os']
    env = {**os.environ,
           'TRIAGE_PATH': triage['triage'],
           'TRIAGE_NAME': triage['name']}

    if plugin:
        type_module, plugin_os, module_name = plugin.split('/')
        # summaryzators запускаются отдельно, после обработки всех триажей
        if type_module != 'summaryzators' and plugin_os == os_name:
            run_module(module_name, type_module, os_name, env)
        return

    for module in list_modules('parsers', os_name):
        run_module(module, 'parsers', os_name, env)
    if do_all:
        for module in list_modules('analyzators', os_name):
            run_module(module, 'analyzators', os_name, env)

def run_summarize(triages, plugin):
    env = {**os.environ,
           'TRIAGE_PATHES': ";".join(f"{t['triage']},{t['os']}" for t in triages)}

    if plugin:
        _, os_name, module_name = plugin.split('/')
        run_module(module_name, 'summaryzators', os_name, env)
        return

    for os_name in ('lin', 'win'):
        for module_name in list_modules('summaryzators', os_name):
            run_module(module_name, 'summaryzators', os_name, env)

def lin_or_win(triage_path):
    if os.path.exists(f'{triage_path}/[root]/') or \
            os.path.exists(f'{triage_path}/chkrootkit/'):
        return 'lin'
    elif os.path.exists(f'{triage_path}/Target/') or \
            os.path.exists(f'{triage_path}/C/$MFT'):
        return 'win'
    return None

def validate_plugin(ctx, param, plugin):
    if plugin is None:
        return None
    plugin = plugin.strip('/')
    parts = plugin.split('/')
    if len(parts) != 3 or parts[0] not in MODULE_TYPES or \
            not os.path.isfile(f'{BASE_DIR}/modules/{plugin}/{parts[2]}.py'):
        raise click.BadParameter(f'module "{plugin}" not found, see list of available modules in --help')
    return plugin

def make_triages(paths):
    triages = []
    for path in paths:
        path = os.path.realpath(path)
        os_name = lin_or_win(path)
        if os_name is not None:
            triages.append({'triage': path, 'os': os_name, 'name': os.path.basename(path)})
    return triages

@click.version_option("0.2.0", prog_name="Xoctopus")
@click.command(no_args_is_help=True, epilog=build_epilog())
@click.option('-t', '--triage', default=None, help='Path to triage (target)')
@click.option('-p', '--plugin', default=None, callback=validate_plugin, help='Use specific plugin(module) example "parsers/lin/bodytime"')
@click.option('-c', '--current', is_flag=True, help='Use current directory for analyze many triages')
@click.option('-m', '--many-triage-dir', default=None, help='Path to dir with many triages')
@click.option('-s', '--summarize', is_flag=True, help='Use summarizing mode')
@click.option('-a', '--do-all', is_flag=True, help='Just do it all: parse, analyze and summarize')
@click.option('-z', '--zimmerman-path', envvar='ZIMMERMAN_TOOLS_PATH', default=DEFAULT_ZIMMERMAN_PATH, show_default=True,
              help='Path to Zimmerman tools (or env ZIMMERMAN_TOOLS_PATH)')

def main(triage, plugin, current, many_triage_dir, summarize, do_all, zimmerman_path):
    os.environ['ZIMMERMAN_TOOLS_PATH'] = zimmerman_path

    if current or many_triage_dir:
        base_dir = f'{BASE_DIR}/..' if current else many_triage_dir
        paths = [os.path.join(base_dir, d) for d in sorted(os.listdir(base_dir))]
    else:
        latest_path = f"{BASE_DIR}/cache/latest.conf"
        if triage:
            os.makedirs(f"{BASE_DIR}/cache", exist_ok=True)
            with open(latest_path, "w") as latest:
                latest.write(triage)
        elif os.path.exists(latest_path):
            with open(latest_path, "r") as latest:
                triage = latest.readline().strip()
            click.echo(f'Using latest triage: {triage}')
        else:
            click.echo('Please specify -t or -c parametr')
            sys.exit(1)
        paths = [triage]

    triages = make_triages(paths)
    if not triages:
        click.echo('No suitable triages found (unable to determine OS of triage)')
        sys.exit(1)

    for triage in tqdm(triages, disable=len(triages) == 1):
        print(f"### TRIAGE: {triage['name']} ({triage['os']}) ###")
        run_parse_and_analyze(triage, plugin, do_all)

    if summarize or do_all or (plugin and plugin.startswith('summaryzators/')):
        print('### RUN SUMMARYZATORS###')
        run_summarize(triages, plugin)

    if failed_modules:
        print(colorama.Fore.RED + 'Failed modules:')
        for module, triage_name, code in failed_modules:
            print(f'  {module} [{triage_name}]: exit code {code}')
        print(colorama.Style.RESET_ALL, end='')
        sys.exit(1)

if __name__ == "__main__":
    main()
