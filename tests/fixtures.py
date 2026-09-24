from telegram_structure_cloner.blueprint import Blueprint


def sample_blueprint() -> dict:
    blueprint = Blueprint.empty()
    blueprint.source = {
        "id": 123,
        "title": "Source Forum",
        "type": "supergroup_forum",
        "is_forum": True,
    }
    blueprint.settings = {
        "about": "Example source",
        "slowmode_seconds": 10,
        "entity_flags": {
            "join_to_send": True,
            "join_request": False,
            "noforwards": False,
        },
    }
    blueprint.permissions = {
        "default_banned_rights": {
            "_": "ChatBannedRights",
            "send_messages": False,
        }
    }
    blueprint.forum = {
        "enabled": True,
        "topics": [
            {
                "id": 1,
                "title": "Announcements",
                "icon_color": 7322096,
                "icon_emoji_id": None,
            }
        ],
    }
    blueprint.configuration_media = {"photo": {"photo_id": 456}}
    blueprint.add_unsupported("invite_links", "Not exported in M1.")
    return blueprint.to_dict()
