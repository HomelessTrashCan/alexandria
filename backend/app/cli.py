import click
from flask import Flask

from backend.app.extensions import db
from backend.app.models import ConfigItemType, FieldDefinition, User
from domain.field_types import FieldType
from domain.roles import Role


def register_cli(app: Flask) -> None:
    @app.cli.command("seed-demo")
    def seed_demo() -> None:
        """Legt ein Demo-Admin-Konto und einen Beispiel-CI-Typ an (idempotent).

        Nuetzlich, solange es noch keine Admin-Oberflaeche fuer Typen/Felder
        und Benutzerverwaltung gibt.
        """
        admin = User.query.filter_by(username="admin").first()
        if admin is None:
            admin = User(
                username="admin",
                first_name="Demo",
                last_name="Admin",
                email="admin@example.com",
                role=Role.ADMIN,
                email_verified=True,
            )
            admin.set_password("ChangeMe123!")
            db.session.add(admin)
            click.echo("Admin-Konto angelegt: admin / ChangeMe123!")
        else:
            click.echo("Admin-Konto existiert bereits.")

        server_type = ConfigItemType.query.filter_by(name="Server").first()
        if server_type is None:
            server_type = ConfigItemType(name="Server", description="Physische oder virtuelle Server")
            db.session.add(server_type)
            db.session.flush()
            db.session.add_all(
                [
                    FieldDefinition(config_item_type_id=server_type.id, name="IP-Adresse", field_type=FieldType.TEXT, required=True, position=1),
                    FieldDefinition(
                        config_item_type_id=server_type.id,
                        name="Betriebssystem",
                        field_type=FieldType.SELECT,
                        options='["Ubuntu", "Windows Server", "Debian"]',
                        position=2,
                    ),
                    FieldDefinition(config_item_type_id=server_type.id, name="RAM (GB)", field_type=FieldType.NUMBER, position=3),
                ]
            )
            click.echo("CI-Typ 'Server' mit 3 Feldern angelegt.")
        else:
            click.echo("CI-Typ 'Server' existiert bereits.")

        db.session.commit()
