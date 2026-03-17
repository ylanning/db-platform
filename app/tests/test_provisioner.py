"""Tests for ProvisionerService using fake implementations.

Uses fake Cloud SQL and Secret Manager clients to verify provisioning
logic without calling real GCP APIs.
"""

from unittest.mock import patch

import pytest

from app.models.schemas import ProvisionRequest, RotateCredentialsRequest
from app.services.errors import UpstreamError
from app.services.provisioner import ProvisionerService


class FakeSqlClient:
    """Fake Cloud SQL client for testing."""

    def __init__(self):
        self.databases: list[str] = []
        self.users: dict[str, str] = {}
        self.should_fail = False
        self.fail_on: str | None = None

    def create_database(self, db_name: str) -> None:
        self._maybe_fail("create_database")
        self.databases.append(db_name)

    def delete_database(self, db_name: str) -> None:
        self._maybe_fail("delete_database")
        if db_name in self.databases:
            self.databases.remove(db_name)

    def create_user(self, user_name: str, password: str) -> None:
        self._maybe_fail("create_user")
        self.users[user_name] = password

    def delete_user(self, user_name: str) -> None:
        self._maybe_fail("delete_user")
        self.users.pop(user_name, None)

    def update_user_password(self, user_name: str, password: str) -> None:
        self._maybe_fail("update_user_password")
        self.users[user_name] = password

    def is_upstream_error(self, exc: Exception) -> bool:
        return self.should_fail

    def _maybe_fail(self, method: str) -> None:
        if self.should_fail and (self.fail_on is None or self.fail_on == method):
            raise Exception(f"Fake {method} error")


class FakeSecretManager:
    """Fake Secret Manager service for testing."""

    def __init__(self):
        self.secrets: dict[str, str] = {}
        self.should_fail = False

    def generate_password(self) -> str:
        return "test-password-123"

    def create_or_update_secret(self, db_id: str, value: str) -> str:
        self.secrets[db_id] = value
        return f"projects/test/secrets/dbp-{db_id}-conn"

    def delete_secret(self, db_id: str) -> None:
        if self.should_fail:
            raise Exception("Secret not found")
        self.secrets.pop(db_id, None)


@pytest.fixture
def fake_sql():
    return FakeSqlClient()


@pytest.fixture
def fake_secrets():
    return FakeSecretManager()


@pytest.fixture
def patch_services(fake_sql, fake_secrets):
    """Patch provisioner dependencies with fakes."""
    with patch("app.services.provisioner.CloudPostgresqlAdminClient", return_value=fake_sql), patch(
        "app.services.provisioner.SecretManagerService", return_value=fake_secrets
    ):
        yield


@pytest.fixture
def patch_timeout():
    """Make run_with_timeout call the function directly."""

    async def passthrough(func, *args):
        return func(*args)

    with patch("app.services.provisioner.run_with_timeout", side_effect=passthrough):
        yield


@pytest.mark.asyncio
async def test_provision_creates_db_and_user(fake_sql, fake_secrets, patch_services, patch_timeout):
    """Verify provision creates database, user, and stores connection secret."""
    svc = ProvisionerService()
    req = ProvisionRequest(db_id="mydb", owner="team-backend")

    resp = await svc.provision(req)

    assert resp.db_id == "mydb"
    assert resp.status == "provisioned"
    assert resp.connection_secret_name == "projects/test/secrets/dbp_mydb_conn"
    assert "mydb" in fake_sql.databases
    assert "user_mydb" in fake_sql.users
    assert fake_sql.users["user_mydb"] == "test-password-123"
    assert "mydb" in fake_secrets.secrets


@pytest.mark.asyncio
async def test_provision_upstream_error(fake_sql, fake_secrets, patch_services, patch_timeout):
    """Verify provision raises UpstreamError when Cloud SQL fails."""
    fake_sql.should_fail = True
    fake_sql.fail_on = "create_database"

    svc = ProvisionerService()
    req = ProvisionRequest(db_id="mydb", owner="team-backend")

    with pytest.raises(UpstreamError, match="Failed to provision database"):
        await svc.provision(req)


@pytest.mark.asyncio
async def test_deprovision_deletes_resources(fake_sql, fake_secrets, patch_services, patch_timeout):
    """Verify deprovision removes database, user, and secret."""
    fake_sql.databases.append("mydb")
    fake_sql.users["user_mydb"] = "old-password"
    fake_secrets.secrets["mydb"] = "old-conn-string"

    svc = ProvisionerService()
    req = ProvisionRequest(db_id="mydb", owner="team-backend")

    resp = await svc.deprovision(req)

    assert resp.status == "deprovisioned"
    assert resp.connection_secret_name is None
    assert "mydb" not in fake_sql.databases
    assert "user_mydb" not in fake_sql.users
    assert "mydb" not in fake_secrets.secrets


@pytest.mark.asyncio
async def test_deprovision_continues_on_secret_error(
    fake_sql, fake_secrets, patch_services, patch_timeout
):
    """Verify deprovision completes even if secret deletion fails."""
    fake_secrets.should_fail = True

    svc = ProvisionerService()
    req = ProvisionRequest(db_id="mydb", owner="team-backend")

    resp = await svc.deprovision(req)

    assert resp.status == "deprovisioned"


@pytest.mark.asyncio
async def test_status_returns_db_status(patch_services):
    """Verify status returns current database provisioning state."""
    svc = ProvisionerService()

    resp = await svc.status("mydb")

    assert resp.db_id == "mydb"
    assert resp.status == "provisioned"


@pytest.mark.asyncio
async def test_rotate_credentials_updates_password(
    fake_sql, fake_secrets, patch_services, patch_timeout
):
    """Verify rotate_credentials generates new password and updates secret."""
    fake_sql.users["user_mydb"] = "old-password"

    svc = ProvisionerService()
    req = RotateCredentialsRequest(db_id="mydb")

    resp = await svc.rotate_credentials(req)

    assert resp.status == "rotated"
    assert resp.secret_name == "projects/test/secrets/dbp_mydb_conn"
    assert fake_sql.users["user_mydb"] == "test-password-123"
    assert "mydb" in fake_secrets.secrets


@pytest.mark.asyncio
async def test_rotate_credentials_upstream_error(
    fake_sql, fake_secrets, patch_services, patch_timeout
):
    """Verify rotate_credentials raises UpstreamError when password update fails."""
    fake_sql.should_fail = True
    fake_sql.fail_on = "update_user_password"

    svc = ProvisionerService()
    req = RotateCredentialsRequest(db_id="mydb")

    with pytest.raises(UpstreamError, match="Failed to rotate credentials"):
        await svc.rotate_credentials(req)
