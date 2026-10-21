"""Profile and installed-tool capability checks without loading game files."""
import importlib.util
from pathlib import Path
import platform
import shutil
import sys

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'dm/games'))
import game


def profiles(system=None):
    system = system or platform.system()
    result = []
    for g in game.all_games():
        graphics = g.get('graphics', 'detect')
        reason = ''
        if system == 'Windows':
            if graphics == 'vulkan':
                reason = 'Windows does not support Vulkan builds.'
            elif any(g.get(k, 'off') == 'on' for k in ('shader_glslc_capture', 'shader_vk_capture')):
                reason = 'This game needs runtime shader capture on a Mac.'
            elif g.words('shader_versions') != [g.get('package')]:
                reason = 'Windows requires one shader version matching the package.'
        elif system != 'Darwin':
            reason = 'Application builds require Windows or Apple Silicon macOS.'
        if not reason and graphics == 'detect': reason = 'Renderer and runtime-capture requirements are checked after extraction.'
        supported = not reason or graphics == 'detect' and reason.startswith('Renderer')
        result.append(dict(id=g.id, name=g.get('name'), version=g.get('package'), builds=g.builds(),
                           graphics=graphics, ios=supported, mac=system == 'Darwin', reason=reason))
    return result


def environment(config):
    system = platform.system()
    root = Path(config['tools'])
    exe = '.exe' if system == 'Windows' else ''
    expected = {'extractor': root / 'nx_extract' / ('nx_extract' + exe),
                'dotnet': root / 'dotnet' / ('dotnet' + exe)}
    if system == 'Windows':
        expected.update(clang=root / 'ios-cross/toolchain/windows/iphone/bin/clang.exe',
                        lld=root / 'ios-cross/toolchain/windows/iphone/bin/lld.exe',
                        sdk=Path(config.get('sdk') or root / 'ios-cross/iPhoneOS26.5.sdk'),
                        metal=Path(config.get('metal') or root / 'metal/metal.exe'),
                        spirv_cross=root / 'spirv-cross-build/spirv-cross.exe')
    checks = [dict(name=k, path=str(v), available=v.exists()) for k, v in expected.items()]
    if system == 'Darwin':
        for name in ('xcodebuild', 'xcrun', 'xcodegen', 'make', 'zstd', 'spirv-cross', 'codesign', 'ditto'):
            found = shutil.which(name)
            checks.append(dict(name=name, path=found or '', available=bool(found)))
    for name in ('lz4', 'capstone', 'fontTools', 'PIL'):
        checks.append(dict(name=name, path='Python package', available=importlib.util.find_spec(name) is not None))
    return dict(system=system, machine=platform.machine(), checks=checks, profiles=profiles(system))
