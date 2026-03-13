from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.utils.config import get_database_settings

class CloudPostgresqlAdmin:
    def __init__(self) -> None:
        settings = get_database_settings()
        if not settings.project_id or not settings.instance_id:
            raise RuntimeError('Missing project_id or instance_id in database settings')
        self.project_id = settings.project_id
        self.instance_id = settings.instance_id
        self._service = build('sqladmin', 'v1', cache_discovery=False)

    def create_database(self, db_name: str) -> None:
        body = {"name": db_name}
        request = self._service.databases().insert(project=self.project_id, instance=self.instance_id, body=body)
        request.execute()

    def delete_database(self, db_name: str) -> None:
        request = self._service.databases().delete(project=self.project_id, instance=self.instance_id, database=db_name)
        request.execute()

    def create_user(self, user_name: str, password: str) -> None:
        body = {"name": user_name, "password": password}
        request = self._service.users().insert(project=self.project_id, instance=self.instance_id, body=body)
        request.execute()

    def delete_user(self, user_name: str) -> None:
        request = self._service.users().delete(project=self.project_id, instance=self.instance_id, name=user_name, host='%')
        request.execute()

    def create_backup(self, db_name: str) -> str:
        request = self._service.instances().backuprun().insert(project=self.project_id, instance=self.instance_id, body={"description": f"Backup for {db_name}"})
        response = request.execute()
        return str(response.get('id', ''))

    def get_backup_status(self, backup_id: str) -> str:
        request = self._service.instances().backuprun().get(project=self.project_id, instance=self.instance_id, id=backup_id)
        response = request.execute()
        return response.get('status', '')

    def is_not_found(self, exc:Exception) -> bool:
        return isinstance(exc, HttpError) and exc.resp.status == 404