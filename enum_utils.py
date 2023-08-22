from pathlib import Path


def get_stack_dir(aoi_name: str) -> Path:
    """Ensures that this directory's convention is shared across notebooks
    """
    return Path(f'out/{aoi_name}/stack/')


def get_enum_dir(aoi_name: str, neighbors: int) -> Path:
    """Ensures that this directory's convention is shared across notebooks
    """
    return Path(f'out/{aoi_name}/enum/neighbors_{neighbors}')
