import datetime
from pathlib import Path, PosixPath
from typing import Optional

import yaml
from pydantic import ValidationInfo, field_validator, validator
from pydantic.dataclasses import dataclass


def posix_path_encoder(dumper, data):
    return dumper.represent_scalar("tag:yaml.org,2002:str", str(data))


def none_encoder(dumper, _):
    return dumper.represent_scalar("tag:yaml.org,2002:null", "")


yaml.add_representer(PosixPath, posix_path_encoder)
yaml.add_representer(type(None), none_encoder)


@dataclass
class enumParams:
    """Creates a model to track all the paths for enumerating SLC pairs

    Expects:

    AOI/{aoi_name}.geojson

    And then saves items to stacks, pairs and yml to:

    {data_dir}/{aoi_name}__<enum_param_tokens>/
    """

    temporal_baseline_days: list[int]
    n_secondaries_per_reference: int | list[int]
    aoi_name: str
    n_seeds: int = 1
    track_numbers: Optional[list[int]] = None
    data_directory: Optional[Path | str] = Path("out")
    date_of_enum: datetime.date = datetime.date.today()
    stack_dir: Optional[Path | str] = None
    enum_dir: Optional[Path | str] = None
    yaml_path: Optional[Path | str] = None
    weather_model: Optional[str] = None
    month_constraint: Optional[list[int]] = None
    exclusive_month_constraints: Optional[bool] = False
    aoi_geojson_path: Optional[str | Path] = None
    valid_date_ranges: Optional[list[tuple]] = None

    def __post_init__(self):
        tbs_str = list(map(str, self.temporal_baseline_days))
        neigh = self.n_secondaries_per_reference
        neighbors_token = neigh if isinstance(neigh, int) else "-".join(list(map(str, neigh)))
        tmp_dir_name = f'{self.aoi_name}__tb_{"-".join(tbs_str)}__neigh_{neighbors_token}'

        self.enum_parent_dir = Path(f"out/{tmp_dir_name}")
        self.stack_dir = Path(f"out/{tmp_dir_name}/stack/")
        self.enum_dir = Path(f"out/{tmp_dir_name}/enum/")
        [
            data_dir.mkdir(exist_ok=True, parents=True)
            for data_dir in [self.enum_parent_dir, self.stack_dir, self.enum_dir]
        ]

        self.yaml_path = self.enum_parent_dir / f"enum_params_{self.date_of_enum}.yml"

        yamls_dir = Path('enum_configs')
        yamls_dir.mkdir(exist_ok=True)
        self.yaml_path_record = yamls_dir / f"{self.aoi_name}_{self.date_of_enum.year}-{self.date_of_enum.month:02d}.yml"

    @validator("valid_date_ranges")
    def str_to_dates(cls, v):
        if v is None:
            return v
        if isinstance(v, list):
            def to_dt(dt_str: str) -> datetime.datetime:
                return datetime.datetime.strptime(dt_str, '%Y-%m-%d')
            # Ensures both validation and correct casting
            utc_tz = datetime.timezone.utc
            v = [(to_dt(item[0]).replace(tzinfo=utc_tz),
                  to_dt(item[1]).replace(tzinfo=utc_tz)) for item in v]
        return v

    @validator("stack_dir", "enum_dir", "yaml_path", "data_dir", "data_dir", pre=True)
    def create_date_ranges(cls, v):
        if isinstance(v, str):
            return Path(v)
        return v

    @validator("n_secondaries_per_reference")
    def check_list_length(cls, v, values):
        if isinstance(v, list):
            tbs = values.get("temporal_baseline_days")
            if len(tbs) != len(v):
                raise ValueError("n_secondaries_per_reference must have the same length as temporal_baselines")
        return v

    @validator("aoi_geojson_path", pre=True, always=True)
    @classmethod
    def aoi_geojson_exists(cls, v: str, values):
        v = Path('AOIs') / f'{values['aoi_name']}.geojson'
        path_exists = v.exists()
        if not path_exists:
            raise ValueError(f'The aoi_name "{v.stem}" needs to have geojson path {v}')
        return v

    @field_validator("month_constraint")
    @classmethod
    def check_valid_month(cls, v: list, info: ValidationInfo) -> list:
        if isinstance(v, list):
            is_valid = all([m in list(range(1, 13)) for m in v])
            assert is_valid, f"{info.field_name} must have months as 1, 2, ..., 12"
        return v

    @classmethod
    def from_yaml(cls, yaml_file: str | Path) -> "enumParams":
        with open(yaml_file) as f:
            params_dict = yaml.safe_load(f)["enumeration_parameters"]

        obj = cls(**params_dict)
        return obj

    def to_yaml(self) -> Path:
        data = {"enumeration_parameters": self.__dict__}
        with open(self.yaml_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False)

        with open(self.yaml_path_record, "w") as f:
            yaml.dump(data, f, default_flow_style=False)

        return self.yaml_path_record
