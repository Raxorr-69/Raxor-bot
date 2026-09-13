import importlib
import pkgutil

import commands as command_package


async def load_commands(bot):
    """Automatically load all command extensions."""

    for module_info in pkgutil.walk_packages(
        command_package.__path__,
        prefix=f"{command_package.__name__}.",
    ):
        module_name = module_info.name

        module = importlib.import_module(module_name)

        if hasattr(module, "setup"):
            await bot.load_extension(module_name)
