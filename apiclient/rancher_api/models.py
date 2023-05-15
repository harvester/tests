class UserSpec:
    _data = None

    def __init__(self, password, display_name="", description="",
                 change_pwd=False, enabled=True, permissions=None):
        self.password = password
        self.display_name = display_name
        self.change_pwd = change_pwd
        self.description = description
        self.enabled = enabled

    def to_dict(self, username):
        data = {
            "type": "user",
            "enabled": self.enabled,
            "username": username,
            "mustChangePassword": self.change_pwd,
            "password": self.password
        }

        if self.display_name:
            data['name'] = self.display_name
        if self.description:
            data['description'] = self.description

        return data

    @classmethod
    def from_dict(cls, data):
        obj = cls(**dict(
            display_name=data.get('name'),
            description=data.get('description'),
            change_pwd=data.get('mustChangePassword'),
            enabled=data.get('enabled'),
        ))
        obj._data = data
        return obj
