import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from typing import List, Optional

from alembic.autogenerate import compare_metadata
from alembic.runtime.migration import MigrationContext
from loguru import logger
from sqlalchemy import MetaData
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from sqlalchemy.util import FacadeDict

from settings import settings


@dataclass
class MetadataDifference:
    difference: Optional[List]
    metadata_tables: FacadeDict
    sorted_metadata: Optional[FacadeDict] = None

    def __post_init__(self) -> None:
        metadata_tables_dict = dict(self.metadata_tables)
        sorted_metadata_tables = {}
        for table_name, table in metadata_tables_dict.items():
            comment = table.__dict__.get('comment')
            if comment is not None:
                comment = json.loads(comment)
                delete_table = comment.get('delete_table')
                if not delete_table:
                    table.__dict__['comment'] = json.dumps(comment)
                    sorted_metadata_tables[table_name] = table
                else:
                    continue
            else:
                table.__dict__['comment'] = json.dumps(comment)
                sorted_metadata_tables[table_name] = table

        self.sorted_metadata = FacadeDict(sorted_metadata_tables)


class AlembicHandler:
    def __init__(
        self,
        sql_session: Session,
        sql_client: Engine,
        metadata: MetaData
    ) -> None:
        self._sql_session = sql_session
        self._sql_connection_string: str = settings.sql_connection_string
        self._sql_client = sql_client
        self._metadata = metadata

        self._current_database_name: str = (
            self._sql_connection_string.split('/')[-1].split('?')[0]
        )
        if settings.alembic_debug:
            self._alembic_path = './services/alembic'
        else:
            self._alembic_path = (
                f'{settings.files_root}{self._current_database_name}'
            )

        self._temporary_database_name: str = (
            'temporary_' + self._current_database_name
        )
        self._temporary_database_sql_connection_string: str = (
            self._sql_connection_string.replace(
                self._current_database_name, self._temporary_database_name
            )
        )

    def execute(self) -> FacadeDict:
        self._alembic_setup()
        metadata_difference = self._getting_differences()
        if len(metadata_difference.difference) > 0:
            logger.info(f'Found migrations to accept!')
            self._apply_migrations()
        else:
            logger.info('The application of migrations is not required...')

        return metadata_difference.sorted_metadata

    def _alembic_setup(self) -> None:
        logger.info('Checking the availability of the Alembic environment...')
        availability_alembic = self._check_availability_alembic()
        if availability_alembic:
            logger.info('The Alembic environment is available!')
            return

        if settings.is_first_start:
            self._init_alembic()
            self._create_base_revision()
        else:
            self._init_alembic()
            self._create_temporary_db()
            self._edit_sql_connection_string_for_temporary_database()
            self._create_base_revision()
            self._delete_temporary_database()
            self._edit_sql_connection_string_for_main_database()
            self._alembic_stump_head()

        logger.info(
            'Setting up the Alembic environment and creating the '
            'Base Revision was successful!'
        )

    def _check_availability_alembic(self) -> bool:
        try:
            return 'alembic' in os.listdir(self._alembic_path)
        except FileNotFoundError:
            return self._current_database_name in os.listdir(
                settings.files_root
            )

    def _init_alembic(self) -> None:
        logger.info(
            'Alembic\'s environment has not been found.'
            ' Started the creation of the environment...'
        )
        shutil.copytree(
            './services/alembic/alembic_template/alembic',
            f'{self._alembic_path}/alembic',
            symlinks=False,
            ignore=None,
            copy_function=shutil.copy2,
            ignore_dangling_symlinks=False,
            dirs_exist_ok=True
        )
        shutil.copy2(
            './services/alembic/alembic_template/alembic.ini',
            f'{self._alembic_path}/alembic',
        )
        self._check_availability_versions()
        logger.info('The Alembic environment has been successfully created!')

    def _check_availability_versions(self) -> None:
        if not 'versions' in os.listdir(f'{self._alembic_path}'):
            self._execute_sh_command(
                f'mkdir -p {self._alembic_path}/alembic/versions'
            )

    def _create_temporary_db(self) -> None:
        logger.info(
            'Preparing to create Base Revision. '
            'The creation of a temporary database begins...'
        )
        self._sql_session.execute(
            f'SELECT "CREATE DATABASE {self._temporary_database_name}" '
            f'WHERE NOT EXISTS '
            f'(SELECT FROM pg_database '
            f'WHERE datname = {self._temporary_database_name})\gexec;'
        )
        self._sql_session.commit()
        logger.info(
            'A temporary database has been successfully created!'
        )

    def _edit_sql_connection_string_for_temporary_database(self) -> None:
        with open(f'{self._alembic_path}/alembic/env.py', 'r') as file:
            env_file = file.read()
            env_file = env_file.replace(
                'settings.sql_connection_string',
                f'"{self._temporary_database_sql_connection_string}"'
            )
        with open(f'{self._alembic_path}/alembic/env.py', 'w') as file:
            file.write(env_file)
            file.flush()

        logger.info(
            'The settings for Alembic to connect to it have been '
            'successfully applied!'
        )

    def _create_base_revision(self) -> None:
        logger.info(
            'Starting the creation of the first Base Revision...'
        )
        self._execute_sh_command(
            'alembic revision --autogenerate -m "base revision"',
            'Base Revision has been successfully created!'
        )

    def _delete_temporary_database(self) -> None:
        self._sql_session.execute(
            f'SELECT "DROP DATABASE {self._temporary_database_name}" '
            f'WHERE EXISTS '
            f'(SELECT FROM pg_database '
            f'WHERE datname = {self._temporary_database_name})\gexec;'
        )
        self._sql_session.commit()
        logger.info('Temporary database successfully deleted!')

    def _edit_sql_connection_string_for_main_database(self) -> None:
        with open(f'{self._alembic_path}/alembic/env.py', 'r') as file:
            env_file = file.read()
            env_file = env_file.replace(
                f"{self._temporary_database_sql_connection_string}",
                'settings.sql_connection_string'
            )
            env_file = env_file.replace('"', '')
        with open(f'{self._alembic_path}/alembic/env.py', 'w') as file:
            file.write(env_file)
            file.flush()

        logger.info(
            'Setup for further migrations from existing '
            'database successfully installed!'
        )

    def _alembic_stump_head(self) -> None:
        self._execute_sh_command(
            'alembic stamp head',
            'Base Revision has been successfully applied to '
            'the current database!'
        )

    def _getting_differences(self) -> MetadataDifference:
        logger.info('Checking for the necessary migration...')
        with self._sql_client.connect() as connection:
            migration_context = MigrationContext.configure(connection)
            metadata_difference = compare_metadata(
                migration_context, self._metadata
            )
            connection.close()
        return MetadataDifference(metadata_difference, self._metadata.tables)

    def _apply_migrations(self) -> None:
        version_counter = 0
        for migration in os.listdir(f'{self._alembic_path}/alembic/versions'):
            if migration.endswith('.py'):
                version_counter += 1

        self._execute_sh_command(
            'alembic revision --autogenerate -m '
            f'"Revision {version_counter}"',
            'The migration file was successfully created! '
            'Starting the migrations...'
        )
        if settings.auto_apply_migrations:
            self._execute_sh_command(
                'alembic upgrade head',
                'Migrations successfully completed!'
            )

    @staticmethod
    def _execute_sh_command(
        sh_command: str,
        success_text: Optional[str] = None
    ) -> None:
        try:
            subprocess.run(
                sh_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                # encoding='utf-8',
                shell=True,
            )
            if success_text is not None:
                logger.info(success_text)
        except subprocess.CalledProcessError as exception:
            logger.error(str(exception))
