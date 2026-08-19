from pathlib import Path

from boostlet_reconstruction.config import load_config


ROOT = Path(__file__).resolve().parents[1]


def test_paper_configuration_has_the_primary_grid() -> None:
    config = load_config(ROOT / "configs/paper.json")
    assert config.experiment.nx == config.experiment.nt == 128
    assert config.experiment.mask_types == ("random", "vertical")
    assert config.experiment.sampling_ratios == (0.3, 0.4, 0.5)
    assert config.experiment.input_snrs_db == (0.0, 5.0, 10.0, 15.0, 20.0)
    assert config.experiment.trials == 100
    assert config.dataset.path == ROOT / "data/rir_NBI_line.h5"
