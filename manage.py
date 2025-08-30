#!/usr/bin/env python

import os
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from app import create_app, db
from config import get_config

#Load environment variable for config
env=os.getenv("APP_CONFIG", "development")
app = create_app(get_config(env))

# Setup Flask-Migrate
migrate = Migrate(app, db)

#Setup Manager for CLI commands
manager = Manager(app)
manager.add_command('db', MigrateCommand)

if __name__ == '__main__':
    manager.run()
