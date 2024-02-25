import logging
import json
import os
from pathlib import Path
from ulauncher.utils.semver import satisfies
from ulauncher.api.version import api_version

logger = logging.getLogger(__name__)


def find_extensions(ext_dir):
    """
    Yields `(extension_id, extension_path)` tuples found in a given extensions dir
    """
    if not os.path.exists(ext_dir):
        return

    dirs = [d for d in os.listdir(ext_dir) if os.path.isdir(os.path.join(ext_dir, d))]
    for dir in dirs:
        ext_path = os.path.join(ext_dir, dir)
        if os.path.isfile(os.path.join(ext_path, 'manifest.json')):
            try:
                manifest = json.loads(Path(ext_path, 'manifest.json').read_text('utf-8'))
                api_version_range = manifest.get('required_api_version', manifest.get('api_version'))
                if satisfies(api_version, api_version_range):
                    yield (dir, ext_path)
                else:
                    logger.warning(
                        'Ignoring incompatible extension %s (extension API expected %s, but the current version is %s)',
                        dir, api_version_range, api_version
                    )
            except Exception as e:
                logger.error('Ignoring extension %s (has a broken manifest.json file): %s', dir, e)
