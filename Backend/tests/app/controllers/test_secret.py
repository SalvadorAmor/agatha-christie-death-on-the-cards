import pytest

from app.models.game import GameStatus
from app.models.secret import Secret, SecretType
from app.controllers.secret import UpdateSecretDTO
from tests.conftest import PlayerFactory, GameFactory


@pytest.fixture
def fake_secret():
    return Secret(
        id=1,
        game_id=10,
        owner=5,
        name="Asesino",
        content="Secreto importante",
        revealed=False,
        type= SecretType.MURDERER
    )

def test_get_secret_not_found(mocker, test_client):
    mock_service = mocker.patch('app.controllers.secret.SecretService.read', return_value=None)
    
    response = test_client.get('/api/secret/999')
    
    assert response.status_code == 404
    assert response.json()['detail'] == "Secreto no encontrado"
    
    mock_service.assert_called_once()
    
def test_get_secret_ok(mocker, test_client, fake_secret):
    mock_service = mocker.patch('app.controllers.secret.SecretService.read', return_value=fake_secret)
    response = test_client.get("/api/secret/1")
    
    assert response.status_code == 200
    assert response.json()["id"] == 1
    mock_service.assert_called_once()

def test_patch_secret_not_found_secret(mocker, test_client):
    dto = UpdateSecretDTO(revealed=True)

    mock_secret_service = mocker.patch('app.controllers.secret.SecretService.read', return_value=None)
    response = test_client.patch("/api/secret/1?token=abc", json=dto.model_dump(exclude_none=True))

    assert response.status_code == 404
    assert response.json()['detail'] == "Secreto no encontrado"
    mock_secret_service.assert_called_once()

def test_patch_secret_player_not_found(mocker, test_client, fake_secret):
    dto = UpdateSecretDTO(revealed=True)

    mock_secret_service = mocker.patch('app.controllers.secret.SecretService.read', return_value=fake_secret)
    mock_player_service = mocker.patch('app.controllers.secret.PlayerService.read', return_value=None)
    mock_update = mocker.patch('app.controllers.secret.SecretService.update')

    response = test_client.patch("/api/secret/1?token=abc", json=dto.model_dump(exclude_none=True))

    assert response.status_code == 404
    assert response.json()['detail'] == "Jugador no encontrado"
    mock_secret_service.assert_called_once()
    mock_player_service.assert_called_once()
    mock_update.assert_not_called()

def test_patch_secret_unauthorized_user(mocker, test_client, fake_secret):
    fake_player=PlayerFactory(token="AAA")
    dto = UpdateSecretDTO(revealed=True)
    
    mock_read = mocker.patch('app.controllers.secret.SecretService.read', return_value=fake_secret)
    mock_update = mocker.patch('app.controllers.secret.SecretService.update', return_value=fake_secret)
    mocker.patch('app.controllers.secret.PlayerService.read', return_value=fake_player)
    response = test_client.patch("/api/secret/1?token=ZZZ", json=dto.model_dump(exclude_none=True))

    assert response.status_code == 401
    assert response.json()['detail'] == "Autorizacion invalida"
    
    mock_read.assert_called_once()
    mock_update.assert_not_called()


def test_patch_secret_ok(mocker, test_client, fake_secret):
    fake_player = PlayerFactory(token="abc")
    dto = UpdateSecretDTO(revealed=True)

    update_secret = fake_secret.model_copy()
    update_secret.revealed = True

    mock_read = mocker.patch('app.controllers.secret.SecretService.read', return_value=fake_secret)
    mock_update = mocker.patch('app.controllers.secret.SecretService.update', return_value=update_secret)
    mocker.patch('app.controllers.secret.PlayerService.read', return_value=fake_player)

    response = test_client.patch("/api/secret/1?token=abc", json=dto.model_dump(exclude_none=True))

    data = response.json()
    assert response.status_code == 200
    assert data["id"] == 1
    assert data["revealed"] == True

    mock_read.assert_called_once()
    mock_update.assert_called_once()
    
def test_post_secret_ok(mocker, test_client, fake_secret):
    mocker_service = mocker.patch('app.controllers.secret.SecretService.search', return_value=[fake_secret])
    
    response = test_client.post("/api/secret/search", json={"owner_eq":5})
    
    assert response.status_code == 200
    assert response.json()[0]["owner"] == 5
    
    mocker_service.assert_called_once()
