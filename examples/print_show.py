from sachmis.config import model_api_names, model_uniques
from sachmis.utils import printer

printer.model_table(model_uniques(), model_api_names())
