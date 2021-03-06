# !/usr/bin/env python3
import subprocess
import sys
import os
import zipfile
import logging

project_name = 'mos-chinadns'

logger = logging.getLogger(__name__)

# more info: https://golang.org/doc/install/source
# [(env : value),(env : value)]
envs = [
    [['GOOS', 'darwin'], ['GOARCH', 'amd64']],

    # [['GOOS', 'linux'], ['GOARCH', '386']],
    [['GOOS', 'linux'], ['GOARCH', 'amd64']],

    [['GOOS', 'linux'], ['GOARCH', 'arm'], ['GOARM', '7']],
    [['GOOS', 'linux'], ['GOARCH', 'arm64']],

    # [['GOOS', 'linux'], ['GOARCH', 'mips'], ['GOMIPS', 'hardfloat']],
    # [['GOOS', 'linux'], ['GOARCH', 'mips'], ['GOMIPS', 'softfloat']],
    # [['GOOS', 'linux'], ['GOARCH', 'mipsle'], ['GOMIPS', 'hardfloat']],
    [['GOOS', 'linux'], ['GOARCH', 'mipsle'], ['GOMIPS', 'softfloat']],

    # [['GOOS', 'linux'], ['GOARCH', 'mips64'], ['GOMIPS64', 'hardfloat']],
    # [['GOOS', 'linux'], ['GOARCH', 'mips64'], ['GOMIPS64', 'softfloat']],
    # [['GOOS', 'linux'], ['GOARCH', 'mips64le'], ['GOMIPS64', 'hardfloat']],
    # [['GOOS', 'linux'], ['GOARCH', 'mips64le'], ['GOMIPS64', 'softfloat']],

    # [['GOOS', 'freebsd'], ['GOARCH', '386']],
    # [['GOOS', 'freebsd'], ['GOARCH', 'amd64']],

    # [['GOOS', 'windows'], ['GOARCH', '386']],
    [['GOOS', 'windows'], ['GOARCH', 'amd64']],
]


def init_release_resources():
    if len(sys.argv) > 1 and '-list' in sys.argv[1:]:
        from scripts.update_chn_ip_domain import update_domain, update_ip
        update_domain()
        update_ip()


def go_build():
    logger.info(f'building {project_name}')

    global envs
    if len(sys.argv) == 2 and sys.argv[1].isdigit():
        index = int(sys.argv[1])
        envs = [envs[index]]

    VERSION = 'dev/unknown'
    try:
        VERSION = subprocess.check_output('git describe --tags --long --always', shell=True).decode().rstrip()
    except subprocess.CalledProcessError as e:
        logger.error(f'get git tag failed: {e.args}')

    for env in envs:
        os_env = os.environ.copy()  # new env

        s = project_name
        for pairs in env:
            os_env[pairs[0]] = pairs[1]  # add env
            s = s + '-' + pairs[1]
        zip_filename = s + '.zip'

        suffix = '.exe' if os_env['GOOS'] == 'windows' else ''
        bin_filename = project_name + suffix

        logger.info(f'building {zip_filename}')
        try:
            subprocess.check_call(
                f'go build -ldflags "-s -w -X main.version={VERSION}" -trimpath -o {bin_filename}', shell=True,
                env=os_env)

            if len(sys.argv) > 1 and '-upx' in sys.argv[1:]:
                try:
                    subprocess.check_call(f'upx -9 -q {bin_filename}', shell=True, stderr=subprocess.DEVNULL,
                                          stdout=subprocess.DEVNULL)
                except subprocess.CalledProcessError as e:
                    logger.error(f'upx failed: {e.args}')

            with zipfile.ZipFile(zip_filename, mode='w', compression=zipfile.ZIP_DEFLATED,
                                 compresslevel=5) as zf:
                zf.write(bin_filename)
                zf.write('README.md')
                zf.write('config.yaml')
                zf.write('chn.list')
                zf.write('chn_domain.list')
                zf.write('LICENSE')
                if os_env['GOOS'] == 'windows':
                    zf.write('scripts\windows\mos-chinadns-winsw.xml','mos-chinadns-winsw.xml')
                    zf.write('scripts\windows\service_control.bat','service_control.bat')

        except subprocess.CalledProcessError as e:
            logger.error(f'build {zip_filename} failed: {e.args}')
        except Exception:
            logger.exception('unknown err')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    init_release_resources()
    go_build()
