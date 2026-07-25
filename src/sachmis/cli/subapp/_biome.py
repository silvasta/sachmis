from sstcore import SafeTyper
from typer import Context

from ...cli import args
from .executor import BiomeOperator


def main() -> None:
    app()


app = SafeTyper(
    name="biome",
    help="Biome - Home of Every Forest",
)


@app.command()
def setup(ctx: Context, name: args.Name = ""):
    """Create new Biome with global data structure"""
    BiomeOperator(sst=ctx.obj["system"]).create(name)


@app.command()
def select(ctx: Context):
    """Show all Biome Files and select active Biome"""
    BiomeOperator(sst=ctx.obj["system"]).select()


@app.command()
def show(ctx: Context):
    """Show all Biomes and active Biome"""
    BiomeOperator(sst=ctx.obj["system"]).select()


@app.command("stat")
def arboreal_statistic(ctx: Context):
    """Show statistics of active Biome"""
    BiomeOperator(sst=ctx.obj["system"]).stat()


if __name__ == "__main__":
    main()
