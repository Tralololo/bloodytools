from bloodytools.utils.simulation_objects import Simulation_Data, Simulation_Group
from .simulator import Simulator
import os
import pkg_resources
import yaml


class MissingTalentTreePathFileError(Exception):
    pass


class TierSetSimulator(Simulator):
    @classmethod
    def name(cls) -> str:
        return "Tier Set"

    def pre_processing(self, data_dict: dict) -> dict:
        data_dict = super().pre_processing(data_dict)

        # load predefined talent paths from file
        file_path = os.path.join(
            "talent_tree_paths",
            f"{self.wow_spec.wow_class.simc_name}_{self.wow_spec.simc_name}.yaml",
        )
        try:
            with pkg_resources.resource_stream(__name__, file_path) as f:
                data_dict["data_profile_overrides"] = yaml.safe_load(f)
        except FileNotFoundError as e:
            raise MissingTalentTreePathFileError() from e

        if data_dict["data_profile_overrides"] is None:
            data_dict["data_profile_overrides"] = {}

        if "profile" in data_dict and "character" in data_dict["profile"]:
            if "talents" in data_dict["profile"]["character"]:
                data_dict["data_profile_overrides"]["custom_profile"] = [  # type: ignore
                    data_dict["profile"]["character"]["talents"]
                ]
            elif (
                "class_talents" in data_dict["profile"]["character"]
                and "spec_talents" in data_dict["profile"]["character"]
            ):
                data_dict["data_profile_overrides"]["custom_profile"] = [  # type: ignore
                    "class_talents="
                    + data_dict["profile"]["character"]["class_talents"],
                    "spec_talents=" + data_dict["profile"]["character"]["spec_talents"],
                ]

        return data_dict

    def add_simulation_data(
        self, simulation_group: Simulation_Group, data_dict: dict
    ) -> None:
        tier_mapping = {
            "no tier": [
                "set_bonus=tier29_2pc=0",
                "set_bonus=tier29_4pc=0",
            ],
            "2p": [
                "set_bonus=tier29_2pc=1",
                "set_bonus=tier29_4pc=0",
            ],
            "4p": [
                "set_bonus=tier29_2pc=1",
                "set_bonus=tier29_4pc=1",
            ],
        }

        for tier, simc_input in tier_mapping.items():
            for i, k_v in enumerate(data_dict["data_profile_overrides"].items()):
                human_name, simc_args = k_v

                if len(simulation_group.profiles) == 0:
                    profile = data_dict["profile"]
                else:
                    profile = {}

                clear_talents = [
                    "talents=",
                    "spec_talents=",
                    "class_talents=",
                ]

                merged_simc_args = simc_input + clear_talents + simc_args

                data = Simulation_Data(
                    name=self.profile_split_character().join([human_name, tier]),
                    simc_arguments=merged_simc_args,
                    fight_style=self.fight_style,
                    profile=profile,
                    target_error=self.settings.target_error.get(
                        self.fight_style, "0.1"
                    ),
                    ptr=self.settings.ptr,
                    default_actions=self.settings.default_actions,
                    executable=self.settings.executable,
                    iterations=self.settings.iterations,
                )

                if len(simulation_group.profiles) == 0:
                    custom_apl = None
                    if self.settings.custom_apl:
                        with open("custom_apl.txt") as f:
                            custom_apl = f.read()
                    if custom_apl:
                        data.simc_arguments.append("# custom_apl")
                        data.simc_arguments.append(custom_apl)

                    custom_fight_style = None
                    if self.settings.custom_fight_style:
                        with open("custom_fight_style.txt") as f:
                            custom_fight_style = f.read()
                    if custom_fight_style:
                        data.simc_arguments.append("# custom_fight_style")
                        data.simc_arguments.append(custom_fight_style)

                simulation_group.add(data)

    def post_processing(self, data_dict: dict) -> dict:
        data_dict = super().post_processing(data_dict)

        self.create_sorted_key_key_value_data(data_dict)

        return data_dict
