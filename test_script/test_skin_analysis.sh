export NO_ALBUMENTATIONS_UPDATE=1
source .venv/bin/activate

python -m pytest tests/unit/test_skin_analysis_tools.py -v