from pathlib import Path

HH_URL = 'https://api.hh.ru/vacancies'

ID_EMPLOYERS_LIST = ['80', '67611',
                     '5390761', '733',
                     '9418714', '599',
                     '3388', '84585',
                     '41862', '3776'
                     ]
PARAM_FILE_NAME = Path(__file__).parent.joinpath('database.ini')

SECTION = 'postgresql'

DATA_BASE_NAME = 'cw_5'
