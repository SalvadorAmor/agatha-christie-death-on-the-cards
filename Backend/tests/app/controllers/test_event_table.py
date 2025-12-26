from app.services.event_table import EventTableFilter
from conftest import EventTableFactory

def test_event_table_search(mocker, test_client):
    # Given
    event_table_filter = EventTableFilter(player_id__eq=1, game_id__eq=1, turn_played__eq=1, completed_action__eq=False)
    event_table = EventTableFactory()
    mocker_service = mocker.patch('app.controllers.event_table.EventTableService.search', return_value=[event_table])
    # When
    response = test_client.post('/api/event_table/search', json=event_table_filter.model_dump(mode='json'))
    # Then
    assert response.status_code == 200
    mocker_service.assert_called_once()