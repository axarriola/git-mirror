TEMP_DIR: str = "/server/temp"

LOGGING_CONFIG: dict = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s %(levelname)s: %(message)s'
        },
        'simple': {
            'format': '%(levelname)s: %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'uvicorn.error': {
            'propagate': False,
            'handlers': ['console'],
        },
        'gunicorn.error': {
            'propagate': False,
            'handlers': ['console'],
        },
        'app': {
            'handlers': ['console'],
            'propagate': False,
            'level': 'INFO',
        }
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
